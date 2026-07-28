# Multiply Harbor Strands

Self-contained multiply rollout using `HarborBackend` with the Strands agent integration. Each Harbor trial runs in a SkyPilot Sandbox. The Harbor task definition is kept inside this rollout folder under `multiply_harbor_task/`.

Run from the project root:

```bash
osmosis --json doctor
osmosis --json eval submit configs/eval/multiply-harbor-strands.toml --yes
osmosis --json train submit configs/training/multiply-harbor-strands.toml
```

## Sandbox environment

`multiply_harbor_task/environment/Dockerfile` defines the trial environment. Osmosis builds it and runs the sandbox from it — you do not build or push the image, configure registry credentials, or choose a cluster.
