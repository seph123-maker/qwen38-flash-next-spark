[Home](../README.md) · [Settings](CONFIGURATION.md)

# Terms used in this recipe

| Term | Meaning here |
|---|---|
| Recipe | A particular combination of model files, serving software, patches and settings |
| Checkpoint / weights | The stored learned parameters loaded by the model server |
| Abliterated checkpoint | A derivative whose weights were modified to reduce refusal behavior; the label alone does not establish quality or how closely it matches the original |
| Token | A piece of text used by the model; not necessarily a whole word |
| Context window | The configured token capacity for input and generated output; capacity alone does not establish reasoning quality at that length |
| Prefill | Processing the input prompt before generation |
| Decode | Generating the answer after processing the prompt |
| MTP / speculative decoding | Draft possible next tokens, then verify them together; in this model the drafter is built in |
| K2 / K3 | Draft two / three tokens ahead |
| Draft acceptance | How often proposed tokens survive verification; an efficiency measure, not a direct intelligence score |
| PLE | This model's large lookup-table component, served from a file by this recipe |
| mmap | Map a file into a process's address space so the operating system can bring required portions into memory |
| KV cache | Stored attention history reused during generation |
| Prefix caching | Reuse processing for identical beginnings of prompts |
| Compilation cache | Saved compiled code; separate from prompt history and model weight loading |
| NVFP4 / FP8 / BF16 | Numerical formats used for different model components; they have different memory costs and precision |
| YaRN | The RoPE position-scaling method configured here to extend the context window |
| CUDA graph / PIECEWISE | A way to replay GPU operations with less launch overhead; this recipe captures sections while leaving CPU-dependent work outside |
| Preemption | A request is rescheduled when the server cannot keep progressing with its available cache resources; it can add latency |
| Deterministic top-k | Repeatable selection of the highest-scoring attention candidates; not a guarantee of identical whole-model output across all executions |
| Container / image | A running isolated server process / the packaged software used to start it |
| Pin | An exact source revision or image digest, used instead of a moving `latest` reference |
