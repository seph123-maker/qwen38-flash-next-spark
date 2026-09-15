import pathlib,ast
root=pathlib.Path('/usr/local/lib/python3.12/dist-packages/vllm/v1/core')
p=root/'kv_cache_manager.py';s=p.read_text()
anchor='            # Cannot allocate new blocks\n            return None'
assert s.count(anchor)==1
replacement='''            # Local diagnostics only: do not change allocation or scheduling.
            logger.warning("BLOCK_A_ALLOC_FAIL computed=%d prompt=%d new=%d lookahead=%d required=%d available=%d reserved=%d watermark=%d groups=%s",
                request.num_computed_tokens, request.num_prompt_tokens, num_new_tokens,
                num_lookahead_tokens, required_blocks, available_blocks, reserved_blocks,
                watermark_blocks, [(type(m).__name__, len(m.req_to_blocks.get(request.request_id, [])))
                                   for m in self.coordinator.single_type_managers])
            return None'''
assert 'logger =' in s and 'req_to_blocks' in (root/'single_type_kv_cache_manager.py').read_text()
s=s.replace(anchor,replacement);ast.parse(s);p.write_text(s)
p=root/'sched/scheduler.py';s=p.read_text()
anchor='        self._free_request_blocks(request)\n        self.encoder_cache_manager.free(request)'
assert s.count(anchor)==1
s=s.replace(anchor,'''        logger.warning("BLOCK_A_PREEMPT computed=%d prompt=%d generated=%d drop_stale=%s free_blocks=%d",
                       request.num_computed_tokens, request.num_prompt_tokens,
                       request.num_output_tokens, drop_stale_output,
                       self.kv_cache_manager.block_pool.get_num_free_blocks())
'''+anchor)
ast.parse(s);p.write_text(s)
print('Allocation and preemption diagnostics installed; no scheduler behavior changed')
