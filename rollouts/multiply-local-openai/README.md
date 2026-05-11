# Multiply Local OpenAI

Self-contained multiply rollout using `LocalBackend` and the OpenAI Agents SDK
integration. The workflow, tool, grader, and server entrypoint all live in
`main.py` so this folder can be treated as an independent rollout package.

Run from the project root:

```bash
osmosis --json rollout validate configs/eval/multiply-local-openai.toml
osmosis --json eval run configs/eval/multiply-local-openai.toml
osmosis --json train submit configs/training/multiply-local-openai.toml
```
