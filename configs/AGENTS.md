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
- `branch` is optional and pins training code to a branch.
- `commit_sha` is optional and pins training code to a specific pushed commit.
- `branch` and `commit_sha` are mutually exclusive; omit both to use the connected repository's default branch.

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
- `[env]` for non-secret literal environment variables.
- `[secrets]` for platform secret record names. Training configs may omit `[secrets]` when no secret refs are needed; if the section is present, it must include `required`.

### Environment Variables and Secrets

```toml
[env]
# Literal values visible in this file. Do NOT put secrets here.
LOG_LEVEL = "INFO"
MY_CONFIG = "some-value"

[secrets]
# Each name is a platform environment_secret record name. The platform resolves and injects it server-side.
# Include this block only when the rollout needs platform secret refs.
# When this block is present, it must include `required`.
required = ["OPENAI_API_KEY"]
```

Rules:

- Keys must match `^[A-Z_][A-Z0-9_]*$`.
- Secret names must match `^[A-Z][A-Z0-9_]*$`.
- The same name cannot appear in both sections.
- Env var names starting with `_OSMOSIS_` are reserved by the platform.

Inside the rollout container both sets of vars are available via `os.environ`.

## Eval Configs

Start from the default template:

```bash
cp configs/eval/default.toml configs/eval/<run-name>.toml
```

If `configs/eval/default.toml` was deleted in this workspace, recover the shape from the repo-root fallback `.agents/skills/evaluate-rollouts/references/eval-default.toml`.

Eval configs must include `[secrets]`; default OpenAI eval configs should include `OPENAI_API_KEY`, and `required = []` is only for evaluations that need no secret refs.

Use one evaluation config per rollout/model setup. `entrypoint` must point at the rollout's Python server file; SDK-generated configs usually use `main.py`, but another filename is valid when explicitly configured. `dataset` must be a platform dataset name from `osmosis dataset list`.

```toml
[experiment]
rollout = "calculator"
entrypoint = "main.py" # SDK default; change this if the rollout uses another server file.
model_path = "openai/gpt-5-mini"      # LiteLLM-style model name
dataset = "calculator"
# branch = "my-feature"
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

[secrets]
# Default OpenAI eval models need this platform secret.
# Use required = [] only when this evaluation needs no secret refs.
required = ["OPENAI_API_KEY"]
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
