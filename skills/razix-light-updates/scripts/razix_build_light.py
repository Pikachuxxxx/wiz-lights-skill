import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from wiz_control import WizBulb

DEFAULT_REPO = "Pikachuxxxx/Razix"
DEFAULT_BULB_IP = "192.168.0.120"
GITHUB_API = "https://api.github.com"


@dataclass
class BuildInfo:
    repo: str
    workflow: str
    run_id: int
    run_number: int
    status: str
    conclusion: Optional[str]
    branch: str
    commit_sha: str
    actor: str
    created_at: str
    updated_at: str
    html_url: str

    @property
    def state_key(self) -> str:
        if self.status != "completed":
            return self.status
        return self.conclusion or "unknown"


@dataclass
class RepoStats:
    repo: str
    default_branch: str
    stars: int
    forks: int
    watchers: int
    open_issues: int
    open_prs: int
    recent_commits: int
    unique_authors: int
    last_commit_at: str
    total_recent_runs: int
    completed_recent_runs: int
    success_rate: float
    success_streak: int
    health_score: int
    vibe: str


def _api_get(url: str, token: Optional[str] = None) -> Dict:
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "razix-build-light")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def get_recent_runs(repo: str, token: Optional[str], per_page: int = 30) -> List[Dict]:
    qs = urllib.parse.urlencode({"per_page": per_page})
    url = f"{GITHUB_API}/repos/{repo}/actions/runs?{qs}"
    data = _api_get(url, token)
    return data.get("workflow_runs", [])


def get_latest_build(repo: str, workflow_filter: Optional[str], token: Optional[str]) -> BuildInfo:
    runs = get_recent_runs(repo, token, per_page=40)
    if workflow_filter:
        needle = workflow_filter.lower()
        runs = [r for r in runs if needle in str(r.get("name", "")).lower()]

    if not runs:
        wf_msg = f" (filter='{workflow_filter}')" if workflow_filter else ""
        raise RuntimeError(f"No workflow runs found for {repo}{wf_msg}")

    run = runs[0]
    return BuildInfo(
        repo=repo,
        workflow=run.get("name", "unknown"),
        run_id=run.get("id", 0),
        run_number=run.get("run_number", 0),
        status=run.get("status", "unknown"),
        conclusion=run.get("conclusion"),
        branch=run.get("head_branch", "unknown"),
        commit_sha=run.get("head_sha", "")[:8],
        actor=(run.get("actor") or {}).get("login", "unknown"),
        created_at=run.get("created_at", ""),
        updated_at=run.get("updated_at", ""),
        html_url=run.get("html_url", ""),
    )


def color_for_build(build: BuildInfo) -> Tuple[int, int, int, int, str]:
    key = build.state_key
    mapping = {
        "success": (0, 220, 80, 80, "green (success)"),
        "failure": (255, 25, 25, 100, "red (failed)"),
        "timed_out": (255, 60, 0, 100, "orange-red (timed out)"),
        "action_required": (255, 90, 0, 100, "orange-red (action required)"),
        "startup_failure": (255, 0, 60, 100, "crimson (startup failure)"),
        "cancelled": (90, 90, 255, 55, "blue (cancelled)"),
        "skipped": (140, 100, 255, 45, "violet (skipped)"),
        "neutral": (80, 160, 255, 50, "cool blue (neutral)"),
        "stale": (180, 110, 220, 45, "muted purple (stale)"),
        "queued": (255, 180, 0, 70, "amber (queued)"),
        "in_progress": (255, 130, 0, 80, "orange (in progress)"),
        "waiting": (255, 180, 0, 70, "amber (waiting)"),
        "requested": (255, 180, 0, 70, "amber (requested)"),
        "pending": (255, 180, 0, 70, "amber (pending)"),
        "unknown": (200, 200, 200, 40, "white (unknown)"),
    }
    return mapping.get(key, mapping["unknown"])


