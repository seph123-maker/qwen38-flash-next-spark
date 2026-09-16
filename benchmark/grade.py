import json,pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent

def clean(content):
    m=re.fullmatch(r'\s*```(?:python|json)?\s*\n(.*?)\n```\s*',content,re.S)
    return (m.group(1),True) if m else (content.strip(),False)

def grade(fixture,response):
    choice=response['choices'][0];message=choice['message'];text,fenced=clean(message.get('content') or '')
    result={'pass':False,'format_fenced':fenced,'truncated':choice['finish_reason']=='length'}
    if result['truncated']:return result
    key=fixture['key']
    try:
        if key['kind']=='code':
            proc=subprocess.run([sys.executable,'-I',str(ROOT/'safe_code.py')],input=json.dumps({'code':text,'test':key['test']}),text=True,capture_output=True,timeout=4)
            result['pass']=proc.returncode==0 and proc.stdout.strip()=='PASS'
            if not result['pass']:result['reason']='code_test_failed'
        elif key['kind']=='json':
            result['pass']=json.loads(text)==key['expected']
            if not result['pass']:result['reason']='json_value_mismatch'
        else:
            calls=[]
            for call in message.get('tool_calls') or []:
                fun=call['function'];args=fun['arguments'];args=json.loads(args) if isinstance(args,str) else args
                calls.append({'name':fun['name'],'arguments':args})
            canonical=lambda xs:sorted(json.dumps(x,sort_keys=True,ensure_ascii=False) for x in xs)
            result['pass']=canonical(calls)==canonical(key['calls']) and not text
            if not result['pass']:result['reason']='native_tool_calls_mismatch'
    except Exception as exc:result['reason']=type(exc).__name__
    return result
