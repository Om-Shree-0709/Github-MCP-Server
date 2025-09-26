"""
MCP GitHub Server
-----------------
This MCP server exposes GitHub functionality to Claude Desktop.

Usage:
    uv run server github_mcp stdio
"""

import os
import requests
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("GitHubConnector")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = "https://api.github.com"

if not GITHUB_TOKEN:
    raise RuntimeError("Please set the GITHUB_TOKEN environment variable in your .env file.")

def github_request(endpoint: str, params=None):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


@mcp.tool()
def get_user_info(username: str) -> dict:
    """Fetch GitHub profile information for a given username."""
    return github_request(f"/users/{username}")

@mcp.tool()
def list_repos(username: str) -> list:
    """List public repositories of a GitHub user."""
    repos = github_request(f"/users/{username}/repos")
    return [
        {"name": r["name"], "url": r["html_url"], "stars": r["stargazers_count"]}
        for r in repos
    ]

@mcp.tool()
def get_repo_issues(owner: str, repo: str, state: str = "open") -> list:
    """List issues from a repository (open by default)."""
    issues = github_request(f"/repos/{owner}/{repo}/issues", params={"state": state})
    return [
        {"title": i["title"], "url": i["html_url"], "user": i["user"]["login"]}
        for i in issues
    ]


@mcp.resource("github://user/{username}")
def github_user(username: str) -> str:
    """Dynamic resource: GitHub user profile summary."""
    user = github_request(f"/users/{username}")
    return f"{user['login']} has {user['public_repos']} public repos and {user['followers']} followers."


@mcp.prompt()
def summarize_repo(owner: str, repo: str) -> str:
    """Generate a writing prompt to summarize a GitHub repo."""
    r = github_request(f"/repos/{owner}/{repo}")
    return (
        f"Write a clear, concise summary of the GitHub repository '{r['name']}'. "
        f"Description: {r.get('description', 'No description provided')}. "
        f"It has {r['stargazers_count']} stars and {r['forks_count']} forks."
    )

if __name__ == "__main__":
    mcp.run()
