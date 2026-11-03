'use strict';
const $ = id => document.getElementById(id);
const state = {task:null, course:null, before:null, after:null, analysis:null, epoch:0, importEpoch:0, config:null};
const labels = {pass:'通过',missing:'缺失',mismatch:'不符合',unknown:'未知'};
const names = {os:'操作系统',python:'课程 Python',run:'固定程序运行','package:requests':'requests 依赖','package:torch':'PyTorch 依赖','package:transformers':'Transformers 依赖','model:weights':'固定模型权重','model:inference':'本地离线推理'};

async function api(path,body){
  const r=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});
  const data=await r.json(); if(!r.ok)throw Error(data.error||'请求失败'); return data;
}
function notice(text,error=false){$('notice').textContent=text;$('notice').classList.toggle('error',error);}
async function action(button,fn){if(button)button.disabled=true;try{await fn();}catch(e){notice(e.message,true);}finally{if(button)button.disabled=false;}}
function save(name,obj){
  const text=typeof obj==='string'?obj:JSON.stringify(obj,null,2);
  const u=URL.createObjectURL(new Blob([text],{type:'application/json'}));
  const a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);
}
function clearAI(){
  $('ai-preview-panel').hidden=true;$('ai-consent').checked=false;$('send-ai').disabled=true;
  $('ai-preview').value='';$('ai-output').textContent='';
}
function clearReports(){
  state.importEpoch++; Object.assign(state,{before:null,after:null,analysis:null});
  $('results').replaceChildren();$('comparison').textContent='';$('before-file').value='';$('after-file').value='';
  $('after-file').disabled=true;$('export').disabled=true;$('export-preview').hidden=true;$('save-export').hidden=true;
  $('diagnosis').hidden=true;clearAI();
}
function clearTask(){
  state.epoch++;clearReports();state.task=null;state.course=null;$('task-panel').hidden=true;$('command').textContent='';
}
async function chooseTask(loader,course=null){
  clearTask();const epoch=state.epoch; const spec=await loader();if(epoch!==state.epoch)return;
  state.task=spec;state.course=course;$('task-panel').hidden=false;
  $('task-title').textContent=spec.title;
  $('task-summary').textContent=`Windows · Python ${spec.python.min} 至 ${spec.python.max_exclusive}（不包含上限） · ${Object.entries(spec.packages).map(([k,v])=>`${k} ≥ ${v}`).join('，')}`;
  $('task-id').textContent=`固定任务摘要 ${spec.id}`;
  $('model-options').hidden=spec.scenario!=='local-qwen';$('infer').checked=false;
  $('download-tool').href=course?`/api/tool?course=${encodeURIComponent(course)}`:`/api/tool?goal=${spec.scenario}`;
  await guidance();notice('任务已确定。先查看步骤，再到目标电脑手动采集报告。');
}
async function guidance(){
  if(!state.task)return;
  const epoch=state.epoch;const mode=$('mode').value;
  const data=await api('/api/plan',{task:state.task,mode,resources:(state.after||state.before)?.resources});
  if(epoch!==state.epoch||mode!==$('mode').value)return;
  const list=document.createElement('ol');list.className='steps';
  for(const step of data.steps){const item=document.createElement('li');const title=document.createElement('strong');title.textContent=step.title;const body=document.createElement('p');body.textContent=step.body;item.append(title,body);list.append(item);}
  $('guidance').replaceChildren(list);
  if(data.recommendation){const p=document.createElement('p');p.className='notice';p.textContent=data.recommendation;$('guidance').append(p);}
  const links=document.createElement('div');links.className='official-links';
  for(const link of data.links){const a=document.createElement('a');a.textContent=link.title;a.href=link.url;a.target='_blank';a.rel='noopener noreferrer';links.append(a);}
  $('guidance').append(links);
  $('prepared-hint').textContent={unsure:'先对照任务要求。选择准备情况只调整提示，不代表环境通过。',missing:'先查看官方下载和安装操作参考，按课程允许的版本自行安装。',installed:'确认课程解释器的完整路径，再生成只读采集命令。'}[$('prepared').value];
}
$('goal').addEventListener('change',()=>{clearTask();notice('目标已更换，请确认新的任务。');});
$('course-code').addEventListener('input',()=>{if(state.course)clearTask();});
$('goal-form').addEventListener('submit',e=>{e.preventDefault();action(e.submitter,()=>chooseTask(()=>api(`/api/goal?goal=${encodeURIComponent($('goal').value)}`)));});
$('course-form').addEventListener('submit',e=>{e.preventDefault();const code=$('course-code').value.trim().toUpperCase();action(e.submitter,()=>chooseTask(()=>api('/api/course/'+encodeURIComponent(code)),code));});
$('teacher-form').addEventListener('submit',e=>{
  e.preventDefault();action(e.submitter,async()=>{
    const result=await api('/api/course',{title:$('teacher-title').value,scenario:$('teacher-goal').value,python_min:$('python-min').value,python_max:$('python-max').value,requests_min:$('requests-min').value});
    $('published').textContent=`课程码 ${result.code} · 本机入口 ${location.origin}/?course=${result.code}`;
    await chooseTask(async()=>result.task,result.code);
  });
});
$('download-task').addEventListener('click',()=>save('task.json',state.task));
for(const id of ['mode','prepared'])$(id).addEventListener('change',()=>{clearAI();guidance().catch(e=>notice(e.message,true));});

