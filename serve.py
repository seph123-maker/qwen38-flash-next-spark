#!/usr/bin/env python3
"""Launch the published configuration; refuses to replace an existing container."""
import argparse,json,pathlib,subprocess,shlex
from effort_alias import prepare

def command(args):
    p=json.loads((pathlib.Path(__file__).parent/'production.json').read_text())
    hf=pathlib.Path(args.hf_cache).expanduser().resolve()
    cache=pathlib.Path(args.compile_cache).expanduser().resolve()
    cmd=['docker','run','-d','--name',args.name,'--restart',p['restart'],
         '--gpus','all','--ipc='+p['ipc_mode'],'--shm-size',str(p['shm_size']),
         '-p',f'{args.port}:8000','-v',f'{hf}:/hf',
         '--tmpfs','/tmp/vllm-prometheus:rw,size=256m']
    for k,v in p['environment'].items():cmd+=['-e',k+'='+v]
    for n in ['vllm','flashinfer']:cmd+=['-v',f'{cache/n}:/root/.cache/{n}']
    template=cache/'chat-templates'/'effort-alias.jinja'
    cmd+=['-v',f'{template}:/qwen38/chat_template.jinja:ro']
    # Docker accepts one entrypoint executable; preserve the remaining argv.
    cmd+=['--entrypoint',p['entrypoint'][0],args.image]+p['entrypoint'][1:]+p['command']
    return p,hf,cache,cmd

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--hf-cache',required=True)
    a.add_argument('--compile-cache',default='./compile-cache')
    a.add_argument('--name',default='qwen38-published')
    a.add_argument('--image',default='qwen38-published:20260915')
    a.add_argument('--port',type=int,default=8000)
    a.add_argument('--dry-run',action='store_true')
    args=a.parse_args();p,hf,cache,cmd=command(args)
    if args.dry_run:print(shlex.join(cmd));return
    if subprocess.run(['docker','container','inspect',args.name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
        raise SystemExit('Container already exists; choose a new name or manage it explicitly.')
    model=hf/pathlib.Path(p['command'][0]).relative_to('/hf')
    if not (model/'config.json').is_file():raise SystemExit('Prepared pinned model missing: '+str(model))
    for n in ['vllm','flashinfer']:(cache/n).mkdir(parents=True,exist_ok=True)
    prepare(model,cache/'chat-templates'/'effort-alias.jinja')
    subprocess.run(cmd,check=True)
    print('Started loading. Check /health before sending inference requests.')

if __name__=='__main__':main()
