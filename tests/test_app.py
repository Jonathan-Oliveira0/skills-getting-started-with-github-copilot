from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


INITIAL_ACTIVITIES = deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def isolate_activities(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(INITIAL_ACTIVITIES))


@pytest.fixture
def client():
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert activities["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_signup_adds_participant(client):
    activity = "Soccer Team"
    email = "student@mergington.edu"

    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in app_module.activities[activity]["participants"]


def test_signup_rejects_duplicate_participant(client):
    activity = "Soccer Team"
    email = "student@mergington.edu"
    signup_url = f"/activities/{activity}/signup"

    first_response = client.post(signup_url, params={"email": email})
    duplicate_response = client.post(signup_url, params={"email": email})

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 400
    assert duplicate_response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert app_module.activities[activity]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_participant_removes_signup(client):
    activity = "Chess Club"
    email = "michael@mergington.edu"

    response = client.delete(
        f"/activities/{activity}/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity}"}
    assert email not in app_module.activities[activity]["participants"]


def test_remove_participant_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Activity/participants",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_participant_rejects_unregistered_email(client):
    activity = "Chess Club"
    email = "not-signed-up@mergington.edu"

    response = client.delete(
        f"/activities/{activity}/participants",
        params={"email": email},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found"}