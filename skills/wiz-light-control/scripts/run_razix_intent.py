#!/usr/bin/env python3
import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def build_args_from_intent(intent: str) -> list[str]:
    text = intent.strip().lower()

    if "sync" in text and "build" in text and "light" in text:
        return ["--status", "--set-light"]

    if "fun" in text and "stats" in text and ("lightshow" in text or "light show" in text):
        return ["--status", "--fun-stats", "--fun-lightshow"]

    if "fun" in text and "stats" in text:
        return ["--status", "--fun-stats"]

    if "last build" in text or "build status" in text or text == "status":
        return ["--status"]

    if "lightshow" in text or "light show" in text or "aura" in text or "party" in text:
        return ["--fun-lightshow"]

    if "rhythm" in text or "music" in text:
        if "apple music" in text or "system music" in text:
            if "beat" in text or "match" in text or "drop" in text:
                return ["apple-music-sync", "--mode", "beat"]
            if "visualizer" in text or "pulse" in text or "sync" in text:
                return ["apple-music-sync", "--mode", "visualizer"]
            if "club" in text:
                return ["apple-music-sync", "--mode", "scene", "--scene-id", "26"]
            if "ocean" in text:
                return ["apple-music-sync", "--mode", "scene", "--scene-id", "1"]
            if "deep" in text or "dive" in text:
                return ["apple-music-sync", "--mode", "scene", "--scene-id", "23"]
            if "unique" in text or "color" in text:
                return ["apple-music-sync", "--mode", "color"]
            return ["apple-music-sync", "--mode", "scene", "--scene-id", "4"]
        return ["--scene", "31"]

    # For broad or conversational requests, rely on the script's own NLP parser.
    return ["--command", intent]


def main() -> int:
    default_script = Path(__file__).resolve().parent / "razix_build_light.py"
    parser = argparse.ArgumentParser(
        description="Map natural-language Razix intents to razix_build_light.py CLI args"
    )
    parser.add_argument("--intent", required=True, help="Natural-language request")
    parser.add_argument(
        "--script-path",
        default=str(default_script),
        help="Path to razix_build_light.py (default: bundled copy in this skill)",
    )
    parser.add_argument("--repo", help="GitHub repo override: owner/name")
    parser.add_argument("--workflow", help="Workflow name filter")
    parser.add_argument("--ip", help="WiZ bulb IP override")
    parser.add_argument("--token", help="GitHub token override")
    parser.add_argument("--delay", type=float, help="Lightshow phase delay seconds")
    parser.add_argument("--json", action="store_true", help="Append --json")
    parser.add_argument("--dry-run", action="store_true", help="Print command only")
    args = parser.parse_args()

    script_path = Path(args.script_path)
    if not script_path.exists():
        print(f"Error: script not found: {script_path}", file=sys.stderr)
        return 2

    intent_args = build_args_from_intent(args.intent)
    if intent_args and intent_args[0] == "apple-music-sync":
        sync_script = Path(__file__).resolve().parent / "apple_music_sync.py"
        cmd = [sys.executable, str(sync_script)]
        cmd.extend(intent_args[1:]) # Pass --mode, --scene-id, etc.
        if args.ip:
            cmd.extend(["--ip", args.ip])
        print("Executing Apple Music Sync:", shlex.join(cmd))
        if args.dry_run:
            return 0
        result = subprocess.run(cmd)
        return result.returncode

    cmd = [sys.executable, str(script_path)]
    cmd.extend(intent_args)

    if args.repo:
        cmd.extend(["--repo", args.repo])
    if args.workflow:
        cmd.extend(["--workflow", args.workflow])
    if args.ip:
        cmd.extend(["--ip", args.ip])
    if args.token:
        cmd.extend(["--token", args.token])
    if args.delay is not None:
        cmd.extend(["--delay", str(args.delay)])
    if args.json:
        cmd.append("--json")

    print("Executing:", shlex.join(cmd))

    if args.dry_run:
        return 0

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
