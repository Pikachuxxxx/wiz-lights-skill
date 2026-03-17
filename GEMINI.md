# Gemini Instructions: WiZ Light Control

Use this repository to control WiZ smart lights and monitor Razix build status.

## Primary Scripts

- `skills/wiz-light-control/scripts/run_razix_intent.py`
- `skills/wiz-light-control/scripts/razix_build_light.py`
- `skills/wiz-light-control/scripts/wiz_control.py`

Run commands from the repository root unless absolute paths are used.

## Overview

This skill focuses on natural language control for WiZ smart lights, with bonus capabilities for reporting Razix GitHub Actions build status, syncing light states to build results, and triggering fun lightshows based on build stats.

## Intent Mapping Rules

Map user requests to deterministic flags when possible:

- `sync build light` -> `--status --set-light`
- `last build status` / `build status` / `status` -> `--status`
- `fun stats` -> `--status --fun-stats`
- `fun stats lightshow` -> `--status --fun-stats --fun-lightshow`
- `lightshow` / `aura` / `party` -> `--fun-lightshow`

If request does not fit known patterns, pass through as NLP command:

```bash
python3 skills/wiz-light-control/scripts/razix_build_light.py --command "<user request>"
```

## Common Overrides

Append these when provided by user or needed:

- `--repo owner/name`
- `--workflow "CI Build"`
- `--ip 192.168.0.120`
- `--token <github_token>`
- `--delay 1.2`
- `--json`

## Operational Behavior

1. For status requests, execute and return key fields: workflow, run id, run number, branch, commit, status, conclusion, updated time, actions URL.
2. For sync requests, execute status + light update and report bulb response.
3. If GitHub API calls fail due to limits/auth, retry with `--token` or `GITHUB_TOKEN`.
4. Keep `wiz_control.py` colocated with `razix_build_light.py`.
