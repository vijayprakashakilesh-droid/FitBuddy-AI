from typing import Any, Optional

from .gemini_client import get_gemini_client
from .config import settings
from .schemas import WorkoutPlan


def update_workout_plan(
    original_plan: dict[str, Any],
    feedback: str,
    goal: Optional[str] = None,
    intensity: Optional[str] = None,
    age: Optional[int] = None,
    weight: Optional[float] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Update an existing workout plan based on user feedback.
    """

    client = get_gemini_client()

    prompt = f"""
You are FitBuddy, an AI fitness planning assistant.

Update the user's existing workout plan based on their feedback.

USER INFORMATION
Age: {age if age is not None else "Not provided"}
Weight: {weight if weight is not None else "Not provided"} kg
Fitness Goal: {goal if goal else "Not provided"}
Workout Intensity: {intensity if intensity else "Not provided"}

ORIGINAL WORKOUT PLAN:
{original_plan}

USER FEEDBACK:
{feedback}

INSTRUCTIONS:
1. Modify the workout plan according to the user's feedback.
2. Keep exercises safe and realistic.
3. Preserve useful parts of the original plan.
4. Make changes relevant to the user's fitness goal.
5. Do not recommend dangerous or extreme exercises.
6. Return ONLY valid JSON matching the WorkoutPlan schema.
"""

    response = client.models.generate_content(
        model=settings.gemini_workout_model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": WorkoutPlan,
        },
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response while updating the workout plan."
        )

    updated_plan = WorkoutPlan.model_validate_json(response.text)

    return updated_plan.model_dump()