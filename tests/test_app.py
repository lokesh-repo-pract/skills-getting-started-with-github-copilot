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
    """Reset activities to a known state before each test"""
    # Store original state
    original_activities = {
        activity_name: {
            **activity_data,
            "participants": activity_data["participants"].copy()
        }
        for activity_name, activity_data in activities.items()
    }
    
    yield
    
    # Restore original state
    for activity_name in activities:
        activities[activity_name]["participants"] = original_activities[activity_name]["participants"]


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Basketball" in data
        assert "Tennis Club" in data
        assert "Debate Team" in data
    
    def test_get_activities_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
    
    def test_get_activities_participants_are_list(self, client):
        """Test that participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post("/activities/Basketball/signup", params={"email": "test@mergington.edu"})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant"""
        email = "newstudent@mergington.edu"
        initial_count = len(activities["Basketball"]["participants"])
        
        response = client.post("/activities/Basketball/signup", params={"email": email})
        assert response.status_code == 200
        
        # Verify participant was added
        assert len(activities["Basketball"]["participants"]) == initial_count + 1
        assert email in activities["Basketball"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup fails for non-existent activity"""
        response = client.post("/activities/NonExistent/signup", params={"email": "test@mergington.edu"})
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that duplicate signups fail"""
        email = "alex@mergington.edu"  # Already signed up for Basketball
        response = client.post("/activities/Basketball/signup", params={"email": email})
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_different_activities(self, client, reset_activities):
        """Test that same student can sign up for different activities"""
        email = "multi@mergington.edu"
        
        # Sign up for Basketball
        response1 = client.post("/activities/Basketball/signup", params={"email": email})
        assert response1.status_code == 200
        
        # Sign up for Tennis Club
        response2 = client.post("/activities/Tennis Club/signup", params={"email": email})
        assert response2.status_code == 200
        
        # Verify both signups succeeded
        assert email in activities["Basketball"]["participants"]
        assert email in activities["Tennis Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, client, reset_activities):
        """Test successful unregister from an activity"""
        email = "alex@mergington.edu"  # Already in Basketball
        response = client.post("/activities/Basketball/unregister", params={"email": email})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        email = "marcus@mergington.edu"  # In Debate Team
        initial_count = len(activities["Debate Team"]["participants"])
        
        response = client.post("/activities/Debate Team/unregister", params={"email": email})
        assert response.status_code == 200
        
        # Verify participant was removed
        assert len(activities["Debate Team"]["participants"]) == initial_count - 1
        assert email not in activities["Debate Team"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister fails for non-existent activity"""
        response = client.post("/activities/NonExistent/unregister", params={"email": "test@mergington.edu"})
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_not_participant(self, client, reset_activities):
        """Test unregister fails when student is not signed up"""
        response = client.post("/activities/Basketball/unregister", params={"email": "nothere@mergington.edu"})
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_unregister_twice_fails(self, client, reset_activities):
        """Test that unregistering twice fails"""
        email = "grace@mergington.edu"  # In Tennis Club
        
        # First unregister succeeds
        response1 = client.post("/activities/Tennis Club/unregister", params={"email": email})
        assert response1.status_code == 200
        
        # Second unregister should fail
        response2 = client.post("/activities/Tennis Club/unregister", params={"email": email})
        assert response2.status_code == 400
        assert "not signed up" in response2.json()["detail"].lower()


class TestRootRedirect:
    """Tests for root endpoint"""
    
    def test_root_redirects(self, client):
        """Test that root path redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
