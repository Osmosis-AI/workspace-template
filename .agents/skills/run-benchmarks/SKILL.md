---
name: run-benchmarks
description: Use when configuring or submitting an Osmosis managed benchmark run, selecting benchmark tasks, choosing one or more agent harnesses and models, or diagnosing benchmark submit validation errors.
---

# Run Benchmarks

Use managed benchmarks to compare agent harness and model combinations on a workspace benchmark. Benchmark runs execute on Platform-managed infrastructure and do not use the workspace's rollout code.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md`.
2. Run `osmosis --json doctor`.
3. Confirm the benchmark is already present in the current workspace in the Platform UI.
4. Copy `configs/benchmark/default.toml` to a descriptive filename under the same directory.
5. Set `[experiment].benchmark` to the benchmark's user-facing workspace name (exact, case-sensitive).
6. Before an HLE submission, recommend `[tasks] task_set = "parity"` so the result is comparable with published HLE scores. Full HLE runs and custom task selections remain allowed when the user intends them.
7. For HLE, create the implicit Platform secret record with `osmosis secret set HF_TOKEN`; never define `HF_TOKEN` in literal env.
8. HLE and GDPVal require `[execution].judge_api_key_secret`; create that Platform record with `osmosis secret set <NAME>`. `judge_model` may be omitted to use the benchmark default. Omit both judge fields for non-judge benchmarks.
9. Configure at least one `[[agents]]` entry and its `[agents.model]` table. If its harness requires separate authentication, set the per-agent `harness_api_key_secret` described below.
10. Create every referenced secret record with `osmosis secret set <NAME>`; never write secret values into TOML.

## Task selection

- Omit `[tasks]` to run the full benchmark.
- Prefer exactly one of `task_set`, `task_names`, or `categories`; multiple selectors can obscure or expand paid task scope.
- `task_set = "parity"` takes precedence over `task_names` and `categories` when combined, so remove the ignored selectors. For HLE, recommend parity for comparability with published scores.
- Use `task_names` for exact benchmark task IDs, such as `terminal-bench/git-multibranch`, and prefer it for bounded or smoke runs.
- Use `categories` cautiously: a category can resolve to many tasks. Verify its task scope separately before approval; the pre-submit confirmation shows only the category count, not the resolved task count.
- Start with a small explicit task list when validating a new agent setup.

## Agents and models

- `type = "provider"` uses a provider model name and `api_key_secret`.
- `type = "endpoint"` also requires `base_url`; optional `extra_headers` contain literal header values, not secrets.
- `type = "hosted"` identifies a deployed Osmosis model with `base_model` and `checkpoint_name`.
- Supported harnesses include `codex`, `claude-code`, `terminus-2`, `openhands`, `cursor-cli`, `mini-swe-agent`, `gemini-cli`, and `opencode`; some benchmarks require the official scaffold and therefore omit `harness`.
- `cursor-cli` and `mini-swe-agent` require `harness_api_key_secret`; it may name any valid Platform secret record (for example, `MY_CURSOR_TOKEN` or `MY_MSWEA_TOKEN`). The Platform injects the resolved values under fixed destination names `CURSOR_API_KEY` and `MSWEA_API_KEY`. Omit the field for harnesses that do not require separate authentication.
- `[env]` applies literal variables to every agent. `[agents.env]` applies them only to that agent.

## Credentials and environment

- Create each model, harness, or judge secret record with `osmosis secret set <NAME>` before submission.
- For each provider or endpoint agent, its model `api_key_secret` name cannot also appear in top-level `[env]` or that agent's `[agents.env]`.
- Model `api_key_secret` cannot reference runner-reserved `HF_TOKEN`, `DAYTONA_API_KEY`, `DAYTONA_API_URL`, `SKYPILOT_SERVICE_ACCOUNT_TOKEN`, or `SKYPILOT_API_SERVER_ENDPOINT`. The Daytona and SkyPilot names are Platform-managed sandbox plumbing; choose another Platform record name for model credentials.
- A `judge_api_key_secret` name cannot also appear in top-level `[env]` or any `[agents.env]`.
- Do not define the fixed harness destinations `CURSOR_API_KEY` or `MSWEA_API_KEY` in top-level `[env]` or the corresponding agent's `[agents.env]`.
- `HF_TOKEN` is reserved in literal env for every benchmark. HLE obtains it only from the implicit Platform secret record named `HF_TOKEN`; never put it in top-level `[env]` or any `[agents.env]`.

## Submit

Review the benchmark, task scope, agent count, attempts, concurrency, and referenced secret scopes in the confirmation output. If the benchmark is HLE and the task set is not `parity`, call out the CLI's recommendation before asking the user to approve the run; do not block an intentional full run or custom subset. Benchmark runs can incur model and sandbox charges, so use `--yes` only after the user has approved the run.

```bash
osmosis --json benchmark submit configs/benchmark/<name>.toml --yes
```

The structured result includes the generated run name, task count, status, and `platform_url`. Use `platform_url` to open the Platform page, monitor the run, and inspect results.

## Guardrails

- Do not use Harbor config fields; benchmark TOML is an Osmosis-owned contract.
- Do not submit local dataset or task paths. The selected workspace benchmark owns its source and manifest.
- Do not place secrets in `[env]`, `[agents.env]`, or endpoint `extra_headers`.
- Prefer one agent and a small task selection for the first smoke run.
- Do not submit a paid full run without explicit user approval.
