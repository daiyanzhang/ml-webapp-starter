"""
JupyterHub API client for managing users and servers
"""
import os
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings


class JupyterHubClient:
    """Client for interacting with JupyterHub API"""

    def __init__(self):
        self.hub_url = "http://jupyterhub:8000"  # Internal Docker network URL
        self.api_token = "webapp-starter-hub-api-token"  # From jupyterhub_config.py
        self.headers = {
            "Authorization": f"token {self.api_token}",
            "Content-Type": "application/json"
        }

    async def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information from JupyterHub"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.hub_url}/hub/api/users/{username}",
                    headers=self.headers
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    response.raise_for_status()
        except Exception as e:
            print(f"Error getting user info for {username}: {e}")
            return None

    async def create_user(self, username: str) -> bool:
        """Create a user in JupyterHub"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.hub_url}/hub/api/users/{username}",
                    headers=self.headers
                )
                print(f"Create user {username}: status={response.status_code}, response={response.text}")
                return response.status_code in [201, 409]  # 201 created, 409 already exists
        except Exception as e:
            print(f"Error creating user {username}: {e}")
            return False

    async def start_server(self, username: str) -> Dict[str, Any]:
        """Start a Jupyter server for the user"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.hub_url}/hub/api/users/{username}/server",
                    headers=self.headers,
                    timeout=300  # 5 minutes timeout for server start
                )

                print(f"Start server {username}: status={response.status_code}, response={response.text}")
                if response.status_code == 201:
                    return {"status": "started", "message": "Server started successfully"}
                elif response.status_code == 202:
                    return {"status": "starting", "message": "Server start request accepted, starting in progress"}
                elif response.status_code == 400:
                    return {"status": "already_running", "message": "Server is already running"}
                else:
                    return {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}

        except httpx.TimeoutException:
            return {"status": "timeout", "message": "Server start timed out"}
        except Exception as e:
            print(f"Error starting server for {username}: {e}")
            return {"status": "error", "message": str(e)}

    async def stop_server(self, username: str) -> bool:
        """Stop a user's Jupyter server"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.hub_url}/hub/api/users/{username}/server",
                    headers=self.headers
                )
                return response.status_code in [202, 204, 404]  # 202 accepted, 204 no content, 404 not running
        except Exception as e:
            print(f"Error stopping server for {username}: {e}")
            return False

    async def get_server_status(self, username: str) -> Dict[str, Any]:
        """Get the status of a user's Jupyter server"""
        user_info = await self.get_user_info(username)
        if not user_info:
            return {"status": "user_not_found"}

        servers = user_info.get("servers", {})
        if not servers:
            return {"status": "not_running"}

        # Check default server (empty string key)
        default_server = servers.get("", {})
        if default_server:
            return {
                "status": "running",
                "url": f"{self.hub_url}/user/{username}/",
                "ready": default_server.get("ready", False),
                "pending": default_server.get("pending", None),
                "started": default_server.get("started", None)
            }

        return {"status": "not_running"}

    async def get_user_url(self, username: str) -> Optional[str]:
        """Get the URL for accessing user's Jupyter server"""
        status = await self.get_server_status(username)
        if status.get("status") == "running":
            # Return external URL (mapped to host port 8001)
            return f"http://localhost:8001/user/{username}/"
        return None

    async def ensure_user_session(self, username: str) -> Dict[str, Any]:
        """Ensure user exists and has an active session"""
        # 1. Create user if doesn't exist
        user_created = await self.create_user(username)
        if not user_created:
            return {"status": "error", "message": "Failed to create user"}

        # 2. Check server status
        server_status = await self.get_server_status(username)

        if server_status["status"] == "running":
            return {
                "status": "ready",
                "url": await self.get_user_url(username),
                "message": "Session already active"
            }

        # 3. Start server if not running
        start_result = await self.start_server(username)
        if start_result["status"] in ["started", "already_running", "starting"]:
            return {
                "status": "starting",
                "url": await self.get_user_url(username),
                "message": start_result.get("message", "Session is starting")
            }

        return {
            "status": "error",
            "message": start_result.get("message", "Failed to start session")
        }


# Global instance
jupyterhub_client = JupyterHubClient()