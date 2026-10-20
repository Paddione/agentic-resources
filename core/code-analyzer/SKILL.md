---
name: code-analyzer
description: Derive prioritized, actionable code improvements from repository code graphs and source evidence. Use for architecture audits, refactoring priorities, technical debt, hotspots, coupling, cycles, or requests to turn graph findings into concrete changes. Pair with codebase-memory for graph evidence. Not for graph generation alone, simple symbol lookup, or implementing a known fix.
compatibility: Harness-independent. Existing central graph hub, Git and project-configured analysis tools. Graph access is optional with explicit evidence limitations.
---

# Actionable code analysis

Turn evidence into a small set of changes worth making. Read [sources](references/sources.md) for provenance. Use the finding contract below rather than a quota or a generic best-practices checklist.

## Scope and authorization

Infer the repository, subsystem and question from the request. If the repository is ambiguous, ask for it while inspecting available context. Record scope and exclusions, checkout SHA and dirty state. Prefer a bounded subsystem to a shallow repository-wide audit.

An audit authorizes analysis and its requested report, not code changes, installations, commits or issue creation. Existing explicit authorization to implement remains valid: hand confirmed findings to the repository development workflow without asking again. Respect repository worktrees and lifecycle rules. Return findings inline unless a persistent report was requested or the repository defines its location. Never print secret values.

## Gather evidence

1. Read architecture, entry points, manifests and configured checks. State a short model of the actual boundaries before judging them.
2. Read the installed `codebase-memory` skill for graph work. Discover tools through the existing central hub; do not install another graph backend or register a bypass server. Use its Verify tier by default, recording project/root, successful generation receipt, checkout identity, query scope, edge types, pagination and coverage. A stale, unavailable or partial graph is a limitation, not an empty graph. Fall back to bounded source searches and disclose that graph conclusions remain unverified.
3. Resolve exact symbols and inspect source at the same revision. Trace relevant callers/callees and affected tests. Confirm cross-service relationships from both endpoints and route/config evidence. Separate parsed edges, inferred edges and observed runtime paths.
4. Add change history for the same scope. State the time window (default six months), count commits touching each file, exclude generated/vendor outputs, and disclose shallow history or bulk formatting/rename distortions. Use file churn as file-level context, not proof that every function changed. Git churn and graph degree indicate where to inspect, not defects.
5. Run existing, relevant configured checks with bounded runtime. Use installed tools only. Inspect commands for writes, downloads and network use before running them; no automatic dependency installation, formatter, autofix or new baseline configuration. Record skipped checks and failures without interpreting them as clean results.

## Diagnose before recommending

- Cycles: show the verified dependency path and explain an actual boundary or maintenance problem. Recommend the smallest edge change that resolves it, preserving initialization and public contracts. A cycle alone is not a bug.
- Highly connected modules: distinguish stable shared utilities from frequently changed mixed responsibilities. Recommend extraction only when source and change history show a concrete reason.
- Unused candidates: zero incoming edges is insufficient. Check exports, plugin/route registration, reflection, dynamic loading and coverage gaps. If unresolved, recommend investigation rather than deletion.
- Test gaps: include tests explicitly in queries and verify test/helper source. Propose behavior tests for exposed risks, not tests mirroring implementation. Graph reachability neither proves runtime coverage nor replaces required checks.
- Duplication and performance: confirm semantic equivalence or a plausible expensive execution path. Avoid abstractions based solely on similarity and speedup claims without measurement.

Before publishing, reopen material source anchors and check upstream validation, dynamic uses and counterexamples. Drop or downgrade findings that do not survive. Include intentional structures considered and left unchanged when relevant; do not invent examples to fill a section.

## Prioritize

Separate severity from confidence. Severity reflects a concrete failure or maintenance cost; confidence reflects evidence completeness. Use high confidence for source-verified claims with required relationships checked, medium for plausible claims with a named unresolved assumption, low for hypotheses needing investigation. Do not promote missing evidence to high confidence.

Rank confirmed correctness/security failures first, then recurring change cost supported by churn and coupling, then localized improvements. Compare expected benefit, effort (S/M/L with assumptions), blast radius and prerequisites. Explain ordering in words instead of an uncalibrated numerical score. High-degree stable utilities can rank below a modest but frequently broken module. Keep uncertain candidates in an investigation list. There is no minimum finding count.

## Finding contract and handoff

For each actionable finding provide:

- Stable ID and short title, severity and confidence.
- Evidence: path:line, qualified symbols, verified relationships or dependency path, revision/receipt and coverage limitations. Reference shared audit metadata rather than repeating it.
- Impact: the concrete failure scenario or recurring maintenance cost, with churn window/count when used.
- Smallest change: files/symbols to alter, behavior/contracts to preserve, and a short diff sketch only when useful.
- Priority rationale, effort assumptions, blast radius and dependencies on other findings.
- Verification: affected behavior tests and exact repository commands with expected results. Distinguish proposed commands from executed checks. If commands cannot be established, mark them unresolved rather than inventing them.
- Acceptance: measurable before/after criterion tied to the impact, such as removal of a specified cycle edge while public import and behavior tests pass. Avoid arbitrary line-count targets.

Deliver the top actionable findings, investigation candidates, relevant intentional structures and analysis limits. Deduplicate related symptoms under their root cause. Give repository planning/execution tools the scoped findings, evidence, dependencies and verification criteria. After an authorized implementation, rerun relevant checks and compare the same bounded source/graph cases at the new successful generation; report behavior results separately from structural improvements.

## Zusammenspiel bei Flow-Analysen

Bei einer zusammenhängenden Repo-/Agent-Flow-Analyse dem [gemeinsamen Ablauf](../repo-flow-analysis/SKILL.md) folgen. Dieser Skill liefert seinen Fachbeitrag; seine Einzelanwendung bleibt eigenständig.
