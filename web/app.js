'use strict';
const $ = id => document.getElementById(id);
const state = {task:null, course:null, before:null, after:null, analysis:null, epoch:0, importEpoch:0, config:null, hardware:null, needEpoch:0,teacherEpoch:0};
const practiceState={practice:null,package:null,courses:null,epoch:0,session:0,submissionEpoch:0,reviewEpoch:0,submission:null,attempts:[],environment:{}};
const labels = {pass:'通过',missing:'缺失',mismatch:'不符合',unknown:'未知'};
const names = {os:'操作系统',node:'课程 Node.js',npm:'同一环境的 npm',python:'课程 Python',run:'固定程序运行','package:requests':'requests 依赖','package:torch':'PyTorch 依赖','package:transformers':'Transformers 依赖','model:weights':'固定模型权重','model:inference':'本地离线推理'};
const newCourses={'notebook-data':'Notebook · 真实内核数据分析','java-jdk':'Java/JDK · 编译运行','sqlite-basics':'SQLite · 只读SQL入门','ai-web-deepseek':'DeepSeek · 网页/客户端学习','deepseek-api':'DeepSeek API · 编程准备','dsh-desktop':'DeepSeek Harness · Windows桌面','dsh-cli':'DeepSeek Harness · npm/CLI/Web'};
Object.assign(names,{'package:jupyter_client':'Jupyter通信组件','package:ipykernel':'Python内核组件','package:numpy':'NumPy','package:pandas':'Pandas','notebook:spec':'所选内核定义','notebook:identity':'真实内核解释器','notebook:run':'固定数据计算','notebook:cleanup':'临时内核清理','java:java':'所选java','java:javac':'所选javac','java:identity':'同源JDK身份','java:compile':'固定源码编译','java:run':'编译产物运行','sqlite:runtime':'SQLite运行时','sqlite:database':'数据库文件身份','sqlite:readonly':'只读及文件未变','sqlite:query':'固定SELECT','api:dependency':'API编程依赖','api:request':'实际请求内容','api:protocol':'实际响应协议','api:exercise':'课程响应核对','web:workspace':'练习目录','web:self-record':'本人完成记录','web:artifact':'课程成果','web:login':'自动登录/连接证据','dsh:software':'DSH安装身份','dsh:node':'CLI所选Node','dsh:workspace':'专用工作区','dsh:model':'实际模型接入','dsh:permission':'本人实际授权','dsh:tools':'Agent工具回合','dsh:artifact':'固定任务产物'});
for(const select of [$('goal'),$('teacher-goal')]){
  for(const [label,keys] of [['数据与编程课程',['notebook-data','java-jdk','sqlite-basics']],['AI 使用与 Agent',['ai-web-deepseek','deepseek-api','dsh-desktop','dsh-cli']]]){
    const group=document.createElement('optgroup');group.label=label;
    for(const key of keys){const option=document.createElement('option');option.value=key;option.textContent=newCourses[key];group.append(option);}select.append(group);
  }
}

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
  $('results').replaceChildren();$('comparison').textContent='';$('before-file').value='';$('after-file').value='';$('report-files').value='';
  $('remediation').replaceChildren();
  $('lesson-panel').hidden=true;$('lesson-checks').replaceChildren();$('api-send').checked=false;
  $('prepare-script').textContent='';$('command').textContent='';
  $('after-file').disabled=true;$('export').disabled=true;$('export-preview').hidden=true;$('save-export').hidden=true;
  $('diagnosis').hidden=false;clearAI();progress();
}
function clearTask(){
  state.epoch++;clearReports();state.task=null;state.course=null;$('task-panel').hidden=true;$('empty-state').hidden=false;$('command').textContent='';$('remediation').replaceChildren();
  $('learning-preview-panel').hidden=true;$('learning-preview-text').value='';
}
async function chooseTask(loader,course=null){
  clearTask();const epoch=state.epoch; const spec=await loader();if(epoch!==state.epoch)return;
  state.task=spec;state.course=course;$('task-panel').hidden=false;$('empty-state').hidden=true;
  if(newCourses[spec.scenario])$('target').value='';
  $('task-title').textContent=spec.title;
  const node=spec.scenario==='node-basics', vm=spec.scenario==='vm-linux';
  const summaries={'notebook-data':'所选Python + 已有kernelspec → 真内核身份 → NumPy/Pandas固定计算',
    'java-jdk':'显式JDK目录 → 同源java/javac → 临时固定源码编译运行',
    'sqlite-basics':'SQLite单机入门 → 明确数据库文件 → 只读固定SELECT；不代表MySQL/PostgreSQL',
    'ai-web-deepseek':'本人课程提问与结果核对 → 学习记录；登录/连接仍无自动检测证据',
    'deepseek-api':`DeepSeek · ${spec.api?.model} · ${spec.api?.endpoint} · 单次同意后本人终端调用`,
    'dsh-desktop':'所选Windows桌面程序 → 专用工作区/权限 → 本人真实DSH任务证据；桌面自带运行时',
    'dsh-cli':'所选Node>=24.9.0 + DSH固定包 → 模型/工作区 → 本人真实Agent任务证据'};
  $('task-summary').textContent=summaries[spec.scenario]||(vm?'Windows宿主 → 所选虚拟化软件 → 具体实例 → Linux来宾固定验证；各层分别核对':node?`Windows · Node.js ${spec.node.min} 至 ${spec.node.max_exclusive} · npm ${spec.npm.min} 至 ${spec.npm.max_exclusive}（均不包含上限）`:`Windows · Python ${spec.python.min} 至 ${spec.python.max_exclusive}（不包含上限） · ${Object.entries(spec.packages).map(([k,v])=>`${k} ≥ ${v}`).join('，')}`+(spec.scenario==='pytorch-gpu'?' · 必须实际GPU运算':''));
  $('task-source').textContent=spec.source;
  $('target-label').textContent=vm?'所选虚拟化软件完整路径（VBoxManage.exe 或 vmrun.exe）':node?'课程 Node.js 完整路径（明确选择 node.exe）':'课程解释器完整路径';
  $('target').placeholder=vm?'例如 C:\\Program Files (x86)\\VMware\\VMware Workstation\\vmrun.exe':node?'例如 C:\\Program Files\\nodejs\\node.exe':'例如 C:\\CoursePython\\python.exe';
  const targets={'java-jdk':['课程JDK根目录','例如 C:\\Program Files\\Zulu\\zulu-21'],
    'sqlite-basics':['SQLite演示数据库文件完整路径','例如 D:\\CoursePractice\\demo.sqlite'],
    'ai-web-deepseek':['本人练习资料目录','例如 D:\\CoursePractice'],
    'dsh-desktop':['已安装DSH Windows桌面程序完整路径','例如 C:\\DSH\\DeepSeek Harness.exe'],
    'dsh-cli':['明确选择课程Node完整路径','例如 D:\\Program Files\\nodejs\\node.exe']};
  if(targets[spec.scenario])[$('target-label').textContent,$('target').placeholder]=targets[spec.scenario];
  $('target-help').textContent=node?'npm 使用所选 node.exe 同目录的 node_modules/npm/bin/npm-cli.js，并由该 node.exe 执行；PATH 中其他 npm 不作证据。':'py 不可用时，从安装目录或编辑器的解释器设置寻找 python.exe。';
  if(newCourses[spec.scenario])$('target-help').textContent='只采集本人明确选择的目标。工具运行时与课程环境分别记录；不自动安装、登录或启动DSH。';
  $('task-id').textContent=`固定任务摘要 ${spec.id}`;
  $('model-options').hidden=spec.scenario!=='local-qwen';$('infer').checked=false;
  $('torch-options').hidden=spec.scenario!=='pytorch-gpu';$('gpu-run').checked=false;$('vm-options').hidden=!vm;
  for(const [id,visible] of [['notebook-options',spec.scenario==='notebook-data'],['sqlite-options',spec.scenario==='sqlite-basics'],['web-learning-options',spec.scenario==='ai-web-deepseek'],['api-learning-options',spec.scenario==='deepseek-api'],['dsh-options',spec.scenario.startsWith('dsh-')]])$(id).hidden=!visible;
  $('dsh-package-options').hidden=spec.scenario!=='dsh-cli';
  $('simple-collector').hidden=!['python-basics','notebook-data'].includes(spec.scenario)||!state.config?.portable_available;
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
  const fixed=['pytorch-cpu','pytorch-gpu','vm-linux',...Object.keys(newCourses)].includes($('teacher-goal').value);
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
    if(state.task.scenario==='notebook-data')command+=' --kernel-spec '+ps(requirePath($('kernel-spec').value.trim(),'所选kernel.json'));
    if(state.task.scenario==='ai-web-deepseek'&&$('learning-record').value.trim())command+=' --learning-record '+ps(requirePath($('learning-record').value.trim(),'本人学习记录'));
    if(state.task.scenario==='deepseek-api'){
      if($('api-preview-path').value.trim())command+=' --api-preview '+ps(requirePath($('api-preview-path').value.trim(),'请求预览JSON'));
      if($('api-send').checked)command+=' --api-send';
    }
    if(state.task.scenario.startsWith('dsh-')){
      if(state.task.scenario==='dsh-cli')command+=' --package-json '+ps(requirePath($('dsh-package').value.trim(),'DSH package.json'));
      command+=' --workspace '+ps(requirePath($('dsh-workspace').value.trim(),'专用练习目录'));
      for(const [id,flag] of [['dsh-provider','--provider'],['dsh-model','--model']]){
        const value=$(id).value.trim();if(!/^[A-Za-z0-9][A-Za-z0-9._:/-]{0,99}$/.test(value)||value.toLowerCase().startsWith('sk-'))throw Error('提供方/模型只填公开标识，不填密钥');command+=' '+flag+' '+ps(value);
      }
      if($('dsh-evidence').value.trim())command+=' --agent-evidence '+ps(requirePath($('dsh-evidence').value.trim(),'必要工具摘要'));
    }
    lines.push(command,"if ($LASTEXITCODE -ne 0) { throw '采集未完成；请查看错误，不要把旧报告当作本次结果' }");
    $('command').textContent=lines.join('\n');notice('已生成命令。先检查路径和操作内容，再由本人到目标电脑运行。');
  }catch(e){$('command').textContent='';notice(e.message,true);}
});
for(const id of ['tool-dir','target','tool-python','model-dir','infer','report-stage','gpu-run','vm-id','guest-path'])$(id).addEventListener('input',()=>{$('command').textContent='';if(['target','model-dir','vm-id'].includes(id)){invalidatePracticeEnvironment();clearReports();}});
for(const id of ['kernel-spec','dsh-package','dsh-workspace','dsh-provider','dsh-model','dsh-evidence','learning-record','api-preview-path','learning-preview-text'])$(id).addEventListener('input',()=>{invalidatePracticeEnvironment();clearReports();});
$('api-send').addEventListener('change',()=>{$('command').textContent='';});

