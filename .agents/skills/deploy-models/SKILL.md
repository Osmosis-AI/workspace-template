---
name: deploy-models
description: Use when the user explicitly asks to deploy or undeploy a LoRA model for inference, choose a checkpoint to serve, or query a deployed model's OpenAI-compatible endpoint.
---

# Deploy Models

Deployment is never automatic: deploy, undeploy, and endpoint calls happen only when the user explicitly asks.

Run model commands inside the connected repository for Git-derived scope. From any other directory, select the exact platform workspace with root `osmosis --workspace <workspace-name> ...`; explicit-scope JSON reports `workspace.name` without fabricated local Git fields.

## Choose a checkpoint

```bash
osmosis --json model list
osmosis --json model info <lora-model-name>
```

Checkpoints from finished training runs appear as LoRA models. When choosing among them, prefer the highest training reward, and confirm the choice with the user before deploying. `model info` reports a model's checkpoint step, training reward, Hugging Face upload status, deployment status, `inference_model`, and `platform_url`.

## Deploy / undeploy

```bash
osmosis --json model deploy <lora-model-name>
osmosis --json model undeploy <lora-model-name>
```

Both are idempotent, and base models cannot be deployed. A workspace can have at most 5 inference deployments — `model list` reports `active_deployments` and `max_active_deployments`; when at the limit, undeploy a model instead of retrying.

## Query the endpoint

Deployed models serve an OpenAI-compatible API at `https://inference.osmosis.ai/v1`:

- `POST /chat/completions`
- Header `Authorization: Bearer $OSMOSIS_API_KEY` (an Osmosis API key)
- `model` set to the `inference_model` value from `osmosis --json model info` (`<base_model_path>:<lora-model-name>`)
- `stream: true` is supported

`osmosis model info <lora-model-name>` prints a ready-to-run request for deployed models.

## API key

`OSMOSIS_API_KEY` is an Osmosis API key kept in `.env`. If it's unset, ask the user to create one on the platform's API Keys page (`model info` prints the link) and add it to `.env` themselves — never ask for the secret in chat or print its value. `.env` is not auto-exported to the shell; load it with `set -a && source .env && set +a` before running curl commands that reference the variable.
