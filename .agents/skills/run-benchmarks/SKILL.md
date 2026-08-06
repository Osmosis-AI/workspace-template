---
name: run-benchmarks
description: Use when configuring, submitting, monitoring, stopping, or downloading an Osmosis managed benchmark run; selecting benchmark tasks; choosing agent harnesses and models; or diagnosing benchmark failures.
---

# Run Benchmarks

Use managed benchmarks to compare agent harness and model combinations on a workspace benchmark. Benchmark runs execute on Platform-managed infrastructure and do not use the workspace's rollout code.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md`.
2. Run `osmosis --json doctor`.
3. Run `osmosis --json benchmark list` to confirm the benchmark is present in the current workspace and copy its key. Check its `sync_status`: only `ready` can be submitted. A `failed` row reports a `sync_error`, and its `platform_url` opens the benchmark's page; retry the sync from that page in the Platform.
4. Run `osmosis --json benchmark info <key>` and inspect its task sets, categories, complete task manifest, harness and judge requirements, `default_harness` and pass threshold. The response also carries the benchmark's leaderboard and the workspace's runs on it. Every task's `difficulty` is `easy`, `medium`, `hard`, or `null`; treat `null` as source metadata not provided and never infer a difficulty.
5. Copy `configs/benchmark/default.toml` to a descriptive filename under the same directory.
6. Set `[experiment].benchmark` to the benchmark's key, name, or ID. All three are exact and case-sensitive.
7. Before an HLE submission, recommend `[tasks] task_set = "parity"` so the result is comparable with published HLE scores. Full HLE runs and custom task selections remain allowed when the user intends them.
8. Never define `HF_TOKEN` in literal env; it is reserved by the runner, and a gated benchmark's dataset credential is platform infrastructure that a run never supplies.
9. Match the `[execution]` judge fields to `requires_judge_model` and `requires_judge_api_key` from step 4. Both true: `judge_api_key_secret` is required, and `judge_model` may be omitted to use the benchmark default. Only `requires_judge_api_key`: `judge_api_key_secret` is required and `judge_model` is rejected. Both false: each field is rejected. Create the record with `osmosis secret set <NAME>`.
10. Configure at least one `[[agents]]` entry and its `[agents.model]` table; a run supports at most 8 agents. If an agent's harness requires separate authentication, set the per-agent `harness_api_key_secret` described below.
11. Create every referenced secret record with `osmosis secret set <NAME>`; never write secret values into TOML.

## Task selection

- Omit `[tasks]` to run the full benchmark.
- Prefer exactly one of `task_set`, `task_names`, or `categories`; multiple selectors can obscure or expand paid task scope.
- Use the named task sets, category names, and exact task IDs returned by `benchmark info`; do not invent selectors.
- `task_set = "parity"` takes precedence over `task_names` and `categories` when combined, so remove the ignored selectors. For HLE, recommend parity for comparability with published scores.
- Use `task_names` for exact benchmark task IDs, such as `terminal-bench/git-multibranch`, and prefer it for bounded or smoke runs.
- Use `categories` cautiously: a category can resolve to many tasks. Verify its task scope separately before approval; the pre-submit confirmation shows only the category count, not the resolved task count.
- Start with a small explicit task list when validating a new agent setup.
- A run ranks on the benchmark's leaderboard only when it covers the full task set or is a parity run on a benchmark whose parity set is leaderboard-eligible (currently HLE); subset runs never rank, so tell the user when a proposed selection is not leaderboard-eligible.

## Agents and models

- `type = "provider"` uses a provider model name and `api_key_secret`.
- `type = "endpoint"` also requires `base_url`; optional `extra_headers` contain literal header values, not secrets.
- `type = "hosted"` runs one of the workspace's own LoRA models. Take both values from `osmosis --json model list --type lora`: `base_model` is the LoRA model's base model, `lora_model_name` is the LoRA model name. It must already be deployed with `osmosis model deploy`, and a `base_model` that disagrees with what the LoRA model was trained on is rejected. No `api_key_secret` applies.
- Supported harnesses include `codex`, `claude-code`, `terminus-2`, `openhands`, `cursor-cli`, `mini-swe-agent`, `gemini-cli`, and `opencode`. Every agent still needs its own `[[agents]]` entry: a benchmark that runs only its official scaffold rejects every harness, and one that merely allows a harness runs its official scaffold when `harness` is omitted. `benchmark info` reports which applies and names the default.
- `cursor-cli` and `mini-swe-agent` require `harness_api_key_secret`. Set it to `CURSOR_API_KEY` for `cursor-cli` or `MSWEA_API_KEY` for `mini-swe-agent` (the variables the harnesses read); any other value is rejected. Omit the field for harnesses that do not require separate authentication.
- When `benchmark info` reports a `default_harness`, that is the scaffold the benchmark's published scores were measured on. Recommend it, and call out the loss of comparability before proposing another.
- `[env]` applies literal variables to every agent. `[agents.env]` applies them only to that agent.

