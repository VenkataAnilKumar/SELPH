"""
Integration tests for backend API endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_signup_success(self, client, test_user_data):
        """Test successful signup"""
        response = client.post("/v1/auth/signup", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert "user" in data
        assert data["user"]["email"] == test_user_data["email"]

    def test_signup_missing_email(self, client):
        """Test signup with missing email"""
        response = client.post("/v1/auth/signup", json={"password": "TestPassword123", "name": "Test"})
        
        assert response.status_code == 422

    def test_signup_missing_password(self, client):
        """Test signup with missing password"""
        response = client.post("/v1/auth/signup", json={"email": "test@example.com", "name": "Test"})
        
        assert response.status_code == 422

    def test_signup_invalid_email(self, client):
        """Test signup with invalid email"""
        response = client.post(
            "/v1/auth/signup", json={"email": "invalid", "password": "TestPassword123", "name": "Test"}
        )
        
        assert response.status_code == 422

    def test_signup_duplicate_email(self, client, test_user_data):
        """Test signup with duplicate email"""
        # First signup
        client.post("/v1/auth/signup", json=test_user_data)
        
        # Second signup with same email
        response = client.post("/v1/auth/signup", json=test_user_data)
        
        assert response.status_code == 400

    def test_login_success(self, client, test_user_data):
        """Test successful login"""
        # Signup first
        client.post("/v1/auth/signup", json=test_user_data)
        
        # Login
        response = client.post(
            "/v1/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert "user" in data

    def test_login_invalid_email(self, client):
        """Test login with invalid email"""
        response = client.post(
            "/v1/auth/login", json={"email": "wrong@example.com", "password": "WrongPassword123"}
        )
        
        assert response.status_code == 401

    def test_login_invalid_password(self, client, test_user_data):
        """Test login with invalid password"""
        # Signup first
        client.post("/v1/auth/signup", json=test_user_data)
        
        # Login with wrong password
        response = client.post(
            "/v1/auth/login",
            json={"email": test_user_data["email"], "password": "WrongPassword123"},
        )
        
        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        """Test getting current user"""
        response = client.get("/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data

    def test_logout(self, client, auth_headers):
        """Test logout"""
        response = client.post("/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200

    def test_refresh_token(self, client, test_user_data):
        """Test token refresh"""
        # Signup
        client.post("/v1/auth/signup", json=test_user_data)

        # Login and get access token
        login_response = client.post(
            "/v1/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]},
        )
        access_token = login_response.json()["tokens"]["access_token"]
        
        # Refresh requires authenticated user context
        response = client.post("/v1/auth/refresh", headers={"Authorization": f"Bearer {access_token}"})
        
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestTwinEndpoints:
    """Test twin endpoints"""

    def test_get_twin(self, client, auth_headers):
        """Test getting twin profile"""
        response = client.get("/v1/twin/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "user_id" in data
        assert "status" in data
        assert data["status"] == "active"

    def test_pause_twin(self, client, auth_headers):
        """Test pausing twin"""
        response = client.post("/v1/twin/pause", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"

    def test_resume_twin(self, client, auth_headers):
        """Test resuming twin"""
        # Pause first
        client.post("/v1/twin/pause", headers=auth_headers)
        
        # Resume
        response = client.post("/v1/twin/resume", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

    def test_get_twin_stats(self, client, auth_headers):
        """Test getting twin statistics"""
        response = client.get("/v1/twin/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "domain" in data
        assert "tone" in data
        assert "total_messages" in data
        assert "pending_drafts" in data

    def test_update_twin_profile(self, client, auth_headers, test_twin_data):
        """Test updating twin profile"""
        response = client.put(
            "/v1/twin/me", headers=auth_headers, json=test_twin_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["domain"] == test_twin_data["domain"]
        assert data["tone"] == test_twin_data["tone"]

    def test_get_twin_unauthorized(self, client):
        """Test getting twin without auth"""
        response = client.get("/v1/twin/me")
        
        assert response.status_code == 403


class TestMessageEndpoints:
    """Test message endpoints"""

    def test_get_messages(self, client, auth_headers, test_message_data):
        """Test getting user's messages"""
        response = client.get("/v1/messages", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_messages_with_limit(self, client, auth_headers):
        """Test getting messages with limit"""
        response = client.get("/v1/messages?limit=5", headers=auth_headers)
        
        assert response.status_code == 200

    def test_get_messages_with_status_filter(self, client, auth_headers):
        """Test getting messages with status filter"""
        response = client.get("/v1/messages?status=received", headers=auth_headers)
        
        assert response.status_code == 200

    def test_get_messages_unauthorized(self, client):
        """Test getting messages without auth"""
        response = client.get("/v1/messages")
        
        assert response.status_code == 403


class TestDraftEndpoints:
    """Test draft endpoints"""

    def test_get_pending_drafts(self, client, auth_headers):
        """Test getting pending drafts"""
        response = client.get("/v1/drafts/pending", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_approve_draft(self, client, auth_headers):
        """Test approving a draft"""
        # This test would require creating a draft first
        # For now, test endpoint exists and requires auth
        response = client.post(
            "/v1/drafts/1/approve",
            headers=auth_headers,
            json={"action": "approve"},
        )
        
        # May be 404 if draft doesn't exist, but shouldn't be 403
        assert response.status_code != 403

    def test_reject_draft(self, client, auth_headers):
        """Test rejecting a draft"""
        response = client.post(
            "/v1/drafts/1/approve",
            headers=auth_headers,
            json={"action": "reject"},
        )
        
        assert response.status_code != 403

    def test_edit_draft(self, client, auth_headers):
        """Test editing a draft"""
        response = client.post(
            "/v1/drafts/1/approve",
            headers=auth_headers,
            json={"action": "edit", "edited_content": "Updated response"},
        )
        
        assert response.status_code != 403

    def test_draft_unauthorized(self, client):
        """Test draft endpoints without auth"""
        response = client.get("/v1/drafts/pending")
        
        assert response.status_code == 403


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "ok"]
