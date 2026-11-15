'use strict';
const KehangExtensions = (()=>{
  const legacy=new Set(['dsh-desktop','dsh-cli','deepseek-api','ai-web-deepseek','local-qwen']);
  let selected=null, catalog=null, pending=null;
  function node(tag,text){const element=document.createElement(tag);element.textContent=text;return element;}
  function link(title,url){const a=node('a',title);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;}
  function current(){return selected;}
  function render(){
    const guide=catalog.guides.find(item=>item.id===selected);
    $('extensions-title').textContent=guide?guide.title:'拓展工具';
    $('extensions-intro').textContent=guide?guide.summary:'按需要选择安装、配置或使用指南';
    $('extension-back').hidden=!guide;
    $('extension-list').hidden=!!guide;
    $('extension-guide').hidden=!guide;
    $('extension-guide').replaceChildren();
    if(!guide)return;
    $('extension-guide').append(node('p',guide.version));
    const layout=document.createElement('div');layout.className='extension-content';
    const nav=document.createElement('nav');nav.setAttribute('aria-label','本指南目录');
    const article=document.createElement('div');
    guide.sections.forEach((item,i)=>{
      const id='extension-section-'+i;
      const a=node('a',item.title);a.href='#'+id;nav.append(a);
      const section=document.createElement('section');section.id=id;
      const title=node('h2',item.title);title.tabIndex=-1;section.append(title);
      for(const text of item.paragraphs)section.append(node('p',text));
      if(item.code){const pre=node('pre',item.code);pre.tabIndex=0;pre.setAttribute('aria-label',item.title+'参考代码');section.append(pre);}
      article.append(section);
    });
    layout.append(nav,article);$('extension-guide').append(layout);
    const sources=document.createElement('section');sources.className='extension-sources';
    sources.append(node('h2','参考来源'),node('p','核对日期：'+catalog.checked+' · '+(guide.id==='kehang-ai'?'课航源码与官方接口资料':'官方资料核查；本轮未实际安装或调用')));
    for(const [title,url] of guide.sources)sources.append(url.startsWith('https://')?link(title,url):node('p',title+'：'+url.slice(6)));
    $('extension-guide').append(sources);
  }
  async function load(){
    if(catalog)return;
    if(!pending)pending=api('/api/extensions').then(value=>{catalog=value;}).finally(()=>{pending=null;});
    await pending;
    const list=$('extension-list');list.replaceChildren();
    for(const group of [...new Set(catalog.guides.map(item=>item.group))]){
      const section=document.createElement('section');section.append(node('h2',group));
      for(const guide of catalog.guides.filter(item=>item.group===group)){
        const button=document.createElement('button');button.type='button';button.className='option-row';button.dataset.extension=guide.id;
        const copy=document.createElement('span');copy.append(node('strong',guide.title),node('small',guide.summary));
        const arrow=node('span','→');arrow.setAttribute('aria-hidden','true');button.append(copy,arrow);
        button.addEventListener('click',()=>open(guide.id));section.append(button);
      }
      list.append(section);
    }
  }
  async function open(id=null){
    selected=id;
    showRoute('extensions');
    $('extensions-intro').textContent='正在读取指南…';
    $('extension-guide').hidden=true;$('extension-list').hidden=true;
    const epoch=guided.navigationEpoch;
    try{
      await load();
      if(epoch!==guided.navigationEpoch)return;
      if(id&&!catalog.guides.some(item=>item.id===id))throw Error('未找到对应指南');
      render();document.dispatchEvent(new Event('kehang-context'));$('extensions-title').focus({preventScroll:true});
    }catch(error){if(epoch===guided.navigationEpoch){$('extensions-intro').textContent='指南读取失败，可重新点击拓展工具重试。';notice(error.message,true);}}
  }
  $('extensions-nav').addEventListener('click',()=>open());
  $('start-extensions').addEventListener('click',()=>open());
  $('extension-back').addEventListener('click',()=>open());
  $('extensions-course').addEventListener('click',()=>showRoute('selection'));
  $('chat-setup-guide').addEventListener('click',()=>open('kehang-ai'));
  const fromURL=new URLSearchParams(location.search).get('extension');
  if(fromURL)queueMicrotask(()=>open(fromURL));
  return {open,current,isLegacy:id=>legacy.has(id)};
})();
