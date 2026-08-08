# Multiply Harbor Strands

Self-contained multiply rollout using the SDK v0.3 `HarborBackend` with the Strands agent integration. The backend packages this rollout project as a wheel, installs it inside each Harbor trial, and runs the trial in a SkyPilot Sandbox. The Harbor task definition is kept inside this rollout folder under `multiply_harbor_task/`.

Run from the project root:

```bash
osmosis --json doctor
osmosis --json eval submit configs/eval/multiply-harbor-strands.toml --yes
osmosis --json train submit configs/training/multiply-harbor-strands.toml
```

## Sandbox environment

`multiply_harbor_task/environment/Dockerfile` defines only the task environment. Do not copy rollout source or install `osmosis-ai` there: `HarborBackend` preinstalls the bundle dependencies, then installs the rollout wheel per trial. `main.py` prewarms the task image and agent setup before the server accepts traffic. You do not build or push the image, configure registry credentials, or choose a cluster.
