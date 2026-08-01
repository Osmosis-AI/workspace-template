# Osmosis Workspace Repository

This repository is the source of truth for the rollout code, evaluation configs, and training configs linked to a single Osmosis platform workspace. Datasets in this folder are just local copies for inspecting data; the real datasets live on the platform. Run Osmosis CLI commands from within this repository so they're scoped to the linked workspace, which the CLI identifies from the GitHub `origin` remote.

## Setup

Start here after creating or joining an Osmosis platform workspace and cloning the connected workspace repository.

```bash
cd <workspace-repository>
pip install -e .
osmosis auth login
osmosis doctor
osmosis auth whoami
```

`osmosis doctor` checks that the Git remote, workspace layout, and required directories are valid. If the scaffold is missing required directories, run:

```bash
osmosis doctor --fix
```

For AI agents or automation, prefer `osmosis --json ...` for structured output or `osmosis --plain ...` for low-noise text.

## Repository Layout

```text
repository/
├── rollouts/            # AgentWorkflow + Grader code
├── configs/
│   ├── benchmark/       # Managed benchmark run configs
│   ├── eval/            # Evaluation run configs
│   └── training/        # Training run configs
├── data/                # Local dataset files for upload
├── AGENTS.md            # Workspace contract for AI coding assistants
├── CLAUDE.md            # Claude Code entrypoint for the same contract
└── pyproject.toml       # Workspace Python package
```

The CLI expects `rollouts/`, `configs/eval/`, `configs/training/`, and `data/` to exist. Benchmark configs submitted through the CLI must live under `configs/benchmark/`. Keep code and configs in their canonical paths so submissions can discover them.

## Run the Starter Example

Use the included multiply example to verify the full loop before building a custom rollout.

```bash
pip install -e rollouts/multiply-local-openai
export OPENAI_API_KEY="sk-..."
osmosis dataset upload data/multiply.jsonl
git push
osmosis eval submit configs/eval/multiply-local-openai.toml
osmosis train submit configs/training/multiply-local-openai.toml
```

The evaluation and training configs reference the uploaded platform dataset as `multiply`.

## Build Your Own Rollout

Create a blank scaffold:

```bash
osmosis rollout init my-rollout
pip install -e rollouts/my-rollout
git add rollouts/my-rollout configs/eval/my-rollout.toml configs/training/my-rollout.toml
git commit -m "add my rollout"
git push
osmosis eval submit configs/eval/my-rollout.toml
```

Or adapt one of the starter rollouts included in this repository by default: `multiply-local-strands`, `multiply-local-openai`, or `multiply-harbor-strands`.

```bash
pip install -e rollouts/multiply-local-strands
git push
osmosis eval submit configs/eval/multiply-local-strands.toml
```

Each rollout should expose one concrete `AgentWorkflow` and one concrete `Grader` from the configured entrypoint, usually `main.py`. Route policy model calls through Osmosis-supported integrations such as `OsmosisStrandsAgent` or `OsmosisAgent` so evaluation runs and training runs can collect samples and attach rewards.

## Configs and Data

Evaluation and training configs live in `configs/eval/*.toml` and `configs/training/*.toml`. Both use platform dataset names from:

```bash
osmosis dataset list
```

Push rollout code and configs, then submit evals with:

```bash
git push
osmosis eval submit configs/eval/<name>.toml
```

Managed benchmark configs live in `configs/benchmark/*.toml`. Start from the included default, then set the workspace benchmark name and agent model:

```bash
osmosis benchmark catalog list
osmosis benchmark catalog info <benchmark-key>
cp configs/benchmark/default.toml configs/benchmark/<name>.toml
```

`benchmark catalog info` shows the benchmark's key and workspace name, available task sets, categories, harness and judge requirements, the default harness its published scores were measured on, pass threshold, and implicit required secret record names. Set `[experiment].benchmark` to the key for an Osmosis-managed benchmark, or the name for a Harbor registry one, whose key pins a revision that changes when the publisher ships a new one. Use `osmosis --json benchmark catalog info <benchmark-key>` to inspect the complete task manifest and `required_secret_names` before selecting `task_names` or `categories`. Every task has a `difficulty` value of `easy`, `medium`, `hard`, or `null`; `null` means the source did not provide a difficulty, so never infer one. Create every listed secret record with `osmosis secret set NAME`; `required_secret_names` contains names only. Omit `[tasks]` to run the full benchmark.

Before submitting Humanity's Last Exam (HLE), we recommend selecting its parity task set so your result is comparable with published HLE scores:

