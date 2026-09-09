# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Enforce activity capacity on the server
- Manage activities and publish their lifecycle state as an organizer

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   export MERGINGTON_ADMIN_TOKEN="replace-with-a-secret"
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |

Organizer activity management endpoints require the `X-Admin-Token` header. New
activities start as drafts and become visible to students after an organizer
sets their status to `active`:

- `POST /admin/activities/{activity_name}` - create an activity
- `PUT /admin/activities/{activity_name}` - edit an activity
- `PATCH /admin/activities/{activity_name}/status?status=active|draft|archived`
- `DELETE /admin/activities/{activity_name}` - delete an activity

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
