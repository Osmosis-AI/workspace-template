# Training and Eval Configs

Configs are workspace-scoped and must stay in their canonical directories.

## Canonical Paths

- Training: `configs/training/<name>.toml`
- Eval: `configs/eval/<name>.toml`

Do not place these configs elsewhere. The CLI validates these locations.

For AI agents or automation, prefer `osmosis --json ...` for structured output or `osmosis --plain ...` for low-noise text.

## Training Configs

Start from the default template:

```bash
cp configs/training/default.toml configs/training/<run-name>.toml
```

If `configs/training/default.toml` was deleted in this workspace, recover the shape from the repo-root fallback `.agents/skills/submit-training/references/training-default.toml` instead of inventing the TOML schema from memory.

Required `[experiment]` fields:

- `rollout` must match a directory under `rollouts/`.
- `entrypoint` must be a Python file relative to that rollout. SDK-generated configs usually use `main.py`, but any in-rollout Python entrypoint is valid when the config names it.
- `model_path` must be a supported base model.
- `dataset` must be a platform dataset name from `osmosis dataset list`.
- `commit_sha` is optional and pins training code to a specific pushed commit.

Common optional `[training]` fields:

- `lr`
- `total_epochs`
- `n_samples_per_prompt`
- `rollout_batch_size`
- `max_prompt_length`
- `max_response_length`
- `agent_workflow_timeout_s`
- `grader_timeout_s`

Optional sections:

- `[sampling]` for rollout sampling parameters.
- `[checkpoints]` for eval and checkpoint cadence.
- `[advanced]` for backend-specific fields.
- `[env]` for non-secret literal environment variables.
- `[secrets]` for platform secret record names.

### Environment Variables and Secrets

```toml
[env]
# Literal values visible in this file. Do NOT put secrets here.
LOG_LEVEL = "INFO"
MY_CONFIG = "some-value"

[secrets]
# Value is the name of a workspace environment_secret record, not the secret value itself. The platform resolves and injects it server-side.
OPENAI_API_KEY = "openai-api-key"
```

Rules:

- Keys must match `^[A-Z_][A-Z0-9_]*$`.
- The same key cannot appear in both sections.
- Env var names starting with `_OSMOSIS_` are reserved by the platform and forbidden in both sections.

Inside the rollout container both sets of vars are available via `os.environ`.

## Eval Configs

Start from the default template:

```bash
cp configs/eval/default.toml configs/eval/<run-name>.toml
```

If `configs/eval/default.toml` was deleted in this workspace, recover the shape from the repo-root fallback `.agents/skills/evaluate-rollouts/references/eval-default.toml`.

Use one eval config per rollout/model setup. `entrypoint` must point at the rollout's Python server file; SDK-generated configs usually use `main.py`, but another filename is valid when explicitly configured. `dataset` must be a platform dataset name from `osmosis dataset list`.

```toml
[experiment]
rollout = "calculator"
entrypoint = "main.py" # SDK default; change this if the rollout uses another server file.
model_path = "openai/gpt-5-mini"      # LiteLLM-style model name
dataset = "calculator"
# commit_sha =

[evaluation]
# Optional. Omit values to use platform defaults.
# limit = 200
# n = 3
# batch_size = 2
# pass_threshold = 1.0
# agent_workflow_timeout_s = 450
# grader_timeout_s = 150

# [env]
# LOG_LEVEL = "INFO"

# [secrets]
# OPENAI_API_KEY = "openai-api-key"
```

## Commands

```bash
osmosis doctor
osmosis dataset upload data/train.jsonl
git push
osmosis eval submit configs/eval/<name>.toml
osmosis train submit configs/training/<name>.toml
osmosis train info <run-name>
```
