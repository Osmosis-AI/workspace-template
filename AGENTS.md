# Osmosis Workspace Repository

This clone contains the workspace instructions, rollout examples, and config templates needed to work with its linked Osmosis platform workspace. Use [README.md](README.md) for setup and CLI examples; `CLAUDE.md` imports this file for Claude Code.

## Workspace Contract

- Keep rollouts in `rollouts/<name>/`, evaluation configs in `configs/eval/`, training configs in `configs/training/`, and local datasets in `data/`. Repository-managed benchmark configs belong in `configs/benchmark/`, although `benchmark submit` accepts any readable TOML path. Do not introduce other top-level directories unless the user asks.
- Prefer the installed CLI and SDK-generated files over remembered examples. Use `osmosis --json rollout init <name>` for a new rollout; edit its generated configs rather than replacing them with defaults. Use the bundled defaults under `configs/` only when the needed config is missing.
- Use `osmosis --json doctor` to diagnose workspace setup; `doctor --fix` repairs missing scaffold directories. Setup and scaffold repair are not prerequisites for unrelated documentation edits.
- Read [configs/AGENTS.md](configs/AGENTS.md) when creating or changing configs. Never write secret values into TOML.
- `.osmosis/` contains local state, not source. Use `.osmosis/research/program.md` when present; a fresh clone need not contain a research plan or past run artifacts.

## Skills

Osmosis workflow skills live in [Osmosis-AI/osmosis-plugin](https://github.com/Osmosis-AI/osmosis-plugin). Use an installed Osmosis skill when it matches the task; if the skills are not installed yet, confirm with the user before installing them from `https://github.com/Osmosis-AI/osmosis-plugin` following its installation instructions.

## Rollout and Evaluation Boundaries

- Use one dataset schema throughout: metadata mode (a non-empty `metadata` object on every row) or prompt mode (`user_prompt` and `ground_truth`, with optional `system_prompt`). Configs name platform datasets; local evaluation can explicitly select a file with `--dataset-file`.
- A rollout exposes one concrete `AgentWorkflow` and one concrete `Grader` from the configured entrypoint inside `rollouts/<name>/`; `main.py` is only the scaffold default. Each execution produces one sample, and its async grader assigns a reward in `[0.0, 1.0]`. Policy calls must use the active Osmosis rollout context.
- The rollout entrypoint must build its server with `create_rollout_server` and listen on `0.0.0.0` and `_OSMOSIS_ROLLOUT_PORT` (default `8000`); see `rollouts/multiply-*/` or the `create-rollouts` skill for SDK sample sources, integrations, and Harbor packaging.
- `eval run` uses files on disk and the configured backend. Keep that backend; Daytona, other Harbor cloud environments, and model-calling Harbor Docker on Linux need `cloudflared` on `PATH` for the automatic tunnel. Local `--dataset-file` execution without `--upload` requires no platform credentials; platform datasets and uploads require authenticated workspace context.
- Re-run only the ungraded samples of an existing run with `eval run --name <run-name> --retry-failed`; successes carry forward, and `--upload` replaces that run's published results instead of creating a second run. A managed run retries with `eval retry <run-name>`, which keeps its ID and configuration. A run that supplied secret values at submit time needs them again on retry; the platform names them and the CLI resolves them from `--secrets-file`, the environment, or a prompt.
- Uploading a completed local evaluation publishes evidence; it does not execute a managed evaluation or prove Git sync. Before training, require a passing full-size managed `eval submit` on the intended revision, dataset, and config. Changes that affect that result require a fresh evaluation.
- Managed evaluation and training fetch pushed rollout code from the connected repository. A local edit is not a deployed revision. Benchmark runs instead use Platform-managed tasks and do not require workspace rollout code.

## Authorization and CLI Use

- Follow the user's requested scope and existing authorization for commits, pushes, uploads, and other mutations. A workflow's need for pushed code is not itself permission to commit or push. Do not repeat approval already given for the same action and scope.
- Obtain explicit approval for the actual scope of a paid managed evaluation, benchmark, or training run before submitting it. Deployment, undeployment, endpoint calls, and stopping runs are user-initiated actions; do not add them automatically to another workflow.
- Prefer `osmosis --json ...` for automation or `--plain` for concise text. JSON errors use `error.code`, `error.message`, and `error.details`, not `request_id`. An `INTERACTIVE_REQUIRED` response describes missing inputs or confirmation; supply missing inputs or use `--yes` only within the user's authorization.
- Run from the connected repository for Git-derived workspace scope. Root `--workspace <name>` selects an exact workspace explicitly; source-backed eval/train submissions still need an absolute config path in the matching repository's canonical directory. See [README.md](README.md) for command-specific scope and local upload/resume behavior.
- Non-production `OSMOSIS_TOKEN` use requires a matching `OSMOSIS_TOKEN_PLATFORM_URL`. Use the Platform UI for renames and deletions unavailable in the CLI.
