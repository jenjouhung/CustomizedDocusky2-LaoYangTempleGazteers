import {parse,search,intersect} from './query.js';
import {filter} from './facets.js';
export class State {
 constructor(index,facets,count){this.index=index;this.facets=facets;this.count=count;this.reset()}
 reset(){this.queries=[];this.conditions={};this.page=1}
 base(){let ids=new Set(Array.from({length:this.count},(_,i)=>i));for(const q of this.queries)ids=intersect(ids,q.ids);return ids}
 results(){return filter(this.base(),this.conditions,this.facets)}
 query(source){const ast=parse(source);if(ast.type==='all')return;const ids=search(ast,this.index,this.count);const count=intersect(this.results(),ids).size;this.queries.push({source,ast,ids,count});this.page=1}
 apply(field,values){if(values.length)this.conditions[field]=values;else delete this.conditions[field];this.page=1}
}
