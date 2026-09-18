// Tag positions use Unicode code points; browser search positions use UTF-16.
export function segments(parsed, terms=[], conditions={}) {
 const text=parsed.text??'', offsets=[0];
 for(const char of text) offsets.push(offsets.at(-1)+char.length);
 const tags=(parsed.tags||[]).map(t=>({...t,start:offsets[t.start],end:offsets[t.end]}));
 const hits=[];
 for(const term of new Set(terms.filter(Boolean))){
  for(let p=text.indexOf(term);p!==-1;p=text.indexOf(term,p+1))hits.push([p,p+term.length]);
 }
 const boundaries=new Set([0,text.length]);
 for(const t of tags){boundaries.add(t.start);boundaries.add(t.end)}
 for(const [a,b] of hits){boundaries.add(a);boundaries.add(b)}
 const points=[...boundaries].sort((a,b)=>a-b),out=[];
 for(let i=0;i<points.length-1;i++){
  const start=points[i],end=points[i+1],tag=tags.find(t=>t.start<=start&&t.end>=end);
  const active=!!tag&&(conditions['tag:'+tag.name]||[]).some(v=>JSON.parse(v)===tag.term);
  out.push({text:text.slice(start,end),tag:!!tag,active,hit:hits.some(([a,b])=>a<=start&&b>=end)});
 }
 return out;
}

export function renderText(parsed, terms, conditions){
 const p=document.createElement('p');p.className='text';
 for(const part of segments(parsed,terms,conditions)){
  if(!part.tag&&!part.hit){p.append(document.createTextNode(part.text));continue}
  const node=document.createElement(part.hit?'mark':'span');
  node.className=[part.tag?'tag-text':'',part.active?'tag-active':'',part.hit?'search-hit':''].filter(Boolean).join(' ');
  node.textContent=part.text;p.append(node);
 }
 return p;
}
