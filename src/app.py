"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
import os
from pathlib import Path
from threading import Lock

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

ADMIN_TOKEN = os.getenv("MERGINGTON_ADMIN_TOKEN")
activity_lock = Lock()


class ActivityInput(BaseModel):
    description: str = Field(min_length=1)
    schedule: str = Field(min_length=1)
    max_participants: int = Field(gt=0)


def require_admin(x_admin_token: str | None = Header(default=None)):
    if not ADMIN_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Organizer authentication is not configured",
        )
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Organizer authentication required")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "status": "active",
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "status": "active",
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "status": "active",
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "status": "active",
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "status": "active",
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "status": "active",
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "status": "active",
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "status": "active",
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "status": "active",
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return {
        name: activity
        for name, activity in activities.items()
        if activity.get("status", "active") == "active"
    }


@app.post("/admin/activities/{activity_name}", status_code=201,
          dependencies=[Depends(require_admin)])
def create_activity(activity_name: str, activity_input: ActivityInput):
    with activity_lock:
        if activity_name in activities:
            raise HTTPException(status_code=409, detail="Activity already exists")
        activities[activity_name] = {
            **activity_input.model_dump(),
            "status": "draft",
            "participants": [],
        }
    return activities[activity_name]


@app.put("/admin/activities/{activity_name}",
         dependencies=[Depends(require_admin)])
def update_activity(activity_name: str, activity_input: ActivityInput):
    with activity_lock:
        if activity_name not in activities:
            raise HTTPException(status_code=404, detail="Activity not found")
        activity = activities[activity_name]
        if activity_input.max_participants < len(activity["participants"]):
            raise HTTPException(
                status_code=400,
                detail="Capacity cannot be lower than current participants",
            )
        activity.update(activity_input.model_dump())
    return activity


@app.patch("/admin/activities/{activity_name}/status",
           dependencies=[Depends(require_admin)])
def set_activity_status(activity_name: str, status: str):
    if status not in {"draft", "active", "archived"}:
        raise HTTPException(status_code=400, detail="Invalid activity status")
    with activity_lock:
        if activity_name not in activities:
            raise HTTPException(status_code=404, detail="Activity not found")
        activities[activity_name]["status"] = status
    return activities[activity_name]


@app.delete("/admin/activities/{activity_name}",
            dependencies=[Depends(require_admin)])
def delete_activity(activity_name: str):
    with activity_lock:
        if activity_name not in activities:
            raise HTTPException(status_code=404, detail="Activity not found")
        del activities[activity_name]
    return {"message": f"Deleted {activity_name}"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    with activity_lock:
        if activity.get("status", "active") != "active":
            raise HTTPException(status_code=404, detail="Activity not found")

        # Validate student is not already signed up.
        if email in activity["participants"]:
            raise HTTPException(
                status_code=400,
                detail="Student is already signed up"
            )

        if len(activity["participants"]) >= activity["max_participants"]:
            raise HTTPException(status_code=409, detail="Activity is full")

        activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