## Credentials and environment

- Create each model, harness, or judge secret record with `osmosis secret set <NAME>` before submission.
- For each provider or endpoint agent, its model `api_key_secret` name cannot also appear in top-level `[env]` or that agent's `[agents.env]`.
- Model `api_key_secret` cannot reference runner-reserved `HF_TOKEN`, `DAYTONA_API_KEY`, `DAYTONA_API_URL`, `SKYPILOT_SERVICE_ACCOUNT_TOKEN`, or `SKYPILOT_API_SERVER_ENDPOINT`. The Daytona and SkyPilot names are Platform-managed sandbox plumbing; choose another Platform record name for model credentials.
- A `judge_api_key_secret` name, or any secret named in `[verifier.env]`, cannot also appear in top-level `[env]` or any `[agents.env]`.
- Do not define `CURSOR_API_KEY` or `MSWEA_API_KEY` in top-level `[env]` or the corresponding agent's `[agents.env]`; the resolved harness secret record owns that variable.
- `HF_TOKEN` is reserved in literal env for every benchmark; never put it in top-level `[env]` or any `[agents.env]`.

## Submit

Review the benchmark, task scope, agent count, attempts, concurrency, and referenced secret scopes in the confirmation output. If the benchmark is HLE and the task set is not `parity`, call out the CLI's recommendation before asking the user to approve the run; do not block an intentional full run or custom subset. Benchmark runs can incur model and sandbox charges, so use `--yes` only after the user has approved the run.

```bash
osmosis --json benchmark submit configs/benchmark/<name>.toml --yes
```

The structured result includes the generated run name, task count, status, and `platform_url`.

## Monitor and inspect

Run-lifecycle commands live under `benchmark runs` and take the generated run name:

```bash
osmosis --json benchmark runs list
osmosis --json benchmark runs info <run-name>
osmosis --json benchmark runs logs <run-name>
```

- Use `benchmark runs list` to find recent runs and their status.
- Use `benchmark runs info` to inspect configuration, agents, progress, result totals, metrics, and `platform_url`.
- Use `benchmark runs logs` to diagnose a pending, running, or failed run. If JSON output returns `next_cursor`, pass it with `--cursor` to retrieve older entries.
- Bare `benchmark list` and `benchmark info` act on benchmarks themselves (the workspace list and one benchmark's summary, leaderboard, and runs), while everything that manages an individual run lives under `benchmark runs`.
- In `benchmark info` leaderboard output, a `#N*` rank with the table caption means the entry is tied for first (not statistically distinguishable from the leader), and a `[parity]` suffix on the agent label marks a parity-task-set entrant.

## Stop

Stopping a run is a user-initiated mutation. Confirm the exact run and obtain approval before passing `--yes`:

```bash
osmosis --json benchmark runs stop <run-name> --yes
```

Only pending, queued, or running runs can be stopped.

## Download

The default download includes `summary.csv` and `results.csv`. Select `summary`, `results`, `artifacts`, or `logs` with a comma-separated `--type` value, or use `all`:

```bash
osmosis --json benchmark runs download <run-name> --yes
osmosis --json benchmark runs download <run-name> --type all --yes
```

Downloads use this fixed layout under `.osmosis/benchmarks/<run-name>/` by default:

```text
summary.csv
results.csv
logs.txt
artifacts/<result-id>/<path>
```

Pending and queued runs do not have downloadable outputs. A running run downloads a current snapshot. Re-running the command skips complete files unless `--overwrite` is set, so use the same command to resume a partial download and add `--overwrite` when refreshing a running snapshot.

## Guardrails

- Do not use Harbor config fields; benchmark TOML is an Osmosis-owned contract.
- Do not submit local dataset or task paths. The selected workspace benchmark owns its source and manifest.
- Do not place secrets in `[env]`, `[agents.env]`, or endpoint `extra_headers`.
- Prefer one agent and a small task selection for the first smoke run.
- Do not submit a paid full run without explicit user approval.
