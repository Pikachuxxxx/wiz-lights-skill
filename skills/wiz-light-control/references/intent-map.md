# Intent Map

Use this mapping before falling back to `--command`.

## Phrase Patterns to Flags

- `sync build light` -> `--status --set-light`
- `last build status` / `build status` / `status` -> `--status`
- `fun stats` -> `--status --fun-stats`
- `fun stats lightshow` -> `--status --fun-stats --fun-lightshow`
- `lightshow` / `aura` / `party` -> `--fun-lightshow`
- `music` / `rhythm` -> `--scene 31`

## Fallback

For anything not covered above, pass through:

```bash
python3 razix_build_light.py --command "<user request>"
```

## Common Overrides

- `--repo owner/name`
- `--workflow "filter"`
- `--ip 192.168.x.x`
- `--token <github-token>`
- `--scene 31`
- `--delay 1.2`
- `--json`
