import platform
import datetime
import threading
import os
from sentinel.core.config import ConfigManager
import schedule
from sentinel.tools.smart_index import smart_find

from sentinel.tools import (
    apps, browser, clock, email_ops, file_ops, indexer, notes, office,
    system_ops, navigation, flights, sql_index, desktop, vision, audio,
    context, calendar_ops, memory_ops, weather_ops, organizer, macros,
    factory, installer
)
from sentinel.core import scheduler, cognitive

CURRENT_OS = platform.system()
OS_VERSION = platform.release()
NOW = datetime.datetime.now()

cfg = ConfigManager()
settings = cfg.load() if cfg.exists() else {}


def initialize_tools():
    print("\n[System] 🔄 Initializing File Systems...")

    t1 = threading.Thread(target=sql_index.build_index, args=(True,))
    t1.daemon = True
    t1.start()

    schedule.every(60).minutes.do(sql_index.build_index, silent=True)
    scheduler.start_scheduler_service()

def ask_permission(tool_name, func, **kwargs):
    """
    Intervention Layer: Pauses execution to ask the user for confirmation.
    """
    print(f"\n[🛑 SECURITY ALERT] Agent wants to run: {tool_name}")
    # Hide agent_config from display
    display_args = {k: v for k, v in kwargs.items() if k != 'agent_config'}
    print(f"   Arguments: {display_args}")

    choice = input(f"   >>> Allow this? (y/N): ").lower()

    if choice == 'y':
        try:
            log_args = {k: v for k, v in kwargs.items() if k != 'agent_config'}
            memory_ops.log_activity(tool_name, str(log_args))
        except:
            pass
        return func(**kwargs)
    else:
        return f"Action '{tool_name}' denied by user."


def safe_run_cmd(cmd):
    """Extra guardrails for terminal commands."""
    dangerous_keywords = ["del", "rm", "format", "shutdown", "reboot", ">"]
    if any(k in cmd.lower() for k in dangerous_keywords):
        print(f"\n[⚠️ HIGH RISK] Command contains dangerous keywords: '{cmd}'")
        confirm = input("   >>> TYPE 'CONFIRM' TO EXECUTE: ")
        if confirm != "CONFIRM":
            return "Safety block: Command denied."

    return ask_permission("run_cmd", system_ops.run_cmd, cmd=cmd)


def draft_code(filename, content):
    """Safe Coding: Writes to 'drafts/' instead of executing."""
    safe_path = os.path.join("drafts", os.path.basename(filename))
    try:
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Code saved to '{safe_path}'. Review it manually before running."
    except Exception as e:
        return f"Error drafting code: {e}"

TOOLS = {
    # System & Apps
    "open_app": apps.open_app,
    "close_app": lambda **k: ask_permission("close_app", apps.close_app, **k),
    "run_cmd": safe_run_cmd,
    "get_clipboard": system_ops.get_clipboard,
    "kill_process": lambda **k: ask_permission("kill_process", system_ops.kill_process, **k),
    "get_system_stats": system_ops.get_system_stats,
    "play_music": apps.play_music,

    # Browser
    "search_web": browser.search_web,
    "open_url": browser.open_url,
    "read_webpage": browser.read_webpage,

    # Files & Index
    "read_file": file_ops.read_file,
    "write_file": file_ops.write_file,
    "draft_code": draft_code,
    "build_index": indexer.build_index,
    "search_index": indexer.search_index,
    "find_file": sql_index.search_db,
    "rebuild_memory": sql_index.build_index,
    "organize_files": lambda **k: ask_permission("organize_files", organizer.organize_files, **k),
    "bulk_rename": lambda **k: ask_permission("bulk_rename", organizer.bulk_rename, **k),

    # Office & Documents
    "create_word": office.create_word,
    "create_excel": office.create_excel,
    "append_excel": office.append_excel,
    "read_excel": office.read_excel,
    "create_document": factory.create_document,

    # Time & Email
    "get_time": clock.get_time,
    "set_timer": clock.set_timer,
    "set_alarm": clock.set_alarm,
    "send_email": lambda **k: ask_permission("send_email", email_ops.send_email, **k),
    "read_emails": email_ops.read_emails,

    # Memory & Cognitive
    "add_note": notes.add_note,
    "list_notes": notes.list_notes,
    "store_fact": memory_ops.store_fact,
    "delete_fact": memory_ops.delete_fact,
    "retrieve_knowledge": lambda **kwargs: memory_ops.retrieve_relevant_context(
        query=" ".join([str(v) for v in kwargs.values() if v])
    ),

    "reflect_on_day": memory_ops.reflect_on_day,
    "daily_briefing": lambda: cognitive.get_daily_briefing(cfg),

    # Navigation & Flights
    "geocode": navigation.geocode,
    "reverse_geocode": navigation.reverse_geocode,
    "calc_distance": navigation.calc_distance,
    "get_directions": navigation.get_directions,
    "find_nearby": navigation.find_nearby,
    "search_flights": flights.search_flights,

    # Desktop Control
    "set_volume": desktop.set_volume,
    "set_brightness": desktop.set_brightness,
    "minimize_window": desktop.minimize_window,
    "maximize_window": desktop.maximize_window,
    "type_text": desktop.type_text,
    "speak": desktop.speak,

    # Perception
    "listen": audio.listen,
    "analyze_screen": vision.analyze_screen,
    "capture_webcam": vision.capture_webcam,
    "get_active_app": context.get_active_app,
    "get_weather": weather_ops.get_current_weather,

    # Autonomy (Scheduler)
    "schedule_task": lambda interval, task: ask_permission(
        "schedule_task",
        scheduler.schedule_task,
        interval_minutes=interval,
        task_description=task,
        agent_config=settings
    ),
    "stop_tasks": scheduler.stop_all_jobs,

    # Calendar
    "list_calendar_events": calendar_ops.list_upcoming_events,
    "get_calendar_range": calendar_ops.get_events_in_frame,
    "create_calendar_event": lambda **k: ask_permission("create_event", calendar_ops.create_event, **k),
    "calendar_quick_add": lambda **k: ask_permission("quick_add", calendar_ops.quick_add, **k),

    # Macros & Installers
    "run_macro": macros.run_macro,
    "install_software": installer.install_software,
    "list_installed_apps": installer.list_installed,

    "find_my_file": lambda query: "\n".join(smart_find(query)),

}

