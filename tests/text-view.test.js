import test from 'node:test';
import assert from 'node:assert/strict';
import {segments} from '../web/core/text-view.js';
test('Tag位置、非BMP字元、跨界搜尋及同Term不同類別',()=>{
 const parsed={text:'𠮷道揚道揚尾',tags:[{name:'person',term:'法師',start:1,end:3},{name:'other',term:'法師',start:3,end:5}]};
 const parts=segments(parsed,['𠮷道','揚道揚'],{'tag:person':['"法師"']});
 assert.equal(parts.map(x=>x.text).join(''),parsed.text);
 assert.equal(parts.filter(x=>x.active).map(x=>x.text).join(''),'道揚');
 assert.equal(parts.filter(x=>x.hit).map(x=>x.text).join(''),'𠮷道揚道揚');
 assert.equal(parts.filter(x=>x.tag).map(x=>x.text).join(''),'道揚道揚');
 assert(!segments(parsed,[],{}) .some(x=>x.active));
});
test('僅標記來源區間、多類別與多值同時加強',()=>{
 const parsed={text:'甲甲乙丙',tags:[{name:'a',term:'甲',start:0,end:1},{name:'a',term:'乙',start:2,end:3},{name:'b',term:'丙',start:3,end:4}]};
 const parts=segments(parsed,[],{'tag:a':['"甲"','"乙"'],'tag:b':['"丙"']});
 assert.equal(parts.filter(x=>x.active).map(x=>x.text).join(''),'甲乙丙');
 assert.equal(parts.filter(x=>!x.tag).map(x=>x.text).join(''),'甲');
});
