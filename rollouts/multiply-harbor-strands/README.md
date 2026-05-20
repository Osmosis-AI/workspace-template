# Multiply Harbor Strands

Self-contained multiply rollout using `HarborBackend` with a Daytona Harbor
sandbox and the Strands agent integration. The Harbor task definition is kept
inside this rollout folder under `multiply_harbor_task/`.

Run from the project root:

```bash
osmosis --json doctor
osmosis --json eval run configs/eval/multiply-harbor-strands.toml --limit 1 --fresh
osmosis --json train submit configs/training/multiply-harbor-strands.toml
```

Managed training requires a registered `DAYTONA_API_KEY` environment secret.