# --- PROMPT ---
SYSTEM_PROMPT = f"""
You are **Sentinel**, an autonomous AI Operating System layer.
Your role is to translate user intent into safe, deterministic system actions.

System Context:
- OS: {CURRENT_OS} {OS_VERSION}
- Current Time: {NOW}

USER PROFILE:
Name: {cfg.get("user.name")}
Location: {cfg.get("user.location")}

CORE BEHAVIOR:
1. You operate in **command mode**, not conversation mode.
2. Your output must be valid JSON for tool execution.
3. Never explain tools unless explicitly asked.
4. Prefer direct action over discussion.

DECISION POLICY:
- If the user intent is ambiguous → ask a minimal clarifying question.
- If the intent maps to a tool → call it immediately.
- If no tool fits → respond with {{"tool": "response", "args": {{"text": "..."}}}}

CRITICAL SAFETY PROTOCOLS:
1. **NO CHITCHAT**: Output JSON only.
2. **HUMAN-IN-THE-LOOP**:
   - Killing processes
   - Running shell commands
   - Sending emails
   - Scheduling tasks
   
3. **CODE SAFETY**:
   - NEVER execute generated code.
   - ALWAYS use `draft_code`.

MEMORY PROTOCOLS:
1. **Active Listening**:
   If the user reveals a stable preference, habit, goal, or identity:
   → Immediately call `store_fact`.

2. **Context Recall**:
   Before solving complex tasks:
   → Check `retrieve_knowledge` or `list_notes`.

3. **Persistence Triggers**:
   Phrases like:
   - "remember this"
   - "from now on"
   - "in the future"
   Must result in memory storage.

AUTONOMY RULES:
- Background agents must be:
  - Explicitly approved
  - Clearly scoped
  - Easy to stop

AVAILABLE TOOLS:
(only use tools listed below, no hallucinations)

**INSTRUCTION:** Do NOT ask for permission in the chat. Call the tool directly. The system will handle the approval step.

SYSTEM & APPS:
- open_app(name): launch an application
- close_app(name): close a running application [REQUIRES APPROVAL]
- run_cmd(cmd): run shell command [REQUIRES APPROVAL]
- get_clipboard(): get clipboard text
- kill_process(name): kill a running process [REQUIRES APPROVAL]
- get_system_stats(): CPU, RAM, battery status
- play_music(song_name): play music

BROWSER:
- search_web(query): search internet
- open_url(url): open website
- read_webpage(url): extract webpage text

FILES & INDEX:
- read_file(path): read file
- write_file(path, content): write file
- draft_code(filename, content): save code safely
- build_index(verbose): scan filesystem
- search_index(query): semantic file search
- find_file(query): exact filename search (SQL, literal)
- find_my_file(query): semantic + recency search (vague queries like "that pdf I edited last week")
- rebuild_memory(verbose): rebuild index
- organize_files(directory, strategy): organize files [REQUIRES APPROVAL]
- bulk_rename(directory, pattern, replace_with): rename files [REQUIRES APPROVAL]

OFFICE & DOCUMENTS:
- create_word(filename, content)
- create_excel(filename, data_list)
- append_excel(filename, data_list)
- read_excel(filename)
- create_document(filename, blocks)

TIME & EMAIL:
- get_time()
- set_timer(seconds)
- set_alarm(time_str)
- send_email(to, subject, body, html=(true/false)) [REQUIRES APPROVAL]
- read_emails(limit)

MEMORY & COGNITIVE:
- add_note(category, content)
- list_notes(category)
- store_fact(subject, predicate, obj)
- delete_fact(subject, predicate, obj): remove stored memory facts
- retrieve_knowledge(subject, predicate, obj)
- reflect_on_day(date_str)
- daily_briefing()

NAVIGATION & FLIGHTS:
- geocode(address)
- reverse_geocode(lat, lon)
- calc_distance(origin, destination, mode)
- get_directions(origin, destination)
- find_nearby(lat, lon, type)
- search_flights(departure_id, arrival_id, date)

DESKTOP CONTROL:
- set_volume(level)
- set_brightness(level)
- minimize_window(app_name)
- maximize_window(app_name)
- type_text(text)
- speak(text)
- focus_window(app_name): brings window to the front

PERCEPTION:
- listen(timeout)
- analyze_screen(prompt)
- capture_webcam(prompt)
- get_active_app()
- get_weather(location): retrieve the current location first/else ask user if cannot find

AUTONOMY:
- schedule_task(interval, task) [REQUIRES APPROVAL]
- stop_tasks()

CALENDAR:
- list_calendar_events(max_results)
- get_calendar_range(start_iso, end_iso)
- create_calendar_event(summary, start_time, duration_mins, description) [REQUIRES APPROVAL]
- calendar_quick_add(text) [REQUIRES APPROVAL]

MACROS & INSTALLERS:
- run_macro(name)
- install_software(package_list): install Windows apps via winget
- list_installed_apps(): list installed applications


FINAL RULE:
Your response MUST ALWAYS be one of:
1. Tool call JSON
2. {{"tool": "response", "args": {{"text": "..."}}}}

NO prose. NO markdown. NO explanations.
"""