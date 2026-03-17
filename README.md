# WiZ Light Control Skill

This repository provides a Gemini CLI skill to control WiZ smart bulbs via natural language, with bonus capabilities for fetching Razix GitHub Actions build status and syncing light states to build outcomes.

## Core Features

- **WiZ Control**: Natural language commands for controlling smart bulbs.
- **Razix Integration**: Check build status, sync light color to build results, and view fun build stats.

## Quick Usage

Run from any directory:

```bash
python3 /Users/phanisrikar/.codex/skills/wiz-light-control/scripts/run_razix_intent.py --intent "sync build light"
```

Or run from this repo backup copy:

```bash
python3 skills/wiz-light-control/scripts/run_razix_intent.py --intent "last build status"
```

## Common Intents

- `last build status`
- `sync build light`
- `razix fun stats`
- `razix fun stats lightshow`

## Optional Overrides

- `--repo owner/name`
- `--workflow "CI Build"`
- `--ip 192.168.0.120`
- `--token <github_token>`
- `--delay 1.2`
- `--json`

## Notes

- If GitHub API limits are hit, set `GITHUB_TOKEN` or pass `--token`.
- Keep `wiz_control.py` next to `razix_build_light.py` for imports to work.
