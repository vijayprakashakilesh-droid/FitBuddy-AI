import json

from .config import settings
from .gemini_client import get_gemini_client
from .schemas import WorkoutPlan


def generate_workout_gemini(
    name: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str
) -> dict:

    client = get_gemini_client()

    prompt = f"""
You are FitBuddy, an AI fitness planning assistant.

Create a safe, realistic and personalized 7-day beginner-friendly
fitness plan.

User information:

Name: {name}
Age: {age}
Weight: {weight} kg
Fitness goal: {goal}
Workout intensity: {intensity}

Requirements:

1. Create exactly 7 workout days.
2. Each day must have:
   - day
   - focus
   - warmup
   - exercises
   - cooldown
3. Every exercise should contain:
   - name
   - sets when applicable
   - reps when applicable
   - duration when applicable
   - rest when applicable
4. Include recovery/rest days where appropriate.
5. Respect the selected intensity.
6. Do not prescribe dangerous or extreme exercises.
7. Do not diagnose medical conditions.
8. Encourage the user to consult a qualified healthcare professional
   if they have injuries, medical conditions, or significant concerns.

Return ONLY JSON matching the requested schema.
"""

    response = client.models.generate_content(
        model=settings.gemini_workout_model,
        contents=prompt,
        config={
            "temperature": 0.4,
            "response_mime_type": "application/json",
            "response_schema": WorkoutPlan,
        },
    )

    raw = response.text

    if not raw:
        raise RuntimeError(
            "Gemini returned an empty workout response."
        )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini returned invalid JSON."
        ) from exc

    validated = WorkoutPlan.model_validate(data)

    return validated.model_dump()