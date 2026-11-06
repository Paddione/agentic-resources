---
name: transformers-js
description: Use Transformers.js to run state-of-the-art machine learning models directly in JavaScript/TypeScript. Supports NLP (text classification, translation, summarization), computer vision (image classification, object detection), audio (speech recognition, audio classification), and multimodal tasks. Works in browsers and server-side runtimes (Node.js, Bun, Deno) with WebGPU/WASM using pre-trained models from Hugging Face Hub.
license: Apache-2.0
metadata:
  author: huggingface
  version: "4.x"
  category: machine-learning
  repository: https://github.com/huggingface/transformers.js
compatibility: Requires Node.js 18+ (or compatible Bun/Deno runtime) or modern browser with ES modules support. WebGPU requires runtime and hardware support; WASM is the broad fallback. Internet access is needed for downloading models from Hugging Face Hub (optional if using local models).
---

# Transformers.js - Machine Learning for JavaScript

Transformers.js enables running state-of-the-art machine learning models directly in JavaScript across browsers and server-side runtimes (Node.js, Bun, Deno), with no Python server required.

## When to Use This Skill

Use this skill when you need to:
- Run ML models for text analysis, generation, or translation in JavaScript
- Perform image classification, object detection, or segmentation
- Implement speech recognition or audio processing
- Build multimodal AI applications (text-to-image, image-to-text, etc.)
- Run models client-side in the browser without a backend

## Installation

```bash
npm install @huggingface/transformers
```
Browser (CDN): `import { pipeline } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers';`

## Core Concepts

**Pipeline API** (easiest entry — preprocessing + inference + postprocessing):
```javascript
import { pipeline } from '@huggingface/transformers';
const pipe = await pipeline('sentiment-analysis');
const result = await pipe('I love transformers!');
await pipe.dispose();  // ALWAYS dispose to free memory
```
**Model selection:** second argument (`pipeline('sentiment-analysis', 'model-id')`); browse `library=transformers.js` models — [references/model-selection.md](references/model-selection.md).
**Device:** `device: 'webgpu'` for GPU, default CPU/WASM. **Quantization:** `dtype: 'q4' | 'q8' | 'fp16' | 'fp32'` (precision vs. size trade-off).

## Tasks

Task IDs + one-line usage: [references/supported-tasks.md](references/supported-tasks.md) — NLP (classification, NER, QA, generation incl. streaming/chat in [references/TEXT_GENERATION.md](references/TEXT_GENERATION.md), translation, summarization, zero-shot), vision (classification, detection, segmentation, depth, zero-shot), audio (ASR, classification, TTS), multimodal (captioning, doc-QA, zero-shot detection), embeddings.

Full task-ID table: `text-classification`, `token-classification`, `question-answering`, `fill-mask`, `summarization`, `translation`, `text-generation`, `text2text-generation`, `zero-shot-classification`, `image-classification`, `image-segmentation`, `object-detection`, `depth-estimation`, `image-to-image`, `zero-shot-image-classification`, `zero-shot-object-detection`, `automatic-speech-recognition`, `audio-classification`, `text-to-speech`, `image-to-text`, `document-question-answering`, `feature-extraction`, `sentence-similarity`.

## Advanced Configuration

Details in [references/advanced-config.md](references/advanced-config.md): `env` object (remote/local models, caches, logging, custom fetch), `ModelRegistry` (v4: inspect files/cache/dtypes), standalone `@huggingface/tokenizers`, manual tokenizer+model control, batch processing, structured output / constrained decoding (v4.3), WebGPU (v4 C++ rewrite, Safari 26+), WASM, progress callbacks.

## Operations

[references/ops.md](references/ops.md): try-catch error handling, 7 performance tips, memory management (`dispose()` — when and why, React/server patterns in [references/EXAMPLES.md](references/EXAMPLES.md)), troubleshooting (model not found, memory, WebGPU).

## Best Practices

1. **Always Dispose Pipelines** — critical against memory leaks
2. **Start with Pipelines** unless fine-grained control is needed
3. **Test Locally First** with small inputs
4. **Monitor Model Sizes** for web apps
5. **Handle Loading States** (progress indicators)
6. **Version Pin** (`{ revision: 'abc123' }`) in production
7. **Error Boundaries** — wrap pipeline calls in try-catch
8. **Progressive Enhancement** — fallbacks for unsupported browsers
9. **Reuse Models** — load once, use many times
10. **Graceful Shutdown** — dispose on SIGTERM/SIGINT

## Reference Documentation

### This Skill
- **[Supported Tasks](./references/supported-tasks.md)** - All tasks with code examples
- **[Model Selection](./references/model-selection.md)** - Hub browsing, choosing guide, tips
- **[Advanced Configuration](./references/advanced-config.md)** - `env`, ModelRegistry, tokenizers, constrained decoding, WebGPU/WASM, progress
- **[Operations](./references/ops.md)** - Error handling, performance, memory, troubleshooting
- **[Pipeline Options](./references/PIPELINE_OPTIONS.md)** - Configure `pipeline()` with `progress_callback`, `device`, `dtype`, etc.
- **[Configuration Reference](./references/CONFIGURATION.md)** - Global `env` configuration for caching and model loading
- **[ModelRegistry Reference](./references/MODEL_REGISTRY.md)** - Inspect files, cache status, dtypes, and clear cache before loading pipelines
- **[Caching Reference](./references/CACHE.md)** - Browser Cache API, Node.js filesystem cache, and custom cache implementations
- **[Text Generation Guide](./references/TEXT_GENERATION.md)** - Streaming, chat format, and generation parameters
- **[Model Architectures](./references/MODEL_ARCHITECTURES.md)** - Supported models and selection tips
- **[Code Examples](./references/EXAMPLES.md)** - Real-world implementations for different runtimes

### Official Transformers.js
- Official docs: https://huggingface.co/docs/transformers.js
- API reference: https://huggingface.co/docs/transformers.js/api/pipelines
- Model hub: https://huggingface.co/models?library=transformers.js
- GitHub: https://github.com/huggingface/transformers.js
- Examples: https://github.com/huggingface/transformers.js-examples

---
This skill enables you to integrate state-of-the-art machine learning capabilities directly into JavaScript applications without requiring separate ML servers or Python environments.
