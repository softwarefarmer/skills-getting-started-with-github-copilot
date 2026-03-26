"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to a known state for each test"""
    original_activities = {
        "Test Club": {
            "description": "A club for testing",
            "schedule": "Mondays, 3:00 PM",
            "max_participants": 5,
            "participants": ["alice@test.edu", "bob@test.edu"]
        },
        "Study Group": {
            "description": "Study together",
            "schedule": "Wednesdays, 4:00 PM",
            "max_participants": 10,
            "participants": []
        }
    }
    
    # Clear and repopulate activities
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert "Test Club" in data
        assert "Study Group" in data
    
    def test_get_activities_has_correct_structure(self, client, reset_activities):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Test Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_get_activities_includes_participants(self, client, reset_activities):
        """Test that participants are included in response"""
        response = client.get("/activities")
        data = response.json()
        
        assert data["Test Club"]["participants"] == ["alice@test.edu", "bob@test.edu"]
        assert data["Study Group"]["participants"] == []


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Study%20Group/signup",
            params={"email": "charlie@test.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "charlie@test.edu" in data["message"]
        assert "charlie@test.edu" in activities["Study Group"]["participants"]
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent/signup",
            params={"email": "test@test.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_already_registered(self, client, reset_activities):
        """Test that student cannot signup twice for same activity"""
        response = client.post(
            "/activities/Test%20Club/signup",
            params={"email": "alice@test.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_adds_to_participants_list(self, client, reset_activities):
        """Test that signup adds participant to the list"""
        initial_count = len(activities["Study Group"]["participants"])
        
        response = client.post(
            "/activities/Study%20Group/signup",
            params={"email": "newstudent@test.edu"}
        )
        
        assert response.status_code == 200
        assert len(activities["Study Group"]["participants"]) == initial_count + 1
    
    def test_signup_multiple_different_students(self, client, reset_activities):
        """Test multiple students signing up for the same activity"""
        emails = ["student1@test.edu", "student2@test.edu", "student3@test.edu"]
        
        for email in emails:
            response = client.post(
                "/activities/Study%20Group/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        assert len(activities["Study Group"]["participants"]) == 3
        for email in emails:
            assert email in activities["Study Group"]["participants"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregister from an activity"""
        response = client.delete(
            "/activities/Test%20Club/unregister",
            params={"email": "alice@test.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "alice@test.edu" in data["message"]
        assert "alice@test.edu" not in activities["Test Club"]["participants"]
    
    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent/unregister",
            params={"email": "test@test.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_not_registered(self, client, reset_activities):
        """Test unregister when student is not registered"""
        response = client.delete(
            "/activities/Test%20Club/unregister",
            params={"email": "unknown@test.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()
    
    def test_unregister_removes_from_participants(self, client, reset_activities):
        """Test that unregister removes participant from list"""
        initial_count = len(activities["Test Club"]["participants"])
        
        response = client.delete(
            "/activities/Test%20Club/unregister",
            params={"email": "bob@test.edu"}
        )
        
        assert response.status_code == 200
        assert len(activities["Test Club"]["participants"]) == initial_count - 1
    
    def test_unregister_all_participants(self, client, reset_activities):
        """Test unregistering all participants from an activity"""
        participants = activities["Test Club"]["participants"].copy()
        
        for email in participants:
            response = client.delete(
                "/activities/Test%20Club/unregister",
                params={"email": email}
            )
            assert response.status_code == 200
        
        assert len(activities["Test Club"]["participants"]) == 0


class TestSignupAndUnregister:
    """Integration tests for signup and unregister flows"""
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Test signing up and then unregistering"""
        email = "test@test.edu"
        
        # Sign up
        response = client.post(
            "/activities/Study%20Group/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email in activities["Study Group"]["participants"]
        
        # Unregister
        response = client.delete(
            "/activities/Study%20Group/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email not in activities["Study Group"]["participants"]
    
    def test_signup_unregister_signup_again(self, client, reset_activities):
        """Test that student can signup again after unregistering"""
        email = "test@test.edu"
        
        # Sign up
        response = client.post(
            "/activities/Study%20Group/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Unregister
        response = client.delete(
            "/activities/Study%20Group/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Sign up again
        response = client.post(
            "/activities/Study%20Group/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email in activities["Study Group"]["participants"]
