'use strict';
// Only server-issued target IDs cross back to the fixed collector service.
const KehangTargets=(()=>{
  let taskId='',serial=0,fields={},selected={},loading=false;
  const status=text=>$('local-target-status').textContent=text;
  function render(){
    const host=$('local-target-fields');host.replaceChildren();
    for(const [field,meta] of Object.entries(fields)){
      const row=document.createElement('div');row.className='local-target-row';
      const label=document.createElement('label'),select=document.createElement('select'),browse=document.createElement('button');
      select.id='local-field-'+field;select.dataset.field=field;label.htmlFor=select.id;label.textContent=meta.label;
      const empty=document.createElement('option');empty.value='';empty.textContent=meta.required?'请选择…':'暂不选择';select.append(empty);
      for(const choice of meta.choices){const option=document.createElement('option');option.value=choice.id;option.textContent=choice.path;option.title=choice.source;select.append(option);}
      select.value=selected[field]||'';select.disabled=localState.running;
      select.addEventListener('change',()=>{selected[field]=select.value;status('选择已更新；还没有开始检测。');});
      browse.type='button';browse.className='secondary';browse.textContent=meta.kind==='folder'||meta.kind==='jdk'?'选择目录…':'选择文件…';browse.disabled=localState.running;
      browse.addEventListener('click',()=>action(browse,async()=>{
        const requestSerial=serial,navigation=guided.navigationEpoch;
        status('请在本机文件窗口选择，或点击取消。');
        const result=await localAPI('/api/local-check/pick',{task:state.task,field});
        if(requestSerial!==serial||navigation!==guided.navigationEpoch)return;
        if(!result.selected){status('已取消选择；未开始检测。');return;}
        if(!meta.choices.some(item=>item.id===result.selected.id))meta.choices.push(result.selected);
        selected[field]=result.selected.id;render();$('local-field-'+field).focus();status('已选择；点击“开始本机检测”后才运行。');
      }));
      const controls=document.createElement('div');controls.className='local-target-controls';controls.append(select,browse);row.append(label,controls);host.append(row);
      if(meta.required&&!meta.choices.length){const hint=document.createElement('p');hint.className='muted';hint.textContent='尚未选择。可查找候选，或用文件窗口选择。';row.append(hint);}
    }
  }
  async function sync(){
    if(!state.task||!state.config||taskId===state.task.id)return;
    taskId=state.task.id;const requestSerial=++serial;fields={};selected={};loading=true;render();
    for(const id of ['local-gpu','local-infer','local-host-only'])$(id).checked=false;
    $('local-vm-uuid').value='';
    $('local-gpu-option').hidden=state.task.scenario!=='pytorch-gpu';$('local-infer-option').hidden=state.task.scenario!=='local-qwen';$('local-vm-option').hidden=state.task.scenario!=='vm-linux';
    status('正在读取本课程的选择项…');
    try{
      const config=await localAPI('/api/local-check/options',{task:state.task});if(requestSerial!==serial)return;
      fields=config.fields;$('local-scope').textContent=config.note;render();status('');
    }catch(error){if(requestSerial===serial){taskId='';status(error.message);}}
    finally{if(requestSerial===serial)loading=false;}
  }
  $('local-discover').addEventListener('click',event=>action(event.target,async()=>{
    const requestSerial=serial,navigation=guided.navigationEpoch;status('正在查找登记、PATH 或标准目录中的候选…');
    const result=await localAPI('/api/local-check/discover',{task:state.task});
    if(requestSerial!==serial||navigation!==guided.navigationEpoch)return;
    for(const [field,meta] of Object.entries(result.fields)){
      for(const item of fields[field]?.choices||[])if(!meta.choices.some(choice=>choice.id===item.id))meta.choices.push(item);
    }
    fields=result.fields;render();const count=Object.values(fields).reduce((n,meta)=>n+meta.choices.length,0);
    status(count?'已找到候选，请确认本课程使用的目标。候选不代表检查通过。':'未发现候选，不代表没有安装。请用文件窗口选择，或查看准备指引。');
  }));
  function request(){
    if(loading)throw Error('选择项正在读取，请稍候。');
    const selections=Object.fromEntries(Object.entries(selected).filter(([,value])=>value));
    // Preserve the existing Python multi-environment discovery path as an option.
    if(state.task.scenario==='python-basics'&&!selections.target)return {};
    for(const [field,meta] of Object.entries(fields))if(meta.required&&!selections[field]){document.getElementById('local-field-'+field)?.focus();throw Error('请先选择'+meta.label);}
    const options={};
    if(state.task.scenario==='pytorch-gpu')options.gpu_run=$('local-gpu').checked;
    if(state.task.scenario==='local-qwen')options.infer=$('local-infer').checked;
    if(state.task.scenario==='vm-linux'){options.vm_uuid=$('local-vm-uuid').value.trim();options.host_only=$('local-host-only').checked;}
    return {selections,options};
  }
  sync();return Object.freeze({sync,request,render});
})();
