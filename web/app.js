'use strict';
const $ = id => document.getElementById(id);
const state = {task:null, course:null, before:null, after:null, analysis:null, epoch:0, importEpoch:0, config:null, hardware:null, needEpoch:0,teacherEpoch:0};
const labels = {pass:'通过',missing:'缺失',mismatch:'不符合',unknown:'未知'};
const names = {os:'操作系统',node:'课程 Node.js',npm:'同一环境的 npm',python:'课程 Python',run:'固定程序运行','package:requests':'requests 依赖','package:torch':'PyTorch 依赖','package:transformers':'Transformers 依赖','model:weights':'固定模型权重','model:inference':'本地离线推理'};

async function api(path,body){
  const r=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});
  const data=await r.json(); if(!r.ok)throw Error(data.error||'请求失败'); return data;
}
function notice(text,error=false){$('notice').textContent=text;$('notice').classList.toggle('error',error);}
async function action(button,fn){if(button)button.disabled=true;try{await fn();}catch(e){notice(e.message,true);}finally{if(button)button.disabled=false;}}
function save(name,obj,type='application/json'){
  const text=typeof obj==='string'?obj:JSON.stringify(obj,null,2);
  const u=URL.createObjectURL(new Blob([text],{type}));
  const a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);
}
function clearAI(){
  $('ai-preview-panel').hidden=true;$('ai-consent').checked=false;$('send-ai').disabled=true;
  $('ai-preview').value='';$('ai-output').textContent='';
}
function clearReports(){
  state.importEpoch++; Object.assign(state,{before:null,after:null,analysis:null});
  $('results').replaceChildren();$('comparison').textContent='';$('before-file').value='';$('after-file').value='';
  $('remediation').replaceChildren();
  $('after-file').disabled=true;$('export').disabled=true;$('export-preview').hidden=true;$('save-export').hidden=true;
  $('diagnosis').hidden=false;clearAI();progress();
}
function clearTask(){
  state.epoch++;clearReports();state.task=null;state.course=null;$('task-panel').hidden=true;$('empty-state').hidden=false;$('command').textContent='';$('remediation').replaceChildren();
}
async function chooseTask(loader,course=null){
  clearTask();const epoch=state.epoch; const spec=await loader();if(epoch!==state.epoch)return;
  state.task=spec;state.course=course;$('task-panel').hidden=false;$('empty-state').hidden=true;
  $('task-title').textContent=spec.title;
  const node=spec.scenario==='node-basics', vm=spec.scenario==='vm-linux';
  $('task-summary').textContent=vm?'Windows宿主 → 所选虚拟化软件 → 具体实例 → Linux来宾固定验证；各层分别核对':node?`Windows · Node.js ${spec.node.min} 至 ${spec.node.max_exclusive} · npm ${spec.npm.min} 至 ${spec.npm.max_exclusive}（均不包含上限）`:`Windows · Python ${spec.python.min} 至 ${spec.python.max_exclusive}（不包含上限） · ${Object.entries(spec.packages).map(([k,v])=>`${k} ≥ ${v}`).join('，')}`+(spec.scenario==='pytorch-gpu'?' · 必须实际GPU运算':'');
  $('task-source').textContent=spec.source;
  $('target-label').textContent=vm?'所选虚拟化软件完整路径（VBoxManage.exe 或 vmrun.exe）':node?'课程 Node.js 完整路径（明确选择 node.exe）':'课程解释器完整路径';
  $('target').placeholder=vm?'例如 C:\\Program Files (x86)\\VMware\\VMware Workstation\\vmrun.exe':node?'例如 C:\\Program Files\\nodejs\\node.exe':'例如 C:\\CoursePython\\python.exe';
  $('target-help').textContent=node?'npm 使用所选 node.exe 同目录的 node_modules/npm/bin/npm-cli.js，并由该 node.exe 执行；PATH 中其他 npm 不作证据。':'py 不可用时，从安装目录或编辑器的解释器设置寻找 python.exe。';
  $('task-id').textContent=`固定任务摘要 ${spec.id}`;
  $('model-options').hidden=spec.scenario!=='local-qwen';$('infer').checked=false;
  $('torch-options').hidden=spec.scenario!=='pytorch-gpu';$('gpu-run').checked=false;$('vm-options').hidden=!vm;
  $('download-tool').href=course?`/api/tool?course=${encodeURIComponent(course)}`:`/api/tool?goal=${spec.scenario}`;
  await guidance();await routes();progress();notice('任务已确定。先查看步骤，再到目标电脑手动采集报告。');
  if(innerWidth<760&&epoch===state.epoch)$('task-panel').scrollIntoView({block:'start'});
}
async function guidance(){
  if(!state.task)return;
  const epoch=state.epoch,serial=state.importEpoch;const mode=$('mode').value;
  const data=await api('/api/plan',{task:state.task,mode,resources:(state.after||state.before)?.resources,report:state.after||state.before});
  if(epoch!==state.epoch||serial!==state.importEpoch||mode!==$('mode').value)return;
  const list=document.createElement('ol');list.className='steps';
  for(const step of data.steps){const item=document.createElement('li');const title=document.createElement('strong');title.textContent=step.title;const body=document.createElement('p');body.textContent=step.body;item.append(title,body);list.append(item);}
  $('guidance').replaceChildren(list);
  if(data.recommendation){const p=document.createElement('p');p.className='notice';p.textContent=data.recommendation;$('guidance').append(p);}
  const links=document.createElement('div');links.className='official-links';
  for(const link of data.links){const a=document.createElement('a');a.textContent=link.title;a.href=link.url;a.target='_blank';a.rel='noopener noreferrer';links.append(a);}
  $('guidance').append(links);
  if(data.preparation){const d=document.createElement('details'),s=document.createElement('summary');s.textContent='从未准备到固定本地推理';d.append(s);for(const text of data.preparation){const p=document.createElement('p');p.textContent=text;d.append(p);}$('guidance').append(d);}
  $('remediation').replaceChildren();
  if(data.remediation?.length){const h=document.createElement('h3');h.textContent='按差异处理';$('remediation').append(h);}
  for(const step of data.remediation||[]){const d=document.createElement('div');d.className='remedy';const h=document.createElement('h3');h.textContent=step.title;const p=document.createElement('p');p.textContent=step.body;const v=document.createElement('p');v.className='muted';v.textContent=step.verify;d.append(h,p,v);$('remediation').append(d);}
  $('prepared-hint').textContent={unsure:'先对照任务要求。选择准备情况只调整提示，不代表环境通过。',missing:'先查看官方下载和安装操作参考，按课程允许的版本自行安装。',installed:state.task.scenario==='node-basics'?'确认所选 node.exe 的完整路径，再生成只读采集命令。':'确认课程解释器的完整路径，再生成只读采集命令。'}[$('prepared').value];
}
$('goal').addEventListener('change',()=>{clearTask();notice('目标已更换，请确认新的任务。');});
$('course-code').addEventListener('input',()=>{if(state.course)clearTask();});
$('goal-form').addEventListener('submit',e=>{e.preventDefault();action(e.submitter,()=>chooseTask(()=>api(`/api/goal?goal=${encodeURIComponent($('goal').value)}`)));});
$('course-form').addEventListener('submit',e=>{e.preventDefault();const code=$('course-code').value.trim().toUpperCase();action(e.submitter,()=>chooseTask(()=>api('/api/course/'+encodeURIComponent(code)),code));});
$('teacher-goal').addEventListener('change',()=>{
  const node=$('teacher-goal').value==='node-basics';
  const fixed=['pytorch-cpu','pytorch-gpu','vm-linux'].includes($('teacher-goal').value);
  $('teacher-python-options').hidden=node||fixed;$('teacher-node-requirements').hidden=!node;$('teacher-fixed-requirements').hidden=!fixed;
  const defaults=['Python 基础实验','Node.js/npm 基础环境 · 演示任务','本地模型入门 · 固定离线实验'];
  if(defaults.includes($('teacher-title').value))$('teacher-title').value=node?defaults[1]:($('teacher-goal').value==='local-qwen'?defaults[2]:defaults[0]);
});
$('teacher-form').addEventListener('submit',e=>{
  e.preventDefault();action(e.submitter,async()=>{
    const epoch=state.epoch,serial=state.teacherEpoch;
    const result=await api('/api/course',{title:$('teacher-title').value,scenario:$('teacher-goal').value,python_min:$('python-min').value,python_max:$('python-max').value,requests_min:$('requests-min').value});
    if(epoch!==state.epoch||serial!==state.teacherEpoch)return;
    $('published').textContent=`课程码 ${result.code} · 本机入口 ${location.origin}/?course=${result.code}`;
    await chooseTask(async()=>result.task,result.code);
  });
});
$('teacher-form').addEventListener('input',()=>{state.teacherEpoch++;});
$('download-task').addEventListener('click',()=>save('task.json',state.task));
for(const id of ['mode','prepared'])$(id).addEventListener('change',()=>{clearAI();guidance().catch(e=>notice(e.message,true));});

