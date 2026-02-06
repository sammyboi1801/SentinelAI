import datetime
from sentinel.core.llm import LLMEngine
from sentinel.tools import calendar_ops, weather_ops, memory_ops, notes, email_ops


def get_daily_briefing(config_manager):
    """
    The 'Brain Boot' sequence.
    Gathers context -> Sends to LLM -> Returns Daily Briefing.
    """
    print("🧠 Gathering Daily Context...")

    # 1. Get Date/Time
    now = datetime.datetime.now()
    date_str = now.strftime("%A, %B %d")

    # 2. Get Weather
    settings = config_manager.load()
    location = "New York"

    if "weather" in settings and "location" in settings["weather"]:
        location = settings["weather"]["location"]
    elif "location" in settings:
        location = settings["location"]

    try:
        weather = weather_ops.get_current_weather(location)
    except Exception as e:
        weather = f"Weather unavailable ({e})."

    # 3. Get Calendar (Next 24h)
    try:
        cal_events = calendar_ops.list_upcoming_events(max_results=8)
    except Exception:
        cal_events = "Calendar access unavailable."

    # 4. Get Recent Emails
    try:
        emails = email_ops.read_emails(limit=8)
    except Exception:
        emails = "Email access unavailable."

    # 5. Get Todo List
    try:
        todos = notes.list_notes("todo")
    except Exception:
        todos = "No notes found."

    # 6. Get Yesterday's Reflection
    try:
        yesterday = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        history = memory_ops.reflect_on_day(yesterday)
    except Exception:
        history = "Memory unavailable."

    # 7. Synthesis Prompt
    context = f"""
        DATE: {date_str}
        LOCATION: {location}
        
        WEATHER:
        {weather}
        
        CALENDAR:
        {cal_events}
        
        RECENT EMAILS:
        {emails}
        
        PENDING TASKS:
        {todos}
        
        YESTERDAY'S HISTORY:
        {history}
    """

    sys_prompt = (
        "You are Sentinel, a proactive Chief of Staff. "
        "Summarize this context into a high-level Daily Briefing. "
        "1. Highlight immediate calendar priorities. "
        "2. Mention important or urgent emails. "
        "3. Note the weather if it impacts travel. "
        "4. Remind me of unfinished tasks. "
        "5. Briefly recall where we left off yesterday. "
        "Be concise, strategic, and motivating."
    )

    brain = LLMEngine(config_manager)

    if not brain.api_key and brain.provider != "ollama":
        return f"⚠️ Briefing skipped: No API key for {brain.provider.upper()}."

    report = brain.query(sys_prompt, [{"role": "user", "content": context}])
    return report
