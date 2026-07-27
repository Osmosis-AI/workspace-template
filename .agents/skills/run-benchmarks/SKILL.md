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
6. Configure at least one `[[agents]]` entry and its `[agents.model]` table.
7. Create every referenced secret record with `osmosis secret set <NAME>`; never write secret values into TOML.

## Task selection

- Omit `[tasks]` to run the full benchmark.
- Use `task_names` for an explicit list of tasks.
- Use `categories` to union all tasks in named categories.
- Use `task_set = "parity"` only when the selected benchmark publishes a parity sample.
- Start with a small explicit task list when validating a new agent setup.

## Agent models

- `type = "provider"` uses a provider model name and `api_key_secret`.
- `type = "endpoint"` also requires `base_url`; optional `extra_headers` contain literal header values, not secrets.
- `type = "hosted"` identifies a deployed Osmosis model with `base_model` and `checkpoint_name`.
- `harness` is commonly `codex`, `claude-code`, `terminus-2`, or `openhands`; some benchmarks require the official scaffold and therefore omit it.
- `[env]` applies literal variables to every agent. `[agents.env]` applies them only to that agent.

## Submit

Review the benchmark, task scope, agent count, attempts, concurrency, and referenced secret scopes in the confirmation output. Benchmark runs can incur model and sandbox charges, so use `--yes` only after the user has approved the run.

```bash
osmosis --json benchmark submit configs/benchmark/<name>.toml --yes
```

The result includes the generated run name, task count, status, and `platform_url`. Use the Platform page to monitor the run and inspect results.

## Guardrails

- Do not use Harbor config fields; benchmark TOML is an Osmosis-owned contract.
- Do not submit local dataset or task paths. The selected workspace benchmark owns its source and manifest.
- Do not place secrets in `[env]`, `[agents.env]`, or endpoint `extra_headers`.
- Prefer one agent and a small task selection for the first smoke run.
- Do not submit a paid full run without explicit user approval.
