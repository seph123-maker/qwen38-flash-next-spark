import pathlib,ast
p=pathlib.Path('/usr/local/lib/python3.12/dist-packages/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py')
s=p.read_text()
anchor='    if backend in ["flashinfer", "auto"] and supports_flashinfer:'
insert='    elif (\n        current_platform.is_device_capability_family(120)\n        and head_k_dim == 128\n        and current_platform.get_cuda_runtime_major() >= 13\n    ):\n        # vllm#55715: FlashInfer supports SM12x; CuteDSL remains SM100-only.\n        supports_flashinfer = True\n\n'
assert s.count(anchor)==1
assert 'is_device_capability_family(120)' not in s
s=s.replace(anchor,insert+anchor)
ast.parse(s)
p.write_text(s)
print('Applied vllm#55715 GDN SM12x selector support')