def build_repo_stats(repo: str, workflow_filter: Optional[str], token: Optional[str]) -> RepoStats:
    repo_data = _api_get(f"{GITHUB_API}/repos/{repo}", token)
    default_branch = repo_data.get("default_branch", "main")

    commits = _api_get(
        f"{GITHUB_API}/repos/{repo}/commits?{urllib.parse.urlencode({'sha': default_branch, 'per_page': 30})}",
        token,
    )
    if not isinstance(commits, list):
        commits = []

    pulls = _api_get(
        f"{GITHUB_API}/repos/{repo}/pulls?{urllib.parse.urlencode({'state': 'open', 'per_page': 100})}",
        token,
    )
    if not isinstance(pulls, list):
        pulls = []

    runs = get_recent_runs(repo, token, per_page=40)
    if workflow_filter:
        needle = workflow_filter.lower()
        runs = [r for r in runs if needle in str(r.get("name", "")).lower()]

    completed_runs = [r for r in runs if r.get("status") == "completed"]
    successes = [r for r in completed_runs if r.get("conclusion") == "success"]
    success_rate = (len(successes) / len(completed_runs) * 100.0) if completed_runs else 0.0

    streak = 0
    for run in completed_runs:
        if run.get("conclusion") == "success":
            streak += 1
        else:
            break

    authors = set()
    last_commit_at = ""
    for idx, c in enumerate(commits):
        author = ((c.get("author") or {}).get("login") or "")
        if author:
            authors.add(author)
        if idx == 0:
            last_commit_at = ((c.get("commit") or {}).get("author") or {}).get("date", "")

    stars = int(repo_data.get("stargazers_count", 0))
    forks = int(repo_data.get("forks_count", 0))
    watchers = int(repo_data.get("subscribers_count", 0))
    open_issues = int(repo_data.get("open_issues_count", 0))
    open_prs = len(pulls)
    recent_commits = len(commits)
    unique_authors = len(authors)

    score = 50
    score += min(int(stars / 50), 15)
    score += min(int(success_rate / 4), 25)
    score += min(streak * 2, 10)
    score += min(unique_authors * 2, 10)
    score += min(int(recent_commits / 2), 10)
    score -= min(int(open_issues / 40), 10)
    score -= min(int(open_prs / 10), 5)
    health_score = max(0, min(score, 100))

    if health_score >= 85:
        vibe = "Ship It Mode"
    elif health_score >= 70:
        vibe = "Cruising"
    elif health_score >= 55:
        vibe = "Focused Grind"
    elif health_score >= 40:
        vibe = "Code Yellow"
    else:
        vibe = "Fixathon"

    return RepoStats(
        repo=repo,
        default_branch=default_branch,
        stars=stars,
        forks=forks,
        watchers=watchers,
        open_issues=open_issues,
        open_prs=open_prs,
        recent_commits=recent_commits,
        unique_authors=unique_authors,
        last_commit_at=last_commit_at,
        total_recent_runs=len(runs),
        completed_recent_runs=len(completed_runs),
        success_rate=success_rate,
        success_streak=streak,
        health_score=health_score,
        vibe=vibe,
    )


def color_for_health(score: int) -> Tuple[int, int, int, int, str]:
    s = max(0, min(score, 100))
    r = int(255 * (100 - s) / 100)
    g = int(255 * s / 100)
    b = 35
    brightness = 35 + int((s / 100) * 55)
    return (r, g, b, brightness, f"health score {s}/100")


def color_for_activity(recent_commits: int, unique_authors: int) -> Tuple[int, int, int, int, str]:
    intensity = min(100, recent_commits * 3 + unique_authors * 8)
    if intensity >= 70:
        return (0, 255, 220, 85, "hyper activity")
    if intensity >= 40:
        return (120, 180, 255, 65, "steady activity")
    return (190, 120, 255, 45, "low activity")


def color_for_pr_pressure(open_prs: int, open_issues: int) -> Tuple[int, int, int, int, str]:
    pressure = min(100, open_prs * 10 + open_issues)
    if pressure >= 70:
        return (255, 40, 90, 90, "high review pressure")
    if pressure >= 40:
        return (255, 150, 40, 75, "medium review pressure")
    return (80, 230, 120, 55, "low review pressure")


