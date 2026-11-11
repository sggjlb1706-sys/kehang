"""Record the exact Git bytes of the application, tests and adopted sources."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
    head=git('rev-parse','HEAD').decode().strip()
    files={}
    for row in git('ls-tree','-r','-z',head,'--','campuslab','web','tests','Start-Web.ps1','THIRD_PARTY_NOTICES.md','docs/third-party','docs/reuse.json').split(b'\0'):
        if not row:continue
        meta,name=row.split(b'\t',1);name=name.decode()
        data=(ROOT/name).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest().encode()==meta.split()[-1],name
        files[name]=hashlib.sha256(data).hexdigest()
    assert all(p in files for p in ('campuslab/launcher.py','campuslab/data/practice/README.md','tests/test_practice.py'))
    (ROOT/'records/practice/product.json').write_text(json.dumps(dict(head=head,files=files),indent=2,ensure_ascii=False),encoding='utf8')
    print(head,len(files))
if __name__=='__main__':main()
