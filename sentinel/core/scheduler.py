import schedule
import time
import threading
from sentinel.core.llm import LLMEngine

ACTIVE_JOBS = {}


def _job_runner(task_description, agent_config):
    """Runs the background task."""
    print(f"\n[Scheduler] ⏰ Executing background task: {task_description}")

    brain = LLMEngine(agent_config)

    sys_prompt = f"You are a background monitoring agent. Current Task: {task_description}. Output JSON only."

    try:
        response = brain.query(sys_prompt, [])
        print(f"[Scheduler Result]: {response}")
    except Exception as e:
        print(f"[Scheduler Error]: {e}")


def schedule_task(interval_minutes, task_description, agent_config):
    """Schedules a new task."""
    job_id = f"job_{len(ACTIVE_JOBS) + 1}"

    # Schedule the job
    job = schedule.every(int(interval_minutes)).minutes.do(
        _job_runner, task_description, agent_config
    )

    ACTIVE_JOBS[job_id] = job
    return f"✅ Scheduled: '{task_description}' every {interval_minutes}m. (ID: {job_id})"


def stop_all_jobs():
    """
    EMERGENCY STOP: Clears all background schedules.
    """
    count = len(ACTIVE_JOBS)
    schedule.clear()
    ACTIVE_JOBS.clear()
    return f"🛑 STOPPED {count} background jobs. Scheduler is now empty."


def start_scheduler_service():
    """Starts the loop in a background thread."""

    def loop():
        while True:
            schedule.run_pending()
            time.sleep(1)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    print(">> System: Scheduler Service Online.")