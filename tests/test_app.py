"""
Tests for the Mergington High School Activities API.

Each test follows the AAA pattern:
  - Arrange: set up preconditions and inputs
  - Act:     call the endpoint under test
  - Assert:  verify the response
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Return a synchronous TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state after every test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all_activities(client):
    # Arrange
    expected_count = 9

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == expected_count
    for activity in data.values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_adds_student_to_activity(client):
    # Arrange
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {new_email} for {activity_name}"}
    assert new_email in activities[activity_name]["participants"]


def test_signup_returns_400_when_student_already_registered(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"  # pre-seeded in the fixture

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    unknown_activity = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{unknown_activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

def test_unregister_removes_student_from_activity(client):
    # Arrange
    activity_name = "Chess Club"
    enrolled_email = "michael@mergington.edu"  # pre-seeded in the fixture

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": enrolled_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {enrolled_email} from {activity_name}"}
    assert enrolled_email not in activities[activity_name]["participants"]


def test_unregister_returns_400_when_student_not_enrolled(client):
    # Arrange
    activity_name = "Chess Club"
    unenrolled_email = "nobody@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": unenrolled_email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    unknown_activity = "Nonexistent Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{unknown_activity}/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


# ---------------------------------------------------------------------------
# GET / (redirect)
# ---------------------------------------------------------------------------

def test_root_redirects_to_static_index(client):
    # Arrange
    expected_redirect_url = "/static/index.html"

    # Act – follow_redirects=False so we can inspect the redirect itself
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"] == expected_redirect_url
