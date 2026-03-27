"""
Comprehensive tests for the FastAPI activity management API endpoints.
Tests cover happy paths and error cases for all endpoints.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities_success(self, client):
        """Test successfully retrieving all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify we get all activities
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
    def test_activities_have_correct_structure(self, client):
        """Test that activities contain all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
        
    def test_activities_include_initial_participants(self, client):
        """Test that activities include their initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        chess_participants = data["Chess Club"]["participants"]
        assert len(chess_participants) == 2
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        participants = activities_response.json()["Chess Club"]["participants"]
        assert "newstudent@mergington.edu" in participants
        
    def test_signup_activity_not_found(self, client):
        """Test signup fails when activity doesn't exist"""
        response = client.post(
            "/activities/NonExistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
        
    def test_signup_student_already_registered(self, client):
        """Test signup fails when student is already signed up"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"
        
    def test_signup_multiple_students_to_same_activity(self, client):
        """Test multiple different students can sign up for the same activity"""
        # First signup
        response1 = client.post(
            "/activities/Programming Class/signup",
            params={"email": "student1@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Second signup (different student, same activity)
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": "student2@mergington.edu"}
        )
        assert response2.status_code == 200
        
        # Verify both are registered
        activities_response = client.get("/activities")
        participants = activities_response.json()["Programming Class"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants
        
    def test_signup_same_student_different_activities(self, client):
        """Test the same student can sign up for different activities"""
        student_email = "versatile@mergington.edu"
        
        # Signup for Chess Club
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": student_email}
        )
        assert response1.status_code == 200
        
        # Signup for Programming Class
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": student_email}
        )
        assert response2.status_code == 200
        
        # Verify student in both
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert student_email in activities["Chess Club"]["participants"]
        assert student_email in activities["Programming Class"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successfully unregistering from an activity"""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        participants = activities_response.json()["Chess Club"]["participants"]
        assert "michael@mergington.edu" not in participants
        
    def test_unregister_activity_not_found(self, client):
        """Test unregister fails when activity doesn't exist"""
        response = client.delete(
            "/activities/NonExistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
        
    def test_unregister_student_not_registered(self, client):
        """Test unregister fails when student is not registered"""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Student not registered for this activity"
        
    def test_unregister_multiple_students(self, client):
        """Test unregistering one student doesn't affect others"""
        # Get original participants
        original_response = client.get("/activities")
        original_count = len(original_response.json()["Chess Club"]["participants"])
        
        # Unregister one student
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify only that student was removed
        activities_response = client.get("/activities")
        new_count = len(activities_response.json()["Chess Club"]["participants"])
        assert new_count == original_count - 1
        assert "daniel@mergington.edu" in activities_response.json()["Chess Club"]["participants"]
        
    def test_unregister_and_resign_up(self, client):
        """Test a student can unregister and sign up again"""
        student_email = "michael@mergington.edu"
        
        # Unregister
        response1 = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": student_email}
        )
        assert response1.status_code == 200
        
        # Verify unregistered
        activities_response = client.get("/activities")
        assert student_email not in activities_response.json()["Chess Club"]["participants"]
        
        # Sign up again
        response2 = client.post(
            "/activities/Chess Club/signup",
            params={"email": student_email}
        )
        assert response2.status_code == 200
        
        # Verify signed up again
        activities_response = client.get("/activities")
        assert student_email in activities_response.json()["Chess Club"]["participants"]


class TestIntegration:
    """Integration tests combining multiple endpoints"""

    def test_signup_and_unregister_flow(self, client):
        """Test complete flow: signup, verify, unregister, verify"""
        student_email = "testuser@mergington.edu"
        activity = "Gym Class"
        
        # Initial check - not registered
        response = client.get("/activities")
        assert student_email not in response.json()[activity]["participants"]
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": student_email}
        )
        assert signup_response.status_code == 200
        
        # Verify registered
        response = client.get("/activities")
        assert student_email in response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": student_email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        response = client.get("/activities")
        assert student_email not in response.json()[activity]["participants"]