const ps = value => '"'+value.replace(/[`"$\u2018-\u201f]/g,character=>'`'+character)+'"';
function requirePath(value,label){if(!/^[a-zA-Z]:[\\/]/.test(value)||/[\r\n\0]/.test(value))throw Error(label+'须填写完整的Windows路径');return value;}
$('make-command').addEventListener('click',()=>{
  try{
    if(!state.task)throw Error('请先确定任务');
    const root=requirePath($('tool-dir').value.trim(),'工具目录');const target=requirePath($('target').value.trim(),'课程解释器');
    const toolPython=$('tool-python').value.trim();if(toolPython)requirePath(toolPython,'工具Python');
    if(!toolPython&&!state.config?.portable_available)throw Error('当前工具包未配置独立运行时，请填写已有工具Python；工具Python不代表课程环境。');
    const stage=$('report-stage').value;const lines=["$ErrorActionPreference = 'Stop'",`$taskToolRoot = ${ps(root)}`,`$taskTarget = ${ps(target)}`,"if (!(Test-Path -LiteralPath $taskToolRoot -PathType Container)) { throw '工具目录不存在，请完整解压' }",'$taskSnapshot = Join-Path $taskToolRoot '+ps('task.json'),"if (!(Test-Path -LiteralPath $taskSnapshot -PathType Leaf)) { throw '缺少task.json，请完整解压本任务工具' }",`if ((Get-Content -LiteralPath $taskSnapshot -Raw -Encoding UTF8 | ConvertFrom-Json).id -ne ${ps(state.task.id)}) { throw '工具任务与网页任务不一致，请重新下载' }`,`$taskRunner = ${toolPython?ps(toolPython):'Join-Path $taskToolRoot '+ps('runtime\\python.exe')}`,"if (!(Test-Path -LiteralPath $taskRunner -PathType Leaf)) { throw '工具Python不存在' }",'Set-Location -LiteralPath $taskToolRoot'];
    let command=`& $taskRunner -B -m campuslab.collect --task $taskSnapshot --target $taskTarget --output (Join-Path $taskToolRoot ${ps('report-'+stage+'.json')})`;
    if(state.task.scenario==='local-qwen')command+=' --model-dir '+ps(requirePath($('model-dir').value.trim(),'模型目录'))+($('infer').checked?' --infer':'');
    lines.push(command,"if ($LASTEXITCODE -ne 0) { throw '采集未完成；请查看错误，不要把旧报告当作本次结果' }");
    $('command').textContent=lines.join('\n');notice('已生成命令。先检查路径和操作内容，再由本人到目标电脑运行。');
  }catch(e){$('command').textContent='';notice(e.message,true);}
});
for(const id of ['tool-dir','target','tool-python','model-dir','infer','report-stage'])$(id).addEventListener('input',()=>{$('command').textContent='';});

function render(a){
  state.analysis=a;$('results').replaceChildren();
  const identity=document.createElement('p');identity.textContent=`本次目标：${a.target.requested} · ${a.collected_at}`;$('results').append(identity);
  for(const c of a.checks){
    const row=document.createElement('div');row.className='check';const name=document.createElement('strong');name.textContent=names[c.id]||c.id;
    const status=document.createElement('strong');status.className='state-'+c.status;status.textContent=labels[c.status];
    const detail=document.createElement('p');detail.textContent=JSON.stringify(c.observed);row.append(name,status,detail);$('results').append(row);
  }
  $('export').disabled=false;$('diagnosis').hidden=false;
  $('ai-status').textContent=state.config?.ai.configured?'AI已配置。先检查发送目的地和脱敏内容，再主动发送一次请求。':'AI未配置，尚未发送任何请求。可继续使用完整规则结果与操作指导。';
  notice(a.passed?'本报告全部检查通过。':'仍有缺失、不符合或未知，请按指导处理后复检。');
}
async function importReport(which,file){
  if(!state.task)throw Error('请先选择任务');
  if(which==='after'&&!state.before)throw Error('请先导入有效初检报告A');
  const epoch=state.epoch, serial=++state.importEpoch, spec=state.task;
  clearAI();$('export-preview').hidden=true;$('save-export').hidden=true;
  if(which==='before'){
    Object.assign(state,{before:null,after:null,analysis:null});$('after-file').value='';$('after-file').disabled=true;
    $('results').replaceChildren();$('comparison').textContent='';$('export').disabled=true;$('diagnosis').hidden=true;
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
  await guidance();
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
function redactValue(value){
  if(typeof value==='string')return value.replace(/[A-Z]:[\\/]Users[\\/][^\\/\s]+/gi,'<个人用户目录>').replace(/\bsk-[A-Za-z0-9_-]{8,}/gi,'<密钥已删除>').replace(/\b(?:192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)\b/g,'<私网地址>');
  if(Array.isArray(value))return value.map(redactValue);
  if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,redactValue(v)]));
  return value;
}
$('export').addEventListener('click',()=>{
  $('export-preview').value=JSON.stringify(redactValue({share_only:true,note:'脱敏交流副本，不作为原始复检报告导入',task:state.task,report:state.after||state.before,result:state.analysis}),null,2);
  $('export-preview').hidden=false;$('save-export').hidden=false;notice('已做基础脱敏。请继续检查个人路径、邮箱和无关日志，再保存分享。');
});
$('save-export').addEventListener('click',()=>{try{JSON.parse($('export-preview').value);save('CampusLab-share.json',$('export-preview').value);}catch(e){notice('编辑后须保留有效JSON。',true);}});
api('/api/config').then(config=>{state.config=config;}).catch(e=>notice(e.message,true));
const courseFromURL=new URLSearchParams(location.search).get('course');if(courseFromURL){$('course-code').value=courseFromURL;$('course-form').requestSubmit();}
