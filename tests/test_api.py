import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
FIXTURE_USERS = ROOT_DIR / "schemas" / "users.json"
FIXTURE_POSTS = ROOT_DIR / "schemas" / "posts.json"


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class InstagramBackendAPITests(unittest.TestCase):
    @classmethod
    
    def setUpClass(cls):
        cls.port = get_free_port()
    
        # Start the server
        cls.server = subprocess.Popen([...])
    
        # Wait for server to be ready
        for _ in range(80):
            try:
                response = cls.request("GET", "/health")
                if response["status"] == 200:
                    break
            except:
                time.sleep(0.25)
    
        # Create test users through the real API
        cls.request("POST", "/api/v1/auth/registration", json_body={
            "email": "tony@test.com",
            "username": "tony_123",
            "password": "Tony@123",
            "full_name": "Tony Stark"
        })
        cls.request("POST", "/api/v1/auth/registration", json_body={
            "email": "steve@test.com",
            "username": "steve-rogers", 
            "password": "Steve@456",
            "full_name": "Steve Rogers"
        })
    
    
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "server"):
            cls.server.terminate()
            try:
                cls.server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.server.kill()
        if hasattr(cls, "temp_dir") and cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

    @classmethod
    def request(cls, method: str, path: str, json_body=None, form_body=None, headers=None):
        request_headers = headers.copy() if headers else {}
        request_headers.setdefault("X-Request-ID", "test-request-id")

        data = None
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        elif form_body is not None:
            data = urllib.parse.urlencode(form_body).encode("utf-8")
            request_headers["Content-Type"] = "application/x-www-form-urlencoded"

        request = urllib.request.Request(
            f"http://127.0.0.1:{cls.port}{path}",
            data=data,
            method=method,
            headers=request_headers,
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw_body = response.read().decode("utf-8")
                return {
                    "status": response.status,
                    "headers": dict(response.headers.items()),
                    "body": raw_body,
                    "json": json.loads(raw_body) if raw_body else None,
                }
        except urllib.error.HTTPError as exc:
            raw_body = exc.read().decode("utf-8")
            return {
                "status": exc.code,
                "headers": dict(exc.headers.items()),
                "body": raw_body,
                "json": json.loads(raw_body) if raw_body else None,
            }

    @classmethod
    def login_and_get_token(cls, username: str, password: str) -> str:
        response = cls.request(
            "POST",
            "/api/v1/auth/login",
            form_body={"username": username, "password": password},
        )
        assert response["status"] == 200, response
        return response["json"]["access_token"]

    def test_health_and_version(self):
        health = self.request("GET", "/health")
        version = self.request("GET", "/api/v1")

        self.assertEqual(health["status"], 200)
        self.assertEqual(health["json"], {"status": "ok"})
        self.assertEqual(version["status"], 200)
        self.assertEqual(version["json"]["name"], "instagram_clone")

    def test_existing_user_profile_is_public_and_valid(self):
        response = self.request("GET", "/api/v1/users/tony_123")

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["json"]["username"], "tony_123")
        self.assertIn("avatar_url", response["json"])
        self.assertIn("post_count", response["json"])

    def test_login_returns_token_and_refresh_cookie(self):
        response = self.request(
            "POST",
            "/api/v1/auth/login",
            form_body={"username": "tony_123", "password": "Tony@123"},
        )

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["json"]["token_type"], "bearer")
        self.assertIn("set-cookie", response["headers"])
        self.assertIn("refresh_token=", response["headers"]["set-cookie"])

    def test_invalid_login_returns_401(self):
        response = self.request(
            "POST",
            "/api/v1/auth/login",
            form_body={"username": "tony_123", "password": "wrong-password"},
        )

        self.assertEqual(response["status"], 401)
        self.assertEqual(response["json"]["error"]["message"], "Invalid username or password")

    def test_registration_ignores_privilege_escalation_attempts_by_rejecting_extra_fields(self):
        response = self.request(
            "POST",
            "/api/v1/auth/registration",
            json_body={
                "email": "qa@example.com",
                "username": "qa_user_1",
                "password": "QaUser@123",
                "full_name": "QA User",
                "bio": "testing",
                "role": "super_admin",
            },
        )

        self.assertEqual(response["status"], 422)
        self.assertEqual(response["json"]["error"]["message"], "Validation failed.")

    def test_create_update_and_delete_post_flow(self):
        token = self.login_and_get_token("tony_123", "Tony@123")

        create_response = self.request(
            "POST",
            "/api/v1/posts/",
            json_body={"caption": "Fresh post", "image_url": "https://example.com/new-post.png"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(create_response["status"], 201)
        post_id = create_response["json"]["id"]
        self.assertEqual(create_response["json"]["username"], "tony_123")

        posts_response = self.request("GET", "/api/v1/users/tony_123/posts")
        self.assertEqual(posts_response["status"], 200)
        self.assertTrue(any(post["id"] == post_id for post in posts_response["json"]))

        update_response = self.request(
            "PATCH",
            f"/api/v1/posts/{post_id}",
            json_body={"caption": "Updated caption"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(update_response["status"], 200)
        self.assertEqual(update_response["json"]["caption"], "Updated caption")

        delete_response = self.request(
            "DELETE",
            f"/api/v1/posts/{post_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(delete_response["status"], 204)

        missing_response = self.request("GET", f"/api/v1/posts/{post_id}")
        self.assertEqual(missing_response["status"], 404)

    def test_like_and_unlike_flow(self):
        owner_token = self.login_and_get_token("tony_123", "Tony@123")
        liker_token = self.login_and_get_token("steve-rogers", "Steve@456")

        create_response = self.request(
            "POST",
            "/api/v1/posts/",
            json_body={"caption": "Like me", "image_url": "https://example.com/like-me.png"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        post_id = create_response["json"]["id"]

        like_response = self.request(
            "POST",
            f"/api/v1/posts/{post_id}/like",
            headers={"Authorization": f"Bearer {liker_token}"},
        )
        self.assertEqual(like_response["status"], 200)
        self.assertEqual(like_response["json"]["post"]["like_count"], 1)

        duplicate_like = self.request(
            "POST",
            f"/api/v1/posts/{post_id}/like",
            headers={"Authorization": f"Bearer {liker_token}"},
        )
        self.assertEqual(duplicate_like["status"], 409)

        unlike_response = self.request(
            "DELETE",
            f"/api/v1/posts/{post_id}/like",
            headers={"Authorization": f"Bearer {liker_token}"},
        )
        self.assertEqual(unlike_response["status"], 204)

        second_unlike = self.request(
            "DELETE",
            f"/api/v1/posts/{post_id}/like",
            headers={"Authorization": f"Bearer {liker_token}"},
        )
        self.assertEqual(second_unlike["status"], 409)

    def test_validation_errors_return_422_without_internal_trace(self):
        response = self.request("GET", "/api/v1/posts/abc")

        self.assertEqual(response["status"], 422)
        self.assertEqual(response["json"]["error"]["message"], "Validation failed.")
        self.assertIn("request_id", response["json"]["error"])
        self.assertNotIn("File ", response["body"])


if __name__ == "__main__":
    unittest.main()
