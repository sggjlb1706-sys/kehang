'use strict';
const $ = id => document.getElementById(id);
const state = {task:null, course:null, before:null, after:null, analysis:null, epoch:0, importEpoch:0, config:null, hardware:null, needEpoch:0,teacherEpoch:0};
const practiceState={practice:null,package:null,courses:null,epoch:0,session:0,submissionEpoch:0,reviewEpoch:0,submission:null,attempts:[],environment:{}};
const guided={route:'home',courseStep:0,practiceStep:0,courseVisited:0,practiceVisited:0,fromPractice:false,navigationEpoch:0,manualCollectorChosen:false};
const localState={epoch:0,job:null,running:false,items:[],selected:null,limited:false};
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
function notice(text,error=false){$('notice').textContent=text;$('notice').hidden=false;$('notice').classList.toggle('error',error);if(error)$('notice').scrollIntoView({block:'nearest'});}
async function action(button,fn){const navigationEpoch=guided.navigationEpoch;if(button)button.disabled=true;try{await fn();}catch(e){if(navigationEpoch===guided.navigationEpoch)notice(e.message,true);}finally{if(button)button.disabled=false;}}
function save(name,obj,type='application/json'){
  const text=typeof obj==='string'?obj:JSON.stringify(obj,null,2);
  const u=URL.createObjectURL(new Blob([text],{type}));
  const a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);
}
function clearAI(){
  $('ai-preview-panel').hidden=true;$('ai-consent').checked=false;$('send-ai').disabled=true;
  $('ai-preview').value='';$('ai-output').textContent='';
}
function clearReports(keepLocal=false){
  if(!keepLocal)resetLocal();
  state.importEpoch++; Object.assign(state,{before:null,after:null,analysis:null});
  $('report-stage').value='A';
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
  guided.courseStep=0;guided.courseVisited=0;guided.manualCollectorChosen=false;renderGuide();
  $('tool-dir').value='';updateReportGuide();
  for(const id of ['target','kernel-spec','model-dir','vm-id','guest-path','dsh-package','dsh-workspace','dsh-evidence','api-preview-path','learning-record'])$(id).value='';
}
async function chooseTask(loader,course=null){
  const navigationEpoch=guided.navigationEpoch;
  clearTask();const epoch=state.epoch; const spec=await loader();if(epoch!==state.epoch)return;
  state.task=spec;state.course=course;$('task-panel').hidden=false;$('empty-state').hidden=true;
  if(newCourses[spec.scenario])$('target').value='';
  $('task-title').textContent=spec.title;
  const node=spec.scenario==='node-basics', vm=spec.scenario==='vm-linux';
  $('node-target-guide').hidden=!node;
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
  syncCollector();
  $('download-tool').href=course?`/api/tool?course=${encodeURIComponent(course)}`:`/api/tool?goal=${spec.scenario}`;
  await guidance();await routes();progress();notice('任务已确定。先查看步骤，再到目标电脑手动采集报告。');
  if(epoch===state.epoch&&navigationEpoch===guided.navigationEpoch){
    guided.courseVisited=1;showRoute('course',1);
    syncCollector();
    return true;
  }
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
  renderPreparation(data);
  if(data.preparation){const d=document.createElement('details'),s=document.createElement('summary');s.textContent='从未准备到固定本地推理';d.append(s);for(const text of data.preparation){const p=document.createElement('p');p.textContent=text;d.append(p);}$('guidance').append(d);}
  $('remediation').replaceChildren();
  if(data.remediation?.length){const h=document.createElement('h3');h.textContent='按差异处理';$('remediation').append(h);}
  for(const step of data.remediation||[]){const d=document.createElement('div');d.className='remedy';const h=document.createElement('h3');h.textContent=step.title;const p=document.createElement('p');p.textContent=step.body;const v=document.createElement('p');v.className='muted';v.textContent=step.verify;d.append(h,p,v);$('remediation').append(d);}
  $('prepared-hint').textContent={unsure:'先对照任务要求。选择准备情况只调整提示，不代表环境通过。',missing:'先查看官方下载和安装操作参考，按课程允许的版本自行安装。',installed:state.task.scenario==='node-basics'?'确认所选 node.exe 的完整路径，再生成只读采集命令。':'确认课程解释器的完整路径，再生成只读采集命令。'}[$('prepared').value];
}
$('goal').addEventListener('change',()=>{guided.fromPractice=false;clearTask();notice('目标已更换，请确认新的任务。');});
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
    const epoch=state.epoch,serial=state.teacherEpoch,navigationEpoch=guided.navigationEpoch;
    const result=await api('/api/course',{title:$('teacher-title').value,scenario:$('teacher-goal').value,python_min:$('python-min').value,python_max:$('python-max').value,requests_min:$('requests-min').value});
    if(epoch!==state.epoch||serial!==state.teacherEpoch||navigationEpoch!==guided.navigationEpoch)return;
    $('published').textContent=`课程码 ${result.code} · 本机入口 ${location.origin}/?course=${result.code}`;
    const navigated=await chooseTask(async()=>result.task,result.code);
    if(navigated&&state.course===result.code)showRoute('teacher');
  });
});
$('teacher-form').addEventListener('input',()=>{state.teacherEpoch++;});
$('download-task').addEventListener('click',()=>save('task.json',state.task));
for(const id of ['mode','prepared'])$(id).addEventListener('change',()=>{clearAI();guidance().catch(e=>notice(e.message,true));});