```toml
[tasks]
task_set = "parity"
```

`task_set = "parity"` takes precedence over `task_names` and `categories`, so do not combine these selectors. Full HLE runs and custom task selections remain supported.

HLE and GDPVal also require `[execution].judge_api_key_secret`; create the referenced Platform secret record before submission. `judge_model` is optional and uses the benchmark default when omitted. Non-judge benchmarks must omit both judge fields. As one example of `required_secret_names`, HLE requires the implicit `HF_TOKEN` Platform record:

```bash
osmosis secret set <judge-secret-name>
osmosis secret set HF_TOKEN # HLE only
```

`HF_TOKEN` is reserved in literal `[env]` and `[agents.env]` for every benchmark; HLE resolves it from the Platform secret record only.

```toml
[execution]
judge_api_key_secret = "<judge-secret-name>"
# judge_model = "<provider/model>" # Optional; omit for the benchmark default.
```

Submit the reviewed config with:

```bash
osmosis benchmark submit configs/benchmark/<name>.toml
```

Manage the resulting run by name or ID:

```bash
osmosis benchmark list
osmosis benchmark info <run-name-or-id>
osmosis benchmark logs <run-name-or-id>
osmosis benchmark stop <run-name-or-id>
osmosis benchmark download <run-name-or-id>
```

A Harbor registry benchmark's task list pages in from the registry after it is added. `benchmark catalog list` reports its `sync_status`; submitting before it is `ready` fails. A `failed` row reports a `sync_error` and a `platform_url` to retry its sync from.

`benchmark stop` applies only to pending, queued, or running runs.

`benchmark download` accepts `summary`, `results`, `artifacts`, `logs`, or `all`; the default is `summary,results`. Downloads use this fixed layout under `.osmosis/benchmarks/<run-name>/`:

```text
summary.csv
results.csv
logs.txt
artifacts/<result-id>/<path>
```

Pending and queued runs do not have downloadable outputs. Downloads from a running run are snapshots; use `--overwrite` to refresh existing files.

Upload local JSONL, CSV, or Parquet datasets when you are ready to train:

```bash
osmosis dataset upload data/<dataset>.jsonl
```

Never put secret values in TOML. The `[secrets]` section must contain a `required` list of platform secret record names that the platform resolves server-side and injects as environment variables with the same names. Evaluation configs must include `[secrets]`; default OpenAI eval configs should include `OPENAI_API_KEY`, and `required = []` is only for evaluations that need no secret refs. Training configs may omit `[secrets]`, but any `[secrets]` section must include `required`. Create secret records with `osmosis secret set NAME`; personal scope is the default, and `--scope workspace` creates workspace-shared secrets.

## Git Sync, Eval, and Training

Push rollout code and configs to the connected workspace repository before submitting evaluation runs or training runs. Automatic Git Sync runs from the default branch, and platform runs use the synced code version.

```bash
git add .
git commit -m "add rollout"
git push
osmosis eval submit configs/eval/<name>.toml
osmosis train submit configs/training/<name>.toml
```

Use `commit_sha` in evaluation or training configs when you need to pin a run to a specific pushed commit.

Inspect training runs and deploy LoRA models:

```bash
osmosis train info <run-name>
osmosis model list
osmosis model info <lora-model-name>
osmosis model deploy <lora-model-name>
osmosis model undeploy <lora-model-name>
```

Deployed models serve an OpenAI-compatible API at `https://inference.osmosis.ai/v1` (`model` = `<base_model_path>:<lora-model-name>`, e.g. `Qwen/Qwen3.6-35B-A3B:code-reviewer-v1`, authenticated with an Osmosis API key as the bearer token). The model's detail page on the platform has ready-to-run snippets.

## AI-Assisted Workflow

This workspace includes project-local Agent Skills in `.agents/skills/`:

- `plan-training`
- `create-rollouts`
- `evaluate-rollouts`
- `run-benchmarks`
- `debug-rollouts`
- `submit-training`
- `deploy-models`

`AGENTS.md` contains the always-loaded workspace contract. `CLAUDE.md` imports that contract for Claude Code, and `.claude/skills/<skill-name>` symlinks expose the same skills while pointing back to the canonical `.agents` directories.

A useful initial prompt for a coding agent:

```text
I want to train a model for <task> in this Osmosis workspace. Start with the `plan-training` skill: read the workspace instructions, help me settle the dataset plan, and propose the next step before creating rollouts, running evaluation runs, or submitting a training run.
```
