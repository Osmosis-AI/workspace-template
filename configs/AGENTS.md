# Training, Eval, and Benchmark Configs

Use the root [workspace contract](../AGENTS.md) for authorization, workspace scope, and local versus managed execution. This file owns config-specific rules; follow only the section relevant to the config being changed.

## Templates and Paths

| Config | Repository path | Bundled default | Workflow |
| --- | --- | --- | --- |
| Training | `configs/training/<name>.toml` | [training/default.toml](training/default.toml) | [submit-training](../.agents/skills/submit-training/SKILL.md) |
| Evaluation | `configs/eval/<name>.toml` | [eval/default.toml](eval/default.toml) | [evaluate-rollouts](../.agents/skills/evaluate-rollouts/SKILL.md), [submit-eval](../.agents/skills/submit-eval/SKILL.md) |
| Benchmark | `configs/benchmark/<name>.toml` | [benchmark/default.toml](benchmark/default.toml) | [submit-benchmarks](../.agents/skills/submit-benchmarks/SKILL.md) |

Edit a rollout's existing generated config. Copy a default only when creating a config without `rollout init` or repairing a missing file. If local defaults are missing, use the bundled [training fallback](../.agents/skills/submit-training/references/training-default.toml) or [eval fallback](../.agents/skills/evaluate-rollouts/references/eval-default.toml); do not invent schemas from memory. Eval/train paths are enforced by the CLI; benchmark paths above are a repository convention, and `benchmark submit` accepts any readable TOML path.

## Environment and Secrets

- Never put secret values in TOML, including `[env]`, `[agents.env]`, or endpoint headers. Credential fields contain Platform secret record names.
- `[secrets].required` lists credentials not already referenced by another credential field. Each name resolves at submit from `--secrets-file`, the process environment, stored records, or an interactive prompt, first hit wins. Supplied values are not saved and must be supplied again on reruns; structured output never prompts for them.
- Create other referenced records with `osmosis secret set NAME`; personal scope is the default, and `--scope workspace` creates a workspace-shared record. Resolved secrets are injected under their own names.
- Evaluation configs require `[secrets]`: default OpenAI evals include `OPENAI_API_KEY`, and `required = []` is only for evals needing no secret refs. Training configs may omit `[secrets]`, but any present section must include `required`.
- `[env]` holds non-secret literals. Env keys match `^[A-Z_][A-Z0-9_]*$`; secret names match `^[A-Z][A-Z0-9_]*$`. A name cannot overlap between env and secrets, and `_OSMOSIS_` env names are reserved.
- Daytona rollout configs need `DAYTONA_API_KEY` under `[secrets].required`. Benchmark sandbox credentials are Platform-managed; do not confuse them with rollout credentials.

## Training and Evaluation

- `[experiment]` requires real `rollout`, `entrypoint`, `model_path`, and `dataset` values, with no placeholders. `rollout` names a directory under `rollouts/`; `entrypoint` names its Python server file. Preserve an explicitly configured filename instead of assuming `main.py`.
- `dataset` is a platform dataset name from `osmosis dataset list`, not a dataset ID or local path. A local file is selected separately with `eval run --dataset-file PATH`.
- `branch` and `commit_sha` are optional and mutually exclusive. Omit both for the connected repository's default branch; a pinned commit must be pushed before managed execution.
- Training `model_path` must be a supported base model; evaluation uses the LiteLLM-style name of the model under test. Leave optional `[training]`, `[sampling]`, `[checkpoints]`, and `[evaluation]` settings at their defaults unless deliberately overriding them. Use the bundled TOMLs for field names and examples.
- A smoke eval can limit rows. Remove the limit for a formal full-size evaluation; do not shrink a run to improve its reported score. Training readiness and managed source checks belong to `submit-training`.
- Read [training config gates](../.agents/skills/submit-training/references/training-config-gates.md) when tuning training fields or remote rollout concurrency. Local execution, tunnel selection, upload, and resume instructions belong to `evaluate-rollouts` and `submit-eval`.

## Benchmarks

### Catalog and Task Scope

- Inspect `osmosis --json benchmark list` and `osmosis --json benchmark info <key>` before selecting tasks, harnesses, or judges. `[experiment].benchmark` accepts the workspace benchmark's key, name, or ID, all exact and case-sensitive.
- Submit a registry benchmark only when `sync_status` is `ready`. A failed sync reports `sync_error`; use its `platform_url` to retry from the Platform page.
- Use the returned full task manifest. Difficulty is `easy`, `medium`, `hard`, or `null`; never infer a missing difficulty. Recommend `default_harness` for comparability with published scores and explain departures.
- Omit `[tasks]` for all tasks, or choose one of `task_set`, `task_names`, and `categories`. `task_set = "parity"` overrides the other selectors, so remove ignored selectors. Prefer exact `task_names` for bounded runs; resolve categories to task counts before seeking approval.
- Recommend parity for HLE comparability; intentional full or custom runs remain supported. Only full runs or leaderboard-eligible parity runs (currently HLE) rank; other subsets do not.
- Use Osmosis fields such as `attempts_per_task` and `max_concurrent_attempts`, not Harbor config fields. The `submit-benchmarks` workflow owns trial-count review, approval, submission, and run management.

### Agents and Credentials

- Include one or more `[[agents]]` entries, each with `[agents.model]`. Model type is `provider`, `endpoint`, or `hosted`; see `submit-benchmarks` and the default TOML for the complete model fields.
- Provider/endpoint models use `api_key_secret`. Hosted models use `base_model` and `lora_model_name` from `osmosis --json model list --type lora`, require an already-deployed model with the matching base, and take no `api_key_secret`. Deployment needs the user's explicit request.
- `cursor-cli` requires `harness_api_key_secret = "CURSOR_API_KEY"`. Mini SWE-agent rejects `harness_api_key_secret` for every model type: provider/endpoint models reuse `api_key_secret` as `MSWEA_API_KEY`; hosted models receive no injected model key. Omit `harness_api_key_secret` for all other harnesses.
- Match judge fields to catalog flags. If both `requires_judge_model` and `requires_judge_api_key` are true (HLE, GDPVal), require `judge_api_key_secret` and allow optional `judge_model`, defaulting to the catalog judge. If only the API key is required (BrowseComp), require an OpenAI key and reject `judge_model`. If neither flag is true, reject both fields.
- Registry datasets may name up to 16 verifier secret records in `[verifier].required`, delivered under their own names. Managed benchmarks model credentials in the catalog and reject this section.
- `[env]` applies to every agent; `[agents.env]` overrides literals for one agent. A provider/endpoint model's `api_key_secret` name cannot also appear in its effective env or reference `DAYTONA_API_KEY` or `DAYTONA_API_URL`.
- Judge or verifier secret names cannot appear in any global or agent env. `CURSOR_API_KEY` cannot appear in the corresponding Cursor agent's effective env. `MSWEA_API_KEY` cannot appear in a provider/endpoint Mini SWE-agent's effective env; hosted Mini SWE-agent models may set it explicitly.
