# Operations: Errors, Performance, Memory, Troubleshooting

## Error Handling

```javascript
try {
  const pipe = await pipeline('sentiment-analysis', 'model-id');
  const result = await pipe('text to analyze');
} catch (error) {
  if (error.message.includes('fetch')) {
    console.error('Model download failed. Check internet connection.');
  } else if (error.message.includes('ONNX')) {
    console.error('Model execution failed. Check model compatibility.');
  } else {
    console.error('Unknown error:', error);
  }
}
```

## Performance Tips

1. **Reuse Pipelines**: Create pipeline once, reuse for multiple inferences
2. **Use Quantization**: Start with `q8` or `q4` for faster inference
3. **Batch Processing**: Process multiple inputs together when possible
4. **Cache Models**: Models are cached automatically (see **[Caching Reference](./CACHE.md)** for details on browser Cache API, Node.js filesystem cache, and custom implementations)
5. **WebGPU for Large Models**: Use WebGPU for models that benefit from GPU acceleration
6. **Prune Context**: For text generation, limit `max_new_tokens` to avoid memory issues
7. **Clean Up Resources**: Call `pipe.dispose()` when done to free memory

## Memory Management

**IMPORTANT:** Always call `pipe.dispose()` when finished to prevent memory leaks.

```javascript
const pipe = await pipeline('sentiment-analysis');
const result = await pipe('Great product!');
await pipe.dispose();  // ✓ Free memory (100MB - several GB per model)
```

**When to dispose:**
- Application shutdown or component unmount
- Before loading a different model
- After batch processing in long-running apps

Models consume significant memory and hold GPU/CPU resources. Disposal is critical for browser memory limits and server stability.

For detailed patterns (React cleanup, servers, browser), see **[Code Examples](./EXAMPLES.md)**

## Troubleshooting

### Model Not Found
- Verify model exists on Hugging Face Hub
- Check model name spelling
- Ensure model has ONNX files (look for `onnx` folder in model repo)

### Memory Issues
- Use smaller models or quantized versions (`dtype: 'q4'`)
- Reduce batch size
- Limit sequence length with `max_length`

### WebGPU Errors
- Check browser compatibility: Chrome 113+, Edge 113+, **Safari 26+** (added in Transformers.js v4.3)
- Try `dtype: 'fp16'` if `fp32` fails
- Fall back to WASM if WebGPU unavailable

