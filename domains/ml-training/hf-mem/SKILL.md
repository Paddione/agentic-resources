---
name: hf-mem
description: Estimate the GPU memory needed to run a Hugging Face model (weights, KV cache and inference overhead) and whether it fits on given GPUs, without downloading it. Use when asked how much VRAM a model needs, whether it fits on a GPU, the longest context that fits, or which GGUF quantization to pick.
license: mit
---

# hf-mem

## Repo-Graph zuerst (nur bei Code-Suche)

Suchst oder navigierst du Repo-Code, beginne am zentralen MCP-Hub `fleet-workspace`: `search_graph` → `trace_path` → `get_code_snippet`; Übersicht via `get_architecture`/`query_graph`/`search_code`. Nicht indiziertes Projekt zuerst mit `index_repository` indizieren. Belegpfade mit `check_index_coverage` prüfen und Lücken benennen. `grep`/`rg` nur für nicht-indizierte Nicht-Code-Dateien oder als belegten Fallback. Details: SSOT-Skill `codebase-memory`.

```bash
uvx hf-mem <model> -o json [options]
```

`<model>` is a Hub ID (`org/name`, `org/name@revision`), a Hub URL, a local path, or `org/name-GGUF:Q4_K_M` for one GGUF quantization.

Options:

- `--gpu-memory 24` (GiB per GPU) or `8x80` (8 GPUs): adds `fit`.
- `--max-model-len N`: context length, defaults to the model's maximum, which can dominate the total.
- `--batch-size N`: concurrent sequences, defaults to 1.
- `--kv-cache-dtype fp8` (vLLM names for Safetensors, llama.cpp cache types such as `q8_0` for GGUF).
- `--file <file or variant>` and `--format safetensors|gguf|onnx` to pick the weights.
- `--max-num-batched-tokens 2048` on A100s.
- Gated or private models need `HF_TOKEN` or `--hf-token`.

JSON (sizes in bytes, divide by 2^30 for GiB):

- `total` is the GPU memory for one copy of the model: `weights` + `kv_cache` + `overhead` (vLLM for Safetensors, llama.cpp for GGUF, none for ONNX).
- `offloaded` are weights the engine keeps in CPU memory: excluded from `weights` and `total`, but needed as free system RAM.
- `fit` (with `--gpu-memory`): `fits`, `needed` GPUs, `max_model_len` (the longest context that fits), and the `required` vs `usable` memory across the given GPUs. Use `required` / GPUs for the memory per GPU, not `total` / GPUs, as each GPU also holds its own overhead and replicated KV cache.
- GGUF and ONNX repositories with several files return a `files` list to compare quantizations; pick one with `:TAG` or `--file` to get `fit`.
- Report `warnings` to the user, and errors explain how to fix them.
