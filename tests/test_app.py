from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    with TestClient(app, follow_redirects=False) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_details(client):
    # Arrange
    expected_activity = "Art Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert response.json()[expected_activity]["participants"] == []


def test_signup_adds_participant(client):
    # Arrange
    activity = "Art Club"
    email = "test-student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    registered_participants = client.get("/activities").json()[activity]["participants"]
    assert email in registered_participants


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity = "Art Club"
    email = "test-student@mergington.edu"
    client.post(f"/activities/{activity}/signup", params={"email": email})

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": "test-student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    # Arrange
    activity = "Art Club"
    email = "test-student@mergington.edu"
    signup_response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )
    assert signup_response.status_code == 200

    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    registered_participants = client.get("/activities").json()[activity]["participants"]
    assert email not in registered_participants


def test_unregister_rejects_unregistered_participant(client):
    # Arrange
    activity = "Art Club"

    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": "test-student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": "test-student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
