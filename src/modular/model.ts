export type Axis='row'|'column';
export type Node={id:string;kind:'group'|'metric';name:string;visible:boolean;axis:Axis;gap:number;padding:number;align:'start'|'center'|'end';selfAlign:'auto'|'start'|'center'|'end';scale:number;color:string;background:string;opacity:number;outline:boolean;children:Node[];token:string;width:number;height:number};
export type Layout={schema:'claw-modular-layout';version:1;anchor:string;x:number;y:number;root:Node};
export const anchors=['top-left','top-center','top-right','bottom-left','bottom-center','bottom-right','center-left','center-right'];
export const catalog:Record<string,string>={
 'fps.label':'FPS label','fps.value':'FPS value','fps.ms':'Frametime','fps.average':'Average FPS','fps.low1':'1% low',
 'cpu.label':'CPU label','cpu.load':'CPU load','cpu.temp':'CPU temperature','cpu.clock':'CPU clock','cpu.power':'CPU power',
 'gpu.label':'GPU label','gpu.load':'GPU load','gpu.temp':'GPU temperature','gpu.clock':'GPU clock','gpu.power':'GPU power','gpu.junction':'GPU junction','gpu.fan':'GPU fan','gpu.voltage':'GPU voltage',
 'ram.label':'RAM label','ram.value':'RAM usage','ram.game':'Game RAM','ram.swap':'SWAP','vram.label':'VRAM label','vram.value':'VRAM usage','vram.temp':'VRAM temperature','vram.clock':'VRAM clock',
 'battery.label':'Battery label','battery.value':'Battery charge','battery.time':'Battery time','battery.power':'Power draw','time.value':'Clock','tdp.value':'TDP','graph':'Frametime graph','separator':'Separator line'};
