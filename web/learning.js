'use strict';
// Course buttons reuse the existing task loader; choosing a course runs no collector.
const learningCourses = [
  ['python-basics','Python 基础','解释器、版本与基础依赖','coding','Py'],
  ['node-basics','Node.js / npm','JavaScript 运行与包管理','coding','JS'],
  ['java-jdk','Java / JDK','编译器与 Java 程序运行','coding','Jv'],
  ['notebook-data','Notebook 数据分析','Jupyter 内核、NumPy 与 Pandas','data','Nb'],
  ['sqlite-basics','SQLite 数据库','数据库文件与 SQL 查询','data','SQL'],
  ['pytorch-cpu','PyTorch · CPU','用 CPU 开始张量计算','ai','CPU'],
  ['pytorch-gpu','PyTorch · GPU','CUDA 环境与 GPU 实际运算','ai','GPU'],
  ['local-qwen','本地模型入门','固定 Qwen 模型与离线推理','ai','AI'],
  ['ai-web-deepseek','DeepSeek 使用入门','网页 / 客户端提问与练习','ai','Ds'],
  ['deepseek-api','DeepSeek API','编程依赖与 API 调用准备','ai','API'],
  ['dsh-desktop','DSH 桌面 Agent','桌面工作区、授权与任务证据','ai','App'],
  ['dsh-cli','DSH 命令行 Agent','Node 环境、DSH 包与任务证据','ai','CLI'],
  ['vm-linux','虚拟机 / Linux','虚拟化软件、实例与来宾系统','system','VM']
];
let courseLoading = false;
for(const [value,label] of [['all','全部课程 · 13'],['coding','基础编程'],['data','数据分析'],['ai','AI 与深度学习'],['system','系统环境']]){
  const button=document.createElement('button');button.type='button';button.textContent=label;button.dataset.filter=value;button.setAttribute('aria-pressed',String(value==='all'));
  button.addEventListener('click',()=>{
    for(const item of $('course-filters').children)item.setAttribute('aria-pressed',String(item===button));
    for(const item of $('course-grid').children)item.hidden=value!=='all'&&item.dataset.category!==value;
    $('course-selection-status').textContent='';
  });$('course-filters').append(button);
}
for(const [scenario,title,description,category,monogram] of learningCourses){
  const button=document.createElement('button');button.type='button';button.className='course-card';button.dataset.scenario=scenario;button.dataset.category=category;
  const icon=document.createElement('span');icon.className='course-monogram';icon.textContent=monogram;icon.setAttribute('aria-hidden','true');
  const copy=document.createElement('span'),name=document.createElement('strong'),detail=document.createElement('small'),arrow=document.createElement('span');
  name.textContent=title;detail.textContent=description;copy.append(name,detail);arrow.className='course-arrow';arrow.textContent='↗';arrow.setAttribute('aria-hidden','true');button.append(icon,copy,arrow);
  button.addEventListener('click',async()=>{
    if(courseLoading)return;
    courseLoading=true;for(const item of $('course-grid').children)item.disabled=true;
    $('course-selection-status').textContent='正在打开 '+title+'…';
    try{
      guided.fromPractice=false;showRoute('course',0);$('goal').value=scenario;
      await chooseTask(()=>api('/api/goal?goal='+encodeURIComponent(scenario)));
      if(guided.route==='course')$('notice').hidden=true;
    }catch(error){notice('课程读取失败，请重试。'+error.message,true);}
    finally{courseLoading=false;for(const item of $('course-grid').children)item.disabled=false;$('course-selection-status').textContent='';}
  });$('course-grid').append(button);
}

