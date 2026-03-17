---
name: wiz-light-control
description: Control WiZ smart lights using natural language, featuring bonus capabilities for monitoring Razix GitHub Actions build status, syncing light states to build outcomes, and generating fun build-related stats and lightshows.
---

# WiZ Light Control

## Overview

Use this skill for easy WiZ light control and Razix build status monitoring via natural language.
It supports deterministic CLI flags for reliability and a flexible NLP mode for conversational requests.

## Quick Start

From the repository root containing `razix_build_light.py`:

```bash
python3 razix_build_light.py --status
python3 razix_build_light.py --status --set-light
python3 razix_build_light.py --status --fun-stats
python3 razix_build_light.py --fun-lightshow
python3 razix_build_light.py --command "sync build light"
```

Use the bundled wrapper for intent-to-args mapping:

```bash
python3 "$CODEX_HOME/skills/wiz-light-control/scripts/run_razix_intent.py" \
  --intent "razix fun stats lightshow" \
  --repo "Pikachuxxxx/Razix" \
  --ip "192.168.0.120"
```

## Trigger Conditions
Activate this skill when users:
1. Ask to control WiZ smart lights (e.g., "turn on the lights", "set lights to blue", "dim the lights").
2. Ask about Razix build status (last build, current status).
3. Want to sync their WiZ lights to the Razix build state.
4. Request "fun stats" or "lightshows" related to Razix builds.
5. Use natural language commands like "sync build light", "aura", or "party".

## Workflow

1. Map User Intent: Translate natural language requests into deterministic CLI arguments for `razix_build_light.py`.
2. Handle General Lighting: For basic requests like "set lights to blue" or "turn off lights", use the `--command` flag.
3. Confirm you are in the repo containing `razix_build_light.py`, or pass `--script-path` to the wrapper.
4. Prefer explicit flags for reliability:
- Build snapshot: `--status`
- Sync build color to light: `--status --set-light`
- Metrics view: `--status --fun-stats`
- Multi-phase show: `--fun-lightshow`
5. Use NLP mode (`--command` or wrapper `--intent`) for conversational requests.

## Expert Procedure

Always use the intent wrapper script to execute commands for maximum stability:

```bash
python3 "$CODEX_HOME/skills/wiz-light-control/scripts/run_razix_intent.py" \
  --intent "<user request>"
```
4. Add overrides when needed:
- `--repo owner/name`
- `--workflow "<substring>"`
- `--ip <bulb-ip>`
- `--token <github-token>`
- `--scene <scene-id>`
- `--delay <seconds>`
- `--json`
5. On failures, capture stderr and retry with a token for GitHub API limits/private data.

## Reference

Read [intent-map.md](references/intent-map.md) for the canonical phrase-to-CLI mapping used by this skill.

## Resources

- `scripts/run_razix_intent.py`: Converts natural-language intent into stable CLI args and executes `razix_build_light.py`.
- `references/intent-map.md`: Documents supported phrase patterns and resulting flags.
