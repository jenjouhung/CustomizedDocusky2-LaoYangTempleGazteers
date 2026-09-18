import {label,sortFacets} from './facets.js';

export function normalizeSearch(value){return String(value??'').toLocaleLowerCase()}
export function prepareItems(items,query='',sort='count-desc'){
 const term=normalizeSearch(query);
 return sortFacets(items,sort).map(item=>({...item,label:label(item.value),matched:!term||normalizeSearch(label(item.value)).includes(term)}));
}
export function zoomRowHeight(zoom){const n=Math.max(10,Math.min(200,Number(zoom)||100));return 12+(n-10)*.4}
export function zoomLabelSize(zoom){const n=Math.max(10,Math.min(200,Number(zoom)||100));return Math.round((12+(n-10)*.08)*100)/100}
export function tableRowHeight(zoom){const n=Math.max(10,Math.min(200,Number(zoom)||100));return Math.round((28+(n-10)*48/190)*100)/100}
export function tableFontSize(zoom){const n=Math.max(10,Math.min(200,Number(zoom)||100));return Math.round((12+(n-10)*8/190)*100)/100}
export function prepareTableRows(items,total){
 let cumulative=0;
 return items.map((item,index)=>{cumulative+=item.count;return {...item,rank:index+1,proportion:total>0?item.count/total*100:null,cumulative:total>0?cumulative/total*100:null}})
}
export function formatPercent(value){if(value===null||!Number.isFinite(value))return '—';if(value>0&&value<.1)return '<0.1%';return `${value.toFixed(1)}%`}
function csvCell(value){let text=String(value??'');if(/^[=+\-@]/.test(text))text="'"+text;return /[",\r\n]/.test(text)?`"${text.replaceAll('"','""')}"`:text}
export function tableCSV(rows){return '\ufeff'+[['序號','類別名稱','文件數','比例','累積比例'],...rows.map(row=>[row.rank,row.label,row.count,formatPercent(row.proportion),formatPercent(row.cumulative)])].map(row=>row.map(csvCell).join(',')).join('\r\n')+'\r\n'}
export class VisualizationState{
 constructor(){this.source=null;this.view='bar';this.search='';this.sort='count-desc';this.paletteByView={};this.selected=new Set();this.zoom={bar:100,bubble:100,table:100}}
 get palette(){return this.paletteByView[this.view]||'pine'}
 set palette(value){this.paletteByView[this.view]=value}
 ensurePalette(view=this.view,random=Math.random){if(!this.paletteByView[view]){const used=new Set(Object.entries(this.paletteByView).filter(([key])=>key!==view).map(([,value])=>value)),all=['pine','ochre','indigo','moss'],choices=all.filter(value=>!used.has(value));this.paletteByView[view]=choices[Math.floor(random()*choices.length)%choices.length]}return this.paletteByView[view]}
 setSource(source,preferredSort='count-desc'){if(this.source===source)return;this.source=source;this.view='bar';this.search='';this.sort=['count-desc','title-asc'].includes(preferredSort)?preferredSort:'count-desc';this.selected.clear();this.zoom={bar:100,bubble:100,table:100}}
 toggle(value){this.selected.has(value)?this.selected.delete(value):this.selected.add(value)}
 clearSelection(){this.selected.clear()}
}
