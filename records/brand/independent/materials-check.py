"""Independent read-only PDF/Prompt/version material verification."""
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tools.export_prompt_history import extract
OUT=Path(__file__).parent/'pdf';OUT.mkdir(exist_ok=True)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def main():
    material_head='7f60881d89d371f64b1e02c759c48bd079304b0f'
    def git_bytes(name):return subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),'show',material_head+':'+name],cwd=ROOT)
    pdf_path=ROOT/'output/pdf/课航_技术文档.pdf';assert sha(pdf_path)=='32B3718005CC2AD215EB556B855C9F60E6737681801B81BE28D6062230693451'
    assert pdf_path.read_bytes()==git_bytes(pdf_path.relative_to(ROOT).as_posix())
    build=json.loads((ROOT/'records/brand/pdf/technical-pdf-build.json').read_text(encoding='utf-8'))
    assert build['product_head']=='1eadacb6eee7ab4fc013ca586b863e36d6ef8559' and build['pages']==10
    assert all(sha(ROOT/n)==h for n,h in build['source_sha256'].items())
    pdf=fitz.open(pdf_path);assert len(pdf)==10 and pdf.metadata['title'].startswith('课航')
    pages=[]
    for n,page in enumerate(pdf,1):
        text=page.get_text();assert '1eadacb6eee7' in text and '\ufffd' not in text
        out_of_bounds=[]
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line['spans']:
                    x0,y0,x1,y1=span['bbox']
                    if min(x0,y0)<-1 or x1>page.rect.width+1 or y1>page.rect.height+1:out_of_bounds.append(span['text'])
        assert not out_of_bounds,(n,out_of_bounds)
        pages.append(dict(page=n,text_characters=len(text),out_of_bounds_text=out_of_bounds))
    assert '9组品牌/兼容' in pdf[7].get_text() and '原52组与3项' in pdf[7].get_text()
    assert '8782' in pdf[9].get_text() and 'kehang-courses.sqlite' in pdf[9].get_text()
    poppler=shutil.which('pdftoppm');assert poppler
    subprocess.run([poppler,'-scale-to','1200','-png',str(pdf_path),str(OUT/'page')],check=True,capture_output=True)
    for page in pages:
        n=page['page'];generated=OUT/f'page-{n:02d}.png';original=ROOT/f'records/brand/pdf/page-{n:02d}.png'
        assert sha(generated)==sha(original);page.update(rerender_sha256=sha(generated),original_png_sha_matches=True)
    index_path=ROOT/'records/brand/prompts/index.json';index=json.loads(index_path.read_text(encoding='utf-8'));assert len(index)==1
    item=index[0];export_path=index_path.parent/item['export'];export=json.loads(export_path.read_text(encoding='utf-8'))
    assert sha(export_path)==item['export_sha256'] and sha(export_path.with_suffix('.md'))==item['readable_sha256']
    source=Path('C:/Users/DELL/.codex/sessions/2026/11/09')/item['source_file']
    with source.open('rb') as f:prefix=f.read(item['source_prefix_bytes'])
    assert prefix.endswith(b'\n') and hashlib.sha256(prefix).hexdigest().upper()==item['source_prefix_sha256']
    messages,excluded=extract(prefix.decode('utf-8-sig'))
    assert messages==export['messages'] and excluded==export['excluded']
    counts=dict(visible=len(messages),user=sum(m['role']=='user' for m in messages),assistant=sum(m['role']=='assistant' for m in messages),redacted=sum(m['redacted'] for m in messages))
    assert counts==dict(visible=32,user=6,assistant=26,redacted=2)
    user_lines={m['source_line']:m['text'] for m in messages if m['role']=='user'}
    assert user_lines[1402].strip()=='产品名字我觉得应该改改了，AI实验环境管家有点太局限了' and user_lines[1463].strip()=='可以' and user_lines[1538].strip()=='继续'
    current_docs=['docs/课航命名与版本说明.md','docs/课航视频录制脚本.md','docs/课航提交准备清单.md','docs/课航Prompt与验证索引.md',
                  'README.md','PRODUCT.md','DESIGN.md','TASK.md','PLAN.md','HANDOFF.md','REVIEW.md','PROVENANCE.md']
    for name in current_docs:assert (ROOT/name).read_bytes()==git_bytes(name)
    data=dict(checked_at=datetime.now(timezone.utc).isoformat(),material_head=material_head,product_head=build['product_head'],pdf_sha256=sha(pdf_path),pages=pages,
        independent_poppler_render_all_ten_match=True,pdf_font_text_no_replacement_characters=True,source_files=len(build['source_sha256']),source_sha_matches=True,
        prompt_source_prefix_bytes=item['source_prefix_bytes'],prompt_source_prefix_sha256=item['source_prefix_sha256'],prompt_counts=counts,prompt_excluded=excluded,prompt_messages_reextracted_identical=True,
        naming_feedback_source_line=1402,naming_confirmation_source_line=1463,continue_source_line=1538,material_files_equal_fixed_head=current_docs,scope='Read-only existing PDF and exact visible Prompt prefix; no authoring, external model call, install or D-write.')
    (Path(__file__).parent/'materials-checks.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(pdf_pages=len(pdf),all_rerender_match=True,prompt_counts=counts,source_files=len(build['source_sha256']),passed=True)))
if __name__=='__main__':main()