const ps = value => '"'+value.replace(/[`"$\u2018-\u201f]/g,character=>'`'+character)+'"';
function requirePath(value,label){if(!/^[a-zA-Z]:[\\/]/.test(value)||/[\r\n\0]/.test(value))throw Error(label+'须填写完整的Windows路径');return value;}
$('make-command').addEventListener('click',()=>{
  try{
    if(!state.task)throw Error('请先确定任务');
    const root=requirePath($('tool-dir').value.trim(),'工具目录');const target=requirePath($('target').value.trim(),state.task.scenario==='node-basics'?'课程 Node.js':'课程解释器');
    const toolPython=$('tool-python').value.trim();if(toolPython)requirePath(toolPython,'工具Python');
    if(!toolPython&&!state.config?.portable_available)throw Error('当前工具包未配置独立运行时，请填写已有工具Python；工具Python不代表课程环境。');
    const stage=$('report-stage').value;const lines=["$ErrorActionPreference = 'Stop'",`$taskToolRoot = ${ps(root)}`,`$taskTarget = ${ps(target)}`,"if (!(Test-Path -LiteralPath $taskToolRoot -PathType Container)) { throw '工具目录不存在，请完整解压' }",'$taskSnapshot = Join-Path $taskToolRoot '+ps('task.json'),"if (!(Test-Path -LiteralPath $taskSnapshot -PathType Leaf)) { throw '缺少task.json，请完整解压本任务工具' }",`if ((Get-Content -LiteralPath $taskSnapshot -Raw -Encoding UTF8 | ConvertFrom-Json).id -ne ${ps(state.task.id)}) { throw '工具任务与网页任务不一致，请重新下载' }`,`$taskRunner = ${toolPython?ps(toolPython):'Join-Path $taskToolRoot '+ps('runtime\\python.exe')}`,"if (!(Test-Path -LiteralPath $taskRunner -PathType Leaf)) { throw '工具Python不存在' }",'Set-Location -LiteralPath $taskToolRoot'];
    let command=`& $taskRunner -B -m campuslab.collect --task $taskSnapshot --target $taskTarget --output (Join-Path $taskToolRoot ${ps('report-'+stage+'.json')})`;
    if(state.task.scenario==='local-qwen')command+=' --model-dir '+ps(requirePath($('model-dir').value.trim(),'模型目录'))+($('infer').checked?' --infer':'');
    if(state.task.scenario.startsWith('pytorch-')&&$('gpu-run').checked)command+=' --gpu-run';
    if(state.task.scenario==='vm-linux'){
      const instance=$('vm-id').value.trim();if(instance){if(/[\r\n\0]/.test(instance))throw Error('实例标识含无效字符');command+=' --vm-id '+ps(instance);}
      if($('guest-path').value.trim())command+=' --guest-report '+ps(requirePath($('guest-path').value.trim(),'来宾报告'));
    }
    lines.push(command,"if ($LASTEXITCODE -ne 0) { throw '采集未完成；请查看错误，不要把旧报告当作本次结果' }");
    $('command').textContent=lines.join('\n');notice('已生成命令。先检查路径和操作内容，再由本人到目标电脑运行。');
  }catch(e){$('command').textContent='';notice(e.message,true);}
});
for(const id of ['tool-dir','target','tool-python','model-dir','infer','report-stage','gpu-run','vm-id','guest-path'])$(id).addEventListener('input',()=>{$('command').textContent='';if(['target','model-dir','vm-id'].includes(id))clearReports();});

function render(a){
  state.analysis=a;$('results').replaceChildren();
  const identity=document.createElement('p');identity.textContent=`本次目标：${a.target.requested} · ${a.collected_at}`;$('results').append(identity);
  const next=document.createElement('p');next.className='result-summary';const counts=Object.fromEntries(Object.keys(labels).map(key=>[key,a.checks.filter(x=>x.status===key).length]));
  next.textContent=`通过 ${counts.pass} · 缺失 ${counts.missing} · 不符合 ${counts.mismatch} · 未知 ${counts.unknown}。`+(a.passed?(state.after?'核对同目标复检结论。':'初检已通过，保留原件后采集较晚的B。'):'查看“按差异处理”的下一步，手动处理后复检。');$('results').append(next);
  for(const c of a.checks){
    const row=document.createElement('div');row.className='check';const name=document.createElement('strong');name.textContent=names[c.id]||c.id;
    const status=document.createElement('strong');status.className='state-'+c.status;status.textContent=labels[c.status];
    const detail=document.createElement('details'),summary=document.createElement('summary');summary.textContent='查看事实与要求';const observed=document.createElement('pre');observed.textContent=JSON.stringify({observed:c.observed,requirement:c.requirement},null,2);detail.append(summary,observed);row.append(name,status,detail);$('results').append(row);
  }
  $('export').disabled=false;$('diagnosis').hidden=false;
  $('ai-status').textContent=state.config?.ai.configured?'AI已配置。先检查发送目的地和脱敏内容，再主动发送一次请求。':'AI未配置，尚未发送任何请求。可继续使用完整规则结果与操作指导。';
  notice(a.passed?'本报告全部检查通过。':'仍有缺失、不符合或未知，请按指导处理后复检。');
  progress();
}
async function importReport(which,file){
  if(!state.task)throw Error('请先选择任务');
  if(which==='after'&&!state.before)throw Error('请先导入有效初检报告A');
  const epoch=state.epoch, serial=++state.importEpoch, spec=state.task;
  clearAI();$('export-preview').hidden=true;$('save-export').hidden=true;$('remediation').replaceChildren();
  if(which==='before'){
    Object.assign(state,{before:null,after:null,analysis:null});$('after-file').value='';$('after-file').disabled=true;
    $('results').replaceChildren();$('comparison').textContent='';$('export').disabled=true;$('diagnosis').hidden=false;
  }else{
    state.after=null;$('comparison').textContent='';
    if(state.before){const baseline=await api('/api/analyze',{task:spec,report:state.before});if(epoch!==state.epoch||serial!==state.importEpoch)return;render(baseline);}
  }
  if(!file||file.size>200000)throw Error('请选择小于200KB的JSON报告');
  const report=JSON.parse(await file.text());const analysis=await api('/api/analyze',{task:spec,report});
  let comparison=null;if(which==='after')comparison=await api('/api/compare',{task:spec,before:state.before,after:report});
  if(epoch!==state.epoch||serial!==state.importEpoch)return;
  state[which]=report;render(analysis);$('after-file').disabled=!state.before;
  if(comparison)$('comparison').textContent=({'stable-pass':'同一目标稳定复检通过；两次均通过。',repaired:'同一目标从存在缺失或不符合改善为通过。',verified:'同一目标补齐实际运行证据后通过；不记为故障修复。',incomplete:'同一目标复检仍未全部通过。'})[comparison.outcome];
  progress();await guidance();
}
for(const [id,which] of [['before-file','before'],['after-file','after']])$(id).addEventListener('change',async e=>{try{await importReport(which,e.target.files[0]);}catch(error){e.target.value='';notice(error.message,true);}});

$('prepare-ai').addEventListener('click',e=>action(e.target,async()=>{
  const epoch=state.epoch,serial=state.importEpoch;clearAI();
  const result=await api('/api/preview',{task:state.task,report:state.after||state.before,error:$('user-error').value});
  if(epoch!==state.epoch||serial!==state.importEpoch)return;
  $('ai-preview').value=result.preview;$('ai-preview-panel').hidden=false;
  $('ai-destination').textContent=result.ai.configured?`本次目的地：${result.ai.destination} · 模型 ${result.ai.model}`:'AI未配置，不会发送。预览可供你检查已有证据。';
  $('ai-system').textContent=result.ai.system;
}));
for(const id of ['ai-preview','user-error'])$(id).addEventListener('input',()=>{$('ai-consent').checked=false;$('send-ai').disabled=true;});
$('ai-consent').addEventListener('change',()=>{$('send-ai').disabled=!$('ai-consent').checked||!state.config?.ai.configured;});
$('send-ai').addEventListener('click',e=>action(e.target,async()=>{
  const epoch=state.epoch,serial=state.importEpoch;
  const request={task:state.task,report:state.after||state.before,preview:$('ai-preview').value,consent:$('ai-consent').checked};
  $('ai-consent').checked=false;
  try{const result=await api('/api/diagnose',request);if(epoch===state.epoch&&serial===state.importEpoch)$('ai-output').textContent=result.explanation;}finally{setTimeout(()=>{$('send-ai').disabled=true;},0);}
}));
$('export').addEventListener('click',e=>action(e.target,async()=>{
  const epoch=state.epoch,serial=state.importEpoch;
  const value=await api('/api/share',{task:state.task,report:state.after||state.before});
  if(epoch!==state.epoch||serial!==state.importEpoch)return;
  $('export-preview').value=JSON.stringify(value,null,2);
  $('export-preview').hidden=false;$('save-export').hidden=false;notice('已做基础脱敏。请继续检查个人路径、邮箱和无关日志，再保存分享。');
}));
$('save-export').addEventListener('click',()=>{try{JSON.parse($('export-preview').value);save('CampusLab-share.json',$('export-preview').value);}catch(e){notice('编辑后须保留有效JSON。',true);}});
function progress(){
  $('progress-evidence').textContent=state.before?'② 已有初检事实':'② 准备并采集';
  $('progress-recheck').textContent=state.after?(state.analysis?.passed?'③ 复检全部通过':'③ 复检仍有差异'):'③ 等待同目标复检';
}
async function routes(){
  if(!state.task)return;
  const epoch=state.epoch, hardware=state.hardware;
  const result=await api('/api/recommend',{task:state.task,hardware});
  if(epoch!==state.epoch||hardware!==state.hardware)return;
  const box=$('route-advice');box.replaceChildren();const title=document.createElement('h3');title.textContent='依据当前证据的准备路线';box.append(title);
  const summary=document.createElement('p');summary.textContent=result.summary;box.append(summary);
  for(const text of [...(result.actions||[]),...(result.alternatives||[])]){const p=document.createElement('p');p.textContent=typeof text==='string'?text:JSON.stringify(text);box.append(p);}
}
$('need-form').addEventListener('submit',e=>{e.preventDefault();const serial=++state.needEpoch;action(e.submitter,async()=>{
  const text=$('need-text').value;const result=await api('/api/need',{text});if(serial!==state.needEpoch)return;
  const box=$('need-result');box.replaceChildren();const p=document.createElement('p');p.textContent=result.message+' '+(result.question||'');box.append(p);
  const candidates=result.candidates||[];
  if(result.scenario&&!candidates.some(x=>x.scenario===result.scenario))candidates.unshift({scenario:result.scenario,label:result.scenario});
  for(const candidate of candidates){if(!candidate.scenario)continue;const b=document.createElement('button');b.className='secondary';b.textContent='确认：'+candidate.label;b.addEventListener('click',()=>action(b,async()=>{
    const resolved=await api('/api/need',{text,clarification:candidate.scenario});if(serial!==state.needEpoch)return;
    if(resolved.status!=='recognized'||!resolved.scenario){notice(resolved.message,true);return;}
    $('goal').value=resolved.scenario;await chooseTask(()=>api('/api/goal?goal='+encodeURIComponent(resolved.scenario)));
  }));box.append(b);}
  if(result.error_help){$('user-error').value=text;$('diagnosis').scrollIntoView({block:'nearest'});}
});});
$('need-text').addEventListener('input',()=>{state.needEpoch++;$('need-result').replaceChildren();});
$('course-package').addEventListener('change',e=>action(null,async()=>{
  clearTask();const epoch=state.epoch;
  const file=e.target.files[0];if(!file||file.size>100000)throw Error('课程包须小于100KB');const packageValue=JSON.parse(await file.text());
  const result=await api('/api/import-course',{package:packageValue});
  if(epoch!==state.epoch)return;
  await chooseTask(async()=>result.task,result.code);notice('课程包已导入。请向教师核对任务摘要；摘要一致性不证明发布人身份。');
}));
$('export-course').addEventListener('click',e=>action(e.target,async()=>save('CampusLab-course.json',await api('/api/package',{task:state.task}))));
$('export-guide').addEventListener('click',e=>action(e.target,async()=>{
  const r=await fetch('/api/guide',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:state.task})});
  if(!r.ok)throw Error('指导导出失败');save('CampusLab-guide.html',await r.text(),'text/html');
}));
$('hardware-command').addEventListener('click',()=>{try{
  const root=requirePath($('tool-dir').value.trim(),'先在采集面板填写工具目录');const toolPython=$('tool-python').value.trim();
  if(toolPython)requirePath(toolPython,'工具Python');if(!toolPython&&!state.config?.portable_available)throw Error('请先填写已有工具Python');
  $('hardware-script').textContent=["$ErrorActionPreference = 'Stop'",'Set-Location -LiteralPath '+ps(root),`& ${toolPython?ps(toolPython):ps(root+'\\runtime\\python.exe')} -B -m campuslab.preparation --output ${ps(root+'\\hardware.json')} --drive ${ps(root.slice(0,3))}`,"if ($LASTEXITCODE -ne 0) { throw '硬件预检未完成' }"].join('\n');
}catch(e){notice(e.message,true);}});
$('hardware-file').addEventListener('change',e=>action(null,async()=>{
  const file=e.target.files[0];if(!file||file.size>100000)throw Error('硬件报告须小于100KB');const report=JSON.parse(await file.text());
  await api('/api/recommend',{task:state.task,hardware:report});state.hardware=report;
  const box=$('hardware-results');box.replaceChildren();
  for(const [key,field] of Object.entries(report.fields)){const p=document.createElement('p');p.textContent=key+'：'+(field.value===null?'未知 · '+field.reason:JSON.stringify(field.value))+' · 来源 '+field.source+' · '+field.collected_at;box.append(p);}
  await routes();notice('已导入硬件证据；准备建议不改变课程验收结果。');
}));
Object.assign(names,{'torch:import':'PyTorch 实际导入','torch:cpu':'固定 CPU 张量','torch:cuda-build':'框架 CUDA 构建','torch:gpu-available':'GPU 可用性','torch:gpu-identity':'GPU 设备身份','torch:gpu-run':'实际 GPU 张量','host:virtualization':'宿主虚拟化条件','vm:software':'所选虚拟化软件','vm:instance':'所选虚拟机实例','vm:running':'实例运行证据','guest:identity':'来宾身份','guest:linux':'Linux 系统证据','guest:run':'来宾固定程序'});
api('/api/catalog').then(catalog=>{for(const item of catalog){const d=document.createElement('div');d.className='catalog-item';const h=document.createElement('h3');h.textContent=item.label;const p=document.createElement('p');p.textContent=item.status+' · '+item.extension;d.append(h,p);if(item.source.startsWith('https://')){const a=document.createElement('a');a.textContent='课程来源';a.href=item.source;a.target='_blank';a.rel='noopener noreferrer';d.append(a);}$('catalog').append(d);}}).catch(e=>notice(e.message,true));
api('/api/config').then(config=>{state.config=config;}).catch(e=>notice(e.message,true));
const courseFromURL=new URLSearchParams(location.search).get('course');if(courseFromURL){$('course-code').value=courseFromURL;$('course-form').requestSubmit();}
