export function bubbleScale(items,width,zoom=100){
 const positive=items.filter(item=>item.count>0),sum=positive.reduce((n,item)=>n+item.count,0),max=Math.max(1,...positive.map(item=>item.count)),w=Math.max(320,Number(width)||960),z=Math.max(.1,Math.min(2,Number(zoom)/100||1));
 if(!positive.length)return {nodes:[],zeros:items,scale:0};
 const maxRadius=Math.min(140,w*.115),areaBudget=w*w*.36;
 const scale=Math.min(Math.PI*maxRadius*maxRadius/max,areaBudget/Math.max(1,sum));
 return {nodes:positive.map(item=>({...item,r:Math.sqrt(scale*item.count/Math.PI)*z})),zeros:items.filter(item=>item.count<=0),scale};
}
export function packBubbles(items,width,zoom=100,gap=8){
 const {nodes,zeros,scale}=bubbleScale(items,width,100);
 if(!nodes.length)return {nodes,zeros,width:Math.max(320,width||960),height:240,scale};
 // Place tangent circles along the cluster's outer chain, choosing the
 // next edge nearest the centre. Padding participates in collision checks.
 const circles=nodes.map(node=>({node,r:node.r+gap/2,x:0,y:0}));
 const place=(a,b,c)=>{const dx=b.x-a.x,dy=b.y-a.y,d2=dx*dx+dy*dy,ar=a.r+c.r,br=b.r+c.r;if(!d2){c.x=a.x+ar;c.y=a.y;return}const t=(d2+ar*ar-br*br)/(2*d2),h=Math.sqrt(Math.max(0,ar*ar/d2-t*t));c.x=a.x+t*dx+h*dy;c.y=a.y+t*dy-h*dx};
 const link=c=>({c,next:null,prev:null});
 const hit=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y)<a.r+b.r-1e-7;
 const score=n=>{const a=n.c,b=n.next.c,s=a.r+b.r;return ((a.x*b.r+b.x*a.r)/s)**2+((a.y*b.r+b.y*a.r)/s)**2};
 if(circles.length>1){
  circles[0].x=-circles[1].r;circles[1].x=circles[0].r;
  if(circles.length>2){
   place(circles[0],circles[1],circles[2]);let a=link(circles[0]),b=link(circles[1]),c=link(circles[2]);a.next=c;c.prev=a;c.next=b;b.prev=c;b.next=a;a.prev=b;
   outer:for(let i=3;i<circles.length;i++){
    const current=circles[i];place(a.c,b.c,current);c=link(current);let j=b.next,k=a.prev,sj=b.c.r,sk=a.c.r;
    do{if(sj<=sk){if(hit(j.c,current)){b=j;a.next=b;b.prev=a;i--;continue outer}sj+=j.c.r;j=j.next}else{if(hit(k.c,current)){a=k;a.next=b;b.prev=a;i--;continue outer}sk+=k.c.r;k=k.prev}}while(j!==k.next);
    c.prev=a;c.next=b;a.next=b.prev=c;let best=score(a),candidate=c.next;while(candidate!==c){const value=score(candidate);if(value<best){a=candidate;best=value}candidate=candidate.next}b=a.next;
   }
  }
 }
 const z=Math.max(.1,Math.min(2,Number(zoom)/100||1)),padding=18,minX=Math.min(...circles.map(c=>c.x-c.r)),maxX=Math.max(...circles.map(c=>c.x+c.r)),minY=Math.min(...circles.map(c=>c.y-c.r)),maxY=Math.max(...circles.map(c=>c.y+c.r));
 const side=Math.max(maxX-minX,maxY-minY)+padding*2,cx=(minX+maxX)/2,cy=(minY+maxY)/2;
 for(const c of circles){c.node.x=(c.x-cx+side/2)*z;c.node.y=(c.y-cy+side/2)*z;c.node.r*=z}
 return {nodes,zeros,width:side*z,height:side*z,scale};
}
export function bubbleLevel(count,min,max,steps=6){if(max<=min)return steps-1;return Math.max(0,Math.min(steps-1,Math.floor((count-min)/(max-min)*steps)))}
export function bubbleLabel(label,radius,fontScale=1){
 const growth=Math.max(.55,Math.min(1.5,Number(fontScale)||1)),chars=Array.from(String(label)),size=Math.max(9,Math.min(42,Math.max(14,Math.min(28,radius*.22))*growth)),countSize=Math.max(9,Math.min(44,Math.max(14,Math.min(30,radius*.24))*growth));
 if(radius<30)return {lines:[],size,countSize,startY:0,lineHeight:size*1.08,countY:5};
 const maxLines=radius>=76?3:radius>=45?2:1,capacity=Math.max(2,Math.floor(radius*1.55/size)),lines=[];
 for(let i=0;i<Math.min(chars.length,capacity*maxLines);i+=capacity)lines.push(chars.slice(i,i+capacity).join(''));
 if(chars.length>capacity*maxLines){const last=lines.length-1;lines[last]=Array.from(lines[last]).slice(0,Math.max(1,capacity-1)).join('')+'…'}
 const lineHeight=size*1.08,totalHeight=lines.length*lineHeight+countSize*1.15+Math.max(5,size*.25),startY=-totalHeight/2+size*.82,countY=startY+(lines.length-1)*lineHeight+countSize*1.2;
 return {lines,size,countSize,startY,lineHeight,countY};
}
