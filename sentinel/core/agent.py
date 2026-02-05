import sys
import json
import os
import shutil

from sentinel.core.config import ConfigManager
from sentinel.core.llm import LLMEngine
from sentinel.core.registry import TOOLS, SYSTEM_PROMPT
from sentinel.core.ui import UI
from sentinel.core.schema import AgentAction
from sentinel.tools import memory_ops
from sentinel.paths import USER_DATA_DIR, DB_PATH, VECTOR_PATH, AUDIT_LOG_PATH as AUDIT_LOG

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

FACTORY_RESET_SCRIPT = os.path.join(SCRIPTS_DIR, "factory_reset.bat")
WIPE_VECTOR_SCRIPT = os.path.join(SCRIPTS_DIR, "wipe_vector.bat")

class SentinelAgent:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.brain = LLMEngine(self.config_manager)
        self.history = []
        self.window_size = self.config_manager.get("memory.window_size", 15)

    def _parse_action(self, text) -> AgentAction | None:
        json_data = None

        try:
            json_data = json.loads(text)
        except:
            start = text.find("{")
            if start == -1:
                return None

            stack = 0
            for i in range(start, len(text)):
                if text[i] == "{":
                    stack += 1
                elif text[i] == "}":
                    stack -= 1
                    if stack == 0:
                        try:
                            json_data = json.loads(text[start:i + 1])
                            break
                        except:
                            return None

        if not json_data:
            return None

        try:
            return AgentAction(**json_data)
        except:
            return None

    def _enforce_memory_limit(self):
        max_msgs = self.window_size * 2
        while len(self.history) > max_msgs:
            if len(self.history) < 2: break
            old_user = self.history.pop(0)
            old_ai = self.history.pop(0)
            try:
                memory_ops.archive_interaction(old_user.get('content', ''), old_ai.get('content', ''))
            except:
                pass

    def process_slash_command(self, user_input):
        if not user_input.startswith("/"): return False
        parts = user_input[1:].split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == "memory":
            if not args:
                UI.print_system(f"Current Context Window: {self.window_size} turns.")
            else:
                try:
                    self.window_size = int(args[0])
                    self.config_manager.set("memory.window_size", self.window_size)
                    self._enforce_memory_limit()
                    UI.print_success(f"Context Window updated to {self.window_size} turns.")
                except:
                    UI.print_error("Invalid number.")
            return True

        if cmd == "wipe":
            if input("⚠️  ARE YOU SURE? This will delete ALL long-term memories. (y/n): ").lower() == 'y':
                UI.print_system("Initiating Wipe...")


                try:
                    from sentinel.core import scheduler
                    scheduler.stop_all_jobs()
                except:
                    pass

                # 2. Release Database Locks
                try:
                    memory_ops.teardown()
                except:
                    pass

                # 3. Delete the specific files
                UI.print_system(f"Wiping data from {USER_DATA_DIR}...")

                # Delete Vector DB Folder
                if os.path.exists(VECTOR_PATH):
                    try:
                        shutil.rmtree(VECTOR_PATH)
                        UI.print_success("Deleted Vector Memory.")
                    except Exception as e:
                        UI.print_error(f"Failed to delete vectors: {e}")

                # Delete SQLite DB
                if os.path.exists(DB_PATH):
                    try:
                        os.remove(DB_PATH)
                        UI.print_success("Deleted Brain Database.")
                    except Exception as e:
                        UI.print_error(f"Failed to delete DB: {e}")

                UI.print_system("Wipe Complete. Restarting Sentinel is recommended.")
                sys.exit(0)

            return True

        if cmd == "factory_reset":
            confirm = input("⚠️ This will DELETE EVERYTHING (Config, Keys, Memories). Type YES to confirm: ")
            if confirm == "YES":
                try:
                    # Teardown everything
                    from sentinel.core import scheduler
                    scheduler.stop_all_jobs()
                    memory_ops.teardown()

                    # Nuke the entire .sentinel folder
                    if os.path.exists(USER_DATA_DIR):
                        shutil.rmtree(USER_DATA_DIR)
                        print(f"✔ Deleted {USER_DATA_DIR}")

                    print("Factory Reset Complete. Sentinel is now fresh.")
                    sys.exit(0)
                except Exception as e:
                    print(f"Reset failed: {e}")
                    print(f"Please manually delete this folder: {USER_DATA_DIR}")
            return True

        if cmd == "status":
            UI.print_agent(
                f"**Provider:** {self.brain.provider.upper()}\n**Model:** {self.brain.model}\n**Window:** {self.window_size} turns\n**Active Memory:** {len(self.history)} messages",
                model=self.brain.model
            )
            return True

        if cmd == "clear":
            self.history = []
            UI.print_success("Short-term memory cleared.")
            return True

        if cmd == "help":
            UI.print_help()
            return True

        if cmd in ["switch", "model"]:
            provider = args[0] if args else "openai"
            model = args[1] if len(args) > 1 else None
            from sentinel.tools import system_ops
            res = system_ops.switch_model(provider, model)
            self.brain.reload_config(verbose=True)
            UI.console.print(res)
            return True

        if cmd == "log":
            if not args:
                state = ConfigManager().get("system.audit_logging", True)
                UI.print_system(f"Logging is currently: {'ON' if state else 'OFF'}")
                return True

            mode = args[0].lower()
            if mode in ["on", "true", "enable"]:
                from sentinel.core.audit import audit
                UI.print_success(audit.toggle(True))
            elif mode in ["off", "false", "disable"]:
                from sentinel.core.audit import audit
                UI.print_success(audit.toggle(False))
            return True

        if cmd == "setkey":
            if len(args) < 2: return False
            self.config_manager.set_key(args[0], args[1])
            self.brain.reload_config()
            UI.print_success("Key updated.")
            return True

        if cmd == "auth":
            from sentinel.auth import fix_authentication
            fix_authentication()
            return True

        if cmd == "config":
            from sentinel.core.setup import setup_wizard
            setup_wizard()
            return True

        return False

    def run_loop(self):
        if self.config_manager.get_key(self.brain.provider):
            UI.print_system("Systems Online. Waiting for input...")

        while True:
            try:
                user_input = UI.get_input()
                if not user_input:
                    continue

                if user_input.lower().strip() in ["exit", "quit"]:
                    sys.exit(0)

                if self.process_slash_command(user_input):
                    continue

                relevant_context = memory_ops.retrieve_relevant_context(user_input)
                current_sys = SYSTEM_PROMPT
                if relevant_context:
                    current_sys += f"\n\n[RECALLED MEMORIES]\n{relevant_context}\n"

                self.history.append({"role": "user", "content": user_input})
                memory_ops.log_activity("chat", user_input)

                for _ in range(5):
                    messages = self.history[-self.window_size * 2:]
                    full_resp = self.brain.query(current_sys, messages)
                    action = self._parse_action(full_resp)

                    if not action:
                        clean = full_resp.replace("```json", "").replace("```", "").strip()

                        if not clean:
                            clean = "I don't have any stored long-term information about you yet."

                        UI.print_agent(clean, model=self.brain.model)

                        if full_resp and full_resp.strip():
                            self.history.append({"role": "assistant", "content": full_resp})
                        break

                    tool, args = action.tool, action.args

                    if tool == "response":
                        text = args.get("text", "").strip()
                        if not text:
                            text = "I don't have any stored long-term information about you yet."

                        UI.print_agent(text, model=self.brain.model)
                        self.history.append({"role": "assistant", "content": action.model_dump_json()})
                        break

                    if tool in TOOLS:
                        UI.print_tool(tool)
                        try:
                            res = TOOLS[tool](**args)

                            if not res or not str(res).strip():
                                res = "No long-term memories stored about you yet."

                            UI.print_result(res)

                            self.history.append({"role": "assistant", "content": action.model_dump_json()})

                            if res and str(res).strip():
                                self.history.append({"role": "user", "content": str(res)})

                        except Exception as e:
                            UI.print_error(f"Tool Error: {e}")
                            self.history.append({"role": "system", "content": f"Error: {e}"})
                    else:
                        break

                self._enforce_memory_limit()

            except KeyboardInterrupt:
                sys.exit(0)
            except Exception as e:
                UI.print_error(f"System Error: {e}")
