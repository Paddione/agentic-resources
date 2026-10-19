from pathlib import Path
import json, importlib.util, hashlib, tempfile, copy
s=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('validator',s/'scripts/validate_graph.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
raw=b'def hello():\n    return 1\n'
g={'schema_version':1,'manifest':{'repo':'fixture','commit':'a'*40,'generation':'receipt-1','tool_version':'fixture-1','scope':['.'],'dirty':False,'complete':True,'pagination_exhausted':True},'files':[{'path':'app.py','sha256':hashlib.sha256(raw).hexdigest(),'coverage':'indexed'}],'nodes':[{'id':'hello','kind':'Function','qualified_name':'app.hello','origin':'source','path':'app.py','start_line':1,'end_line':2}],'edges':[{'id':'self','source':'hello','target':'hello','kind':'CALLS','evidence':'parsed','strategy':'fixture'}]}
(s/'evals/valid-graph.json').write_text(json.dumps(g,indent=2)+'\n')
checks=[]
with tempfile.TemporaryDirectory() as directory:
 root=Path(directory); (root/'app.py').write_bytes(raw)
 checks.append(('valid-source',m.validate(g,root)['valid']))
 bad=copy.deepcopy(g);bad['nodes'][0]['end_line']=3
 checks.append(('reject-out-of-file-span',not m.validate(bad,root)['valid']))
 (root/'app.py').write_bytes(b'changed\n')
 checks.append(('reject-stale-source',not m.validate(g,root)['valid']))
for name,edit in [
 ('reject-dangling-edge',lambda x:x['edges'][0].update(target='missing')),
 ('reject-traversal',lambda x:x['files'][0].update(path='../app.py')),
 ('reject-windows-path',lambda x:x['files'][0].update(path='C:\\app.py')),
 ('reject-unexhausted-complete',lambda x:x['manifest'].update(pagination_exhausted=False)),
 ('reject-missing-generation',lambda x:x['manifest'].pop('generation')),
 ('reject-unknown-coverage-complete',lambda x:x['files'][0].update(coverage='unknown',reason='parser')),
 ('reject-duplicate-id',lambda x:x['nodes'].append(copy.deepcopy(x['nodes'][0]))),
 ('reject-bool-confidence',lambda x:x['edges'][0].update(confidence=True)),
 ('reject-embedding-drift',lambda x:x.update(embeddings={'model':'m','dimension':2,'generation':'other','items':[]})),
 ('reject-nonfinite-vector',lambda x:x.update(embeddings={'model':'m','dimension':2,'generation':'receipt-1','items':[{'node_id':'hello','input_sha256':'a'*64,'vector':[float('nan'),1]}]})),
 ('reject-malformed-node',lambda x:x['nodes'].append([]))]:
 bad=copy.deepcopy(g);edit(bad);checks.append((name,not m.validate(bad)['valid']))
partial=copy.deepcopy(g);partial['manifest'].update(complete=False,pagination_exhausted=False);checks.append(('partial-labelled',m.validate(partial)['valid'] and bool(m.validate(partial)['warnings'])))
(s/'evals/validator-results.json').write_text(json.dumps({'checks':[{'name':name,'passed':passed} for name,passed in checks]},indent=2)+'\n')
print(f'{sum(ok for _,ok in checks)}/{len(checks)} artifact checks passed')
assert all(ok for _,ok in checks)