function render(a){
  state.analysis=a;$('results').replaceChildren();
  const identity=document.createElement('p');identity.textContent=`本次目标：${a.target.requested} · ${a.collected_at}`;$('results').append(identity);
  const next=document.createElement('p');next.className='result-summary';const counts=Object.fromEntries(Object.keys(labels).map(key=>[key,a.checks.filter(x=>x.status===key).length]));
  next.textContent=`通过 ${counts.pass} · 缺失 ${counts.missing} · 不符合 ${counts.mismatch} · 未知 ${counts.unknown}。`+(a.passed?(state.after?'核对同目标复检结论。':'初检已通过，保留原件后采集较晚的B。'):'查看“按差异处理”的下一步，手动处理后复检。');$('results').append(next);
  if(a.learning_completed){const p=document.createElement('p');p.className='notice';p.textContent='本人学习记录与固定数字成果已核对；登录/远端连接仍为未知。';$('results').append(p);}
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
function validateSelectedReport(spec,report){
  if(!report||typeof report!=='object'||report.share_only)throw Error('请选择原始采集报告；脱敏分享副本不能导入');
  const samePath=(a,b)=>typeof a==='string'&&typeof b==='string'&&a.replaceAll('/','\\').replace(/\\+$/,'').toLowerCase()===b.replaceAll('/','\\').replace(/\\+$/,'').toLowerCase();
  if($('target').value.trim()&&!samePath($('target').value.trim(),report.target?.requested))throw Error('报告与当前选择的目标不同，请重新初检');
  const fields=spec.scenario==='notebook-data'?[['kernel-spec',report.facts?.kernel?.spec_path]]:spec.scenario.startsWith('dsh-')?[['dsh-workspace',report.facts?.workspace?.requested],...(spec.scenario==='dsh-cli'?[['dsh-package',report.facts?.installation?.package_json]]:[])]:[];
  for(const [id,value] of fields)if($(id).value.trim()&&!samePath($(id).value.trim(),value))throw Error('报告与当前所选组件不同，请重新初检');
  if(spec.scenario.startsWith('dsh-'))for(const id of ['provider','model'])if($('dsh-'+id).value.trim()&&$('dsh-'+id).value.trim()!==report.facts?.model?.[id])throw Error('报告与当前提供方/模型不同，请重新初检');
}
async function importReport(which,file){
  if(!state.task)throw Error('请先选择任务');
  if(which==='after'&&!state.before)throw Error('请先导入有效初检报告A');
  const epoch=state.epoch, serial=++state.importEpoch, spec=state.task;
  invalidatePracticeEnvironment();
  clearAI();$('export-preview').hidden=true;$('save-export').hidden=true;$('remediation').replaceChildren();
  $('lesson-panel').hidden=true;$('lesson-checks').replaceChildren();$('command').textContent='';$('api-send').checked=false;
  if(which==='before'){
    Object.assign(state,{before:null,after:null,analysis:null});$('after-file').value='';$('after-file').disabled=true;
    $('results').replaceChildren();$('comparison').textContent='';$('export').disabled=true;$('diagnosis').hidden=false;
  }else{
    state.after=null;$('comparison').textContent='';
    if(state.before){const baseline=await api('/api/analyze',{task:spec,report:state.before});if(epoch!==state.epoch||serial!==state.importEpoch)return;render(baseline);}
  }
  if(!file||file.size>200000)throw Error('请选择小于200KB的JSON报告');
  const report=JSON.parse(await file.text());
  validateSelectedReport(spec,report);
  const analysis=await api('/api/analyze',{task:spec,report});
  let comparison=null;if(which==='after')comparison=await api('/api/compare',{task:spec,before:state.before,after:report});
  if(epoch!==state.epoch||serial!==state.importEpoch)return;
  state[which]=report;render(analysis);$('after-file').disabled=!state.before;
  if(comparison)$('comparison').textContent=({'stable-pass':'同一目标稳定复检通过；两次均通过。',repaired:'同一目标从存在缺失或不符合改善为通过。',verified:'同一目标补齐实际运行证据后通过；不记为故障修复。',incomplete:'同一目标复检仍未全部通过。'})[comparison.outcome];
  rememberPracticeEnvironment();progress();await guidance();await lesson();
}
for(const [id,which] of [['before-file','before'],['after-file','after']])$(id).addEventListener('change',async e=>{try{await importReport(which,e.target.files[0]);}catch(error){e.target.value='';notice(error.message,true);}});
$('report-files').addEventListener('change',e=>action(null,async()=>{
  const files=[...e.target.files];
  if(files.length===1){await importReport('before',files[0]);return;}
  invalidatePracticeEnvironment();clearReports();
  if(!state.task)throw Error('请先选择任务');
  if(files.length!==2||files.some(f=>f.size>200000))throw Error('请一次选择1—2份小于200KB的原始JSON报告');
  const epoch=state.epoch,serial=++state.importEpoch,spec=state.task;
  const reports=await Promise.all(files.map(async file=>JSON.parse(await file.text())));
  for(const report of reports)validateSelectedReport(spec,report);
  const times=reports.map(r=>Date.parse(r.collected_at));
  if(times.some(t=>!Number.isFinite(t))||times[0]===times[1])throw Error('报告时间无法确定先后，请核对原件并分别导入；相同时间不能作为复检');
  const [before,after]=times[0]<times[1]?reports:reports.reverse();
  await api('/api/analyze',{task:spec,report:before});
  const analysis=await api('/api/analyze',{task:spec,report:after});
  const comparison=await api('/api/compare',{task:spec,before,after});
  if(epoch!==state.epoch||serial!==state.importEpoch)return;
  Object.assign(state,{before,after});render(analysis);$('after-file').disabled=false;
  $('comparison').textContent=({'stable-pass':'已按实际时间导入：同一目标稳定复检通过；两次均通过。',repaired:'已按实际时间导入：同一目标从缺失或不符合改善为通过。',verified:'已按实际时间导入：同一目标补齐运行证据后通过。',incomplete:'已按实际时间导入：同一目标复检仍未全部通过。'})[comparison.outcome];
  rememberPracticeEnvironment();progress();await guidance();await lesson();
}));

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
$('save-export').addEventListener('click',()=>{try{JSON.parse($('export-preview').value);save('Kehang-share.json',$('export-preview').value);}catch(e){notice('编辑后须保留有效JSON。',true);}});
function progress(){
  $('progress-evidence').textContent=state.before?'② 已有初检事实':'② 准备并采集';
  $('progress-recheck').textContent=state.after?(state.analysis?.passed?'③ 复检全部通过':'③ 复检仍有差异'):'③ 等待同目标复检';
}
/* Educates clickable-action.html / examiner-execute-test.html adaptation.
 * Copyright The Educates Authors. Apache-2.0; docs/third-party/educates/NOTICE.
 * Preserves header/title/body action structure; fixed reports replace remote examiner dispatch.
 */
async function lesson(){
  if(!state.before)return;
  const epoch=state.epoch,serial=state.importEpoch;
  const items=await api('/api/lesson',{task:state.task,report:state.after||state.before});
  if(epoch!==state.epoch||serial!==state.importEpoch)return;
  const box=$('lesson-checks');box.replaceChildren();
  for(const item of items){
    const card=document.createElement('section');card.className='clickable-action';card.dataset.handler=item.action;
    const header=document.createElement('div');header.className='clickable-action__header';
    const title=document.createElement('strong');title.className='clickable-action__title';title.textContent=item.title;
    const status=document.createElement('span');status.className='state-'+item.status;status.textContent=labels[item.status];header.append(title,status);
    const body=document.createElement('p');body.className='clickable-action__body';body.textContent=item.description;
    card.append(header,body);box.append(card);
  }
  $('lesson-panel').hidden=false;
}
$('lesson-retry').addEventListener('click',()=>{
  if(!state.before)return;
  $('report-stage').value='B';$('command').textContent='';$('command-panel').open=true;
  $('make-command').focus();notice('保持同一任务与组件，手动采集较晚B后导入。检查状态来自新报告。');
  const button=$('lesson-retry');button.disabled=true;setTimeout(()=>{button.disabled=false;},3000);
});
$('learning-preview').addEventListener('click',e=>action(e.target,async()=>{
  const epoch=state.epoch;clearReports();const value=await api('/api/learning-preview',{task:state.task});
  if(epoch!==state.epoch)return;
  $('learning-preview-text').value=JSON.stringify(value,null,2);$('learning-preview-panel').hidden=false;
}));
$('save-learning-preview').addEventListener('click',()=>{
  try{const value=JSON.parse($('learning-preview-text').value);save('api-preview.json',value);notice('将文件保存到工具目录，并在请求预览路径中填写；密钥不写入该文件。');}
  catch(e){notice('请求预览须保留有效JSON。',true);}
});
function preparationCommand(module,argument,value){
  if(!state.task)throw Error('请先确定任务');
  const root=requirePath($('tool-dir').value.trim(),'工具目录'),tool=$('tool-python').value.trim();
  if(tool)requirePath(tool,'工具Python');if(!tool&&!state.config?.portable_available)throw Error('请填写已有工具Python');
  const runner=tool||root+'\\runtime\\python.exe';
  return ["$ErrorActionPreference = 'Stop'",'Set-Location -LiteralPath '+ps(root),
    '& '+ps(runner)+' -B -m '+module+' '+argument+' '+ps(value)+(module==='campuslab.dsh_course'?' --task '+ps(root+'\\task.json'):''),
    "if ($LASTEXITCODE -ne 0) { throw '准备未完成，已有文件不覆盖' }"].join('\n');
}
$('prepare-sqlite').addEventListener('click',()=>{try{$('prepare-script').textContent=preparationCommand('campuslab.sqlite_course','--prepare-demo',requirePath($('target').value.trim(),'新演示数据库'));}catch(e){notice(e.message,true);}});
$('prepare-dsh').addEventListener('click',()=>{try{$('prepare-script').textContent=preparationCommand('campuslab.dsh_course','--prepare-workspace',requirePath($('dsh-workspace').value.trim(),'新练习目录'));}catch(e){notice(e.message,true);}});
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
$('export-course').addEventListener('click',e=>action(e.target,async()=>save('Kehang-course.json',await api('/api/package',{task:state.task}))));
$('export-guide').addEventListener('click',e=>action(e.target,async()=>{
  const r=await fetch('/api/guide',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:state.task})});
  if(!r.ok)throw Error('指导导出失败');save('Kehang-guide.html',await r.text(),'text/html');
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

function practiceEnvironmentKey(){return {'notebook-data':'notebook','sqlite-basics':'sqlite'}[state.task?.scenario];}
function invalidatePracticeEnvironment(){
  const key=practiceEnvironmentKey();if(key){delete practiceState.environment[key];renderPracticeStates();}
}
function rememberPracticeEnvironment(){
  const key=practiceEnvironmentKey(),spec=practiceState.practice;
  if(key&&spec&&state.task.id===spec.component_task_ids[key]&&state.before){
    practiceState.environment[key]={task_id:state.task.id,before:state.before,after:state.after,analysis:state.analysis};
    renderPracticeStates();
  }
}
const practiceLabels={missing:'缺少成果',invalid:'格式无效',obsolete:'任务或资料不匹配',mismatch:'结果不符合',pass:'成果符合要求'};
function boundedPracticeSubmission(value,spec){
  const exact=(object,keys)=>object&&typeof object==='object'&&!Array.isArray(object)&&Object.keys(object).sort().join('|')===[...keys].sort().join('|');
  if(!exact(value,['schema','kind','practice_id','material_version','dataset_sha256','component_task_ids','notebook','sqlite']))return null;
  if(value.schema!==1||value.kind!=='kehang-practice-result'||value.practice_id!==spec.id||value.material_version!==spec.material_version||value.dataset_sha256!==spec.dataset_sha256)return null;
  if(!exact(value.component_task_ids,['notebook','sqlite'])||Object.entries(spec.component_task_ids).some(([key,id])=>value.component_task_ids[key]!==id))return null;
  const nb=value.notebook,sql=value.sqlite;
  if(nb!==null&&(!exact(nb,['rows','array_sum','group_totals'])||!Number.isSafeInteger(nb.rows)||!Number.isSafeInteger(nb.array_sum)||!exact(nb.group_totals,['A','B'])||Object.values(nb.group_totals).some(n=>!Number.isSafeInteger(n))))return null;
  if(sql!==null&&(!Array.isArray(sql)||sql.length>5||sql.some(row=>!Array.isArray(row)||row.length!==3||!['A','B'].includes(row[0])||!Number.isSafeInteger(row[1])||!Number.isSafeInteger(row[2]))))return null;
  return value;
}
function renderPracticeStates(){
  const parts=['notebook','sqlite'].map(key=>{
    const item=practiceState.environment[key],label=key==='notebook'?'Notebook':'SQLite';
    return label+'：'+(!item?'无当前报告':item.after&&item.analysis.passed?'同目标复检通过':item.analysis.passed?'仅初检通过':'仍有缺失、不符合或未知');
  });
  $('practice-environment').textContent='环境固定探针 · '+parts.join('；');
  $('practice-reading-status').textContent='阅读步骤 · '+($('practice-read').checked?'本人已确认阅读':'本人尚未确认');
  const latest=practiceState.attempts.filter(a=>a.practice_id===practiceState.practice?.id&&a.session===practiceState.session).at(-1);
  $('practice-artifact-status').textContent='实训成果 · '+(latest?practiceLabels[latest.result.status]||'未通过':'尚未提交');
  $('practice-completion').disabled=!practiceState.practice||!latest;
}
function renderPractice(value){
  practiceState.session++;
  practiceState.practice=value.practice;practiceState.package=value.package;practiceState.courses=value.courses||null;
  practiceState.environment={};practiceState.reviewEpoch++;$('practice-teacher-review').replaceChildren();
  practiceState.submission=null;practiceState.submissionEpoch++;$('practice-submission').value='';$('practice-read').checked=false;
  $('practice-result').textContent='';
  const spec=value.practice;
  $('practice-heading').textContent=spec.title;
  $('practice-description').textContent='Notebook 与 SQLite 使用同一份演示CSV。下载资料、跟做并提交数据成果；两个组件的环境证据分别保留。';
  const box=$('practice-steps');box.replaceChildren();
  for(const [title,items] of [['学习目标',spec.objectives],['前置条件',spec.prerequisites]]){
    const h=document.createElement('h3');h.textContent=title;const list=document.createElement('ul');
    for(const text of items){const li=document.createElement('li');li.textContent=text;list.append(li);}box.append(h,list);
  }
  const steps=document.createElement('ol');steps.className='practice-step-list';
  for(const step of spec.steps){const li=document.createElement('li'),h=document.createElement('h3');h.textContent=step.title;li.append(h);
    for(const [prefix,text] of [['操作：',step.body],['应看到：',step.expected],['遇到问题：',step.recovery]]){const p=document.createElement('p');p.textContent=prefix+text;li.append(p);}steps.append(li);
  }
  const scope=document.createElement('p');scope.className='muted';scope.textContent=spec.scope;box.append(steps,scope);
  for(const id of ['practice-notebook','practice-sqlite','practice-export-package','practice-check'])$(id).disabled=false;
  renderPracticeStates();
}
$('practice-read').addEventListener('change',renderPracticeStates);
for(const [id,key,scenario] of [['practice-notebook','notebook','notebook-data'],['practice-sqlite','sqlite','sqlite-basics']]){
  $(id).addEventListener('click',e=>action(e.target,async()=>{
    if(!practiceState.practice)throw Error('请先导入当前实训资料');
    const course=practiceState.courses?.[key];
    $('goal').value=scenario;
    await chooseTask(()=>course?Promise.resolve(course.task):api('/api/goal?goal='+scenario),course?.code||null);
    $('task-panel').scrollIntoView({block:'start'});
  }));
}
$('practice-publish').addEventListener('click',e=>action(e.target,async()=>{
  const epoch=++practiceState.epoch;
  const value=await api('/api/practice/publish',{});
  if(epoch!==practiceState.epoch)return;
  renderPractice(value);
  $('practice-published').textContent='本机已发布 · Notebook课程码 '+value.courses.notebook.code+'；SQLite课程码 '+value.courses.sqlite.code+'。请导出实训课程包并携带完整资料。';
}));
$('practice-export-package').addEventListener('click',()=>{
  if(practiceState.package)save('practice-course.json',practiceState.package);
});
$('practice-package').addEventListener('change',e=>action(null,async()=>{
  const epoch=++practiceState.epoch,file=e.target.files[0];
  practiceState.practice=null;practiceState.package=null;practiceState.courses=null;practiceState.environment={};practiceState.submission=null;practiceState.submissionEpoch++;
  $('practice-read').checked=false;$('practice-submission').value='';$('practice-result').textContent='';$('practice-published').textContent='尚未取得有效实训包';
  for(const id of ['practice-notebook','practice-sqlite','practice-export-package','practice-check','practice-completion'])$(id).disabled=true;
  $('practice-description').textContent='正在核对资料包。旧实训结果已隔离；原提交记录可在本次会话中保留。';renderPracticeStates();
  if(!file||file.size>100000)throw Error('实训课程包须小于100KB');
  const value=await api('/api/practice/import',{package:JSON.parse(await file.text())});
  if(epoch!==practiceState.epoch)return;
  renderPractice(value);$('practice-published').textContent='当前固定资料已导入本机。请通过可信渠道向教师核对实训和两项任务摘要。';
}));
$('practice-submission').addEventListener('change',()=>{
  practiceState.submissionEpoch++;practiceState.submission=null;$('practice-result').textContent='已选择新文件，等待本次核验。';
});
$('practice-check').addEventListener('click',e=>action(e.target,async()=>{
  const spec=practiceState.practice;if(!spec)throw Error('请先取得有效实训资料');
  const epoch=practiceState.epoch,serial=++practiceState.submissionEpoch,file=$('practice-submission').files[0];
  let submission=null,fileError=null;
  let sourceSha256=null;
  if(file){
    if(file.size>200000)throw Error('成果JSON须小于200KB，请选择资料中的限定数据结果');
    const raw=await file.arrayBuffer();sourceSha256=[...new Uint8Array(await crypto.subtle.digest('SHA-256',raw))].map(n=>n.toString(16).padStart(2,'0')).join('');
    try{submission=JSON.parse(new TextDecoder().decode(raw).replace(/^\uFEFF/,''));}catch(error){fileError='不是有效JSON';submission={invalid_json:true};}
  }
  if(epoch!==practiceState.epoch||serial!==practiceState.submissionEpoch)return;
  const result=await api('/api/practice/check',{practice:spec,submission});
  if(epoch!==practiceState.epoch||serial!==practiceState.submissionEpoch)return;
  const retained=boundedPracticeSubmission(submission,spec);
  const attempt={practice_id:spec.id,session:practiceState.session,source_sha256:sourceSha256,file_error:fileError,submission:retained,
    submission_omitted:submission!==null&&retained===null,result};
  practiceState.attempts.push(attempt);practiceState.submission=submission;
  const item=document.createElement('li');item.textContent='第'+practiceState.session+'轮 · '+(result.checked_at||new Date().toISOString())+' · '+(practiceLabels[result.status]||result.status)+' · '+result.next_step;
  $('practice-attempts').append(item);$('practice-attempts-panel').hidden=false;
  $('practice-result').textContent=(practiceLabels[result.status]||result.status)+'。'+result.next_step;
  $('practice-result').className=result.passed?'state-pass':'state-mismatch';renderPracticeStates();
}));
$('practice-completion').addEventListener('click',()=>{
  if(!practiceState.practice)return;
  save('Kehang-practice-completion.json',{schema:1,kind:'kehang-practice-completion',exported_at:new Date().toISOString(),practice:practiceState.practice,current_session:practiceState.session,
    reading_self_declared:$('practice-read').checked,environment:practiceState.environment,
    attempts:practiceState.attempts.filter(a=>a.practice_id===practiceState.practice.id),
    scope:'本次会话记录；教师须重新核验限定成果，不信任已保存的passed结论。无效/旧资料原内容仅保留摘要，需原件才能重核。环境探针、阅读声明和成果核验各自独立。不证明本人完成操作、学习掌握或作品原创。含本机原始报告路径，分享前请检查。'});
});
$('practice-completion-file').addEventListener('change',e=>action(null,async()=>{
  const epoch=practiceState.epoch,serial=++practiceState.reviewEpoch,spec=practiceState.practice,box=$('practice-teacher-review');box.replaceChildren();
  if(!spec)throw Error('请先导入教师当前实训资料');
  const file=e.target.files[0];if(!file||file.size>2000000)throw Error('请选择小于2MB的完成物JSON');
  const completion=JSON.parse(await file.text());
  if(completion.kind!=='kehang-practice-completion'||completion.schema!==1||!Array.isArray(completion.attempts)||completion.attempts.length>100||completion.practice?.id!==spec.id)throw Error('完成物格式或实训身份不匹配，请核对当前资料与学生原件');
  const verified=[];
  for(const attempt of completion.attempts){
    if(epoch!==practiceState.epoch||serial!==practiceState.reviewEpoch)return;
    if(!attempt||attempt.practice_id!==spec.id)throw Error('完成物包含其他任务的提交，请核对原件');
    if(attempt.submission_omitted){verified.push('原内容未保留，不能重新核验；请提供原始成果JSON。');continue;}
    const safe=boundedPracticeSubmission(attempt.submission,spec);
    if(attempt.submission!==null&&!safe)throw Error('完成物含限定格式之外的数据，请让学生提交原始限定成果');
    const result=await api('/api/practice/check',{practice:spec,submission:safe});
    verified.push('本次重新核验：'+(practiceLabels[result.status]||result.status)+'。'+result.next_step);
  }
  if(epoch!==practiceState.epoch||serial!==practiceState.reviewEpoch)return;
  const intro=document.createElement('p');intro.textContent='已重新核验 '+verified.length+' 条历史记录中的可用成果。环境报告与阅读声明需分别核对，不作为数值成果通过依据。';box.append(intro);
  const list=document.createElement('ol');for(const text of verified){const li=document.createElement('li');li.textContent=text;list.append(li);}box.append(list);
}));
api('/api/practice').then(value=>{if(practiceState.epoch===0)renderPractice(value);}).catch(e=>{if(practiceState.epoch===0){$('practice-description').textContent='实训资料读取失败，请重新打开本页。';notice(e.message,true);}});
Object.assign(names,{'torch:import':'PyTorch 实际导入','torch:cpu':'固定 CPU 张量','torch:cuda-build':'框架 CUDA 构建','torch:gpu-available':'GPU 可用性','torch:gpu-identity':'GPU 设备身份','torch:gpu-run':'实际 GPU 张量','host:virtualization':'宿主虚拟化条件','vm:software':'所选虚拟化软件','vm:instance':'所选虚拟机实例','vm:running':'实例运行证据','guest:identity':'来宾身份','guest:linux':'Linux 系统证据','guest:run':'来宾固定程序'});
api('/api/catalog').then(catalog=>{for(const item of catalog){const d=document.createElement('div');d.className='catalog-item';const h=document.createElement('h3');h.textContent=item.label;const p=document.createElement('p');p.textContent=item.status+' · '+item.extension;d.append(h,p);if(item.source.startsWith('https://')){const a=document.createElement('a');a.textContent='课程来源';a.href=item.source;a.target='_blank';a.rel='noopener noreferrer';d.append(a);}$('catalog').append(d);}}).catch(e=>notice(e.message,true));
api('/api/config').then(config=>{state.config=config;if(state.task)$('simple-collector').hidden=!['python-basics','notebook-data'].includes(state.task.scenario)||!config.portable_available;}).catch(e=>notice(e.message,true));
const courseFromURL=new URLSearchParams(location.search).get('course');if(courseFromURL){$('course-code').value=courseFromURL;$('course-form').requestSubmit();}