const KehangChat = (()=>{
  const conversations=new Map();
  let scope='',fingerprint='',preview=null,busy=false,epoch=0,lastTrigger=null,pagePolicy='';
  const desktop=window.matchMedia('(min-width: 1120px)');
  function currentContext(){
    const course=guided.route==='course'&&guided.courseStep>0;
    return {route:guided.route,step:course?guided.courseStep:guided.route==='practice'?guided.practiceStep:0,task:course?state.task:null,report:course?(state.after||state.before):null};
  }
  function conversation(){return conversations.get(scope);}
  function setStatus(text,error=false){$('chat-status').textContent=text;$('chat-status').classList.toggle('state-mismatch',error);}
  function invalidate(){epoch++;preview=null;busy=false;$('chat-preview-panel').hidden=true;updateButtons();}
  function updateButtons(){
    $('chat-preview-button').disabled=busy||!state.config||!$('chat-input').value.trim();
    $('chat-send').disabled=busy||!preview?.ai.configured;
    $('chat-input').readOnly=busy;
    $('chat-preview-button').textContent=busy?'正在处理…':'预览发送 →';
    $('chat-messages').setAttribute('aria-busy',String(busy));
  }
  function renderMessages(){
    const box=$('chat-messages');box.replaceChildren();
    if(!conversation().messages.length){
      const welcome=document.createElement('p');welcome.className='chat-welcome';welcome.textContent=guided.route==='home'||(guided.route==='course'&&guided.courseStep===0)?'想学什么，或者卡在哪一步了？告诉我你的目标，我们从这里开始。':'可以问我当前这一步，也可以粘贴看不懂的报错。';box.append(welcome);
    }
    for(const message of conversation().messages){
      const item=document.createElement('div');item.className='chat-message chat-'+message.role;
      const author=document.createElement('strong'),text=document.createElement('p');author.textContent=message.role==='user'?'你':'课航 AI';text.textContent=message.content;item.append(author,text);box.append(item);
    }
    box.scrollTop=box.scrollHeight;
  }
  function renderContext(){
    const value=currentContext(),key=value.route==='course'?'course:'+(value.task?.id||'selection'):value.route;
    const nextFingerprint=JSON.stringify(value);
    if(nextFingerprint!==fingerprint){
      if(scope&&conversations.has(scope))conversation().draft=$('chat-input').value;
      invalidate();fingerprint=nextFingerprint;
      if(key!==scope){scope=key;if(!conversations.has(scope))conversations.set(scope,{messages:[],draft:''});$('chat-input').value=conversation().draft;renderMessages();}
      setStatus('');
    }
    const stages={home:['欢迎首页'],selection:['选择课程'],course:['选择课程','准备环境','运行检测','查看检测结果'],practice:['了解任务','准备环境','跟做练习','提交成果'],teacher:['教师工作台']};
    $('chat-context').textContent=(value.task?value.task.title+' · ':'')+stages[value.route][value.step];
    const configured=state.config?.ai.configured;
    $('chat-connection').textContent=!state.config?'正在读取连接状态…':configured?'已配置 · '+state.config.ai.model:'尚未连接模型';
    $('chat-setup').hidden=!state.config||configured;
    const suggestions=value.route==='home'||(value.route==='course'&&value.step===0)?['我刚入门，应该选哪门课？','Notebook 和 Python 有什么区别？']:value.step===3&&value.route==='course'?['这个结果意味着什么？','下一步该怎么做？']:['这一步我要准备什么？','我找不到需要的文件，怎么办？'];
    const box=$('chat-suggestions');box.replaceChildren();
    for(const question of suggestions){const button=document.createElement('button');button.type='button';button.className='text-button';button.textContent=question;button.addEventListener('click',()=>open(question));box.append(button);}
    updateButtons();
    const nextPolicy=value.route==='course'&&value.step>0?'workspace':value.route;
    if(pagePolicy!==nextPolicy){pagePolicy=nextPolicy;setOpen(pagePolicy==='workspace'&&desktop.matches);}
  }
  function setOpen(value,focus=false){
    if(value&&!$('learning-chat').contains(document.activeElement))lastTrigger=document.activeElement;
    $('learning-chat').hidden=!value;document.body.classList.toggle('chat-open',value);$('chat-toggle').setAttribute('aria-expanded',String(value));
    if(focus&&value)$('chat-input').focus({preventScroll:true});
    if(!value){
      invalidate();
      if($('learning-chat').contains(document.activeElement))(lastTrigger?.isConnected&&lastTrigger.getClientRects().length?lastTrigger:$('chat-toggle')).focus({preventScroll:true});
    }
  }
  function open(question){
    setOpen(true,true);
    if(question){invalidate();$('chat-input').value=question;conversation().draft=question;updateButtons();}
  }
  $('chat-toggle').addEventListener('click',()=>setOpen($('learning-chat').hidden,true));
  $('chat-close').addEventListener('click',()=>setOpen(false));
  $('home-chat').addEventListener('click',()=>open('我刚入门，应该选哪门课？'));
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!$('learning-chat').hidden){setOpen(false);}});
  document.addEventListener('kehang-context',renderContext);
  $('chat-input').addEventListener('input',()=>{invalidate();conversation().draft=$('chat-input').value;setStatus('');});
  $('chat-clear').addEventListener('click',()=>{invalidate();conversation().messages=[];conversation().draft='';$('chat-input').value='';setStatus('');renderMessages();$('chat-input').focus();});
  $('chat-cancel').addEventListener('click',()=>{invalidate();setStatus('');$('chat-input').focus();});
  $('chat-form').addEventListener('submit',async event=>{
    event.preventDefault();if(busy||!$('chat-input').value.trim())return;
    const requestEpoch=++epoch;busy=true;updateButtons();setStatus('正在整理当前步骤与对话…');
    try{
      const value=await api('/api/chat/preview',{...currentContext(),question:$('chat-input').value.trim(),history:conversation().messages.slice(-20)});
      if(requestEpoch!==epoch)return;
      preview=value;$('chat-preview').textContent=JSON.stringify(value.preview,null,2);$('chat-system').textContent=value.ai.system;
      $('chat-destination').textContent=value.ai.configured?'发送至 '+value.ai.destination+' · '+value.ai.model:'尚未连接模型，本次不会发送。';
      $('chat-preview-panel').hidden=false;setStatus(value.ai.configured?'核对后，点击“同意并发送这条”。':'已整理问题与上下文。请先连接模型，随后重试。',!value.ai.configured);
      $('chat-preview-panel').scrollIntoView({block:'nearest'});
    }catch(error){if(requestEpoch===epoch)setStatus('预览失败：'+error.message+'。请重试。',true);}
    finally{if(requestEpoch===epoch){busy=false;updateButtons();}}
  });
  $('chat-send').addEventListener('click',async()=>{
    if(busy||!preview?.ai.configured)return;
    const request=preview,question=request.preview.messages.at(-1).content,requestEpoch=++epoch;
    preview=null;busy=true;updateButtons();setStatus('AI 正在回复…');$('chat-preview-panel').hidden=true;
    try{
      const result=await api('/api/chat',{token:request.token,consent:true});if(requestEpoch!==epoch)return;
      if(!result.completed){setStatus('AI 暂时未能回复。问题已保留，可重新预览后重试。',true);return;}
      conversation().messages.push({role:'user',content:question},{role:'assistant',content:result.explanation});
      $('chat-input').value='';conversation().draft='';renderMessages();setStatus('可以接着追问。');
    }catch(error){if(requestEpoch===epoch)setStatus('发送未完成：'+error.message+'。问题已保留。',true);}
    finally{if(requestEpoch===epoch){busy=false;updateButtons();}}
  });
  let resizeTimer;
  desktop.addEventListener('change',()=>{
    clearTimeout(resizeTimer);
    resizeTimer=setTimeout(()=>setOpen(pagePolicy==='workspace'&&desktop.matches),200);
  });
  renderContext();
  return Object.freeze({open});
})();
