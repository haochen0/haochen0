# AGENTS.md

Scope: this file applies to `/Users/hao/.codex/projects/haochen0` and all descendants.

Purpose: execution contract distilled from `knowledge.md`.  
Keep `knowledge.md` as living memory; keep this file short and operational.

## P0 Core Execution Rules

- Re-anchor to the core contract before adding layers: restate goal, input, output, and boundaries.
- Prefer the shortest main path. Do not add wrappers, persistent state, or side effects unless required.
- If user gives explicit n+1 / independent review, do that first; do not downgrade it to normal maintenance.
- For ambiguous "why/reason" after analysis, answer content rationale first, then process rationale if needed.
- Use absolute dates for time-sensitive statements; avoid relative wording as final evidence.

## Subagent and Parallel Work

- Keep single-file rewrites and single-conclusion judgments on the main thread by default.
- Delegate only independent side tasks with clear ownership and non-overlapping output.
- For web/source gathering tasks, delegate retrieval and source collection; keep synthesis and final judgment on main thread.
- Isolate subagent context by angle. Close completed agents quickly to avoid context leakage.
- When calling `spawn_agent`, pass exactly one payload mode: `message` or `items`.

## Research and Evidence Discipline

- Always separate `fact`, `inference`, `stance`, and `gap`.
- Prioritize primary sources; map secondary reports back to original posts, filings, docs, or papers.
- For screenshot-driven news tasks, confirm the circled title/source first, then verify with high-quality sources.
- If source quality is weak (paywall summary, rumor, repost), explicitly mark confidence and uncertainty.
- Do not turn one expert's framework into "consensus" without external confirmation.

## Knowledge Management Rules

- `knowledge.md` stores reusable methods, not one-off news facts.
- Before editing `knowledge.md`, scan nearby related entries first and deduplicate.
- Do not scan old sessions by default. Only do history recovery when user explicitly asks.
- For Google Photos public-share links, stay on the current link and current download set: read HTML source first, then `AF_initDataCallback`, then inspect only the newly downloaded images in an isolated temp directory; do not call back an old Codex session unless the current page is missing critical data.
- If recovering `knowledge.md`, follow this order:
  1) inspect current workspace files
  2) list all candidate backups/snapshots/sessions
  3) sort by timestamp
  4) classify version type
  5) lock the last correct baseline before current session
  6) backup current file before restore
- When extracting from noisy artifacts, filter scratch/system/generated files and keep only reusable rules.

## Domain-Specific Reuse Heuristics

- Product comparisons: split by `model`, `app`, and `agent` layers.
- Agent product comparisons: use `control surface`, `execution surface`, `trust model`.
- Pricing comparisons: normalize to `USD per 1M tokens`; separate quota/subscription products.
- Spec-coding tasks: treat AI as implementer, not scope discoverer. Review PRD, edge cases, and cross-platform behavior first.
- Market/news catalyst analysis: separate baseline business from incremental narrative, then bucket by revenue lane and timing.

## Engineering and Ops

- macOS background workers: prefer `launchd` with isolated env files and wrappers.
- Put `PYTHONPYCACHEPREFIX=/tmp` for compile checks when cache permissions are risky.
- On Python 3.9.6 environments, avoid 3.10+ syntax.
- Before push/deploy, run local critical-path validation first; do not rely on delayed remote checks.
- If a Git write fails on `.git/index.lock` or other repo metadata because the sandbox blocks it, stop retrying, explain the blocker plainly, and give the exact local command for the user to run.

## Output Style

- Be concise, structured, and action-oriented.
- Label uncertainty clearly; avoid overstating confidence.
- For complex analysis, provide short-term vs mid-term impacts separately when applicable.

## Command Alias

- Alias: `入库（P0|P1|P2|P3）：<要点>`
- Equivalent intent: `入库这次结论（Pn）：<要点>; 写入 /Users/hao/.codex/projects/haochen0/knowledge.md; 去重合并相近条目。`
- Priority is replaceable: `P0`, `P1`, `P2`, `P3` are all valid.
- If user only says `入库` (no explicit priority), infer priority automatically from impact, reusability, and urgency, then write into `knowledge.md`.
