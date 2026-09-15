"""Adapt Blazux PR #24's reasoning-effort aliases without modifying weights."""
from pathlib import Path

OLD = "{%- set resolved_reasoning_effort = reasoning_effort|default('xhigh') %}"
NEW = "{%- set resolved_reasoning_effort = {'high': 'xhigh', 'max': 'xhigh', 'minimal': 'low'}.get(reasoning_effort|default('xhigh'), reasoning_effort|default('xhigh')) %}"

def prepare(model, destination):
    source = (Path(model) / 'chat_template.jinja').read_text()
    if source.count(OLD) != 1:
        raise ValueError('Unexpected chat template: review before applying effort aliases.')
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.replace(OLD, NEW))
    return target.resolve()
