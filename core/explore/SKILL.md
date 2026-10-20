---
name: explore
description: Explore ideas, investigate problems, and clarify technical choices through discussion grounded in available evidence. Use when the user wants to think something through, compare approaches, or explore before deciding what to build, including requests for OpenSpec-style exploration without its process. Not an implementation or formal planning workflow.
---

# Explore

Help the user develop a clearer understanding of their problem and promising ways forward. Adapt to the conversation rather than running an interview, checklist, or fixed sequence. A useful exploration may end with a decision, a better question, or an explicit uncertainty.

## Work from the problem

Start with the idea or difficulty the user brought. Identify the desired outcome and constraints as they become relevant. Offer plausible directions and follow the thread the user chooses. Challenge assumptions with reasons; do not invent requirements to make the discussion more complete.

When a factual question can be answered from available project context, inspect that context first. For software questions, look at the relevant source, callers, tests, configuration, or documentation to understand current behavior and integration points. Keep investigation proportional to the question. Distinguish observations from hypotheses, and name missing evidence that would change the conclusion.

Compare alternatives against the user's actual constraints. Give a recommendation when supported, explaining the decisive tradeoff. Use a small table or diagram when it makes the options or relationships easier to understand. Avoid producing exhaustive option catalogs by default.

Ask focused questions about information only the user can supply or consequential ambiguity that remains after investigation. Resolve a blocking choice before elaborating its dependent details. Continue useful independent investigation while awaiting an answer. Do not prolong discovery once the user has enough clarity.

## Scale investigation with Quasar workers

You may dispatch up to ten Quasar research workers per exploration when independent subquestions justify it. Choose the smallest useful team based on distinct areas, evidence volume, and uncertainty, rather than prompt length. As guidance: a focused question usually needs no workers; a few separable questions may benefit from 2–4; a broad investigation spanning several areas may warrant 5–10. Ten is a ceiling, not a target. Explain the chosen split briefly before dispatch.

Use the available Quasar research interface, such as `plan-worker-vllm` when exposed by the harness. The local OpenAI-compatible endpoint is `http://127.0.0.1:8123/v1`; discover the served model with `GET /models` (currently `w4a4`). When no Quasar agent interface exists, parallel `POST /chat/completions` requests can analyze evidence packets supplied by the primary agent. These requests cannot browse files or use tools on their own. Do not represent a native agent running a different model as a Quasar worker.

Each packet contains the overall question, one bounded subquestion, relevant constraints, and source excerpts with paths and line numbers or source URLs. Request concise findings, supporting evidence, uncertainties, and implications. Keep packets within the model's advertised context limit and reserve room for the answer. Workers are read-only researchers: no implementation, project writes, commits, or recursive delegation. Do not require a plan, ticket, or result contract to dispatch research.

Run independent packets concurrently within the actual backend capacity and available slots, with at most ten workers in flight; use smaller waves when necessary. Use bounded request timeouts. If Quasar is unavailable or a packet fails, continue the remaining investigation yourself and disclose the missing coverage. Do not start or reconfigure inference servers or silently switch providers.

The primary agent owns synthesis and judgment. Check decisive claims against their sources, resolve contradictions, merge duplicate findings, and distinguish verified evidence from worker suggestions. More workers do not replace verification. Stop dispatching when further research would not affect the answer.

## Keep exploration lightweight

Maintain decisions, assumptions, and open questions in the conversation. Summarize them when useful for the next decision or when the user asks. There is no mandatory deliverable or exit gate.

This skill requires no OpenSpec installation, contracts, proposals, specs, tickets, or plan files. Do not scaffold those artifacts or invoke a development workflow merely because an idea becomes concrete. Existing project artifacts can be read as relevant context.

While the user is exploring, investigate without changing project files or implementing the idea. Suggest experiments when they would resolve uncertainty; perform a mutating experiment only if the user requests it. If the user asks to save notes or a sketch, create the requested artifact within that scope without turning it into a formal change process.

An explicit implementation request ends exploration. Carry the established decisions into the requested work and follow the applicable repository rules. Do not require a special command, contract, proposal, or repeated confirmation to make that transition. Conversely, choosing an option during discussion alone does not request implementation.

## Zusammenspiel bei Flow-Analysen

Bei einer zusammenhängenden Repo-/Agent-Flow-Analyse dem [gemeinsamen Ablauf](../repo-flow-analysis/SKILL.md) folgen. Dieser Skill liefert seinen Fachbeitrag; seine Einzelanwendung bleibt eigenständig.
