"""Fetch terminal jobs with resumable per-file downloads; retry failed targets only."""
import json,sys,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'denovo'))
from japan_client import api,write,utc
from prepare import RUN


def download(folder,item,job):
 path=folder/'artifacts'/item['path'];base=(folder/'artifacts').resolve()
 if not path.resolve().is_relative_to(base):raise ValueError('Unsafe artifact path')
 path.parent.mkdir(parents=True,exist_ok=True)
 receipt=path.with_name(path.name+'.sha256')
 if path.exists() and receipt.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==receipt.read_text().strip():return path
 data=api(item['url'],raw=True,timeout=45)
 if len(data)>64_000_000:raise ValueError('Unexpected artifact size')
 if path.suffix=='.json':json.loads(data)
 if path.suffix=='.cif' and b'_atom_site.' not in data:raise ValueError('Invalid structure artifact')
 tmp=path.with_name(path.name+'.partial');tmp.write_bytes(data);tmp.replace(path)
 receipt.write_text(hashlib.sha256(data).hexdigest()+'\n');return path


def main():
 import argparse
 argparse.ArgumentParser(description=__doc__).parse_args()
 retry=[]
 folders=sorted([p for p in RUN.iterdir() if p.is_dir() and (p/'submission.json').exists()])
 for folder in folders:
  saved=json.loads((folder/'submission.json').read_text());job=api('/v1/jobs/'+saved['job_id']);write(folder/'job.json',job)
  print(folder.name,json.dumps({k:job.get(k) for k in ['status','done','total','partial','error']}),flush=True)
  if job['status']!='succeeded':continue
  results=api('/v1/jobs/'+saved['job_id']+'/results');write(folder/'results.json',results)
  artifacts={r['path']:r for r in results['artifacts'] if r['path'].endswith(('.cif','_pae.json','_pae.npz'))}
  failures=[]
  with ThreadPoolExecutor(max_workers=4) as pool:
   futures={pool.submit(download,folder,item,job):name for name,item in artifacts.items()}
   for f in as_completed(futures):
    try:f.result()
    except Exception as e:failures.append(dict(path=futures[f],error=type(e).__name__))
  write(folder/'per-file-download-receipt.json',dict(job_id=saved['job_id'],utc=utc(),failures=failures,
   artifacts=[dict(path=str(p.relative_to(folder/'artifacts')),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in sorted((folder/'artifacts').rglob('*')) if p.is_file() and p.suffix not in ['.sha256','.partial']]))
  print(folder.name,'downloaded',len(artifacts)-len(failures),'of',len(artifacts),flush=True)
  # Retry is a new explicit logical attempt, never another attempt of a delivered structure.
  if job.get('partial') and 'retry' not in folder.name:
   success={r['id'] for r in results['rows'] if r.get('status')=='ok'};req=json.loads((folder/'request.json').read_text())
   missing=[r for r in req['targets'] if r['name'] not in success]
   dest=folder.with_name(folder.name+'-retry')
   if missing and not dest.exists():
    dest.mkdir();req['targets']=missing;req['name']+='-hardware-retry';write(dest/'request.json',req)
    write(dest/'retry-provenance.json',dict(parent_job=saved['job_id'],reason=job.get('error'),delivered=sorted(success),requested_retry=[r['name'] for r in missing],utc=utc()))
    retry.append(str(dest))
 write(RUN/'new-retries-to-submit.json',retry)

if __name__=='__main__':main()
