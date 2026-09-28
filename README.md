# DSH small-model lab — independent experiment

A budget-capped experiment testing whether DSH profiles improve Qwen3-8B task completion, recovery, memory and context handling. The repository name follows the requested `-opus` suffix; this run's proposer is Codex.

Implementation and experiment code are public. **All tasks, graders, hidden tests, model traces and per-task outcomes live separately in a private repository / private server state.** No capability result is claimed until measured.

- [Preregistered protocol](PROTOCOL.md)
- Original plan: [PLAN](docs/PLAN.md), [TASKS](docs/TASKS.md), [LOOP](docs/LOOP.md), [INFRA](docs/INFRA.md)
- [Provider preflight evidence](evidence/provider-preflight.json)

## Execution

Runtime: `deepseek-harness-sdk==0.1.5rc1`, Docker, Python 3.12. Model: `qwen/qwen3-8b` through the DSH custom OpenAI-compatible adapter. Provider pinned to `alibaba`; temperature 0.6, top_p 0.95, reasoning disabled; paired repetition seeds. The preflight uses temperature 0, separately from evaluations.

Keep `OPENROUTER_API_KEY` in a mode-0600, ignored `.env` on the server. Build the actor image with `docker build -t dsh-opus:0.1.5rc1 .`. Run `python3 scripts/launch_gateway.py` to launch the accounting proxy on the Docker bridge only. Allow Docker bridge clients to TCP 18943 if the host firewall blocks them; do not open this port publicly.

Start/resume a sweep:

```sh
python3 scripts/background.py --bank /private/path/bank.json --sweep baseline --k 5
python3 scripts/summarize.py --sweep baseline
```

The driver alternates randomized arms within task/repetition blocks and saves each completed result atomically. Logs and SQLite cost accounting are under `.local/` and never committed. The Mac control machine runs `caffeinate -dimsu` while sweeps are active. The gateway hard-stops at $18 reserved/reported cost, below the user's $20 cap.

## Cross-evaluation

An external profile is a directory containing `patch.json` (a Cordis patch array) plus any referenced plugin files. It is mounted read-only at `/profile`; plugin paths use `file:///profile/name.mjs`. The underlying unmodified full SDK profile and provider/permission/sandbox settings are fixed by the runner.

```sh
TASK_BANK=/private/path/bank.json scripts/cross-evaluate.sh /absolute/path/external-profile
```

This runs plain standard and the external profile on this experiment's frozen held-out split, k=5, paired and interleaved. Only use the aggregate summary for proposer review. A profile may also be run through the regular driver with `--arms external --external-profile /path` on an authorized split.

The command verifies the frozen bank and requires a valid `patch.json`; it will not silently run an unapplied profile. A private sweep manifest pins the external directory's contents, bank hash, arms, splits and repetition count. Resume with the same sweep name and unchanged profile, or set `SWEEP_NAME` to a new name for a different profile. Concurrent launches of the same sweep are rejected.

## Limits

Hosted provider weights/quantization cannot be fully pinned. The task bank is synthetic and has repeated templates. The planned Qwen3-4B-Instruct-2507 transfer model is absent from the current OpenRouter catalog; no larger model is substituted. See the protocol and eventual `RESULTS.md` for measured limitations and promotion decisions.
