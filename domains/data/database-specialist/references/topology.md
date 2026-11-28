# Topology

Live contexts: `devmesh`, `prodmesh`, `korczewski-prod`
(see `environments/dev.yaml:9`, `environments/prodmesh-korczewski.yaml:7`).
The `fleet` context was decommissioned 2026-10-22
(Bachelorprojekt `AGENTS.md`); residual `fleet` strings in scripts/docs are
legacy. Re-verify via `environments/*.yaml` before trusting any context.

Namespaces `workspace` / `workspace-korczewski` remain valid
(`environments/dev.yaml`, `environments/korczewski-prod.yaml`).
ENV values are keys of `environments/*.yaml` (`dev`,
`prodmesh-korczewski`, `korczewski-prod`, `staging`, …). There is no
`environments/mentolder*` file; `mentolder` is a standalone brand repo.