let serial=0;
export const uid=()=>`n-${Date.now().toString(36)}-${++serial}`;
export function node(kind:Node['kind'],name:string,extra:Partial<Node>={}):Node{return {id:uid(),kind,name,visible:true,axis:'row',gap:8,padding:0,align:'center',selfAlign:'auto',scale:100,color:'',background:'',opacity:85,outline:false,children:[],token:'fps.value',width:180,height:44,...extra}}
export const metric=(token:string,extra:Partial<Node>={})=>node('metric',catalog[token]||token,{token,...(token==='separator'?{width:160,height:2}:{}),...extra});
export const group=(name:string,children:Node[],extra:Partial<Node>={})=>node('group',name,{children,...extra});
export function find(root:Node,id:string):Node|undefined{if(root.id===id)return root;for(const c of root.children){const found=find(c,id);if(found)return found}}
export function parent(root:Node,id:string):Node|undefined{if(root.children.some(c=>c.id===id))return root;for(const c of root.children){const found=parent(c,id);if(found)return found}}
export function flatten(root:Node):Node[]{return [root,...root.children.flatMap(flatten)]}
export function move(layout:Layout,id:string,targetId:string,index?:number):Layout{
 const out=structuredClone(layout),item=find(out.root,id),target=find(out.root,targetId),from=parent(out.root,id);
 if(!item||!target||!from||target.kind!=='group'||find(item,targetId))return layout;
 from.children=from.children.filter(n=>n.id!==id);target.children.splice(index??target.children.length,0,item);return out;
}
// Keep the readings in their existing row while giving the graph its own row.
export function placeGraphBelow(layout:Layout,id:string):Layout{
 const out=structuredClone(layout),graphNode=find(out.root,id);
 if(graphNode?.kind!=='metric'||graphNode.token!=='graph')throw new Error('Select a frametime graph.');
 // The footer should finish at the edge of the readings row, regardless of
 // how many CPU/GPU fields the user has enabled.
 graphNode.width=0;
 const graphParent=parent(out.root,id);
 if(!graphParent)throw new Error('Graph has no parent group.');
 let container:Node=graphParent;
 container.children=container.children.filter(child=>child.id!==id);
 while(container!==out.root&&container.children.length===0){
  const ancestor:Node=parent(out.root,container.id)!;
  ancestor.children=ancestor.children.filter(child=>child.id!==container.id);
  container=ancestor;
 }
 if(out.root.axis==='row'){
  const readings=group('Readings',out.root.children,{axis:'row',align:out.root.align,gap:out.root.gap,padding:0});
  out.root.children=[readings];
  out.root.axis='column';
  out.root.align='start';
  out.root.gap=8;
 }
 graphNode.selfAlign='start';
 out.root.children.push(graphNode);
 return validate(out);
}
export function isHorizontalLayout(layout:Layout):boolean{
 const {root}=layout;
 return root.axis==='row'||(root.axis==='column'&&root.children.length===2&&root.children[0].kind==='group'&&root.children[0].axis==='row'&&root.children[1].kind==='metric'&&root.children[1].token==='graph');
}
const tokens=(...keys:string[])=>keys.map(k=>metric(k));
const cpu=(s?:any)=>group('CPU',tokens('cpu.label','cpu.load',...(!s||s.metrics.cpu_temp?['cpu.temp']:[]),...(!s||s.metrics.cpu_mhz?['cpu.clock']:[]),...(!s||s.metrics.cpu_power?['cpu.power']:[])));
const gpu=(s?:any)=>group('GPU',tokens('gpu.label','gpu.load',...(!s||s.metrics.gpu_temp?['gpu.temp']:[]),...(!s||s.metrics.gpu_core_clock?['gpu.clock']:[]),...(!s||s.metrics.gpu_power?['gpu.power']:[])));
export function preset(kind:string,s:any):Layout{
 const fps=group('FPS',tokens('fps.label','fps.value'),{gap:8});fps.children[1].scale=200;
 let children:Node[],axis:Axis='row';
 if(kind==='two-rows')children=[fps,group('System & graphics',[group('System row',[cpu(),metric('tdp.value'),metric('battery.power')],{gap:20}),group('Graphics row',[gpu(),group('RAM',tokens('ram.label','ram.value')),group('VRAM',tokens('vram.label','vram.value')),metric('graph',{width:110,height:28})],{gap:20})],{axis:'column',align:'start',gap:8})];
 else if(kind==='graph-focus'){axis='column';children=[group('Performance',[group('Frame rate',[fps,metric('fps.ms')],{axis:'column',align:'start'}),metric('graph',{width:520,height:70})],{gap:24}),group('Readings',[cpu(),gpu(),metric('tdp.value'),metric('battery.power')],{gap:20})]}
 else {axis=kind==='vertical'?'column':'row';const map:Record<string,()=>Node>={fps:()=>group('FPS',tokens('fps.label','fps.value',...(s.metrics?.fps_ms?['fps.ms']:[]),...(s.metrics?.fps_average?['fps.average']:[]),...(s.metrics?.fps_low1?['fps.low1']:[]))),cpu:()=>cpu(s),gpu:()=>gpu(s),ram:()=>group('RAM',tokens('ram.label','ram.value',...(s.metrics?.ram_game?['ram.game']:[]),...(s.metrics?.ram_swap?['ram.swap']:[]))),vram:()=>group('VRAM',tokens('vram.label','vram.value')),battery:()=>group('Battery',tokens('battery.label','battery.value',...(s.metrics?.battery_time?['battery.time']:[]))),tdp:()=>metric('tdp.value'),draw:()=>metric('battery.power'),time:()=>metric('time.value'),frametime:()=>metric('graph',{width:s.graph_width||150,height:44})};children=(s.order||Object.keys(map)).filter((k:string)=>s[k]&&map[k]&&(k!=='frametime'||s.metrics?.graph)).map((k:string)=>map[k]());}
 return {schema:'claw-modular-layout',version:1,anchor:'top-center',x:16,y:20,root:group('Overlay',children,{axis,gap:16,padding:14})};
}
export function validate(input:any):Layout{
 if(input?.schema!=='claw-modular-layout'||input.version!==1||!anchors.includes(input.anchor))throw new Error('Expected a modular layout v1 file.');
 const ids=new Set<string>();let count=0;
 const number=(v:any,min:number,max:number)=>{if(typeof v!=='number'||!Number.isFinite(v)||v<min||v>max)throw new Error('Invalid numeric layout value.');return v};
 const color=(v:any)=>{if(typeof v!=='string'||(v!==''&&!/^#[\da-fA-F]{6}$/.test(v)))throw new Error('Invalid color.');return v};
 const visit=(v:any,depth:number):Node=>{
  if(++count>96||depth>8)throw new Error('Limit: 96 elements and 8 nesting levels.');
  if(!v||typeof v.id!=='string'||v.id.length>100||ids.has(v.id)||!['group','metric'].includes(v.kind)||typeof v.name!=='string'||v.name.length>80||typeof v.visible!=='boolean'||!['row','column'].includes(v.axis)||!['start','center','end'].includes(v.align)||!['auto','start','center','end'].includes(v.selfAlign??'auto')||typeof v.outline!=='boolean'||!Array.isArray(v.children))throw new Error('Invalid element or duplicate ID.');
  ids.add(v.id);if(v.kind==='metric'&&(!catalog[v.token]||v.children.length))throw new Error('Invalid metric.');
  const widthMin=v.kind==='metric'&&v.token==='graph'?0:40;
  return {id:v.id,kind:v.kind,name:v.name,visible:v.visible,axis:v.axis,align:v.align,selfAlign:v.selfAlign??'auto',outline:v.outline,token:v.kind==='metric'?v.token:'fps.value',gap:number(v.gap,0,80),padding:number(v.padding,0,80),scale:number(v.scale,50,250),color:color(v.color),background:color(v.background),opacity:number(v.opacity,0,100),width:number(v.width,widthMin,1000),height:number(v.height,v.token==='separator'?1:16,240),children:v.children.map((c:any)=>visit(c,depth+1))};
 };
 const root=visit(input.root,0);if(root.kind!=='group')throw new Error('Root must be a group.');
 return {schema:'claw-modular-layout',version:1,anchor:input.anchor,x:number(input.x,0,2000),y:number(input.y,input.anchor.startsWith('center-')?-2000:0,2000),root};
}

