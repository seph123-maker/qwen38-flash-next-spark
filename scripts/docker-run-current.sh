#!/usr/bin/env bash
# Reproduce the CURRENT live recipe (2026-10-15, v2.1). Source of truth: recipe-current.json
set -euo pipefail
docker run --detach --name qwen38-flash --restart unless-stopped --network bridge --ipc host \
  --shm-size 17179869184 --gpus all --security-opt label=disable \
  --tmpfs /tmp/vllm-prometheus:rw,size=256m -p 8000:8000 \
  -v /home/mogu/.cache/huggingface:/hf \
  -v /home/mogu/nvidia-migration-20260927/compile-cache/vllm:/root/.cache/vllm \
  -v /home/mogu/nvidia-migration-20260927/compile-cache/cuda:/root/.nv \
  -v /home/mogu/nvidia-migration-20260927/compile-cache/triton:/root/.triton \
  -v /home/mogu/nvidia-migration-20260927/compile-cache/flashinfer:/root/.cache/flashinfer \
  -v /home/mogu/nvidia-migration-20260927/compile-cache/chat-templates/effort-alias.jinja:/qwen38/chat_template.jinja:ro \
  -e HF_HOME=/hf -e HF_HUB_OFFLINE=1 -e VLLM_ALLOW_LONG_MAX_MODEL_LEN=1 \
  -e VLLM_PLE_MMAP=1 -e VLLM_PLE_MMAP_MADVISE=random -e VLLM_PLE_MMAP_WORKERS=16 \
  -e VLLM_PLE_MMAP_PREWARM=0 -e VLLM_PLE_MMAP_FAST_ROWS=256 \
  -e VLLM_FP8_HYBRID=1 -e VLLM_QSA_DET_TOPK=1 -e VLLM_QSA_EXACT_TOPK=0 \
  -e VLLM_QSA_DET_LIB=/opt/llm/kernel-det/_C_det.so \
  -e VLLM_MTP_DRAFT_VOCAB=/opt/llm/draft_vocab_65536.npy \
  -e VLLM_USE_DEEP_GEMM=0 -e VLLM_USE_FLASHINFER_SAMPLER=1 \
  -e PROMETHEUS_MULTIPROC_DIR=/tmp/vllm-prometheus \
  qwen38-published:20261004-v031 \
  serve /hf/hub/models--nvidia--Qwen3.8-Flash-Next-NVFP4/snapshots/fc694b54fb0174e0913e6adf86691ef85a4ead47-fp8hybrid --served-model-name qwen3.8-flash-next --host 0.0.0.0 --port 8000 --load-format safetensors --max-model-len 524288 --max-num-seqs 4 --gpu-memory-utilization 0.80 --enable-prefix-caching --enable-chunked-prefill --max-num-batched-tokens 8192 -cc.cudagraph_mode=PIECEWISE '-cc.splitting_ops=["vllm::unified_attention_with_output","vllm::unified_mla_attention_with_output","vllm::mamba_mixer2","vllm::mamba_mixer","vllm::short_conv","vllm::qwen4_exp_ple_short_conv","vllm::qwen4_exp_qsa_with_output","vllm::linear_attention","vllm::qwen_gdn_attention_core","vllm::qwen_gdn_attention_core_fused_norm_packed","vllm::gdn_attention_core_xpu","vllm::olmo_hybrid_gdn_full_forward","vllm::sparse_attn_indexer","vllm::rocm_aiter_sparse_attn_indexer","vllm::deepseek_v4_attention","vllm::hpc_rope_norm_forward","vllm::unified_kv_cache_update","vllm::unified_mla_kv_cache_update","vllm::ple_mmap_lookup_ids"]' --no-enable-flashinfer-autotune --kv-cache-dtype fp8_e4m3 --hf-overrides '{"text_config": {"rope_parameters": {"mrope_interleaved": true, "mrope_section": [11, 11, 10], "rope_type": "yarn", "rope_theta": 10000000, "partial_rotary_factor": 0.25, "factor": 2.0, "original_max_position_embeddings": 262144}}}' --enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3 --chat-template /qwen38/chat_template.jinja --speculative-config '{"method":"mtp","num_speculative_tokens":2,"max_model_len": 524288}'
