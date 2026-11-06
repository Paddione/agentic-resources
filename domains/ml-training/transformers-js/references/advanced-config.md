# Advanced Configuration

## Environment Configuration (`env`)

The `env` object provides comprehensive control over Transformers.js execution, caching, and model loading.

**Quick Overview:**

```javascript
import { env, LogLevel } from '@huggingface/transformers';

// View version
console.log(env.version); // e.g., '4.x'

// Common settings
env.allowRemoteModels = true;  // Load from Hugging Face Hub
env.allowLocalModels = false;  // Load from file system
env.localModelPath = '/models/'; // Local model directory
env.useFSCache = true;         // Cache models on disk (Node.js)
env.useBrowserCache = true;    // Cache models in browser
env.cacheDir = './.cache';     // Cache directory location
// Optional: override logging level (default is LogLevel.WARNING)
env.logLevel = LogLevel.INFO;

// Optional: custom fetch for auth headers, retries, abort signals, etc.
env.fetch = (url, options) =>
  fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
      Authorization: `Bearer ${HF_TOKEN}`,
    },
  });
```

**Configuration Patterns:**

```javascript
// Development: Fast iteration with remote models
env.allowRemoteModels = true;
env.useFSCache = true;

// Production: Local models only
env.allowRemoteModels = false;
env.allowLocalModels = true;
env.localModelPath = '/app/models/';

// Custom CDN
env.remoteHost = 'https://cdn.example.com/models';

// Disable caching (testing)
env.useFSCache = false;
env.useBrowserCache = false;
```

For complete documentation on all configuration options, caching strategies, cache management, pre-downloading models, and more, see:

**→ [Configuration Reference](./CONFIGURATION.md)**

## ModelRegistry (v4)

`ModelRegistry` gives you visibility and control over model assets before loading a pipeline. Use it to estimate download size, check cache status, inspect available dtypes, and clear cached artifacts for a specific task/model/options tuple.

```javascript
import { ModelRegistry } from '@huggingface/transformers';

const task = 'feature-extraction';
const modelId = 'onnx-community/all-MiniLM-L6-v2-ONNX';
const modelOptions = { dtype: 'fp32' };

// List required files for this pipeline
const files = await ModelRegistry.get_pipeline_files(task, modelId, modelOptions);

// Check if assets are already cached
const cached = await ModelRegistry.is_pipeline_cached(task, modelId, modelOptions);

// Inspect precision formats available for this model
const dtypes = await ModelRegistry.get_available_dtypes(modelId);

console.log({ files: files.length, cached, dtypes });
```

For production patterns and full API coverage, see **[ModelRegistry Reference](./MODEL_REGISTRY.md)**.

## Standalone Tokenization (`@huggingface/tokenizers`)

For tokenization-only workflows, use `@huggingface/tokenizers`. It is a separate lightweight package useful when you need fast tokenization/encoding without loading full model inference pipelines.

```bash
npm install @huggingface/tokenizers
```

```javascript
import { Tokenizer } from '@huggingface/tokenizers';
```

## Working with Tensors

```javascript
import { AutoTokenizer, AutoModel } from '@huggingface/transformers';

// Load tokenizer and model separately for more control
const tokenizer = await AutoTokenizer.from_pretrained('bert-base-uncased');
const model = await AutoModel.from_pretrained('bert-base-uncased');

// Tokenize input
const inputs = await tokenizer('Hello world!');

// Run model
const outputs = await model(inputs);
```

```javascript
const classifier = await pipeline('sentiment-analysis');

// Process multiple texts
const results = await classifier([
  'I love this!',
  'This is terrible.',
  'It was okay.'
]);
```

## Structured Output / Constrained Decoding (v4.3)

Added in v4.3 (Sep 2026). Constrain text generation to a JSON schema or regex — no external libraries required.

```javascript
import { pipeline } from '@huggingface/transformers';

const generator = await pipeline('text-generation', 'onnx-community/Qwen2.5-0.5B-Instruct');

// Constrain output to a JSON schema
const result = await generator('Extract the name and age from: "Alice is 30 years old"', {
  max_new_tokens: 50,
  constrained_decoding: {
    type: 'json_schema',
    json_schema: {
      name: { type: 'string' },
      age: { type: 'number' }
    }
  }
});

// Constrain output to a regex
const result2 = await generator('What is the capital of France?', {
  max_new_tokens: 20,
  constrained_decoding: {
    type: 'regex',
    pattern: 'Paris|Lyon|Marseille'
  }
});
```

This enables deterministic, schema-valid output without post-processing or retry loops — useful for tool-calling, data extraction, and structured APIs.



## WebGPU Usage
WebGPU provides GPU acceleration in browsers and server-side runtimes (when supported).

**v4.x: The WebGPU runtime was rewritten in C++ using the ONNX Runtime backend**, providing:
- ~4× speedup for BERT-class embedding models
- Support for models up to 8B+ parameters in-browser
- Works in Node.js, Bun, and Deno server-side (same code path as browser)
- Safari 26+ now supported (v4.3, Sep 2026)

```javascript
const pipe = await pipeline('text-generation', 'onnx-community/gemma-3-270m-it-ONNX', {
  device: 'webgpu',
  dtype: 'fp32'
});
```

**Note**: Use `webgpu` when available and fall back to WASM/CPU when not supported. Check support with:
```javascript
const isWebGPUAvailable = navigator.gpu !== undefined; // browser
// Node.js: @webgpu/types package + runtime that exposes GPU
```


## WASM Performance
WASM is the most compatible execution backend across runtimes:

```javascript
// Optimized for browsers with quantization
const pipe = await pipeline('sentiment-analysis', 'model-id', {
  dtype: 'q8'  // or 'q4' for even smaller size
});
```

## Progress Tracking & Loading Indicators

Models can be large (ranging from a few MB to several GB) and consist of multiple files. Track download progress by passing a callback to the `pipeline()` function:

```javascript
import { pipeline } from '@huggingface/transformers';

// Track progress for each file
const fileProgress = {};

function onProgress(info) {
  if (info.status === 'progress_total') {
    console.log(`Total: ${info.progress.toFixed(1)}%`);
    return;
  }

  console.log(`${info.status}: ${info.file ?? ''}`);

  if (info.status === 'progress') {
    fileProgress[info.file] = info.progress;
    console.log(`${info.file}: ${info.progress.toFixed(1)}%`);
  }

  if (info.status === 'done') {
    console.log(`✓ ${info.file} complete`);
  }
}

// Pass callback to pipeline
const classifier = await pipeline('sentiment-analysis', null, {
  progress_callback: onProgress
});
```

**Progress Info Properties:**

```typescript
interface ProgressInfo {
  status: 'initiate' | 'download' | 'progress' | 'progress_total' | 'done' | 'ready';
  name: string;      // Model id or path
  file?: string;     // File being processed (per-file events)
  progress?: number; // Percentage (0-100, for 'progress' and 'progress_total')
  loaded?: number;   // Bytes downloaded (only for 'progress' status)
  total?: number;    // Total bytes (only for 'progress' status)
}
```

For complete examples including browser UIs, React components, CLI progress bars, and retry logic, see:

**→ [Pipeline Options - Progress Callback](./PIPELINE_OPTIONS.md#progress-callback)**
