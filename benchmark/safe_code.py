"""Restricted, resource-limited child process for these three tiny pure functions."""
import ast,json,resource,sys
resource.setrlimit(resource.RLIMIT_AS,(192*1024**2,192*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(2,2))
resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
data=json.load(sys.stdin);tree=ast.parse(data['code'])
allowed_attrs={'append','extend','sort','pop','items','keys','values','get','split','strip','join','lower','upper','isdigit','copy','add'}
for node in ast.walk(tree):
    if isinstance(node,(ast.Import,ast.ImportFrom,ast.ClassDef,ast.Global,ast.Nonlocal,ast.With,ast.AsyncWith)):
        raise ValueError('Unsupported construct')
    if isinstance(node,ast.Name) and node.id.startswith('__'):raise ValueError('Private name')
    if isinstance(node,ast.Attribute) and node.attr not in allowed_attrs:raise ValueError('Unsupported attribute')
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.decorator_list:raise ValueError('Decorators unsupported')
ns={'__builtins__':{k:v for k,v in vars(__import__('builtins')).items() if k in ('len','min','max','sorted','range','list','dict','set','tuple','str','int','float','bool','enumerate','zip','sum','any','all','isinstance','ValueError','TypeError','AssertionError')}}
exec(compile(tree,'<model>','exec'),ns)
kind=data['test'];f=ns[kind]
if kind=='clamp':
    for args,expected in [((5,0,10),5),((-3,0,10),0),((20,0,10),10),((2,2,2),2),((-5,-8,-2),-5)]:assert f(*args)==expected
    try:f(1,3,2)
    except ValueError:pass
    else:raise AssertionError('invalid interval')
elif kind=='dedupe':
    for seq,expected in [([],[]),([1,2,1,3,2],[1,2,3]),(['a','a','b'],['a','b']),([None,None,0],[None,0])]:
        before=list(seq);assert f(seq)==expected and seq==before
elif kind=='chunked':
    for seq,n,expected in [([],2,[]),([1,2,3,4,5],2,[[1,2],[3,4],[5]]),([1,2],5,[[1,2]]),([1,2],1,[[1],[2]])]:
        before=list(seq);assert f(seq,n)==expected and seq==before
    for n in [0,-1]:
        try:f([1],n)
        except ValueError:pass
        else:raise AssertionError('invalid size')
else:raise ValueError(kind)
print('PASS')