def print_build_summary(build: BuildInfo) -> None:
    print(f"Repo        : {build.repo}")
    print(f"Workflow    : {build.workflow}")
    print(f"Run ID      : {build.run_id}")
    print(f"Run Number  : {build.run_number}")
    print(f"Branch      : {build.branch}")
    print(f"Commit      : {build.commit_sha}")
    print(f"Actor       : {build.actor}")
    print(f"Status      : {build.status}")
    print(f"Conclusion  : {build.conclusion}")
    print(f"Created At  : {build.created_at}")
    print(f"Updated At  : {build.updated_at}")
    print(f"Actions URL : {build.html_url}")


def print_fun_stats(stats: RepoStats, build: BuildInfo) -> None:
    now = datetime.now(timezone.utc)
    last_commit_age = "unknown"
    if stats.last_commit_at:
        age = now - _parse_ts(stats.last_commit_at)
        hrs = int(age.total_seconds() // 3600)
        last_commit_age = f"{hrs}h ago"

    print("--- Razix Engine Fun Stats ---")
    print(f"Repo               : {stats.repo}")
    print(f"Build State        : {build.state_key} ({build.workflow})")
    print(f"Build Success Rate : {stats.success_rate:.1f}% (last {stats.completed_recent_runs} completed runs)")
    print(f"Success Streak     : {stats.success_streak}")
    print(f"Recent Commits     : {stats.recent_commits} on {stats.default_branch}")
    print(f"Unique Authors     : {stats.unique_authors}")
    print(f"Last Commit        : {stats.last_commit_at} ({last_commit_age})")
    print(f"Open PRs           : {stats.open_prs}")
    print(f"Open Issues        : {stats.open_issues}")
    print(f"Stars/Forks        : {stats.stars}/{stats.forks}")
    print(f"Watchers           : {stats.watchers}")
    print(f"Engine Health      : {stats.health_score}/100")
    print(f"Vibe               : {stats.vibe}")


def set_light(ip: str, color: Tuple[int, int, int, int, str]) -> None:
    r, g, b, brightness, label = color
    response = WizBulb(ip).set_color(r, g, b, brightness=brightness)
    print(f"Light set to {label}: rgb=({r},{g},{b}) brightness={brightness}")
    print(f"Bulb response: {response}")


def set_light_for_build(ip: str, build: BuildInfo) -> None:
    set_light(ip, color_for_build(build))


def run_fun_lightshow(ip: str, build: BuildInfo, stats: RepoStats, delay: float) -> None:
    show = [
        ("build", color_for_build(build)),
        ("health", color_for_health(stats.health_score)),
        ("activity", color_for_activity(stats.recent_commits, stats.unique_authors)),
        ("pr-pressure", color_for_pr_pressure(stats.open_prs, stats.open_issues)),
    ]

    print("Running Razix build aura lightshow...")
    for phase, color in show:
        print(f"Phase: {phase}")
        set_light(ip, color)
        time.sleep(delay)


def run_nl_command(command: str, ip: str, repo: str, workflow: Optional[str], token: Optional[str], delay: float) -> None:
    text = command.strip().lower()

    if "last build" in text or "build status" in text:
        build = get_latest_build(repo, workflow, token)
        print_build_summary(build)
        if "set" in text and "light" in text:
            set_light_for_build(ip, build)
        return

    if "sync" in text and "build" in text:
        build = get_latest_build(repo, workflow, token)
        print_build_summary(build)
        set_light_for_build(ip, build)
        return

    if "fun stats" in text or ("stats" in text and "razix" in text):
        build = get_latest_build(repo, workflow, token)
        stats = build_repo_stats(repo, workflow, token)
        print_build_summary(build)
        print_fun_stats(stats, build)
        if "light" in text or "show" in text:
            run_fun_lightshow(ip, build, stats, delay)
        return

    if "lightshow" in text or "aura" in text or "party" in text:
        build = get_latest_build(repo, workflow, token)
        stats = build_repo_stats(repo, workflow, token)
        run_fun_lightshow(ip, build, stats, delay)
        return

    if text in {"on", "turn on", "light on"}:
        print(WizBulb(ip).set_state(True))
        return

    if text in {"off", "turn off", "light off"}:
        print(WizBulb(ip).set_state(False))
        return

    if "rhythm" in text or "music" in text:
        print(WizBulb(ip).set_scene(31, brightness=100))
        return

    if "club mode" in text:
        print(WizBulb(ip).set_scene(26, brightness=100))
        return

    if "ocean mode" in text:
        print(WizBulb(ip).set_scene(1, brightness=100))
        return

    if "deepdive" in text or "deep dive" in text:
        print(WizBulb(ip).set_scene(23, brightness=100))
        return

    presets = {
        "red": (255, 0, 0, 100),
        "green": (0, 255, 0, 100),
        "blue": (0, 0, 255, 100),
        "teal": (20, 190, 170, 55),
        "dark green": (20, 110, 45, 22),
    }
    for name, (r, g, b, bright) in presets.items():
        if name in text:
            print(WizBulb(ip).set_color(r, g, b, brightness=bright))
            return

    rgb = re.search(r"rgb\s*\(?\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)?", text)
    if rgb:
        r, g, b = map(int, rgb.groups())
        print(WizBulb(ip).set_color(r, g, b, brightness=80))
        return

    raise RuntimeError(
        "Could not parse command. Try: 'last build status', 'sync build light', "
        "'razix fun stats lightshow', 'turn off', 'dark green', or 'rgb(255,20,0)'."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check GitHub Actions build status, compute fun repo stats, and control a WiZ bulb"
    )
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repo in owner/name format")
    parser.add_argument("--workflow", help="Optional workflow name filter (substring match)")
    parser.add_argument("--ip", default=DEFAULT_BULB_IP, help="WiZ bulb IP")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub token (optional)")

    parser.add_argument("--status", action="store_true", help="Print latest build status")
    parser.add_argument("--set-light", action="store_true", help="Set light color from latest build status")
    parser.add_argument("--fun-stats", action="store_true", help="Print expanded repository fun stats")
    parser.add_argument("--fun-lightshow", action="store_true", help="Run a multi-phase stats-driven lightshow")
    parser.add_argument("--scene", type=int, help="Set bulb to a specific WiZ scene ID (e.g. 31 for Rhythm/Music)")
    parser.add_argument("--delay", type=float, default=1.2, help="Seconds per phase in fun lightshow")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON payload")
    parser.add_argument("--command", help="Natural language command for AI/web wrappers")

    args = parser.parse_args()

    if not (args.status or args.set_light or args.fun_stats or args.fun_lightshow or args.command or args.scene):
        parser.error("Provide one of --status, --set-light, --fun-stats, --fun-lightshow, --scene, or --command")

    try:
        if args.command:
            run_nl_command(args.command, args.ip, args.repo, args.workflow, args.token, args.delay)
            return 0

        if args.scene is not None:
            print(WizBulb(args.ip).set_scene(args.scene, brightness=100))
            return 0

        build = get_latest_build(args.repo, args.workflow, args.token)
        stats = build_repo_stats(args.repo, args.workflow, args.token)

        if args.status:
            print_build_summary(build)

        if args.fun_stats:
            print_fun_stats(stats, build)

        if args.set_light:
            set_light_for_build(args.ip, build)

        if args.fun_lightshow:
            run_fun_lightshow(args.ip, build, stats, args.delay)

        if args.json:
            payload = {
                "build": build.__dict__,
                "stats": stats.__dict__,
                "build_color": color_for_build(build),
                "health_color": color_for_health(stats.health_score),
                "activity_color": color_for_activity(stats.recent_commits, stats.unique_authors),
                "pr_pressure_color": color_for_pr_pressure(stats.open_prs, stats.open_issues),
            }
            print(json.dumps(payload, indent=2))

        return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        print(f"GitHub API error {exc.code}: {body}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
