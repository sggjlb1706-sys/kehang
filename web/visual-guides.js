'use strict';
/* Locally drawn instructional windows. Nothing here inspects files or executes a command. */
window.KehangVisuals=(()=>{
  const cache=new WeakMap();
  const make=(tag,cls,text)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node;};
  const base=path=>path.replace(/[\\/]+$/,'').split(/[\\/]/).pop()||path;
  const parent=path=>path.replace(/[\\/][^\\/]*[\\/]*$/,'')||path;
  const clean=value=>typeof value==='string'?value.trim().replace(/^"(.*)"$/,'$1'):'';
  function icon(kind='file'){
    const node=make('span','win11-icon win11-icon-'+kind);node.setAttribute('aria-hidden','true');
    if(kind!=='folder')node.textContent=({exe:'EXE',shortcut:'↗',json:'{ }',notebook:'NB',csv:'CSV',script:'PY',database:'DB',model:'AI',terminal:'>_',home:'⌂',pc:'▣',download:'↓',file:''})[kind]||'';
    return node;
  }
  function chrome(title,terminal=false){
    const win=make('div','win11-window'+(terminal?' win11-terminal':''));
    win.setAttribute('role','img');win.setAttribute('aria-label',title+'，Windows 11 操作示意');
    const bar=make('div','win11-titlebar'),tab=make('div','win11-tab');tab.append(icon(terminal?'terminal':'folder'),make('span','win11-tab-caption',title),make('span','win11-tab-close','×'));
    bar.append(tab,make('span','win11-tab-plus','＋'),make('span','win11-window-controls','—　□　×'));win.append(bar);return win;
  }
  function explorer(options){
    const win=chrome(options.title||base(options.path||'课航工具'));
    win.setAttribute('aria-label','Windows 11 操作示意，地址：'+options.path+'；应选：'+options.rows.filter(row=>row.selected).map(row=>row.name).join('、')+'。不是文件扫描结果。');
    const address=make('div','win11-navigation');address.append(make('span','win11-navigation-icons','←　→　↑　⟳'));
    const location=make('div','win11-location');location.append(icon('folder'),make('span','win11-address-text',options.path||'你自己的文件夹'),make('span','win11-location-chevron','⌄'));
    address.append(location,make('span','win11-search','搜索此文件夹　⌕'));win.append(address);
    const toolbar=make('div','win11-commandbar');
    for(const [symbol,label] of [['＋','新建'],['✂','剪切'],['▢','复制'],['▣','粘贴'],['↕','排序'],['☷','查看'],['⋯','更多']]){const item=make('span','win11-tool');item.append(make('span','win11-tool-symbol',symbol),make('span','',label));toolbar.append(item);}
    win.append(toolbar);
    const body=make('div','win11-body'),nav=make('div','win11-sidebar');
    for(const [kind,label] of [['home','主页'],['folder','桌面'],['download','下载'],['folder','文档'],['pc','此电脑']]){const item=make('div','win11-sidebar-item'+(label==='此电脑'?' win11-nav-selected':''));item.append(icon(kind),make('span','',label));nav.append(item);}
    const content=make('div','win11-content');
    const headers=make('div','win11-file-columns');for(const title of ['名称','修改日期','类型'])headers.append(make('span','',title));content.append(headers);
    for(const entry of options.rows){
      const row=make('div','win11-file-row'+(entry.selected?' win11-file-selected':''));if(entry.id)row.id=entry.id;if(entry.hidden)row.hidden=true;
      const name=make('span','win11-file-name');name.append(icon(entry.kind||'file'));
      const label=make(entry.selected?'strong':'span','',entry.name);if(entry.labelId)label.id=entry.labelId;name.append(label);
      row.append(name,make('span','win11-file-date','—'),make('span','win11-file-type',({folder:'文件夹',exe:'应用程序',shortcut:'快捷方式',json:'JSON 文件',notebook:'Jupyter Notebook',csv:'CSV 文件',database:'数据库文件',script:'Python 文件',model:'模型权重',file:'文件'})[entry.kind]||'文件'));
      if(entry.selected){const pointer=make('span','win11-pointer','← 看这里');row.append(pointer);}
      content.append(row);
    }
    if(options.menu){
      const menu=make('div','win11-view-menu');for(const text of ['详细信息','列表','显示　›'])menu.append(make('div',text.includes('显示')?'win11-menu-selected':'',text));
      const submenu=make('div','win11-view-submenu');for(const text of ['导航窗格','项目复选框','✓ 文件扩展名','隐藏的项目'])submenu.append(make('div',text.includes('扩展名')?'win11-menu-selected':'',text));content.append(menu,submenu);
    }
    body.append(nav,content);win.append(body,make('div','win11-statusbar','位置示意 · 文件列表以你实际打开的目录为准'));
    return win;
  }
  function scene(step,fields){
    let folder=(typeof step.path==='function'?step.path(fields):step.path)||'你的课程文件夹',rows=step.rows?.map(row=>({...row}))||[];
    const entered=clean(fields[step.field]);
    if(entered&&/^[A-Za-z]:[\\/]/.test(entered)&&step.bind){
      folder=step.bind==='inside'?entered:parent(entered);
      if(step.bind!=='inside'&&rows.some(row=>row.selected))rows.find(row=>row.selected).name=base(entered);
    }
    if(step.kind==='terminal'){
      const win=chrome('Windows PowerShell',true),text=make('div','win11-terminal-body');
      text.append(make('p','win11-terminal-note','终端操作示意 · 请在你自己的窗口中完成'));
      for(const line of (typeof step.lines==='function'?step.lines(fields):step.lines))text.append(make('p',line.startsWith('PS')?'win11-terminal-command':'',line));
      win.append(text,make('div','win11-terminal-footer','这里不会执行命令，也没有产生检测结果'));return win;
    }
    if(step.kind==='properties'){
      const win=explorer({title:'程序快捷方式',path:'通过“打开文件所在的位置”进入的快捷方式文件夹',rows:[{name:step.shortcut||'Python 快捷方式',kind:'shortcut',selected:true}]});
      win.classList.add('win11-property-window');
      const property=make('div','win11-properties');property.append(make('strong','', '属性 · 快捷方式'),make('div','win11-property-tabs','常规　 快捷方式　 兼容性'),make('span','win11-property-label','目标（T）：'),make('div','win11-property-value',entered||step.example),make('p','', '复制程序路径，回到课航粘贴。'));
      const buttons=make('div','win11-property-buttons');for(const label of ['确定','取消','应用'])buttons.append(make('span','',label));property.append(buttons);
      win.querySelector('.win11-content').append(property);return win;
    }
    return explorer({title:base(folder),path:folder,rows,menu:step.menu});
  }
  function mount(host,key,title,steps,fields={}){
    if(!host)return;
    host.hidden=false;
    let data=cache.get(host);
    if(data?.key===key){data.fields=fields;data.draw();return;}
    data={key,index:0,fields,draw:null};cache.set(host,data);host.replaceChildren();host.classList.add('visual-guide');
    const head=make('div','visual-guide-heading');head.append(make('h3','',title),make('span','visual-example-label','Windows 11 操作示意'));host.append(head);
    const layout=make('div','visual-guide-layout'),stepsNav=make('ol','visual-step-nav'),panel=make('div','visual-guide-panel');
    const message=make('p','visual-step-instruction'),picture=make('div','visual-scene'),foot=make('div','visual-guide-controls');
    const back=make('button','secondary','← 上一幅'),count=make('span','visual-step-count'),next=make('button','secondary','下一幅 →'),jump=make('button','text-button','去填写对应位置');
    for(const button of [back,next,jump])button.type='button';
    const buttons=steps.map((step,index)=>{const li=make('li'),button=make('button','visual-step-button');button.type='button';button.append(make('span','visual-step-number',String(index+1)),make('span','',step.title));button.addEventListener('click',()=>{data.index=index;data.draw();});li.append(button);stepsNav.append(li);return button;});
    back.addEventListener('click',()=>{data.index--;data.draw();});next.addEventListener('click',()=>{data.index++;data.draw();});
    jump.addEventListener('click',()=>{const target=document.getElementById(steps[data.index].field);if(!target||target.disabled)return;for(let node=target.parentElement;node;node=node.parentElement)if(node.tagName==='DETAILS')node.open=true;target.focus({preventScroll:true});target.scrollIntoView({block:'center',behavior:'instant'});});
    foot.append(back,count,next,jump);panel.append(message,picture,foot,make('p','visual-guide-disclaimer','图中是操作示意。请在自己的 Windows 窗口完成；浏览图示不改变检测结论。'));layout.append(stepsNav,panel);host.append(layout);
    data.draw=()=>{
      const step=steps[data.index];message.textContent=step.tip;picture.replaceChildren(scene(step,data.fields));
      buttons.forEach((button,index)=>{if(index===data.index)button.setAttribute('aria-current','step');else button.removeAttribute('aria-current');});
      back.disabled=data.index===0;next.disabled=data.index===steps.length-1;count.textContent=(data.index+1)+' / '+steps.length;
      jump.hidden=!step.field;jump.textContent=step.action||'去填写对应位置';
    };
    data.draw();
  }
  const row=(name,kind='file',selected=false)=>({name,kind,selected});
  const python=()=>({title:'找到课程 Python',tip:'打开这门课使用的 Python 安装目录，选 python.exe。包内 runtime 是工具，不是课程环境。',path:'C:\\课程Python',rows:[row('Lib','folder'),row('Scripts','folder'),row('python.exe','exe',true)],field:'target',bind:'file'});
  const shortcut=(program,example)=>({title:'从快捷方式找程序',tip:'开始菜单右键程序 → 更多／打开文件所在的位置 → 在打开的文件夹里右键快捷方式 → 属性。复制“目标”中的程序路径。',kind:'properties',shortcut:program+' 快捷方式',example,field:'target'});
  const run=(title,lines,field='make-command')=>({title,tip:'按本页生成的固定命令，由你在目标电脑手动运行。图中不是实际执行结果。',kind:'terminal',lines,field,action:'找到本页的操作按钮'});
  const notebook=[python(),{title:'找到所用内核',tip:'用本页选中的课程 Python 完整路径查看内核目录，避免误用 PATH 中另一份 Python。',kind:'terminal',lines:fields=>['PS> & '+(fields.pythonCommand||'"C:\\课程Python\\python.exe"')+' -m jupyter kernelspec list','查看你自己的输出目录，再打开其中的 kernel.json。','仅列出内核不能证明实际运行通过。'],field:'kernel-spec'}, {title:'选择 kernel.json',tip:'选内核定义文件 kernel.json，不能把 python.exe 当作内核文件。',path:'C:\\课程Python\\share\\jupyter\\kernels\\python3',rows:[row('kernel.json','json',true),row('logo-32x32.png')],field:'kernel-spec',bind:'file'}];
  const work=()=>({title:'使用专用练习目录',tip:'填写尚不存在的新练习目录，再点本页的准备按钮。已有私人目录不会被覆盖。',path:'D:\\CoursePractice',rows:[row('DSH-summary','folder',true)],field:'dsh-workspace',bind:'folder'});
  const evidence=()=>({title:'记录真实工具过程',tip:'在 DSH 中亲自授权本次工具操作，完成后填写最小摘要。模板和软件存在都不能代替真实工具记录。',path:'D:\\CoursePractice\\DSH-summary',rows:[row('input.csv','csv'),row('summary.json','json'),row('evidence-bound.json','json',true)],field:'dsh-evidence',bind:'file'});
  const catalog={
    'python-basics':{title:'Python · 看图选择课程环境',steps:[shortcut('Python','C:\\课程Python\\python.exe'),python()]},
    'node-basics':{title:'Node.js · 找到程序，别选开始菜单文件夹',steps:[shortcut('Node.js','C:\\Program Files\\nodejs\\node.exe'),{title:'选择 node.exe',tip:'在实际安装目录找 node.exe。同目录的 node_modules 中才是本任务要核对的 npm。',path:'C:\\Program Files\\nodejs',rows:[row('node_modules','folder'),row('node.exe','exe',true),row('npm.cmd')],field:'target',bind:'file'}]},
    'notebook-data':{title:'Notebook · Python 与内核分别选',steps:notebook},
    'java-jdk':{title:'Java · 选择完整 JDK 文件夹',steps:[{title:'选择 JDK 根目录',tip:'这里填 JDK 根文件夹，不是 bin，也不是 java.exe。',path:'C:\\Program Files\\Java',rows:[row('jdk-21','folder',true)],field:'target',bind:'folder'},{title:'核对两个程序',tip:'根目录的 bin 下应同时有 java.exe 与 javac.exe；是否同源由实际检测核对。',path:fields=>clean(fields.target)?clean(fields.target).replace(/[\\/]+$/,'')+'\\bin':'C:\\Program Files\\Java\\jdk-21\\bin',rows:[row('java.exe','exe',true),row('javac.exe','exe')],field:'target'},run('编译与运行验证',['PS C:\\课航工具> 运行本页生成的采集命令','固定源码在临时目录编译、运行，再生成报告。'])]},
    'sqlite-basics':{title:'SQLite · 找到专用数据库文件',steps:[{title:'先准备数据库',tip:'单项课程用本页准备按钮；连续实训用练习生成的 scores.sqlite。不要覆盖私人数据库。',kind:'terminal',lines:['独立任务：在本页填写新的数据库完整路径，再生成并手动运行准备命令。','连续实训：按资料完成 02_SQLite练习.py，使用它生成的 scores.sqlite。','创建文件与只读检测是两步，文件存在不等于检测通过。'],field:'prepare-sqlite',action:'找到数据库准备按钮'}, {title:'选择 scores.sqlite',tip:'这里选择数据库文件，不是 Python，也不是 sqlite3.exe。固定检测只读核对。',path:'D:\\课航实训',rows:[row('notebook-result.json','json'),row('scores.sqlite','database',true)],field:'target',bind:'file'}]},
    'pytorch-cpu':{title:'PyTorch CPU · 检查课程实际使用的环境',steps:[python(),run('确认 CPU 运算',['PS C:\\课航工具> 运行本页生成的采集命令','实际核对 PyTorch 导入与固定 CPU 张量运算。','示意：版本信息不能代替固定程序运行证据。'])]},
    'pytorch-gpu':{title:'PyTorch GPU · 环境与实际运算分别核对',steps:[python(),run('明确本次 GPU 运算',['选择本页“本次主动执行固定 GPU 张量运算”。','PS C:\\课航工具> 运行你审查过的采集命令','报告分别核对 CUDA 构建、设备和实际 GPU 运算。'],'gpu-run')]},
    'local-qwen':{title:'本地模型 · 环境和模型目录分别选',steps:[python(),{title:'选择完整模型目录',tip:'选包含固定模型配置、分词器和权重的目录；不是只选某一个文件。',path:'D:\\Models',rows:[row('Qwen2.5-0.5B-Instruct','folder',true)],field:'model-dir',bind:'folder'},{title:'核对目录里的文件',tip:'目录应包含配置、分词器与固定权重；填的仍是整个模型文件夹，不是单个权重文件。',path:'D:\\Models\\Qwen2.5-0.5B-Instruct',rows:[row('config.json','json'),row('tokenizer.json','json'),row('model.safetensors','model',true)],field:'model-dir',bind:'inside'},run('本人启动固定推理',['检查本页模型目录与“本次执行固定离线推理”。','固定推理会实际加载本地权重。','下载模型、文件存在和文字建议都不代表推理通过。'],'infer')]},
    'vm-linux':{title:'虚拟机 / Linux · 宿主、实例、来宾三层核对',steps:[{title:'找到虚拟化软件',tip:'VirtualBox 选 VBoxManage.exe；VMware 选 vmrun.exe。不是桌面快捷方式。',path:'C:\\Program Files\\Oracle\\VirtualBox',rows:[row('VirtualBox.exe','exe'),row('VBoxManage.exe','exe',true)],field:'target',bind:'file'},run('确认具体虚拟机',['VirtualBox：在自己的终端手动查看 VBoxManage.exe list vms。','VMware：确认这台虚拟机实际使用的 .vmx 完整路径。','把具体实例标识填到本页，不能只填 Linux 名称。'],'vm-id'),run('取得 Linux 来宾报告',['在已由你启动的 Linux 来宾运行包内固定 guest_probe.py。','报告绑定同一任务与虚拟机标识；带回 guest.json。','此图不会启动虚拟机或替你连接来宾。'],'guest-path')]},
    'ai-web-deepseek':{title:'AI 网页学习 · 提问和核对都需实际完成',steps:[{title:'准备练习目录',tip:'选择自己的课程练习目录，按固定问题实际提问并核对结果。课航不会自动登录。',path:'D:\\CoursePractice',rows:[row('AI练习','folder',true)],field:'target',bind:'folder'},{title:'保存学习记录',tip:'本人填写 web-record.json，保留实际回答与核对声明；空模板不表示完成。',path:'D:\\CoursePractice\\AI练习',rows:[row('web-record.json','json',true)],field:'learning-record',bind:'file'}]},
    'deepseek-api':{title:'API 学习 · 先预览，再在终端单次同意',steps:[python(),{title:'先保存请求预览',tip:'先在本页展开实际请求预览、核对目的地与内容，再保存 api-preview.json。',path:'D:\\课航工具',rows:[row('task.json','json'),row('api-preview.json','json',true)],field:'api-preview-path',bind:'file'},run('终端单次确认',['实际调用只在本人终端预览、单次确认并隐藏输入密钥后发送。','此处不展示真实密钥，也不会发送请求。','未取得实际响应时，不能写成 API 运行通过。'],'api-send')]},
    'dsh-desktop':{title:'DSH 桌面 · 软件、专用目录与真实工具记录',steps:[{title:'找到桌面程序',tip:'选择 DeepSeek Harness.exe 程序本体，不是快捷方式。采集器不启动 DSH。',path:'C:\\DSH',rows:[row('resources','folder'),row('DeepSeek Harness.exe','exe',true)],field:'target',bind:'file'},work(),evidence()]},
    'dsh-cli':{title:'DSH CLI · Node 与 DSH 包身份都要明确',steps:[{title:'选择课程 Node',tip:'选择运行 DSH CLI 的实际 node.exe；不要混用另一环境的 Node。',path:'C:\\Node',rows:[row('node.exe','exe',true),row('node_modules','folder')],field:'target',bind:'file'},{title:'选择 DSH 包定义',tip:'选择所用 @deepseek-ai/dsh 包内的 package.json，不是你自己练习项目的 package.json。',path:'C:\\DSH\\node_modules\\@deepseek-ai\\dsh',rows:[row('package.json','json',true),row('bin','folder')],field:'dsh-package',bind:'file'},work(),evidence()]}
  };
  function course(host,scenario,fields,key){
    const guide=catalog[scenario];if(!guide){host.hidden=true;return;}
    let steps=guide.steps;const vmware=scenario==='vm-linux'&&/vmrun\.exe$/i.test(clean(fields.target));
    if(vmware)steps=[{...steps[0],path:'C:\\Program Files\\VMware',rows:[row('vmrun.exe','exe',true)]},run('确认 VMware 实例',['在 VMware 中核对这台虚拟机的实际 .vmx 配置文件路径。','把同一 .vmx 完整路径填到本页实例标识。','不是系统名称，也不是其他虚拟机的路径。'],'vm-id'),steps[2]];
    host.dataset.course=scenario;mount(host,scenario+':'+key+':'+vmware,guide.title,steps,fields);
  }
  function report(host){
    host.replaceChildren(explorer({title:'课航工具',path:'你解压的课航工具文件夹',rows:[{name:'task.json',kind:'json'},{name:'report-A.json',kind:'json',id:'report-earlier-file',hidden:true},{name:'report-A.json',kind:'json',selected:true,labelId:'report-example-file'}]}));
  }
  function reportPath(host,path,stage){host.querySelector('.win11-address-text').textContent=path||'你解压的课航工具文件夹';host.firstChild.setAttribute('aria-label','Windows 11 报告位置示意：找到 report-'+stage+'.json；不是文件扫描结果');}
  function practice(host,submit=false){
    const steps=submit?[{title:'找到自己的成果',tip:'完成 Notebook 与 SQLite 练习后，选择同一解压目录生成的实训成果.json；成果模板不是最终成果。',path:'你解压的实训资料文件夹',rows:[row('成果模板.json','json'),row('notebook-result.json','json'),row('实训成果.json','json',true)],field:'practice-submission',action:'去选择实训成果'}]:[
      {title:'打开完整资料',tip:'完整解压到新文件夹。Notebook、CSV 与 SQLite 练习放在同一目录。',path:'你解压的实训资料文件夹',rows:[row('scores.csv','csv'),row('01_Notebook练习.ipynb','notebook',true),row('02_SQLite练习.py','script'),row('成果模板.json','json')]},
      {title:'完成 Notebook',tip:'在已有 Jupyter 打开 Notebook，选择已确认的课程内核，填写 TODO 后逐格运行。',path:'你解压的实训资料文件夹',rows:[row('01_Notebook练习.ipynb','notebook',true),row('scores.csv','csv'),row('notebook-result.json','json')]},
      {title:'运行 SQLite 练习',tip:'编辑模板中的固定 SELECT，再用同一课程 Python 主动运行。按程序实际输出检查数据库与成果。',path:'你解压的实训资料文件夹',rows:[row('02_SQLite练习.py','script',true),row('scores.sqlite','database'),row('实训成果.json','json')]}
    ];mount(host,submit?'practice-submit':'practice-work',submit?'看图找到要提交的文件':'连续实训 · 按文件顺序跟做',steps);
  }
  function extensions(host){host.append(explorer({title:'课航工具',path:'你解压的课航工具文件夹',rows:[row('task.json','json'),row('report-A.json','json',true)],menu:true}));}
  return Object.freeze({course,report,reportPath,practice,extensions,scenarios:Object.freeze(Object.keys(catalog))});
})();
KehangVisuals.report(document.getElementById('report-explorer-window'));
KehangVisuals.extensions(document.getElementById('report-extension-window'));
KehangVisuals.practice(document.getElementById('practice-visual-guide'));
KehangVisuals.practice(document.getElementById('practice-submit-guide'),true);
