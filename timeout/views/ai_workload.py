# timeout/ai_workload.py
from django.conf import settings

def get_ai_workload_warning(events):
    """
    Takes a list of events and generates a workload warning message using OpenAI.
    Returns a string message, or None if AI fails.
    """
    if not events or not settings.OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Prepare a simple summary of today's events
        event_summaries = [
            f"- {e['title']} from {e['start_datetime'].strftime('%H:%M')} to {e['end_datetime'].strftime('%H:%M')}"
            if isinstance(e, dict) else
            f"- {e.title} from {e.start_datetime.strftime('%H:%M')} to {e.end_datetime.strftime('%H:%M')}"
            for e in events
        ]

        system_prompt = (
            "You are a helpful assistant. Analyze the user's daily events and determine "
            "if they are overloaded today or have potential scheduling conflicts. "
            "Return a concise warning like 'High workload today: 5 events scheduled' or "
            "'Moderate workload, 2 events with minor overlap'."
        )

        user_prompt = "Today's events:\n" + "\n".join(event_summaries)

        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=60,
        )

        return response.choices[0].message.content.strip()
    except Exception:
        return None