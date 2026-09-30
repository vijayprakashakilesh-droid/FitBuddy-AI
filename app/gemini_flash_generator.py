from .config import settings
from .gemini_client import get_gemini_client
from .schemas import NutritionResponse


def generate_nutrition_tip_with_flash(
    goal: str,
    intensity: str
) -> str:

    client = get_gemini_client()

    prompt = f"""
You are FitBuddy's nutrition and recovery assistant.

Fitness goal:
{goal}

Workout intensity:
{intensity}

Give ONE concise, practical nutrition or recovery tip.

The answer should:

- be easy to understand
- be realistic
- support the fitness goal
- avoid extreme dieting
- avoid unsupported medical claims
- mention hydration or balanced nutrition when relevant

Return JSON only in this format:

{{
    "tip": "your concise tip"
}}
"""

    response = client.models.generate_content(
        model = settings.gemini_nutrition_model,
        contents=prompt,
        config={
            "temperature": 0.3,
            "response_mime_type": "application/json",
            "response_schema": NutritionResponse,
        },
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty nutrition response."
        )

    result = NutritionResponse.model_validate_json(
        response.text
    )

    return result.tip