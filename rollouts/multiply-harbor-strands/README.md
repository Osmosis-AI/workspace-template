# Multiply Harbor Strands

Self-contained multiply rollout using the SDK v0.3 `HarborBackend` with the Strands agent integration. The backend packages this rollout project as a wheel, installs it inside each Harbor trial, and runs the trial in a managed OpenSandbox sandbox on the platform. The Harbor task definition is kept inside this rollout folder under `multiply_harbor_task/`.

`main.py` selects `EnvironmentType.OPENSANDBOX` when `OPENSANDBOX_API_KEY` is set, which the platform's rollout server does for managed eval and training runs, `EnvironmentType.DAYTONA` when only `DAYTONA_API_KEY` is set, and `EnvironmentType.DOCKER` otherwise. Managed runs need no sandbox secret. Local `osmosis eval run` uses the host Docker runtime unless your shell exports one of those keys; on Linux the sandbox cannot reach the local model bridge, so the run starts a `cloudflared` tunnel automatically (keep `cloudflared` on `PATH`, or pass `--listener-port <port> --advertise-url <url>` to use a tunnel you manage).

To use your own Daytona account instead, set `ENVIRONMENT_TYPE = EnvironmentType.DAYTONA`, create the credential record with `osmosis secret set DAYTONA_API_KEY`, add it to `[secrets].required` in the eval config, and add a `[secrets]` section with `required = ["DAYTONA_API_KEY"]` to the training config.

Run from the project root:

```bash
osmosis --json doctor
osmosis --json eval run configs/eval/multiply-harbor-strands.toml
osmosis --json eval submit configs/eval/multiply-harbor-strands.toml --yes
osmosis --json train submit configs/training/multiply-harbor-strands.toml
```

## Sandbox environment

Trials start from the prebuilt `docker_image` in `multiply_harbor_task/task.toml`, which OpenSandbox requires, so that image must already contain Python and the task's system packages. `multiply_harbor_task/environment/Dockerfile` describes the same environment. `main.py` has Docker and Daytona build it, so their trials get the SDK's dependency pre-install; OpenSandbox always runs `docker_image`, so its trials install the bundle's dependencies each time. Do not copy rollout source or install `osmosis-ai` there: `HarborBackend` preinstalls the bundle dependencies, then installs the rollout wheel per trial. `main.py` prewarms the task image and agent setup before the server accepts traffic. You do not build or push the image, configure registry credentials, or choose a cluster.

With SDK 0.3.3 and your own Daytona account, the built-in Daytona environment's default `delete=True` also applies provider-side cleanup: stop after 60 minutes of Daytona-observed inactivity, then delete immediately. For workflows with longer idle periods, set `kwargs={"auto_stop_interval_mins": 120}` on `HarborEnvironmentConfig` in `main.py`, or use `0` to disable automatic stopping. This idle timer is separate from workflow execution timeouts.
