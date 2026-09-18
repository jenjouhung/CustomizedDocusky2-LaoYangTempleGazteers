import {json,loadVersion,compareVersions} from './core/data.js';
import {State} from './core/state.js';
import {counts,filter,label,sortIDs,sortFacets} from './core/facets.js';
import {positiveTerms} from './core/query.js';
import {fields,fieldLabel} from './core/facet-fields.js';
import {renderText} from './core/text-view.js';
import {Visualization} from './visualization.js';
const $=s=>document.querySelector(s),el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n};
let manifest,data,state,field,local=null,renderID=0;
let drafts={},facetSort={};
let facetType='Metadata', lastField={};
const visualization=new Visualization({
 getContext:()=>{const applied=state.conditions[field]||[];let items=counts(state.base(),state.conditions,data.facets,field);if(applied.length)items=items.filter(x=>applied.includes(x.value));const option=fields(data.config,facetType).find(x=>x.id===field);return {key:`${data.meta.id}:${field}`,version:data.meta.id,type:facetType==='Tag'?'內文標籤':'後設資料',field:field,name:option?.label||field,items,documentTotal:filter(state.base(),state.conditions,data.facets,field).size,sort:facetSort[field]||'count-desc'}},
 onClose:()=>$('#visualize').focus()
});
const typeButtons=[...document.querySelectorAll('#facet-type [role="tab"]')];
const fieldHeading=el('div',undefined,'facet-field-heading'),fieldHeadingLabel=document.querySelector('label[for="field"]'),visualizeButton=$('#visualize'),visualizeIcon=el('span',undefined,'visualize-icon');
visualizeIcon.setAttribute('aria-hidden','true');visualizeIcon.append(el('i'),el('i'),el('i'));fieldHeadingLabel.before(fieldHeading);fieldHeading.append(fieldHeadingLabel,visualizeButton);visualizeButton.prepend(visualizeIcon);
function showFacetType(){for(const control of typeButtons){const selected=control.dataset.type===facetType;control.setAttribute('aria-selected',String(selected));control.tabIndex=selected?0:-1}}
function chooseFields(){const options=fields(data.config,facetType);field=options.some(f=>f.id===lastField[facetType])?lastField[facetType]:(options[0]?.id||'');$('#field').replaceChildren(...options.map(f=>{const o=el('option',f.label);o.value=f.id;return o}));$('#field').value=field;$('#field').disabled=!options.length;}
function selectFacetType(next){if(next===facetType)return;lastField[facetType]=field;facetType=next;showFacetType();chooseFields();facets()}
for(const control of typeButtons){control.onclick=()=>selectFacetType(control.dataset.type);control.onkeydown=e=>{if(!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();const offset=e.key==='ArrowRight'?1:-1,index=typeButtons.indexOf(control),next=typeButtons[(index+offset+typeButtons.length)%typeButtons.length];selectFacetType(next.dataset.type);next.focus()}}
$('#result-count').append($('#count'));
function pending(){const draft=drafts[field]||state.conditions[field]||[], applied=state.conditions[field]||[];$('#facet-actions').hidden=draft.length===applied.length&&draft.every(v=>applied.includes(v))}
function message(text=''){$('#message').textContent=text}
function button(text,fn){const b=el('button',text);b.onclick=()=>Promise.resolve(fn()).catch(e=>message(e.message));return b}
function highlight(parsed){return renderText(parsed,state.queries.flatMap(q=>positiveTerms(q.ast)),state.conditions)}
const legend=el('div',undefined,'text-legend');legend.setAttribute('aria-label','全文標示圖例');
for(const [name,cls] of [['一般 Tag','tag-text'],['已套用 Tag','tag-text tag-active'],['搜尋命中','search-hit']])legend.append(el('span',name,cls));
$('.result-toolbar').after(legend);
function openDialog(title){$('#dialog-body').replaceChildren(el('h2',title));if(!$('#dialog').open)$('#dialog').showModal();return $('#dialog-body')}
async function selectVersion(id){const loaded=await loadVersion(id);data=loaded;state=new State(data.index,data.facets,data.meta.count);drafts={};facetSort={};lastField={};facetType='Metadata';showFacetType();chooseFields();$('#title').textContent=data.config.title;document.title=data.config.title;$('#version-label').textContent=`${manifest.current===id?'現行版本':'瀏覽封存版本'} ${id} · ${data.meta.count} 筆`;
 $('#query').value='';message();await render();}
function facets(){
 const list=$('#facet-values');list.replaceChildren();
 const applied=state.conditions[field]||[],mode=facetSort[field]||'count-desc';$('#facet-sort').value=mode;
 let items=counts(state.base(),state.conditions,data.facets,field);
 if(applied.length)items=items.filter(x=>applied.includes(x.value));
 for(const item of sortFacets(items,mode)){
  const row=el('div',undefined,'facet'),check=el('input');check.type='checkbox';check.value=item.value;check.checked=(drafts[field]||applied).includes(item.value);
  check.onchange=()=>{const selected=new Set(drafts[field]||applied);if(check.checked)selected.add(item.value);else selected.delete(item.value);drafts[field]=[...selected];pending()};
  const lab=el('label');lab.append(check,document.createTextNode(' '+label(item.value)));
  row.append(lab,button(String(item.count),()=>{delete drafts[field];state.apply(field,[item.value]);return render()}));list.append(row);
 }
 const hasItems=items.length>0;$('#visualize').disabled=!hasItems;$('#visualize').setAttribute('aria-label',hasItems?`視覺化：${fields(data.config,facetType).find(x=>x.id===field)?.label||field}`:'目前欄位沒有可視覺化項目');
 if(!list.childNodes.length)list.append(el('p',facetType==='Tag'&&!Object.keys(data.facets).some(f=>f.startsWith('tag:'))?'此版本無內文標籤後分類':'此條件下沒有可用分類值'));
 pending();
}
async function render(){const generation=++renderID;message();const ids=sortIDs(state.results(),data.rows,data.config),total=ids.length;state.page=Math.min(state.page,Math.max(1,Math.ceil(total/data.config.pageSize)));$('#count').textContent=`${total} 筆`;$('form label').textContent=state.queries.length||Object.keys(state.conditions).length?'再查詢':'全文查詢';const chips=$('#conditions');chips.replaceChildren();
 state.queries.forEach((q,i)=>chips.append(el('span',`Q${i+1}：${q.source}（該輪 ${q.count} 筆）`,'chip')));
 for(const [f,values] of Object.entries(state.conditions)){const name=fieldLabel(data.config,f),source=f.startsWith('tag:')?'內文標籤':'後設資料';const b=button(`${source}：`+values.map(v=>`{${name}} = ${label(v)}`).join(' OR ')+' ×',()=>{delete drafts[f];state.apply(f,[]);return render()});b.className='chip';chips.append(b)}facets();
 const container=$('#records');container.replaceChildren(el('p','讀取全文…'));const page=ids.slice((state.page-1)*data.config.pageSize,state.page*data.config.pageSize);const rows=await Promise.all(page.map(async n=>{const [raw,parsed]=await Promise.all([data.record(n),data.text(n)]);return {raw,parsed}}));if(generation!==renderID)return;container.replaceChildren();
rows.forEach(({raw:r,parsed})=>{const article=el('article',undefined,'record');article.append(el('h2',String(r[data.config.titleField]??'')));const meta=el('div',undefined,'metadata');for(const f of data.config.display.filter(f=>![data.config.text,data.config.titleField].includes(f)))meta.append(el('span',`${data.config.headers[f].split('(')[0]}：${r[f]??'（空白）'}`));article.append(meta,highlight(parsed),button(`查看全部 ${data.config.headers.length} 個欄位`,()=>{const body=openDialog(String(r[data.config.titleField]));body.append(el('p',`${data.meta.id} · ${r[data.config.key]}`));data.config.headers.forEach((name,f)=>{const row=el('div',undefined,'detail-row');row.append(el('strong',name),f===data.config.text?highlight(parsed):document.createTextNode(r[f]===null?'（空白）':String(r[f])));if(f===data.config.text){const raw=el('details');raw.append(el('summary','原始標記全文'),el('p',String(r[f]??''),'text'));row.append(raw)}body.append(row)})}));container.append(article)});
 if(!total){const empty=el('div',undefined,'empty');empty.append(el('h2','目前條件沒有符合資料'),el('p','已保留查詢條件。可移除後分類條件或重新查詢。'),button('重新查詢',reset));container.append(empty)}
 const pages=Math.max(1,Math.ceil(total/data.config.pageSize)),nav=$('#pagination');nav.replaceChildren();const go=n=>{state.page=n;return render()};for(const [name,n,disabled] of [['第一頁',1,state.page===1],['上一頁',state.page-1,state.page===1]]){const b=button(name,()=>go(n));b.disabled=disabled;nav.append(b)}nav.append(el('span',`${state.page} / ${pages}`));for(let n=Math.max(1,state.page-1);n<=Math.min(pages,state.page+1);n++){const b=button(String(n),()=>go(n));b.className='page-number';if(n===state.page)b.setAttribute('aria-current','page');nav.append(b)}for(const [name,n,disabled] of [['下一頁',state.page+1,state.page===pages],['最後一頁',pages,state.page===pages]]){const b=button(name,()=>go(n));b.disabled=disabled;nav.append(b)}container.scrollTop=0;
}
function reset(){drafts={};state.reset();$('#query').value='';return render()}
async function manage(action,payload={}){if(!local)throw new Error('此操作僅提供於單機版');message('處理中，請稍候…');const r=await fetch('/manage/'+action,{method:'POST',headers:{'Content-Type':'application/json','X-Local-Token':local.token},body:JSON.stringify(payload)});const result=await r.json();if(!r.ok)throw new Error(result.error);return result}
async function versions(){const body=openDialog('資料版本');for(const v of manifest.versions){const row=el('div',undefined,'version-row');row.append(el('span',`${v.id} · ${v.count} 筆 · ${v.created} ${v.id===manifest.current?'（現行）':''}`),button('瀏覽',async()=>{await selectVersion(v.id);$('#dialog').close()}),button('驗證紀錄',()=>{const b=openDialog(v.id+' 匯入驗證');b.append(el('p',v.source),el('p',`工作表：${v.sheet}`),el('p',`SHA-256：${v.sha256}`));for(const w of v.warnings)b.append(el('p',w));if(!v.warnings.length)b.append(el('p','無警告'))}));if(local)row.append(button('設為現行版',async()=>{await manage('current',{version:v.id});await init()}));body.append(row)}
 const a=el('select'),b=el('select');for(const v of manifest.versions){for(const s of [a,b]){const o=el('option',v.id);o.value=v.id;s.append(o)}}b.value=data.meta.id;body.append(el('h3','版本差異比較'),a,b,button('比較',async()=>{const box=openDialog('版本比較中…');const [old,latest]=await Promise.all([loadVersion(a.value),loadVersion(b.value)]);const result=await compareVersions(old,latest);box.replaceChildren(el('h2',`${a.value} → ${b.value}`),el('p',`新增 ${result.added.length} · 刪除 ${result.removed.length} · 修改 ${result.changed.length}`));for(const [type,ids] of [['新增',result.added],['刪除',result.removed]])box.append(el('p',`${type}：${ids.join('、')||'無'}`));for(const [f,n] of Object.entries(result.fields))box.append(el('p',`${old.config.headers[f]}：${n} 筆變更`));for(const item of result.changed){box.append(el('h3',item.id));for(const c of item.changes)box.append(el('p',`${c.field}\n前：${c.before??'（空白）'}\n後：${c.after??'（空白）'}`,'diff'))}}));}
$('#close-dialog').onclick=()=>$('#dialog').close();$('#query-form').onsubmit=async e=>{e.preventDefault();try{state.query($('#query').value);await render()}catch(err){message(err.message)}};$('#clear-input').onclick=()=>{$('#query').value=''};$('#reset').onclick=reset;$('#field').onchange=()=>{field=$('#field').value;facets()};$('#apply').onclick=()=>{state.apply(field,[...document.querySelectorAll('#facet-values input:checked')].map(x=>x.value));render()};$('#clear-facets').onclick=()=>{state.conditions={};state.page=1;render()};$('#versions').onclick=()=>versions().catch(e=>message(e.message));
async function init(){manifest=await json('data/manifest.json');await selectVersion(manifest.current)}
$('#facet-sort').onchange=()=>{facetSort[field]=$('#facet-sort').value;facets()};
$('#visualize').onclick=()=>visualization.open();
$('#apply').onclick=()=>{state.apply(field,drafts[field]||state.conditions[field]||[]);delete drafts[field];render()};
$('#cancel-facets').onclick=()=>{delete drafts[field];facets()};
$('#clear-facets').onclick=()=>{drafts={};state.conditions={};state.page=1;render()};
$('#admin-menu').addEventListener('click',e=>{if(e.target.closest('button'))$('#admin').open=false});
document.addEventListener('click',e=>{if(!$('#admin').contains(e.target))$('#admin').open=false});
document.addEventListener('keydown',e=>{if(e.key==='Escape')$('#admin').open=false});
$('#admin').addEventListener('focusout',()=>setTimeout(()=>{if(!$('#admin').contains(document.activeElement))$('#admin').open=false},0));
const splitter=$('#splitter'),workspace=$('.workspace');
function resizePane(width){const max=Math.min(workspace.clientWidth/2,workspace.clientWidth-540),n=Math.max(280,Math.min(max,width));workspace.style.setProperty('--facet-width',n+'px');splitter.setAttribute('aria-valuenow',Math.round(n))}
splitter.onpointerdown=e=>{splitter.setPointerCapture(e.pointerId);splitter.onpointermove=move=>resizePane(move.clientX-workspace.getBoundingClientRect().left);splitter.onpointerup=()=>{splitter.onpointermove=null}};
splitter.onkeydown=e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();resizePane($('aside').clientWidth+(e.key==='ArrowRight'?20:-20))}};
window.addEventListener('unhandledrejection',e=>{message(e.reason?.message||String(e.reason));e.preventDefault()});
try{if(['localhost','127.0.0.1'].includes(location.hostname)){try{local=await json('/local-info')}catch{}}
 if(local)for(const [id,action] of [['import','import'],['backup','backup'],['restore-backup','restore-backup'],['build','build'],['stop','stop']]){$('#'+id).hidden=false;$('#'+id).onclick=async()=>{try{const result=await manage(action);if(['import','restore-backup'].includes(action)&&!result.cancelled)await init();message(result.message||'操作完成')}catch(e){message(e.message)}}}
 if(local){$('#versions').textContent='版本管理';const b=button('更新程式',async()=>{const result=await manage('update');message(result.message)});$('#admin-menu').append(b)}
 await init();}catch(e){message(e.message)}
