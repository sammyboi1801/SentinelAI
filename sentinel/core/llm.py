from openai import OpenAI
import anthropic
from sentinel.core.ui import UI
from sentinel.core.audit import audit
import time

try:
    from groq import Groq
except ImportError:
    Groq = None


class LLMEngine:
    def __init__(self, config_manager, verbose=True):
        """
        Args:
            verbose (bool): If True, prints "Brain Loaded" on init.
                            Set False for background tasks.
        """
        self.cfg_manager = config_manager
        self.provider = None
        self.model = None
        self.api_key = None
        self.reload_config(verbose=verbose)

    def reload_config(self, verbose=False):
        """Reloads settings and credentials from the config manager."""
        settings = self.cfg_manager.load()
        llm_settings = settings.get("llm", {})

        self.provider = llm_settings.get("provider", "openai").lower()
        self.model = llm_settings.get("model", "gpt-4o")
        self.api_key = self.cfg_manager.get_key(self.provider)

        if verbose:
            is_ready = self.api_key is not None or self.provider == "ollama"
            if is_ready:
                pass

    def stream_query(self, system_prompt, history):
        self.reload_config(verbose=False)

        if not self.api_key and self.provider != "ollama":
            yield f"\n[bold red]Error:[/bold red] No API key found for '{self.provider}'.\n"
            yield f"Please run: [cyan]/setkey {self.provider} YOUR_KEY_HERE[/cyan]"
            return

        messages = []
        for msg in history:
            # Anthropic hates "system" role in messages list
            if msg["role"] != "system":
                messages.append(msg)

        try:
            if self.provider == "groq":
                if not Groq:
                    yield "Error: 'groq' library not installed. Run 'pip install groq'."
                    return
                # Groq (via OpenAI client) EXPECTS system message in list
                groq_msgs = [{"role": "system", "content": system_prompt}] + history

                client = Groq(api_key=self.api_key)
                stream = client.chat.completions.create(
                    messages=groq_msgs, model=self.model, temperature=0.1, stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

            elif self.provider == "openai":
                # OpenAI EXPECTS system message in list
                openai_msgs = [{"role": "system", "content": system_prompt}] + history

                client = OpenAI(api_key=self.api_key)
                stream = client.chat.completions.create(
                    model=self.model, messages=openai_msgs, temperature=0.1, stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

            elif self.provider == "anthropic":
                # --- ANTHROPIC SPECIFIC FIX ---
                # Pass 'system' as a top-level parameter
                client = anthropic.Anthropic(api_key=self.api_key)

                with client.messages.stream(
                        max_tokens=4096,
                        system=system_prompt,
                        messages=messages,
                        model=self.model
                ) as stream:
                    for text in stream.text_stream:
                        yield text

            elif self.provider == "ollama":
                # Ollama likes system message in list
                ollama_msgs = [{"role": "system", "content": system_prompt}] + history
                import requests
                import json
                payload = {"model": self.model, "messages": ollama_msgs, "stream": True}
                with requests.post("http://localhost:11434/api/chat", json=payload, stream=True) as r:
                    for line in r.iter_lines():
                        if line:
                            body = json.loads(line)
                            if "message" in body and "content" in body["message"]:
                                yield body["message"]["content"]

        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "invalid_api_key" in error_str:
                yield f"\n[bold red]🔑 Authentication Failed:[/bold red] The API key for [cyan]{self.provider.upper()}[/cyan] is invalid or expired."
            elif "429" in error_str or "rate_limit_exceeded" in error_str:
                yield f"\n[bold yellow]⏳ Rate Limit Reached:[/bold yellow] {self.provider.upper()} is busy."
            else:
                yield f"\n[bold red]System Error ({self.provider}):[/bold red] {error_str}"

    def query(self, system_prompt, history):
        start_time = time.time()
        full_response = ""
        for token in self.stream_query(system_prompt, history):
            full_response += token

        duration = (time.time() - start_time) * 1000

        audit.log_event(
            event_type="LLM_QUERY",
            provider=self.provider,
            model=self.model,
            input_data=[{"role": "system", "content": system_prompt}] + history,
            output_data=full_response,
            duration_ms=duration
        )

        return full_response