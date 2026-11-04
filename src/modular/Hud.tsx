import React from 'react';
import type {Layout,Node} from './model';
const weights:any={light:300,regular:400,semibold:600,bold:700};
// Match the native renderer's reserved reading widths so alignment and spacing
// do not change when sample values are shorter than live values.
const slots:Record<string,string>={'fps.value':'888','fps.ms':'888.8 ms','cpu.load':'100%','cpu.temp':'888°C','cpu.clock':'8888 MHz','cpu.power':'88.8 W','gpu.load':'100%','gpu.temp':'888°C','gpu.clock':'8888 MHz','gpu.power':'88.8 W','gpu.junction':'888°C Jnc','gpu.fan':'88888 RPM','gpu.voltage':'8888 mV','ram.value':'888.8 GiB','vram.value':'888.8 GiB','vram.temp':'888°C','vram.clock':'8888 MHz','battery.value':'100%','battery.time':'88:88','time.value':'88:88','fps.average':'AVG 8888.8','fps.low1':'1% LOW 8888.8','ram.game':'GAME 888.8 GiB','ram.swap':'SWAP 888.8 GiB'};
export const initialData={fps:84,ms:11.9,average:81,low1:62,cpu:36,cpuTemp:54,cpuClock:3500,cpuPower:8.6,gpu:72,gpuTemp:52,gpuClock:1750,gpuPower:12.4,ram:12.6,gameRam:3.2,swap:0.4,vram:7.4,battery:79,draw:27,tdp:28};
export function rgba(hex:string,opacity:number){const c=(hex||'161820').replace('#','');return `rgba(${parseInt(c.slice(0,2),16)},${parseInt(c.slice(2,4),16)},${parseInt(c.slice(4,6),16)},${opacity/100})`}
export function backgroundStyle(s:any):React.CSSProperties{
 const b=s.background,stops=b.stops.map((p:any)=>`${rgba(p.color,s.opacity)} ${p.position}%`).join(',');
 return {background:b.mode==='linear'?`linear-gradient(${b.angle}deg,${stops})`:b.mode==='radial'?`radial-gradient(circle ${b.radius*2}px at ${b.center_x}% ${b.center_y}%,${stops})`:rgba(b.color,s.opacity),borderRadius:s.rounding,boxShadow:b.outline_enabled?`inset 0 0 0 ${b.outline_width}px ${rgba(b.outline_color,b.outline_opacity)}`:undefined};
}
export function Graph({width,height,color,kind}:{width:number;height:number;color:string;kind:string}){
 const pts=Array.from({length:61},(_,i)=>[i*5,49+Math.sin(i*.71)*5+Math.cos(i*.23)*10+(i===31?-15:0)]);
 const smooth=kind==='smooth'||kind==='dual_layer';
 const points=smooth?pts.flatMap((p,i)=>i===pts.length-1?[p]:Array.from({length:4},(_,j)=>{
  const a=pts[Math.max(0,i-1)][1],b=p[1],c=pts[i+1][1],d=pts[Math.min(pts.length-1,i+2)][1],t=j/4;
  return [p[0]+5*t,.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)];
 })):pts;
 const line='M'+points.map(p=>p.join(',')).join(' L'),area=line+' L300,80 L0,80 Z';
 let average=points[0][1];const layer='M'+points.map(([x,y])=>{average=.85*average+.15*y;return `${x},${average}`}).join(' L');
 return <svg width={width} height={height} viewBox="0 0 300 80" preserveAspectRatio="none" aria-label="Simulated frametime graph">
 {kind==='bars'?pts.map(([x,y],i)=><rect key={i} x={x} y={y} width="4" height={80-y} fill={color}/>):<>
 {['area','dual','dual_layer'].includes(kind)&&<path d={area} fill={color} fillOpacity={kind==='area'?1:kind==='dual'?.22:.14}/>}
 {kind==='dual_layer'&&<path d={layer} fill="none" stroke={color} strokeOpacity={.43} strokeWidth="1" vectorEffect="non-scaling-stroke"/>}
 <path d={line} fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke"/></>}
 </svg>
}
export function ModularHud({layout,settings:s,data:d,selected,onSelect,editing=true}:{layout:Layout;settings:any;data:any;selected:string;onSelect:(id:string)=>void;editing?:boolean}){
 const values:any={'fps.value':d.fps,'fps.ms':`${d.ms} ms`,'fps.average':`AVG ${d.average}`,'fps.low1':`1% LOW ${d.low1}`,'cpu.load':`${d.cpu}%`,'cpu.temp':`${d.cpuTemp}°C`,'cpu.clock':`${d.cpuClock} MHz`,'cpu.power':`${d.cpuPower} W`,'gpu.load':`${d.gpu}%`,'gpu.temp':`${d.gpuTemp}°C`,'gpu.clock':`${d.gpuClock} MHz`,'gpu.power':`${d.gpuPower} W`,'gpu.junction':'68°C','gpu.fan':'2800 RPM','gpu.voltage':'850 mV','ram.value':`${d.ram} GiB`,'ram.game':`GAME ${d.gameRam} GiB`,'ram.swap':`SWAP ${d.swap} GiB`,'vram.value':`${d.vram} GiB`,'vram.temp':'58°C','vram.clock':'900 MHz','battery.value':`${d.battery}%`,'battery.time':'02:15','battery.power':`${s.custom_labels?.draw||'DRAW'} ${d.draw} W`,'tdp.value':`${s.custom_labels?.tdp||'TDP'} ${d.tdp} W`,'time.value':'22:15'};
 const labels:any={fps:'FPS',cpu:'CPU',gpu:'GPU',ram:'RAM',vram:'VRAM',battery:'BATT'};
 function render(n:Node,root=false,parentAlignment:'start'|'center'|'end'='start',parentAxis:'row'|'column'='row'):React.ReactNode{
  if(!n.visible)return null;
  const [category,part]=n.token.split('.');
  const palette=n.token==='fps.label'?'fps_label':n.token==='fps.value'?'fps_value':n.token==='battery.power'?'draw':n.token==='tdp.value'?'tdp':n.token==='time.value'?'time':n.token==='graph'?'graph':part==='label'?category:'text';
  const color=n.color||'#'+(s.token_colors?.[n.token]||s.colors[palette]||s.colors.text);
  const base:React.CSSProperties={position:'relative',flexShrink:0,display:'flex',alignSelf:n.selfAlign==='start'?'flex-start':n.selfAlign==='end'?'flex-end':n.selfAlign==='center'?'center':undefined,alignItems:n.align==='start'?'flex-start':n.align==='end'?'flex-end':'center',gap:n.gap,padding:n.padding,fontSize:`${n.scale/100}em`,borderRadius:root?s.rounding:6,...(root?backgroundStyle(s):{}),...(n.background?{background:rgba(n.background,n.opacity)}:{}),...(n.outline?{boxShadow:'inset 0 0 0 1px #8fb8d9'}:{}),outline:editing&&selected===n.id?'1px dashed #78b5ff':undefined,outlineOffset:3};
  const props:any={'data-node-id':n.id,onClick:(e:React.MouseEvent)=>{if(editing){e.stopPropagation();onSelect(n.id)}},style:base};
  if(n.kind==='group')return <div key={n.id} {...props} className="hud-node hud-group-node" style={{...base,flexDirection:n.axis}}>{n.children.map(c=>render(c,false,n.axis==='column'?n.align:'start',n.axis))}{editing&&!n.children.length&&<span className="empty-group">{n.name} · empty</span>}</div>;
  const value=part==='label'?(s.custom_labels?.[category]||labels[category]):values[n.token]??'--';
  const alignment=parentAxis==='column'&&n.selfAlign!=='auto'?n.selfAlign:parentAlignment;
  return <div key={n.id} {...props} className="hud-node hud-metric" style={{...base,color,fontWeight:s.sans?(weights[s.token_weights?.[n.token]||s.font_weight]||400):400,fontSize:`${n.scale/100}em`}}>{n.token==='graph'?<Graph width={n.width} height={n.height} color={color} kind={s.graph_style}/>:n.token==='separator'?<span style={{display:'block',width:n.width,height:n.height,background:color}}/>:slots[n.token]?<><span aria-hidden="true" style={{visibility:'hidden'}}>{slots[n.token]}</span><span style={{position:'absolute',left:n.padding,right:n.padding,textAlign:alignment}}>{value}</span></>:value}</div>
 }
 const bottom=layout.anchor.startsWith('bottom'),right=layout.anchor.endsWith('right'),center=layout.anchor.endsWith('center');
 return s.enabled?<div className="modular-hud" style={{position:'absolute',top:bottom?undefined:layout.y,bottom:bottom?layout.y:undefined,left:center?'50%':right?undefined:layout.x,right:right?layout.x:undefined,transform:center?`translateX(calc(-50% + ${layout.x}px))`:undefined,fontSize:s.fontsize,fontFamily:s.sans?'ClawPreviewBarlow':'ClawPreviewSans',fontWeight:s.sans?(weights[s.font_weight]||400):400,lineHeight:1.2}}>{render(layout.root,true)}</div>:null;
}

