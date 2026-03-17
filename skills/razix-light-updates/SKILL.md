---
name: razix-light-updates
description: Use the local `razix_build_light.py` CLI to fetch Razix GitHub Actions build updates and control a WiZ light, including natural-language requests mapped to script arguments. Trigger this skill when users ask for Razix build status, syncing build state to lights, fun stats/lightshows, or quick NLP commands like "sync build light", "last build status", and "razix fun stats lightshow".
---

# Razix Light Updates

## Overview

Use this skill to run fast Razix status and light-control tasks from natural language.
Prefer deterministic CLI flags when possible, and fall back to `--command` for free-form requests.

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
python3 "$CODEX_HOME/skills/razix-light-updates/scripts/run_razix_intent.py" \
  --intent "razix fun stats lightshow" \
  --repo "Pikachuxxxx/Razix" \
  --ip "192.168.0.120"
```

## Workflow

1. Confirm you are in the repo containing `razix_build_light.py`, or pass `--script-path` to the wrapper.
2. Prefer explicit flags for reliability:
- Build snapshot: `--status`
- Sync build color to light: `--status --set-light`
- Metrics view: `--status --fun-stats`
- Multi-phase show: `--fun-lightshow`
3. Use NLP mode (`--command` or wrapper `--intent`) for conversational requests.
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
