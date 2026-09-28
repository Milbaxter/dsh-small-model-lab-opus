# Preregistered protocol

This is the independent experiment requested for `Milbaxter/dsh-small-model-lab-opus`. Names follow the user's request; the proposer is Codex, not Opus. No other experiment's tasks, graders, or traces are used.

Plan source: `fe8c9d3973f3f7d0ca9dadfae55cbad1bddf18cf`.
Runtime: published `deepseek-harness-sdk==0.1.5rc1` and matching bundled runtime. Upstream master documentation can differ; settings are checked against the release tag.
Model: `qwen/qwen3-8b`; OpenRouter provider `alibaba`, fallbacks disabled. Temperature 0.6, top_p 0.95, reasoning disabled, seed 928000 + repetition. The provider does not expose a weights revision or quantization pin. Provider metadata is captured with preflight evidence.

## Resources and controls

All model execution on UpCloud CPU, fresh Docker container, workspace and DSH home per run. Actor sees no OpenRouter credential, bank, grader, or hidden tests. Limits: 1.5 CPU, 768 MiB RAM (3× a declared 0.5 CPU/256 MiB minimum), 128 PIDs, 20 API calls, 100,000 cumulative tokens (stop-before-next-call threshold), 450 seconds per task and 150 seconds per user turn. Output max 2,048 per request, including compaction. The gateway permits at most 220,000 serialized request characters. DSH context window is configured to 32,768 tokens to exercise compaction; the hosted endpoint's actual limit is larger. This is a harness pressure setting, not an assertion that the provider enforces 32K.

Gateway reserves $0.04 per in-flight request, retains that reservation if cost is unknown, and stops at $18, leaving $2 headroom under the $20 cap. Direct preflight cost is reported separately. Model usage includes input/tool-schema tokens and all requests, including compaction and retries. Logs and progress remain private. Re-running a sweep skips finished runs; interrupted workspaces are archived before restarting.

`standard` means shipped Python SDK full `sdk` profile; `sdk-minimal` is the shipped standalone shell-only profile (the currently published version has no edit tool). All use the same custom provider, telemetry-disabled setting, and unattended permission mode inside the container. `autonomy` adds only the upstream autonomy-policy plugin, pinned at `02c392bb074fbc8600e7f42386f1105258e267be`.

## Task bank

64 procedurally constructed tasks, four equally represented families, 32 dev / 16 held-out / 16 transfer. Synthetic instances were generated for this experiment. Transfer includes different operation specifications and project domains. Templates repeat within families; claims must acknowledge limited task diversity. Recovery initially covers transient verifier failures, not every fault class in the original plan. Memory uses distinct sessions sharing a workspace and home; context uses balanced distracting turns and actual compaction events are counted. Reference, starting-state and trivial-answer controls validate every grader before freeze.

Calibration uses only dev tasks at k=5. Held-out and transfer are frozen with the full task bank before P3, and are accessed only by the runner and aggregate reporter thereafter. The construction phase ends before the proposer phase; proposer input thereafter is dev-only.

## Comparisons and promotion

All formal comparisons use k=5, randomized arm order within task/repetition blocks. Confidence intervals resample task-level mean differences 10,000 times with a fixed seed, keeping five repeated trials together. Hidden splits report aggregate rates, CIs, family counts, token cost and failure counts; never per-task outcomes or traces.

At most five P3 iterations, one bounded change each. Initial champion is plain standard DSH unless another baseline clears all applicable promotion gates. Every candidate must improve dev, have held-out paired 95% CI lower bound >0, show no transfer regression, beat matched inference budget control, stay within +25% tokens per solve, and pass leakage review. Smoke and dev rejection are valid early exits. No candidate is promoted on an incomplete gate. The plan's named second model, Qwen3-4B-Instruct-2507, was not listed in the OpenRouter model catalog checked during setup. No larger model will be substituted. If unavailable at evaluation, this gate remains untested and cannot be silently counted as passing.

The cross-evaluation interface takes an external profile directory containing `patch.json` and plugin files mounted at `/profile`, and runs it paired with plain standard on the private held-out split. The final bundle has the same interface and contains no task strings, task-specific filenames, graders or expected answers.

## Added independent benchmark gate

User steering: add a real benchmark such as Terminal-Bench, comparing plain DSH, improvements and the final champion. A budget-feasible subset will be selected and frozen before P3, run at k=5 with the same arms, and reported separately from private-bank scores. Published benchmark contamination and subset limitations must be disclosed. The proposer will not inspect benchmark task contents or traces in the loop.

Terminal-Bench execution uses Harbor 0.23.0 and dataset commit `2fd12b88aafdd04a52c298e3940bcb189f9766d6`. The four tasks are selected by the smallest SHA256 values of `dsh-opus-independent-20260928:` plus task ID among the 69 tasks with CPU ≤1, memory ≤2048 MiB and no GPU. The selection file stays private. This selection is independent of scores, instructions, solutions and graders. Oracle validation uses the official solutions and verifiers; the proposer receives only aggregates.

For this added benchmark, keep its official 1 CPU/2 GiB environment allocations and run one trial at a time. This differs from the synthetic bank's 3× declared-minimum allocation, to preserve the official task environment within the shared server's capacity. Both compared arms have identical resources. The inference cap remains the lab cap, so this is a **budget-limited four-task Terminal-Bench 2.0 subset**, not a full benchmark/leaderboard result.

Calibration history: initial plumbing sweeps were discarded after a container firewall issue and a release-incompatible compaction config were corrected. A completed harder-bank pilot scored 0/40. The revised pre-freeze bank includes existing command-line pipelines, explicit and implicit persistence requests, and balanced context messages. Calibration is exploratory and not reused as paired baseline evidence. Completed-run evidence retains complete SDK logs and events compressed; only reproducible native runtime caches are discarded.

The added Terminal-Bench promotion condition is a complete k=5 comparison with no negative aggregate point difference versus plain standard. A tied zero score passes only a non-regression check and supplies **no evidence of benchmark uplift**. Report that limitation explicitly. Original private held-out positive-CI and all other gates remain mandatory.

Matched-budget control is a real best-of-up-to-five standard run: reuse the paired standard run as attempt 0, then execute fresh independent attempts with seeds `928000 + repetition + 100 × attempt`. All attempts in a control repetition share the same 100,000 cumulative-token stopping threshold and 20 API calls as the candidate, with at most five attempts. Scores use the private grader's best result; the proposer sees aggregates only. The controller keeps using remaining budget even after a success, so measured token use can verify it was not starved relative to the candidate. As with primary runs, a final in-flight request can exceed the token stopping threshold; report actual tokens. A missing or incomplete control never passes a promotion gate. The primary run's inference is reused analytically and is not billed twice in total spend.
