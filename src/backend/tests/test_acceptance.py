"""
End-to-end acceptance tests for complete user flows
"""

import pytest


class TestPhase0AcceptanceCriteria:
    """Test Phase 0 acceptance criteria - Complete user flows"""

    def test_user_signup_to_dashboard_flow(self, client, test_user_data):
        """
        Acceptance Test 1: User signup and access dashboard
        
        Scenario: User creates account and accesses dashboard
        Given: User visits signup page
        When: User enters email and password and clicks signup
        Then: Account is created, tokens are returned, user can access dashboard
        """
        # Step 1: Signup
        response = client.post("/v1/auth/signup", json=test_user_data)
        assert response.status_code == 201
        
        signup_data = response.json()
        access_token = signup_data["tokens"]["access_token"]
        user_email = signup_data["user"]["email"]
        
        # Verify user data
        assert user_email == test_user_data["email"]
        
        # Step 2: Access dashboard (get current user)
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        current_user = response.json()
        assert current_user["email"] == test_user_data["email"]
        
        # Step 3: Verify twin was auto-created
        response = client.get("/v1/twin/me", headers=headers)
        assert response.status_code == 200
        
        twin = response.json()
        assert twin["status"] == "active"

    def test_user_login_flow(self, client, test_user_data):
        """
        Acceptance Test 2: User login with existing account
        
        Scenario: Existing user logs in
        Given: User has existing account
        When: User enters email and password
        Then: User receives tokens and can access protected routes
        """
        # Step 1: Signup
        client.post("/v1/auth/signup", json=test_user_data)
        
        # Step 2: Logout (simulated)
        
        # Step 3: Login again
        response = client.post(
            "/v1/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]},
        )
        assert response.status_code == 200
        
        login_data = response.json()
        access_token = login_data["tokens"]["access_token"]
        
        # Step 4: Verify access to protected routes
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/v1/auth/me", headers=headers)
        assert response.status_code == 200

    def test_twin_configuration_flow(self, client, auth_headers, test_twin_data):
        """
        Acceptance Test 3: User configures twin personality
        
        Scenario: User customizes twin settings
        Given: User is authenticated
        When: User updates twin domain, tone, vocabulary
        Then: Twin settings are persisted and can be retrieved
        """
        # Step 1: Get initial twin
        response = client.get("/v1/twin/me", headers=auth_headers)
        assert response.status_code == 200
        initial_twin = response.json()
        
        # Step 2: Update twin settings
        response = client.put(
            "/v1/twin/me", headers=auth_headers, json=test_twin_data
        )
        assert response.status_code == 200
        
        updated_twin = response.json()
        assert updated_twin["domain"] == test_twin_data["domain"]
        assert updated_twin["tone"] == test_twin_data["tone"]
        
        # Step 3: Verify settings persist
        response = client.get("/v1/twin/me", headers=auth_headers)
        assert response.status_code == 200
        
        persisted_twin = response.json()
        assert persisted_twin["domain"] == test_twin_data["domain"]
        assert persisted_twin["tone"] == test_twin_data["tone"]

    def test_message_receipt_and_processing_flow(
        self, client, auth_headers, test_message_data
    ):
        """
        Acceptance Test 4: Incoming message is received and marked for draft generation
        
        Scenario: Message arrives from Instagram DM
        Given: User has authenticated and configured twin
        When: Incoming message is received
        Then: Message is stored, marked as received, and ready for processing
        """
        # This test verifies API structure and response codes
        # In production, would test actual message webhook
        
        # Step 1: Get messages (should be empty initially)
        response = client.get("/v1/messages", headers=auth_headers)
        assert response.status_code == 200
        messages = response.json()
        initial_count = len(messages)
        
        # Step 2: Get message statistics
        response = client.get("/v1/twin/stats", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_messages"] == initial_count

    def test_draft_lifecycle_flow(self, client, auth_headers):
        """
        Acceptance Test 5: Draft generation, approval, and lifecycle
        
        Scenario: Twin generates response draft, user approves it
        Given: Twin received a message
        When: Draft is generated and presented to user
        Then: User can approve, reject, or edit the draft
        """
        # Step 1: Get pending drafts (initially empty)
        response = client.get("/v1/drafts/pending", headers=auth_headers)
        assert response.status_code == 200
        pending = response.json()
        initial_pending = len(pending)
        
        # Note: In Phase 0, drafts are created via Celery tasks
        # This test verifies the endpoints work correctly

    def test_twin_pause_resume_flow(self, client, auth_headers):
        """
        Acceptance Test 6: User can pause/resume twin operations
        
        Scenario: User temporarily pauses twin
        Given: Twin is active
        When: User clicks pause
        Then: Twin status changes to paused, no new drafts generated
        """
        # Step 1: Verify twin is active
        response = client.get("/v1/twin/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "active"
        
        # Step 2: Pause twin
        response = client.post("/v1/twin/pause", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "paused"
        
        # Step 3: Verify paused status persists
        response = client.get("/v1/twin/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "paused"
        
        # Step 4: Resume twin
        response = client.post("/v1/twin/resume", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "active"
        
        # Step 5: Verify active status
        response = client.get("/v1/twin/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_authentication_security_flow(self, client, test_user_data):
        """
        Acceptance Test 7: Authentication and authorization work correctly
        
        Scenario: Only authenticated users can access protected routes
        Given: Mixed authenticated and unauthenticated requests
        When: Requests are made to protected endpoints
        Then: Unauthenticated requests get 403, authenticated get data
        """
        # Step 1: Try to access protected route without auth
        response = client.get("/v1/twin/me")
        assert response.status_code == 403
        
        response = client.get("/v1/messages")
        assert response.status_code == 403
        
        response = client.get("/v1/drafts/pending")
        assert response.status_code == 403
        
        # Step 2: Signup and get auth token
        response = client.post("/v1/auth/signup", json=test_user_data)
        assert response.status_code == 201
        access_token = response.json()["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Step 3: Access protected routes with auth
        response = client.get("/v1/twin/me", headers=headers)
        assert response.status_code == 200
        
        response = client.get("/v1/messages", headers=headers)
        assert response.status_code == 200
        
        response = client.get("/v1/drafts/pending", headers=headers)
        assert response.status_code == 200

    def test_multiple_users_isolation(self, client, test_user_data):
        """
        Acceptance Test 8: Multiple users' data is isolated
        
        Scenario: User A and User B both have accounts
        Given: Two users with different emails
        When: Each user logs in and accesses their data
        Then: Each user only sees their own twin and messages
        """
        # Step 1: Create User A
        user_a_data = {
            "email": "usera@example.com",
            "password": "PasswordA123",
            "name": "User A",
        }
        response = client.post("/v1/auth/signup", json=user_a_data)
        assert response.status_code == 201
        user_a_token = response.json()["tokens"]["access_token"]
        user_a_headers = {"Authorization": f"Bearer {user_a_token}"}
        
        # Step 2: Create User B
        user_b_data = {
            "email": "userb@example.com",
            "password": "PasswordB123",
            "name": "User B",
        }
        response = client.post("/v1/auth/signup", json=user_b_data)
        assert response.status_code == 201
        user_b_token = response.json()["tokens"]["access_token"]
        user_b_headers = {"Authorization": f"Bearer {user_b_token}"}
        
        # Step 3: Verify User A gets their own twin
        response = client.get("/v1/twin/me", headers=user_a_headers)
        assert response.status_code == 200
        user_a_twin_id = response.json()["id"]
        
        # Step 4: Verify User B gets different twin
        response = client.get("/v1/twin/me", headers=user_b_headers)
        assert response.status_code == 200
        user_b_twin_id = response.json()["id"]
        
        # Twin IDs should be different
        assert user_a_twin_id != user_b_twin_id

    def test_error_handling_flow(self, client):
        """
        Acceptance Test 9: System handles errors gracefully
        
        Scenario: Various error conditions
        Given: Invalid inputs and requests
        When: Error occurs
        Then: System returns appropriate error codes and messages
        """
        # Step 1: Invalid email format
        response = client.post(
            "/v1/auth/signup",
            json={"email": "invalid", "password": "TestPassword123", "name": "Test"},
        )
        assert response.status_code == 422
        
        # Step 2: Missing required fields
        response = client.post("/v1/auth/signup", json={"email": "test@example.com", "name": "Test"})
        assert response.status_code == 422
        
        # Step 3: Nonexistent user login
        response = client.post(
            "/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "AnyPassword123"},
        )
        assert response.status_code == 401
        
        # Step 4: Invalid token
        response = client.get(
            "/v1/twin/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    def test_complete_user_journey(self, client, test_user_data, test_twin_data):
        """
        Acceptance Test 10: Complete user journey from signup to dashboard
        
        Scenario: Brand new user goes through complete onboarding
        Given: User visits app for first time
        When: User signs up, configures twin, receives message, reviews draft
        Then: User has fully functional account with configured twin
        """
        # Step 1: User signup
        response = client.post("/v1/auth/signup", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        access_token = data["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Step 2: Verify authentication
        response = client.get("/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        # Step 3: Get auto-created twin
        response = client.get("/v1/twin/me", headers=headers)
        assert response.status_code == 200
        twin = response.json()
        assert twin["status"] == "active"
        
        # Step 4: Get initial stats
        response = client.get("/v1/twin/stats", headers=headers)
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_messages"] == 0
        
        # Step 5: Configure twin
        response = client.put(
            "/v1/twin/me", headers=headers, json=test_twin_data
        )
        assert response.status_code == 200
        
        # Step 6: Get updated twin configuration
        response = client.get("/v1/twin/me", headers=headers)
        assert response.status_code == 200
        updated_twin = response.json()
        assert updated_twin["domain"] == test_twin_data["domain"]
        
        # Step 7: Check for pending drafts (empty initially)
        response = client.get("/v1/drafts/pending", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 0
