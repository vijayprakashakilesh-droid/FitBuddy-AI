import json

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .gemini_flash_generator import (
    generate_nutrition_tip_with_flash,
)
from .gemini_generator import generate_workout_gemini
from .models import User
from .schemas import FeedbackRequest, UserInput
from .updated_plan import update_workout_plan


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "error": None
        }
    )


# ---------------------------------------------------------
# GENERATE WORKOUT - HTML FORM
# ---------------------------------------------------------

@router.post(
    "/generate-workout",
    response_class=HTMLResponse
)
def generate_workout(
    request: Request,

    user_id: str = Form(...),
    name: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),

    db: Session = Depends(get_db),
):

    try:
        user_input = UserInput(
            user_id=user_id.strip(),
            name=name.strip(),
            age=age,
            weight=weight,
            goal=goal.strip(),
            intensity=intensity.strip().lower()
        )

        workout = generate_workout_gemini(
            name=user_input.name,
            age=user_input.age,
            weight=user_input.weight,
            goal=user_input.goal,
            intensity=user_input.intensity
        )

        nutrition_tip = (
            generate_nutrition_tip_with_flash(
                goal=user_input.goal,
                intensity=user_input.intensity
            )
        )

        existing_user = db.scalar(
            select(User).where(
                User.user_id == user_input.user_id
            )
        )

        if existing_user:

            existing_user.name = user_input.name
            existing_user.age = user_input.age
            existing_user.weight = user_input.weight
            existing_user.goal = user_input.goal
            existing_user.intensity = user_input.intensity
            existing_user.original_plan = json.dumps(
                workout,
                ensure_ascii=False,
                indent=2
            )
            existing_user.updated_plan = None
            existing_user.nutrition_tip = nutrition_tip
            existing_user.feedback = None

            db.commit()

            user = existing_user

        else:

            user = User(
                user_id=user_input.user_id,
                name=user_input.name,
                age=user_input.age,
                weight=user_input.weight,
                goal=user_input.goal,
                intensity=user_input.intensity,
                original_plan=json.dumps(
                    workout,
                    ensure_ascii=False,
                    indent=2
                ),
                nutrition_tip=nutrition_tip
            )

            db.add(user)
            db.commit()
            db.refresh(user)

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "workout_plan": workout,
                "nutrition_tip": nutrition_tip,
                "updated": False,
                "error": None
            }
        )

    except ValueError as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(exc)
            },
            status_code=400
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(exc)
            },
            status_code=500
        )


# ---------------------------------------------------------
# FEEDBACK UPDATE
# ---------------------------------------------------------

@router.post(
    "/submit-feedback",
    response_class=HTMLResponse
)
def submit_feedback(
    request: Request,

    user_id: str = Form(...),
    feedback: str = Form(...),

    db: Session = Depends(get_db),
):

    user = db.scalar(
        select(User).where(
            User.user_id == user_id.strip()
        )
    )

    if not user:

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": None,
                "workout_plan": None,
                "nutrition_tip": None,
                "updated": False,
                "error": "User ID was not found."
            },
            status_code=404
        )

    try:

        request_data = FeedbackRequest(
            user_id=user_id.strip(),
            feedback=feedback.strip()
        )

        updated_plan = update_workout_plan(
            original_plan=user.original_plan,
            feedback=request_data.feedback,
            goal=user.goal,
            intensity=user.intensity
        )

        user.updated_plan = json.dumps(
            updated_plan,
            ensure_ascii=False,
            indent=2
        )

        user.feedback = request_data.feedback

        db.commit()
        db.refresh(user)

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "workout_plan": updated_plan,
                "nutrition_tip": user.nutrition_tip,
                "updated": True,
                "error": None
            }
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "workout_plan": None,
                "nutrition_tip": user.nutrition_tip,
                "updated": False,
                "error": str(exc)
            },
            status_code=500
        )


# ---------------------------------------------------------
# ADMIN - VIEW USERS
# ---------------------------------------------------------

@router.get(
    "/view-all-users",
    response_class=HTMLResponse
)
def view_all_users(
    request: Request,
    db: Session = Depends(get_db)
):

    users = db.scalars(
        select(User).order_by(
            User.created_at.desc()
        )
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "users": users
        }
    )


# ---------------------------------------------------------
# ADMIN - DELETE USER
# ---------------------------------------------------------

@router.post("/delete-user/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db)
):

    user = db.scalar(
        select(User).where(
            User.user_id == user_id
        )
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    db.delete(user)
    db.commit()

    return RedirectResponse(
        url="/view-all-users",
        status_code=303
    )


# =========================================================
# JSON API
# =========================================================

@router.post("/api/generate-workout")
def api_generate_workout(
    data: UserInput,
    db: Session = Depends(get_db)
):

    workout = generate_workout_gemini(
        name=data.name,
        age=data.age,
        weight=data.weight,
        goal=data.goal,
        intensity=data.intensity
    )

    nutrition_tip = (
        generate_nutrition_tip_with_flash(
            goal=data.goal,
            intensity=data.intensity
        )
    )

    user = db.scalar(
        select(User).where(
            User.user_id == data.user_id
        )
    )

    if user:

        user.name = data.name
        user.age = data.age
        user.weight = data.weight
        user.goal = data.goal
        user.intensity = data.intensity
        user.original_plan = json.dumps(
            workout,
            ensure_ascii=False
        )
        user.updated_plan = None
        user.nutrition_tip = nutrition_tip
        user.feedback = None

    else:

        user = User(
            user_id=data.user_id,
            name=data.name,
            age=data.age,
            weight=data.weight,
            goal=data.goal,
            intensity=data.intensity,
            original_plan=json.dumps(
                workout,
                ensure_ascii=False
            ),
            nutrition_tip=nutrition_tip
        )

        db.add(user)

    db.commit()

    return {
        "success": True,
        "user_id": data.user_id,
        "workout_plan": workout,
        "nutrition_tip": nutrition_tip
    }


@router.post("/api/submit-feedback")
def api_submit_feedback(
    data: FeedbackRequest,
    db: Session = Depends(get_db)
):

    user = db.scalar(
        select(User).where(
            User.user_id == data.user_id
        )
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    updated_plan = update_workout_plan(
        original_plan=user.original_plan,
        feedback=data.feedback,
        goal=user.goal,
        intensity=user.intensity
    )

    user.updated_plan = json.dumps(
        updated_plan,
        ensure_ascii=False
    )

    user.feedback = data.feedback

    db.commit()

    return {
        "success": True,
        "user_id": data.user_id,
        "updated_plan": updated_plan
    }


@router.get("/api/users")
def api_users(
    db: Session = Depends(get_db)
):

    users = db.scalars(
        select(User).order_by(
            User.created_at.desc()
        )
    ).all()

    return {
        "count": len(users),
        "users": [
            {
                "user_id": user.user_id,
                "name": user.name,
                "age": user.age,
                "weight": user.weight,
                "goal": user.goal,
                "intensity": user.intensity,
                "created_at": user.created_at.isoformat()
            }
            for user in users
        ]
    }


@router.get("/health")
def health_check():

    return {
        "status": "ok",
        "application": "FitBuddy"
    }