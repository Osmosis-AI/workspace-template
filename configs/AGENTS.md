# Training, Eval, and Benchmark Configs

Configs are workspace-scoped and must stay in their canonical directories.

## Canonical Paths

- Training: `configs/training/<name>.toml`
- Eval: `configs/eval/<name>.toml`
- Benchmark: `configs/benchmark/<name>.toml`

Do not place these configs elsewhere. The CLI validates these locations.

For AI agents or automation, prefer `osmosis --json ...` for structured output or `osmosis --plain ...` for low-noise text.

## Supplying Secret Values

This applies to training, eval, and benchmark configs alike. Names under `[secrets].required` may be supplied at submit via `--secrets-file`, the environment, or an interactive prompt instead of a stored record; first hit wins. Those values are never saved and must be re-supplied on every run. Create every other record referenced by a config with `osmosis secret set <NAME>`. Never write a secret value into a TOML.

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

## Benchmark Configs

Start from the default template:

```bash
osmosis --json benchmark list
osmosis --json benchmark info <benchmark-key>
cp configs/benchmark/default.toml configs/benchmark/<run-name>.toml
```

Required fields:

- `[experiment].benchmark` identifies a benchmark already added to the current workspace, by key, name, or ID. `benchmark list` prints the key and the name.
- Use `benchmark info` before editing selectors to verify task sets, categories, harness and judge requirements and the full task manifest. In JSON output, every task's `difficulty` is `easy`, `medium`, `hard`, or `null`; `null` means the source did not provide a difficulty, so never infer one. All three identifiers are exact and case-sensitive.
- A Harbor registry benchmark's task list pages in after it is added. Submit only when `osmosis --json benchmark list` reports `sync_status = "ready"`; a `failed` entry carries a `sync_error`, and its `platform_url` opens the benchmark's page; retry the sync from that page in the Platform.
- One or more `[[agents]]` entries, each with an `[agents.model]` table.
- `[agents.model].type` is `provider`, `endpoint`, or `hosted`.
- Provider and endpoint models use `api_key_secret` to reference a Platform secret record by name. Never put the secret value in the config.
- `hosted` runs one of the workspace's own LoRA models and takes `base_model` plus `lora_model_name`, both from `osmosis --json model list --type lora`: `base_model` is the LoRA model's base model, `lora_model_name` is the LoRA model name. Deploy it with `osmosis model deploy` first; an undeployed LoRA model, or a `base_model` that disagrees with what it was trained on, is rejected. `hosted` takes no `api_key_secret`.
- `cursor-cli` requires a per-agent `harness_api_key_secret` set to `CURSOR_API_KEY` (the variable that harness reads). Create that record with `osmosis secret set CURSOR_API_KEY`. Any other value is rejected. Mini SWE-agent reuses the model's `api_key_secret` and rejects `harness_api_key_secret`. Omit `harness_api_key_secret` for every other harness.
- `benchmark info` reports `requires_judge_model` and `requires_judge_api_key`. Both true (HLE, GDPVal): `[execution].judge_api_key_secret` is required and `[execution].judge_model` is optional; omit it to use the benchmark's default judge model. Only `requires_judge_api_key` (BrowseComp): `judge_api_key_secret` is required and must hold an OpenAI key, and `judge_model` is rejected. Both false: each field is rejected.
- A registry dataset whose verifier reads its own credentials names secret records in `[verifier].required`, at most 16; each is delivered under its own name. Managed benchmarks model their credentials in the catalog and reject the section.

Credential and environment rules:

- A provider or endpoint model's `api_key_secret` name cannot also appear in top-level `[env]` or that agent's `[agents.env]`.
- Model `api_key_secret` cannot reference the runner-reserved names `DAYTONA_API_KEY`, `DAYTONA_API_URL`, `SKYPILOT_SERVICE_ACCOUNT_TOKEN`, or `SKYPILOT_API_SERVER_ENDPOINT`. Those are Platform-managed sandbox plumbing; store model credentials under a different Platform secret record name.
- A `judge_api_key_secret` name, or any secret named in `[verifier].required`, cannot also appear in top-level `[env]` or any `[agents.env]`.
- `CURSOR_API_KEY` cannot appear in top-level `[env]` or the corresponding agent's `[agents.env]`; the resolved Cursor secret owns that variable.

Optional sections:

- `[tasks]` narrows task scope; omit it to run all tasks. Prefer exactly one of `task_set`, `task_names`, or `categories` so the paid scope is unambiguous.
- `task_set = "parity"` takes precedence over `task_names` and `categories` when combined; the other selectors are ignored. Do not leave ignored selectors in the config.
- `task_names` uses exact benchmark task IDs, such as `terminal-bench/git-multibranch`; prefer it for bounded or smoke runs. A category can resolve to many tasks, so verify its scope separately before approval. The pre-submit confirmation shows only the category count, not the resolved task count.
- Before submitting HLE, recommend `[tasks].task_set = "parity"` so the result is comparable with published HLE scores. Full HLE runs and custom task selections remain supported.
- A run appears on the benchmark's leaderboard only when it covers the full task set or is a parity run on a benchmark whose parity set is leaderboard-eligible (currently HLE); `task_names` and `categories` subset runs never rank.
- `[execution]` controls attempts, concurrency, timeout, retries, pass threshold, and optional judge settings.
- `[env]` provides literal environment variables to every agent.
- `[agents.env]` provides literal environment variables to one agent and overrides the same global key.

Use Osmosis field names such as `attempts_per_task` and `max_concurrent_attempts`. Harbor configuration fields are not part of this config contract.

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
osmosis benchmark list
osmosis benchmark info <benchmark-key>
osmosis benchmark submit configs/benchmark/<name>.toml
osmosis benchmark runs list
osmosis benchmark runs info <run-name>
osmosis benchmark runs logs <run-name>
osmosis benchmark runs stop <run-name>
osmosis benchmark runs download <run-name>
osmosis train submit configs/training/<name>.toml
osmosis train info <run-name>
```

`benchmark runs stop` applies only to pending, queued, or running runs.

`benchmark runs download` is unavailable for pending or queued runs. A running run downloads a current snapshot; use `--overwrite` when refreshing it.
