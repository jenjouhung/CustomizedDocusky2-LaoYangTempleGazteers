import test from 'node:test';
import assert from 'node:assert/strict';
import {State} from '../web/core/state.js';
import {counts} from '../web/core/facets.js';
import {fields,fieldLabel} from '../web/core/facet-fields.js';

test('Tag 與 Metadata 交集、同類 OR、文件計數及去除屬性搜尋',()=>{
 const texts=['比丘尼道揚、道積','道揚','道積'], index={};
 texts.forEach((text,id)=>Array.from(text).forEach((ch,pos)=>((index[ch]??={})[id]??=[]).push(pos)));
 const facets={'17':{'"比丘尼"':[0]},'tag:person':{'"揚法師"':[0,1],'"積法師"':[0,2]}};
 const state=new State(index,facets,3);
 state.apply('tag:person',['"揚法師"','"積法師"']);assert.equal(state.results().size,3);
 state.apply('17',['"比丘尼"']);assert.deepEqual([...state.results()],[0]);
 assert.equal(counts(state.base(),state.conditions,facets,'tag:person')[0].count,1);
 state.query('比丘尼道揚');assert.deepEqual([...state.results()],[0]);
 state.query('揚法師');assert.equal(state.results().size,0);
 state.reset();state.query('NOT 揚法師');assert.equal(state.results().size,3);
});
test('Tag 自訂名稱與舊版無 Tag 設定',()=>{
 const c={facets:[0],headers:['人名'],tagFacets:[{name:'person',label:'標記人名'},{name:'place',label:''}]};
 assert.equal(fieldLabel(c,'tag:person'),'Tag：標記人名');
 assert.equal(fieldLabel(c,'0'),'Metadata：人名');
 assert.equal(fields(c,'Tag')[1].label,'place');
 assert.deepEqual(fields({...c,tagFacets:undefined},'Tag'),[]);
});
