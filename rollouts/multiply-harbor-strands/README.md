# Multiply Harbor Strands

Self-contained multiply rollout using the SDK v0.3 `HarborBackend` with the Strands agent integration. The backend packages this rollout project as a wheel, installs it inside each Harbor trial, and runs the trial in a Daytona Sandbox by default. The Harbor task definition is kept inside this rollout folder under `multiply_harbor_task/`.

Local eval keeps the configured `ENVIRONMENT_TYPE`. Daytona and other Harbor cloud environments cannot reach this machine, so `osmosis eval run` starts a `cloudflared` tunnel to the local model bridge automatically; keep `cloudflared` on `PATH`, or pass `--listener-port <port> --advertise-url <url>` to use a tunnel you manage. Optional `--tunnel cloudflared` only forces that tunnel, and switching `ENVIRONMENT_TYPE` in `main.py` to `EnvironmentType.DOCKER` is for when you deliberately want the host Docker runtime.

Create the Daytona credential record before running or submitting this rollout:

```bash
osmosis secret set DAYTONA_API_KEY
```

Run from the project root:

```bash
osmosis --json doctor
osmosis --json eval run configs/eval/multiply-harbor-strands.toml
osmosis --json eval submit configs/eval/multiply-harbor-strands.toml --yes
osmosis --json train submit configs/training/multiply-harbor-strands.toml
```

## Sandbox environment

`multiply_harbor_task/environment/Dockerfile` defines only the task environment. Do not copy rollout source or install `osmosis-ai` there: `HarborBackend` preinstalls the bundle dependencies, then installs the rollout wheel per trial. `main.py` prewarms the task image and agent setup before the server accepts traffic. You do not build or push the image, configure registry credentials, or choose a cluster.

With SDK 0.3.3, the built-in Daytona environment's default `delete=True` also applies provider-side cleanup: stop after 60 minutes of Daytona-observed inactivity, then delete immediately. For workflows with longer idle periods, set `kwargs={"auto_stop_interval_mins": 120}` on `HarborEnvironmentConfig` in `main.py`, or use `0` to disable automatic stopping. This idle timer is separate from workflow execution timeouts.