const ps = value => '"'+value.replace(/[`"$\u2018-\u201f]/g,character=>'`'+character)+'"';
function requirePath(value,label){if(!/^[a-zA-Z]:[\\/]/.test(value)||/[\r\n\0]/.test(value))throw Error(label+'须填写完整的Windows路径');return value;}
function requireNodeFile(value){
  if(value.startsWith('"')&&value.endsWith('"'))value=value.slice(1,-1);
  const path=requirePath(value,'课程 Node.js');
  if(!/\.exe$/i.test(path))throw Error('请选择 node.exe 程序文件，不是开始菜单的 Node.js 文件夹或快捷方式。按路径输入框下方的图示查找。');
  return path;
}
$('make-command').addEventListener('click',()=>{
  try{
    if(!state.task)throw Error('请先确定任务');
    const root=requirePath($('tool-dir').value.trim(),'工具目录');const target=state.task.scenario==='node-basics'?requireNodeFile($('target').value.trim()):requirePath($('target').value.trim(),'课程解释器');
    if(state.task.scenario==='node-basics')$('target').value=target;
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
    lines.push(`Write-Host ('报告已保存：' + (Join-Path $taskToolRoot ${ps('report-'+stage+'.json')}))`,"Write-Host '回到课航，按图选择这份报告。'");
    $('command').textContent=lines.join('\n');notice('已生成命令。先检查路径和操作内容，再由本人到目标电脑运行。');
  }catch(e){$('command').textContent='';notice(e.message,true);}
});
for(const id of ['tool-dir','target','tool-python','model-dir','infer','report-stage','gpu-run','vm-id','guest-path'])$(id).addEventListener('input',()=>{$('command').textContent='';if(['target','model-dir','vm-id'].includes(id)){invalidatePracticeEnvironment();clearReports();}});
for(const id of ['tool-dir','report-stage'])$(id).addEventListener('input',updateReportGuide);
function updateReportGuide(){
  const stage=$('report-stage').value==='B'?'B':'A',filename='report-'+stage+'.json';
  const root=$('tool-dir').value.trim(),known=/^[a-zA-Z]:[\\/]/.test(root)&&!/[\r\n\0]/.test(root);
  $('report-example-file').textContent=filename;
  $('report-earlier-file').hidden=stage!=='B';
  $('report-filename-hint').textContent=stage==='B'?'这次找 report-B.json，保留原来的 A。':'初检通常保存为 report-A.json。';
  $('report-upload-label').textContent='选择 '+filename;
  $('report-folder-address').value=known?root:'你解压的课航工具文件夹';
  $('copy-report-folder').hidden=!known;
  $('report-folder-tip').textContent=known?'复制后，粘贴到文件资源管理器顶部地址栏，按回车。':'就是放着 task.json 的解压文件夹。';
  $('report-copy-status').textContent='';
  KehangVisuals.reportPath($('report-explorer-window'),known?root:null,stage);
}
$('copy-report-folder').addEventListener('click',async()=>{
  const address=$('report-folder-address'),value=address.value,epoch=state.epoch;
  try{
    if(!navigator.clipboard?.writeText)throw Error('clipboard unavailable');
    await navigator.clipboard.writeText(value);
    if(epoch===state.epoch&&address.value===value)$('report-copy-status').textContent='地址已复制。按 Win + E，在顶部地址栏粘贴后回车。';
  }catch(error){
    if(epoch===state.epoch&&address.value===value){address.focus();address.select();$('report-copy-status').textContent='请按 Ctrl + C 复制已选中的地址。';}
  }
});
for(const id of ['kernel-spec','dsh-package','dsh-workspace','dsh-provider','dsh-model','dsh-evidence','learning-record','api-preview-path','learning-preview-text'])$(id).addEventListener('input',()=>{invalidatePracticeEnvironment();clearReports();});
$('api-send').addEventListener('change',()=>{$('command').textContent='';});

function render(a){
  state.analysis=a;$('results').replaceChildren();
  $('review-title').textContent=a.passed?'本次课程环境检查通过':'先处理检查中发现的问题';
  const identity=document.createElement('p');identity.className='result-identity';identity.textContent=`本次目标：${a.target.requested} · ${new Date(a.collected_at).toLocaleString('zh-CN',{hour12:false})}`;$('results').append(identity);
  const next=document.createElement('p');next.className='result-summary';const counts=Object.fromEntries(Object.keys(labels).map(key=>[key,a.checks.filter(x=>x.status===key).length]));
  next.textContent=`通过 ${counts.pass} · 缺失 ${counts.missing} · 不符合 ${counts.mismatch} · 未知 ${counts.unknown}`;$('results').append(next);
  if(a.learning_completed){const p=document.createElement('p');p.className='notice';p.textContent='本人学习记录与固定数字成果已核对；登录/远端连接仍为未知。';$('results').append(p);}
  const checks=document.createElement('details'),checksTitle=document.createElement('summary');checks.className='result-checks';checksTitle.textContent=`查看 ${a.checks.length} 项检测明细`;checks.open=!a.passed;checks.append(checksTitle);$('results').append(checks);
  for(const c of a.checks){
    const row=document.createElement('div');row.className='check';const name=document.createElement('strong');name.textContent=names[c.id]||c.id;
    const status=document.createElement('strong');status.className='state-'+c.status;status.textContent=labels[c.status];
    const detail=document.createElement('details'),summary=document.createElement('summary');summary.textContent='查看事实与要求';const observed=document.createElement('pre');observed.textContent=JSON.stringify({observed:c.observed,requirement:c.requirement},null,2);detail.append(summary,observed);row.append(name,status,detail);checks.append(row);
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
  resetLocal();
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
  if(files.length===1){await importReport(state.before&&$('report-stage').value==='B'?'after':'before',files[0]);return;}
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
  renderGuide();
}

function renderPreparation(plan){
  if(!state.task)return;
  const box=$('prepare-summary'),spec=state.task;
  const requirements=['使用 Windows 电脑完成本次检测'];
  if(spec.python)requirements.push(`课程 Python：${spec.python.min} 至 ${spec.python.max_exclusive}（不含上限）`);
  if(spec.node)requirements.push(`课程 Node.js：${spec.node.min} 至 ${spec.node.max_exclusive}（不含上限）`);
  if(spec.packages&&Object.keys(spec.packages).length)requirements.push('需要的依赖：'+Object.entries(spec.packages).map(([k,v])=>`${k} ≥ ${v}`).join('、'));
  if(!spec.python&&!spec.node)requirements.push($('task-summary').textContent);
  const list=document.createElement('ul');
  for(const text of requirements){const li=document.createElement('li');li.textContent=text;list.append(li);}box.replaceChildren(list);
  const help=$('prepare-help');help.replaceChildren();
  const step=plan.steps[Math.min(1,plan.steps.length-1)];
  if(step){const title=document.createElement('strong'),body=document.createElement('p');title.textContent=step.title;body.textContent=step.body;help.append(title,body);}
  for(const link of plan.links.slice(0,2)){const a=document.createElement('a');a.textContent=link.title;a.href=link.url;a.target='_blank';a.rel='noopener noreferrer';help.append(a);}
}

function localReady(){return state.task?.scenario==='python-basics'&&state.config?.local_check?.available;}
async function localAPI(path,body){
  const response=await fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json','X-Kehang-Local':state.config.local_check.token},...(body?{body:JSON.stringify(body)}:{})});
  const result=await response.json();if(!response.ok)throw Error(result.error||'本机检测请求失败，请刷新后重试');return result;
}
function resetLocal(){
  const job=localState.job,running=localState.running;
  Object.assign(localState,{epoch:localState.epoch+1,job:null,running:false,items:[],selected:null,limited:false});
  if(running&&job)localAPI('/api/local-check/cancel',{id:job.id}).catch(()=>{});
  $('local-result-panel').hidden=true;$('local-environments').replaceChildren();$('local-current').textContent='';
  $('local-start').disabled=false;$('local-cancel').hidden=true;$('local-prepare').hidden=true;
  $('local-status').textContent='点击开始后，结果会自动显示在这里。';
  $('manual-collection').open=!localReady();
}
function renderLocalEnvironments(){
  $('local-result-panel').hidden=!localState.items.length;
  $('local-result-summary').textContent=`本次检查了 ${localState.items.length} 个环境。`+(localState.limited?'候选超过 8 个，仅检查前 8 个。':'')+(localState.items.length===1?'已为你展示检测结果。':'请选择这门课实际使用的环境查看结果。');
  $('local-environments').replaceChildren();
  for(const item of localState.items){
    const row=document.createElement('div');row.className='local-environment';
    const path=document.createElement('strong');path.textContent=item.target;
    const status=document.createElement('span');status.textContent=item.error?'未完成 · 未知':item.analysis.passed?'本课程检查通过':'需要处理或确认';
    status.className=item.analysis?.passed?'state-pass':'state-unknown';
    const button=document.createElement('button');button.className='secondary';button.textContent=item.id===localState.selected?.id?'当前查看':'查看这个环境';
    button.disabled=localState.running;button.setAttribute('aria-pressed',String(item.id===localState.selected?.id));
    button.addEventListener('click',()=>action(button,()=>selectLocal(item)));
    row.append(path,status,button);$('local-environments').append(row);
  }
  $('local-recheck').disabled=!localState.selected?.report||localState.running;
  $('local-ai').disabled=!localState.selected?.report||localState.running;
  $('local-save').disabled=!localState.selected?.report||localState.running;
}
async function selectLocal(item){
  const epoch=localState.epoch,taskEpoch=state.epoch;
  clearReports(true);localState.selected=item;
  if(item.report){
    state.before=item.before||item.report;state.after=item.before?item.report:null;
    render(item.analysis);$('after-file').disabled=false;
    if(item.comparison)$('comparison').textContent=({'stable-pass':'同一目标稳定复检通过；两次均通过。',repaired:'同一目标从存在缺失或不符合改善为通过。',verified:'同一目标补齐实际运行证据后通过。',incomplete:'同一目标复检仍未全部通过。'})[item.comparison.outcome];
  }
  renderLocalEnvironments();
  if(item.report){showRoute('course',3);await guidance();if(epoch!==localState.epoch||taskEpoch!==state.epoch)return;await lesson();}
  else{showRoute('course',2);$('local-status').textContent=item.error;notice(item.error,true);}
}
async function startLocal(recheck=false){
  if(!localReady()||localState.running)return;
  const previous=localState.selected,previousJob=localState.job;
  if(recheck&&(!previous?.report||!previousJob))throw Error('请先完成本机初检');
  const body={task:state.task,consent:true};
  if(recheck)Object.assign(body,{previous_job:previous.job,target_id:previous.id});
  const retained=recheck?localState.items:[],limited=localState.limited;
  resetLocal();clearReports(true);
  localState.items=retained;localState.limited=limited;
  showRoute('course',2);localState.running=true;
  const epoch=localState.epoch,taskEpoch=state.epoch;
  $('manual-collection').open=false;$('local-start').disabled=true;$('local-cancel').hidden=false;
  $('local-status').textContent='正在查找并检查 Python，请稍候……';renderGuide();
  const current=()=>epoch===localState.epoch&&taskEpoch===state.epoch&&guided.route==='course'&&guided.courseStep===2;
  try{
    let job=await localAPI('/api/local-check',body);
    if(!current()){await localAPI('/api/local-check/cancel',{id:job.id});return;}
    localState.job=job;
    while(['running','cancelling'].includes(job.state)){
      $('local-status').textContent=job.total?`正在检测：已完成 ${job.completed} / ${job.total} 个环境。`:'正在查找本机已登记的 Python……';
      $('local-current').textContent=job.current;
      await new Promise(resolve=>setTimeout(resolve,400));
      if(!current())return;
      job=await localAPI('/api/local-check/jobs/'+encodeURIComponent(job.id));
      if(!current())return;
    }
    localState.running=false;localState.job=job;
    $('local-start').disabled=false;$('local-cancel').hidden=true;$('local-current').textContent='';
    if(job.state!=='done'){$('local-status').textContent=job.error||'本次检测已取消，未形成完整检测结论。';return;}
    localState.limited=recheck?limited:job.limited;
    // Each result keeps its owning job for a later same-target recheck.
    for(const item of job.results)item.job=job.id;
    localState.items=recheck?retained.map(item=>item.id===previous.id?job.results[0]:item):job.results;
    if(!job.results.length){
      $('local-status').textContent='没有找到可检测的 Python。这不代表没有安装；可以查看准备指引，或展开手动工具选择课程环境。';
      $('local-prepare').hidden=false;return;
    }
    $('local-status').textContent='检测完成，报告已自动返回。';
    const item=job.results.find(item=>item.report)||job.results[0];
    await selectLocal(item);
  }catch(error){
    if(current()){
      if(localState.job)localAPI('/api/local-check/cancel',{id:localState.job.id}).catch(()=>{});
      localState.running=false;$('local-start').disabled=false;$('local-cancel').hidden=true;
      $('local-status').textContent='未完成检测，请重试或展开手动工具。';notice(error.message,true);
    }
  }finally{if(current())renderGuide();}
}
$('local-start').addEventListener('click',()=>action(null,()=>startLocal()));
$('local-recheck').addEventListener('click',()=>action(null,()=>startLocal(true)));
$('local-cancel').addEventListener('click',()=>{resetLocal();$('local-status').textContent='已请求取消检测；正在结束本次固定检查。可稍后重新开始。';renderGuide();});
$('local-prepare').addEventListener('click',()=>{showRoute('course',1);$('prepared').value='missing';guidance().catch(e=>notice(e.message,true));});
$('local-ai').addEventListener('click',()=>KehangChat.open('这个检测结果意味着什么？接下来我该做什么？'));
$('local-save').addEventListener('click',()=>{if(localState.selected?.report)save('Kehang-local-report.json',localState.selected.report);});
window.addEventListener('pagehide',()=>{if(localState.running&&localState.job)fetch('/api/local-check/cancel',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json','X-Kehang-Local':state.config.local_check.token},body:JSON.stringify({id:localState.job.id})}).catch(()=>{});});

function syncCollector(){
  const simple=!!state.task&&['python-basics','notebook-data'].includes(state.task.scenario)&&!!state.config?.portable_available;
  $('simple-collector').hidden=!simple;
  $('kernel-path-help').hidden=state.task?.scenario!=='notebook-data';
  $('command-panel').open=!simple||guided.manualCollectorChosen;
  $('command-panel').querySelector('summary').textContent=simple?'无法双击运行？使用手动采集入口':'填写本次检测要用的路径';
  const local=localReady();
  $('local-check-panel').hidden=!local;
  $('manual-collection').classList.toggle('manual-only',!local);
  if(!local)$('manual-collection').open=true;
  else if(!guided.manualCollectorChosen)$('manual-collection').open=false;
}

function showRoute(route,step=0){
  if(localState.running&&(route!=='course'||step!==2))resetLocal();
  guided.navigationEpoch++;guided.route=route;
  if(route==='course'){guided.courseStep=step;guided.courseVisited=Math.max(guided.courseVisited,step);}
  if(route==='practice'){guided.practiceStep=step;guided.practiceVisited=Math.max(guided.practiceVisited,step);}
  $('notice').hidden=true;renderGuide();
  const title=route==='home'?$('welcome-title'):route==='teacher'?$('teacher-heading'):$('guide-title');
  title.tabIndex=-1;title.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});
}

function renderGuide(){
  updateCourseVisualGuide();
  const course=guided.route==='course',practice=guided.route==='practice',teacher=guided.route==='teacher';
  document.body.classList.toggle('in-flow',course||practice);
  const shareSlot=$('teacher-share-slot');
  (teacher?shareSlot:$('review-stage')).append($('course-sharing'));
  shareSlot.hidden=!teacher||!state.task;
  $('teacher-current-task').textContent=state.task?'当前任务：'+state.task.title:'';
  $('home-screen').hidden=guided.route!=='home';$('guide-shell').hidden=!course&&!practice;
  $('teacher-screen').hidden=!teacher;$('course-screen').hidden=!course;$('practice-panel').hidden=!practice;
  $('help-panel').hidden=!course||guided.courseStep!==3;
  $('python-quick-check').hidden=!course||state.task?.scenario!=='python-basics'||!localReady();
  for(const [id,current] of [['home-nav',guided.route==='home'],['teacher-nav',teacher]]){
    if(current)$(id).setAttribute('aria-current','page');else $(id).removeAttribute('aria-current');
  }
  $('back-practice').hidden=!course||!guided.fromPractice;
  if(course&&!state.task){guided.courseStep=0;guided.courseVisited=0;}
  if(course&&guided.courseStep===3&&!state.before){guided.courseStep=2;guided.courseVisited=Math.min(guided.courseVisited,2);}
  const index=course?guided.courseStep:guided.practiceStep;
  $('course-choice').hidden=!course||index!==0;
  $('task-panel').hidden=!course||!state.task||index===0;$('empty-state').hidden=true;
  $('preparation').hidden=!course||index!==1;$('collect-stage').hidden=!course||index!==2;$('review-stage').hidden=!course||index!==3;
  $('local-result-panel').hidden=!course||localState.running||!localState.items.length||![2,3].includes(index);
  const resultHost=index===3?$('review-stage'):$('task-panel');
  if($('local-result-panel').parentElement!==resultHost)resultHost.insertBefore($('local-result-panel'),index===3?$('results'):$('collect-stage'));
  for(const [i,id] of ['practice-intro','practice-prepare','practice-work','practice-submit'].entries())$(id).hidden=!practice||index!==i;
  $('guide-context').textContent=course?'课程环境准备':'Notebook ＋ SQLite 连续实训';
  const labels=course?['选择课程','准备环境','运行检测','查看与复检']:['了解任务','准备环境','跟做练习','提交成果'];
  const titles=course?['选择你要学习的课程','准备好，再开始检测','在你的电脑上运行检测','查看结果，完成同目标复检']:['先了解这堂实训','确认实训需要的环境','下载资料，开始动手练习','提交结果，保留完成记录'];
  $('guide-title').textContent=titles[index];$('guide-count').textContent=`第 ${index+1} 步 / 共 4 步`;
  const nav=$('guide-progress').querySelector('ol');
  if(!nav.children.length)for(let i=0;i<4;i++){
    const li=document.createElement('li'),button=document.createElement('button');button.type='button';
    button.addEventListener('click',()=>showRoute(guided.route,i));li.append(button);nav.append(li);
  }
  [...nav.children].forEach((li,i)=>{
    const button=li.firstChild,num=document.createElement('span'),name=document.createElement('span');
    num.className='nav-number';num.textContent=i+1;name.textContent=labels[i];button.replaceChildren(num,name);
    button.disabled=i>(course?guided.courseVisited:guided.practiceVisited)||(course&&i>0&&!state.task)||(course&&i===3&&!state.before);
    if(i===index)button.setAttribute('aria-current','step');else button.removeAttribute('aria-current');
  });
  const next=$('guide-next');next.hidden=course&&index===0;next.disabled=false;
  $('guide-prev').hidden=index===0;
  $('guide-footnote').textContent=course?'步骤位置只表示浏览进度；环境结论以实际报告为准。':'环境报告、阅读声明与成果核验分别记录。';
  if(course){
    const recheck=$('report-stage').value==='B'&&!!state.before;
    $('collect-title').textContent=recheck?'保持同一目标，再检测一次':'下载工具，做一次检测';
    $('collect-intro').textContent=recheck?'用原来的任务和目标采集较晚的复检 B。不要覆盖初检报告；更换目标需要重新初检。':'检测工具会生成一份报告，帮你确认课程环境是否准备好了。';
    $('collector-stage-hint').textContent=recheck?'这次选择 B，得到 report-B.json。保持同一课程 Python 和内核，原报告不覆盖。':'第一次检测选 A，得到 report-A.json。包内 runtime 只是检测工具，不是课程 Python。';
    updateReportGuide();
    $('report-ready').textContent=state.after?'两份报告已读取，可以进入下一步核对复检结论。':state.before?(recheck?'已保留初检；导入有效 B 后可查看复检结果。':'初检报告已读取，点击“下一步”查看结果。'):'';
    $('review-hint').textContent=state.after?(state.analysis?.passed?'本次同目标复检全部通过。可以预览分享报告，或返回学习首页。':'复检仍有缺失、不符合或未知。按下面的差异处理，再采集新的复检报告。'):state.analysis?.passed?'初检全部通过。还需保持同一目标采集较晚的 B，才能形成复检结论。':'查看下面的具体差异。由你决定如何处理，再保持同一目标采集复检 B。';
    $('command-entry-hint').hidden=!$('simple-collector').hidden;
    next.textContent=index===1?'准备好了，去检测 →':index===2?'下一步：查看结果 →':state.after&&state.analysis?.passed?'返回学习首页':'去采集复检报告 →';
    next.disabled=(index>0&&!state.task)||(index===2&&(!state.before||!state.analysis));
    if(index===2&&!state.before)$('guide-footnote').textContent='运行后导入有效报告，即可查看检测结果；下载工具不会让环境变成通过。';
    if(localReady()){
      $('collect-title').textContent=localState.running?'正在检测本机 Python':'直接检测，不用找路径';
      $('collect-intro').textContent='在运行课航本地服务的这台电脑完成固定检查，结果自动回到网页。';
      if(index===2)$('guide-footnote').textContent=localState.running?'检测进行中；离开本步骤会取消。':'点击“开始本机检测”；也可展开手动工具，检测另一台电脑。';
    }
    if(localState.selected){
      $('guide-title').textContent=index===3?'本机检测结果':titles[index];
      $('review-hint').textContent=state.after?'已对同一环境再次检测，下面分别列出结果与变化。':state.analysis?.passed?'这个环境已满足本次 Python 基础课要求，可以开始学习。需要时可再检测一次。':'查看具体差异和处理指引；处理后点击“重新检测当前环境”。';
      if(index===3)next.textContent='返回学习首页';
    }
  }else if(practice){
    next.textContent=['下一步：准备环境 →','下一步：下载并跟做 →','下一步：提交成果 →','返回学习首页'][index];
    next.disabled=index<3&&!practiceState.practice;
  }
  document.dispatchEvent(new Event('kehang-context'));
}

function updateCourseVisualGuide(){
  const host=$('course-visual-guide');
  if(!state.task){host.hidden=true;return;}
  const fields=Object.fromEntries(['target','kernel-spec','model-dir','dsh-workspace','dsh-evidence','dsh-package','api-preview-path','learning-record'].map(id=>[id,$(id).value]));
  fields.pythonCommand=ps($('target').value.trim().replace(/^"(.*)"$/,'$1')||'C:\\课程Python\\python.exe');
  KehangVisuals.course(host,state.task.scenario,fields,state.epoch);
}
for(const id of ['target','kernel-spec','model-dir','dsh-workspace','dsh-evidence','dsh-package','api-preview-path','learning-record'])$(id).addEventListener('input',updateCourseVisualGuide);

$('guide-prev').addEventListener('click',()=>showRoute(guided.route,(guided.route==='course'?guided.courseStep:guided.practiceStep)-1));
$('guide-next').addEventListener('click',()=>{
  if(guided.route==='practice'){
    if(guided.practiceStep===3)showRoute('home');else showRoute('practice',guided.practiceStep+1);
  }else if(guided.courseStep===3){
    if(localState.selected){showRoute('home');return;}
    if(state.after&&state.analysis?.passed)showRoute('home');
    else{$('report-stage').value='B';$('command').textContent='';$('report-files').value='';showRoute('course',2);}
  }else showRoute('course',guided.courseStep+1);
});
for(const id of ['home-link','home-nav','back-home','teacher-home'])$(id).addEventListener('click',e=>{e.preventDefault();showRoute('home');});
$('teacher-nav').addEventListener('click',()=>{guided.fromPractice=false;showRoute('teacher');});
$('choose-course').addEventListener('click',()=>{guided.fromPractice=false;showRoute('course',0);});
$('start-python').addEventListener('click',e=>action(e.target,()=>startLocal()));
$('start-practice').addEventListener('click',()=>showRoute('practice',0));
$('back-practice').addEventListener('click',()=>showRoute('practice',1));
$('import-entry').addEventListener('click',()=>{guided.fromPractice=false;showRoute('course',0);$('student-import').open=true;$('student-import').scrollIntoView({block:'nearest'});});
const teacherShare=document.createElement('section'),teacherTask=document.createElement('h3');
teacherShare.id='teacher-share-slot';teacherTask.id='teacher-current-task';teacherShare.append(teacherTask);$('teacher-course-panel').before(teacherShare);
const runtimeFallback=document.createElement('details'),runtimeSummary=document.createElement('summary');
runtimeSummary.textContent='工具包没有运行时？使用已有工具 Python';runtimeFallback.append(runtimeSummary);
const runtimeLabel=$('tool-python').labels[0];runtimeLabel.before(runtimeFallback);runtimeFallback.append(runtimeLabel,$('tool-python'));
$('command-panel').querySelector('summary').addEventListener('click',()=>{guided.manualCollectorChosen=!$('command-panel').open;});
$('command-panel').addEventListener('focusin',e=>{if(e.target.tagName!=='SUMMARY')guided.manualCollectorChosen=true;});
renderGuide();
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
  $('report-stage').value='B';$('command').textContent='';$('report-files').value='';$('command-panel').open=true;
  $('make-command').focus();notice('保持同一任务与组件，手动采集较晚B后导入。检查状态来自新报告。');
  const button=$('lesson-retry');button.disabled=true;setTimeout(()=>{button.disabled=false;},3000);
  showRoute('course',2);
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
$('need-form').addEventListener('submit',e=>{e.preventDefault();const serial=++state.needEpoch,navigationEpoch=guided.navigationEpoch;action(e.submitter,async()=>{
  const text=$('need-text').value;const result=await api('/api/need',{text});if(serial!==state.needEpoch||navigationEpoch!==guided.navigationEpoch)return;
  const box=$('need-result');box.replaceChildren();const p=document.createElement('p');p.textContent=result.message+' '+(result.question||'');box.append(p);
  const candidates=result.candidates||[];
  if(result.scenario&&!candidates.some(x=>x.scenario===result.scenario))candidates.unshift({scenario:result.scenario,label:result.scenario});
  for(const candidate of candidates){if(!candidate.scenario)continue;const b=document.createElement('button');b.className='secondary';b.textContent='确认：'+candidate.label;b.addEventListener('click',()=>action(b,async()=>{
    const candidateNavigationEpoch=guided.navigationEpoch;
    const resolved=await api('/api/need',{text,clarification:candidate.scenario});if(serial!==state.needEpoch||candidateNavigationEpoch!==guided.navigationEpoch)return;
    if(resolved.status!=='recognized'||!resolved.scenario){notice(resolved.message,true);return;}
    $('goal').value=resolved.scenario;await chooseTask(()=>api('/api/goal?goal='+encodeURIComponent(resolved.scenario)));
  }));box.append(b);}
  if(result.error_help){$('user-error').value=text;$('help-panel').hidden=false;$('help-panel').open=true;$('diagnosis').scrollIntoView({block:'nearest'});}
});});
$('need-text').addEventListener('input',()=>{state.needEpoch++;$('need-result').replaceChildren();});
$('course-package').addEventListener('change',e=>action(null,async()=>{
  clearTask();const epoch=state.epoch,navigationEpoch=guided.navigationEpoch;
  const file=e.target.files[0];e.target.value='';if(!file||file.size>100000)throw Error('课程包须小于100KB');const packageValue=JSON.parse(await file.text());
  const result=await api('/api/import-course',{package:packageValue});
  if(epoch!==state.epoch||navigationEpoch!==guided.navigationEpoch){if(epoch===state.epoch)e.target.value='';return;}
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
  renderGuide();
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
    guided.fromPractice=true;showRoute('course',0);
    $('goal').value=scenario;
    await chooseTask(()=>course?Promise.resolve(course.task):api('/api/goal?goal='+scenario),course?.code||null);
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
  const epoch=++practiceState.epoch,file=e.target.files[0],navigationEpoch=guided.navigationEpoch;
  e.target.value='';
  practiceState.reviewEpoch++;
  $('practice-teacher-review').replaceChildren();
  $('practice-completion-file').value='';
  practiceState.practice=null;practiceState.package=null;practiceState.courses=null;practiceState.environment={};practiceState.submission=null;practiceState.submissionEpoch++;
  $('practice-read').checked=false;$('practice-submission').value='';$('practice-result').textContent='';$('practice-published').textContent='尚未取得有效实训包';
  for(const id of ['practice-notebook','practice-sqlite','practice-export-package','practice-check','practice-completion'])$(id).disabled=true;
  $('practice-description').textContent='正在核对资料包。旧实训结果已隔离；原提交记录可在本次会话中保留。';renderPracticeStates();
  if(!file||file.size>100000)throw Error('实训课程包须小于100KB');
  const value=await api('/api/practice/import',{package:JSON.parse(await file.text())});
  if(epoch!==practiceState.epoch||navigationEpoch!==guided.navigationEpoch){
    if(epoch===practiceState.epoch){e.target.value='';$('practice-description').textContent='已离开资料导入步骤。请重新导入资料；也可刷新页面恢复示例实训。';}
    return;
  }
  renderPractice(value);$('practice-published').textContent='当前固定资料已导入本机。请通过可信渠道向教师核对实训和两项任务摘要。';
  showRoute('practice',0);
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
  const componentStates=Object.entries(result.components).map(([key,c])=>(key==='notebook'?'Notebook':'SQLite')+'：'+practiceLabels[c.status]);
  $('practice-result').textContent=[(practiceLabels[result.status]||result.status)+'。'+result.next_step,...componentStates].join(' ');
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
api('/api/config').then(config=>{state.config=config;if(state.task)syncCollector();renderGuide();}).catch(e=>notice(e.message,true));
const courseFromURL=new URLSearchParams(location.search).get('course');if(courseFromURL){$('course-code').value=courseFromURL;$('course-form').requestSubmit();}
