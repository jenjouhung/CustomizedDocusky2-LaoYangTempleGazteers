// Parser and positional index search. No DOM or dataset-specific field names.
export function parse(source) {
  const tokens=[]; let i=0;
  const fail=(message,pos=i)=>{throw new Error(`${message}（位置 ${pos+1}）`)};
  while(i<source.length){
    if(/\s/u.test(source[i])){i++;continue}
    const pos=i; let value='',literal=false;
    if('()'.includes(source[i])){tokens.push({type:source[i++],pos});continue}
    if(source[i]==='"'){
      literal=true;i++;let closed=false;
      while(i<source.length){if(source[i]==='"'){i++;closed=true;break}if(source[i]==='\\'){i++;if(i===source.length)fail('跳脫字元缺少對象')}value+=source[i++]}
      if(!closed)fail('雙引號未閉合',pos);if(!value)fail('查詢詞不可為空',pos);
    }else{
      while(i<source.length&&!/[\s()]/u.test(source[i])){
        if(source[i]==='"')fail('引號須位於查詢詞開頭');
        if(source[i]==='\\'){literal=true;i++;if(i===source.length)fail('跳脫字元缺少對象')}
        value+=source[i++];
      }
    }
    tokens.push({type:!literal&&/^(AND|OR|NOT)$/i.test(value)?value.toUpperCase():'term',value,pos});
  }
  if(!tokens.length)return {type:'all'};
  let p=0;const peek=t=>tokens[p]?.type===t;
  function atom(){const t=tokens[p++];if(!t)fail('缺少查詢詞',source.length);if(t.type==='term')return t;if(t.type==='NOT')return {type:'NOT',child:atom()};if(t.type==='('){const n=or();if(!peek(')'))fail('括號未閉合',t.pos);p++;return n}fail('此處需要查詢詞',t.pos)}
  function and(){let n=atom();while(peek('AND')){p++;n={type:'AND',left:n,right:atom()}}return n}
  function or(){let n=and();while(peek('OR')){p++;n={type:'OR',left:n,right:and()}}return n}
  const ast=or();if(p<tokens.length)fail('缺少 AND 或 OR',tokens[p].pos);return ast;
}
export const intersect=(a,b)=>new Set([...a].filter(x=>b.has(x)));
export function search(ast,index,count){
  const all=()=>new Set(Array.from({length:count},(_,i)=>i));
  if(ast.type==='all')return all();
  if(ast.type==='term'){
    const chars=Array.from(ast.value),first=index[chars[0]]||{},out=new Set();
    for(const [id,positions] of Object.entries(first)){
      if(positions.some(start=>chars.every((ch,k)=>(index[ch]?.[id]||[]).includes(start+k))))out.add(+id);
    }return out;
  }
  if(ast.type==='NOT'){const b=search(ast.child,index,count);return new Set([...all()].filter(x=>!b.has(x)))}
  const a=search(ast.left,index,count),b=search(ast.right,index,count);
  return ast.type==='AND'?intersect(a,b):new Set([...a,...b]);
}
export function positiveTerms(ast,neg=false){if(ast.type==='term')return neg?[]:[ast.value];if(ast.type==='NOT')return positiveTerms(ast.child,!neg);return ast.left?[...positiveTerms(ast.left,neg),...positiveTerms(ast.right,neg)]:[]}
