from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class UserInput(BaseModel):
    user_id: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=20, lt=400)

    goal: str = Field(
        min_length=2,
        max_length=100
    )

    intensity: str

    @field_validator("intensity")
    @classmethod
    def validate_intensity(cls, value: str):
        value = value.lower().strip()

        allowed = {
            "low",
            "medium",
            "high"
        }

        if value not in allowed:
            raise ValueError(
                "Intensity must be low, medium or high."
            )

        return value


class FeedbackRequest(BaseModel):
    user_id: str
    feedback: str = Field(
        min_length=3,
        max_length=2000
    )


class Exercise(BaseModel):
    name: str
    sets: Optional[str] = None
    reps: Optional[str] = None
    duration: Optional[str] = None
    rest: Optional[str] = None


class WorkoutDay(BaseModel):
    day: str
    focus: str
    warmup: str
    exercises: List[Exercise]
    cooldown: str


class WorkoutPlan(BaseModel):
    title: str
    goal: str
    intensity: str
    days: List[WorkoutDay]


class NutritionResponse(BaseModel):
    tip: str