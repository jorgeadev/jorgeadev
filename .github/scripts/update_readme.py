"""
Fetches Jorge's most recently pushed public repos (non-fork) from the GitHub API
and updates the CURRENTLY_WORKING_ON and LAST_PROJECT sections in README.md.
"""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone

USERNAME = "jorgeadev"
README_PATH = "README.md"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def fetch_repos() -> list[dict]:
    url = (
        f"https://api.github.com/users/{USERNAME}/repos"
        "?sort=pushed&direction=desc&per_page=20&type=public"
    )
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def format_repo(repo: dict) -> str:
    name = repo["name"]
    url = repo["html_url"]
    desc = (repo.get("description") or "No description provided.").strip()
    lang = repo.get("language") or "—"
    stars = repo.get("stargazers_count", 0)
    pushed = repo.get("pushed_at", "")

    if pushed:
        dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        pushed_str = dt.strftime("%b %d, %Y")
    else:
        pushed_str = "—"

    star_badge = f"⭐ {stars}" if stars else "⭐ 0"
    return (
        f"**[{name}]({url})**  \n"
        f"> {desc}  \n"
        f"> `{lang}` &nbsp;·&nbsp; {star_badge} &nbsp;·&nbsp; 🕒 {pushed_str}"
    )


def update_section(content: str, marker: str, new_content: str) -> str:
    pattern = rf"(<!-- {re.escape(marker)}:START -->).*?(<!-- {re.escape(marker)}:END -->)"
    replacement = rf"\1\n{new_content}\n\2"
    return re.sub(pattern, replacement, content, flags=re.DOTALL)


def main():
    repos = fetch_repos()
    # Keep only own non-fork public repos, exclude the profile repo itself
    repos = [
        r for r in repos
        if not r.get("fork", False) and r["name"] != USERNAME
    ]

    current = repos[0] if len(repos) > 0 else None
    last = repos[1] if len(repos) > 1 else None

    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    if current:
        readme = update_section(readme, "CURRENTLY_WORKING_ON", format_repo(current))
    if last:
        readme = update_section(readme, "LAST_PROJECT", format_repo(last))

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme)

    print(f"Updated: currently working on [{current['name'] if current else 'N/A'}], "
          f"last project [{last['name'] if last else 'N/A'}]")


if __name__ == "__main__":
    main()
