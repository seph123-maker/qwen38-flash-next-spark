"""Bounded same-fixture regression screen; raw responses never need chat inspection."""
import argparse, hashlib, json, pathlib, time, urllib.request
from grade import grade

ROOT = pathlib.Path(__file__).resolve().parent
API = 'http://127.0.0.1:8000'

def save(p, obj):
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(p)

def metrics():
    raw = urllib.request.urlopen(API + '/metrics', timeout=15).read().decode()
    m = {}
    for line in raw.splitlines():
        if line.startswith('vllm:'):
            key, value = line.rsplit(' ', 1)
            m[key] = float(value)
    return m

def total(m, name):
    return sum(v for k,v in m.items() if k.split('{')[0] == 'vllm:' + name)

def request(payload):
    r = urllib.request.Request(API + '/v1/chat/completions', json.dumps(payload,ensure_ascii=False).encode(), {'Content-Type':'application/json'})
    with urllib.request.urlopen(r, timeout=1500) as f:
        return json.load(f)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('arm');ap.add_argument('--only', default='');args=ap.parse_args()
    out=ROOT/args.arm;out.mkdir(exist_ok=True)
    results=[]
    for f in sorted((ROOT/'fixtures').glob('*.json')):
        fixture=json.loads(f.read_text())
        if args.only and fixture['id'] not in args.only.split(','):continue
        dest=out/(fixture['id']+'.result.json')
        if dest.exists():results.append(json.loads(dest.read_text()));continue
        payload=fixture['payload'];payload['stream']=False
        payload['cache_salt']=hashlib.sha256(('upgrade0913-'+args.arm+'-'+fixture['id']).encode()).hexdigest()
        before=metrics()
        if total(before,'num_requests_running') or total(before,'num_requests_waiting'):
            raise RuntimeError('Foreign inference traffic; paused before '+fixture['id'])
        save(out/(fixture['id']+'.request.json'),payload)
        start=time.monotonic();response=request(payload);elapsed=time.monotonic()-start
        save(out/(fixture['id']+'.response.json'),response)
        after=metrics();save(out/(fixture['id']+'.metrics.json'),{'before':before,'after':after})
        successes=total(after,'request_success_total')-total(before,'request_success_total')
        if successes != 1 or total(after,'num_requests_running') or total(after,'num_requests_waiting'):
            raise RuntimeError('Foreign traffic or invalid request counters at '+fixture['id'])
        tokens=response.get('usage',{}).get('completion_tokens',0)
        decode=total(after,'inter_token_latency_seconds_sum')-total(before,'inter_token_latency_seconds_sum')
        if decode<=0:decode=None
        scored=grade(fixture,response)
        row={'id':fixture['id'],'category':fixture['category'],'grade':scored,'seconds':elapsed,
             'prompt_tokens':response.get('usage',{}).get('prompt_tokens'),'completion_tokens':tokens,
             'decode_counter_seconds':decode,'decode_counter_tps':tokens/decode if decode else None,
             'preemptions':total(after,'num_preemptions_total')-total(before,'num_preemptions_total'),
             'answer_sha256':hashlib.sha256(json.dumps(response['choices'][0]['message'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()}
        save(dest,row);results.append(row);save(out/'summary.json',results)
        print(json.dumps({'id':row['id'],'pass':scored['pass'],'seconds':round(elapsed,2),'tokens':tokens}),flush=True)
    save(out/'summary.json',results)

if __name__=='__main__':main()
