"""GitHub public API integration for fetching developer profile signals.

Uses unauthenticated requests (60/hour rate limit, sufficient for single-user recruiting tool).
Callers should never crash on GitHub API failure — this is enrichment, not critical path.
"""

import httpx
from datetime import datetime, timezone
from typing import Optional

GITHUB_API_BASE = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "ai-recruiting-saas/1.0",
}


def fetch_github_profile(username: str) -> Optional[dict]:
    """Fetch public GitHub profile signals for a username.

    Returns None if user not found, rate-limited, or network error.
    Never raises — failures are silently returned as None.
    """
    username = username.strip().lstrip("@")
    if not username:
        return None

    try:
        # 1. User profile
        user_url = f"{GITHUB_API_BASE}/users/{username}"
        user_resp = httpx.get(user_url, headers=HEADERS, timeout=15)
        if user_resp.status_code != 200:
            return None
        user_data = user_resp.json()

        # 2. Repos for stars and language stats
        repos_url = f"{GITHUB_API_BASE}/users/{username}/repos?per_page=100&sort=updated"
        repos_resp = httpx.get(repos_url, headers=HEADERS, timeout=15)
        languages = []
        total_stars = 0
        if repos_resp.status_code == 200:
            repos = repos_resp.json()
            lang_counts = {}
            for repo in repos:
                total_stars += repo.get("stargazers_count", 0)
                lang = repo.get("language")
                if lang:
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1
            languages = sorted(lang_counts, key=lang_counts.get, reverse=True)[:5]

        # 3. Account age
        created = user_data.get("created_at", "")
        account_age_days = 0
        if created:
            created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            account_age_days = (datetime.now(timezone.utc) - created_dt).days

        # 4. Recent events as activity proxy
        events_url = f"{GITHUB_API_BASE}/users/{username}/events/public?per_page=100"
        events_resp = httpx.get(events_url, headers=HEADERS, timeout=15)
        recent_activity = 0
        if events_resp.status_code == 200:
            events = events_resp.json()
            recent_activity = len(events)

        return {
            "username": username,
            "public_repos": user_data.get("public_repos", 0),
            "followers": user_data.get("followers", 0),
            "total_stars": total_stars,
            "top_languages": languages,
            "recent_activity_count": recent_activity,
            "account_age_days": account_age_days,
            "profile_url": f"https://github.com/{username}",
        }
    except (httpx.HTTPError, httpx.TimeoutException):
        return None
