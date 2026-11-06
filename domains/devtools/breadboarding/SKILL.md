---
name: breadboarding
description: Transform a workflow description into affordance tables showing UI and Code affordances with their wiring. Use to map existing systems or design new ones from shaped parts.
---

# Breadboarding

Breadboarding transforms a workflow description into a complete map of affordances and their relationships. The output is always a set of tables showing numbered UI and Code affordances with their Wires Out and Returns To relationships. The tables are the truth. Mermaid diagrams are optional visualizations for humans.

Two functions (details: [references/use-cases.md](references/use-cases.md)):
1. **Mapping an Existing System** — workflow (operator perspective) → UI/Code affordance tables (+ optional Mermaid). Multi-app flows: ONE breadboard, label places per system.
2. **Designing from Shaped Parts** — parts + R (+ optional existing system) → tables (+ optional Mermaid). Mixtures: breadboard existing + new together.

## Workflow

**Mapping** (10 steps — [references/procedures.md](references/procedures.md)): identify flow → list places → trace components → list affordances (name the real thing, no abstractions) → Control → Wires Out → Returns To → stores as affordances → framework mechanisms → verify against code. Worked example: [references/example-mapping.md](references/example-mapping.md).

**Designing** (8 steps — [references/procedures.md](references/procedures.md)): list parts → translate to affordances → every U needs supporting N → classify places (existing/new) → wire → connect to existing → completeness check → user-visible outputs are Us. Worked example incl. slicing: [references/example-design.md](references/example-design.md).

## Concepts & Output

- **Core concepts** (Places, blocking test, IDs, references, modes, subplaces, containment vs wiring, navigation, affordances): [references/core-concepts.md](references/core-concepts.md)
- **Output tables** (Places, UI, Code, Stores + column definitions): [references/tables.md](references/tables.md) — the tables are the truth.
- **Principles** (check data not memory, real names, mechanisms aren't affordances, two flows, data sources, connected Ns, side-effect stores, inline navigation, store placement): [references/principles.md](references/principles.md)
- **Catalog** (elements, relationships, qualification, verification checks): [references/catalog.md](references/catalog.md)

## Techniques

- **Chunking** (one wire in/out subsystems): [references/chunking.md](references/chunking.md)
- **Visualization** (Mermaid structure, line/color conventions, subgraphs, multi-system, step annotations): [references/visualization.md](references/visualization.md)
- **Slicing** (vertical V1–V9 implementation slices with demos): [references/slicing.md](references/slicing.md)

## Flow Analyses

Bei einer zusammenhängenden Repo-/Agent-Flow-Analyse dem [gemeinsamen Ablauf](../../../core/repo-flow-analysis/SKILL.md) folgen. Dieser Skill liefert seinen Fachbeitrag; seine Einzelanwendung bleibt eigenständig.
