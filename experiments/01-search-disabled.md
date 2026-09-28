# Iteration 1: omit an unavailable search tool

Date: 2026-09-28. Status: preregistered; not yet evaluated.

Target: repeated calls to a tool whose provider has no configured credential. A dev-only inspection of the first 23 completed standard baseline dev runs found eight successes, eight reasoning-tagged failures and seven budget failures. Two inspected memory-family failures repeatedly invoked web search for local project information after receiving `WEB_PROVIDER_CREDENTIAL_MISSING`. These partial diagnostics motivate the mechanism; they are not a capability estimate or a selection gate.

Hypothesis: disabling the unconfigured `web_search` tool reduces dead-end actions and schema overhead, leaving more inference for useful local work. The single change is `tool-web.config.search = false`. HTTP fetch, local tools, prompts, memory, permissions, model, provider and budgets stay fixed. This is suitable only when search credentials are unavailable; it does not establish that disabling working search is beneficial.

Disconfirmation: no positive paired dev task-bootstrap lower bound, more budget failures, or failure of any subsequent promotion gate. No task-specific strings or special-case behavior are added.

Author pass: one configuration flag, grounded in observed dev tool failures and the pinned release's documented registration switch. Reviewer pass: source confirms `search: false` omits the tool; it does not intercept outputs or implement task solutions. No hidden content was used. Task diversity, repeated templates and unavailable search in the baseline limit generalization. The independent Terminal-Bench gate is still required for promotion.

Champion: plain standard SDK profile, baseline code commit `b20f9339c2137507d84df8371aa60cbbfd67514a`. Candidate commit: recorded by the evaluation launch manifest after committing this record and patch.

Runtime: deepseek-harness-sdk 0.1.5rc1. Model: qwen/qwen3-8b; OpenRouter alibaba, no fallback; temperature 0.6, top_p 0.95, reasoning disabled, output cap 2048, paired repetition seeds 928000–928004. No vLLM is used.

Task bank: 64 tasks, 32 dev / 16 held-out / 16 transfer, frozen commit `17d3d4653992dc1f1a1334ac6a5a54f305121f50`. Budgets: 100,000 cumulative-token stop-before-next-call threshold, 20 API calls, 450 seconds per task, 150 seconds per turn. Same budgets in both arms. Smoke: eight balanced dev tasks × one run. Formal dev: 32 × five × two interleaved arms. Hidden evaluation follows only if dev clears the preregistered gate.

Pending fields: dev rates/difference/CI; held-out rates/difference/CI; transfer and second-model evidence; matched-budget control; tokens per solve/schema overhead; dev failure shifts and newly solved/regressed IDs; decision; trace locations. Missing gates will be recorded as untested, never passed.

Critical reviewer pass after runtime implementation, before formal dev scores were inspected:

- Utility: prevent repeated calls to a search provider that has no credential, particularly when the needed information is local.
- Fit: DSH already provides a registration switch. A single flag is sufficient; no new plugin or task-solving logic is needed.
- Correctness: the pinned release supports the flag. Eight smoke runs completed without infrastructure errors. The actual native request exposes 24 tools, omits `web_search`, and retains `web_fetch`. Smoke score was 2/8 and is not evidence of uplift.
- Autonomy: permissions, scope and sandbox limits are unchanged. The predicted benefit is fewer dead ends, not extra authority.
- Cost: no dependencies, storage or policy text are added. Tool/schema overhead is removed; its measured token effect and total tokens per solve are deferred to the completed comparison.
- Regression risk: this setting removes useful capability when a search credential is available. It applies to the tested unconfigured-search setup; reverting the flag restores registration.
- Evidence: configuration loading and model-facing tool visibility are verified. Improved task completion remains a hypothesis pending k=5 results.
- Disconfirmation: reject promotion if the preregistered dev confidence gate or any subsequent gate fails. Plain standard DSH is the unchanged alternative; reduced tool availability could harm discovery or alter useful model behavior.

Reviewer verdict: accept for evaluation, not promotion. Confidence is high in mechanical correctness and low in predicted capability gain before formal scoring. Author and reviewer passes use the same frontier model, as permitted by the upstream judgment rubric.
