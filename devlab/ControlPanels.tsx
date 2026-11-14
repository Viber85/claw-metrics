import React,{useState} from 'react';
import {anchors,catalog,flatten,isGraph,group,metric,validate,type Layout,type Node} from '../src/modular/model';
import {ClassicSeparators} from './ClassicSeparators';
import {serializeDesign} from '../src/modular/design';

const weights=['light','regular','semibold','bold'];
const tones=(key:string)=>key.split('_').join(' ').split('.').join(' · ');
const card=(title:string,children:React.ReactNode,open=false)=><details className="lab-panel" open={open||undefined}><summary>{title}</summary><div className="lab-body">{children}</div></details>;

export type NamedStyle={name:string;design:string};
export function ControlPanels({layout,settings,styles,onLayout,onSettings,onStyles,onMessage}:{layout:Layout;settings:any;styles:Record<string,NamedStyle>;onLayout:(l:Layout)=>void;onSettings:(s:any)=>void;onStyles:(styles:Record<string,NamedStyle>)=>void;onMessage:(s:string)=>void}){
 const [token,T]=useState('fps.average'),[styleName,N]=useState('My overlay'),[selectedStyle,Selected]=useState(''),[filter,Filter]=useState('');
 const patch=(v:any)=>onSettings({...settings,...v});
 const patchBackground=(v:any)=>patch({background:{...settings.background,...v}});
 const editLayout=(edit:(draft:Layout)=>void)=>{try{const draft=structuredClone(layout);edit(draft);onLayout(validate(draft))}catch(e){onMessage(String(e))}};
 const activeStyle=styles[selectedStyle]?selectedStyle:Object.keys(styles)[0]||'';
 const all=flatten(layout.root);
 const included=new Set(all.filter(n=>n.kind==='metric').map(n=>n.token));
 const groupVisibility=(id:string,visible:boolean)=>editLayout(d=>{const node=flatten(d.root).find(n=>n.id===id);if(node)node.visible=visible});
 const addToken=()=>{if(included.has(token)){onMessage('Reading already exists; use the Builder to move it.');return}
   editLayout(d=>{const root=d.root; const prefix=token.split('.')[0];let target=root.children.find(n=>n.kind==='group'&&n.name.toLowerCase()===prefix);
   if(!target){target=group(prefix.toUpperCase(),[],{axis:'column',align:'start',gap:4});root.children.push(target)}
   target.children.push(metric(token));});onMessage('Reading added. Continue editing it in Layout Builder.')};
 const swap=(id:string,dir:number)=>editLayout(d=>{const list=d.root.children;const i=list.findIndex(n=>n.id===id);if(i<0||i+dir<0||i+dir>=list.length)return;[list[i],list[i+dir]]=[list[i+dir],list[i]]});
 const saveStyle=()=>{const name=styleName.trim().slice(0,24);if(!name){onMessage('Enter a style name.');return}
   const id='local-'+Date.now();onStyles({...styles,[id]:{name,design:serializeDesign(layout,settings)}});Selected(id);onMessage('Style saved locally in this browser. Export JSON to transfer it to your handheld.')};
 const loadStyle=()=>{const item=styles[activeStyle];if(!item)return;try{const design=JSON.parse(item.design);onSettings(design.appearance);onLayout(validate(design.layout));onMessage('Saved browser style loaded. Export JSON to transfer it.') }catch(e){onMessage(String(e))}};
 const colorInput=(key:string,value:string,update:(value:string)=>void)=><label className="lab-field" key={key}><span>{tones(key)}</span><input type="color" aria-label={tones(key)+' color'} value={'#'+value} onChange={e=>update(e.target.value.slice(1).toUpperCase())}/></label>;
 const range=(name:string,value:number,min:number,max:number,change:(v:number)=>void)=><label className="lab-field"><span>{name}: <b>{value}</b></span><input aria-label={name} type="range" min={min} max={max} value={value} onChange={e=>change(+e.target.value)}/></label>;
 const select=(name:string,value:string,options:string[],change:(v:string)=>void)=><label className="lab-field"><span>{name}</span><select aria-label={name} value={value} onChange={e=>change(e.target.value)}>{options.map(option=><option key={option} value={option}>{tones(option)}</option>)}</select></label>;
 return <section className="lab-panels" aria-label="DevLab controls">
 {card('Overlay & Layout',<div className="lab-grid">
  {select('Screen position',layout.anchor,anchors,v=>editLayout(d=>{d.anchor=v;if(v.startsWith('center-')&&d.y< -2000)d.y=0}))}
  {range('X offset',layout.x,0,2000,v=>editLayout(d=>{d.x=v}))}
  {range('Y offset',layout.y,layout.anchor.startsWith('center-')?-2000:0,2000,v=>editLayout(d=>{d.y=v}))}
  {select('Orientation',layout.root.axis,['row','column'],v=>editLayout(d=>{d.root.axis=v as Node['axis']}))}
  {range('Group spacing',layout.root.gap,0,240,v=>editLayout(d=>{d.root.gap=v}))}
  {range('Overlay horizontal padding',layout.paddingX??0,0,160,v=>editLayout(d=>{d.paddingX=v}))}
  {range('Overlay vertical padding',layout.paddingY??0,0,160,v=>editLayout(d=>{d.paddingY=v}))}
  {range('Corner radius',settings.rounding,0,1000,v=>patch({rounding:v}))}
  {range('Background opacity',settings.opacity,0,100,v=>patch({opacity:v}))}
  {select('Frametime graph style',settings.graph_style,['line','area','bars','dual','smooth','dual_layer'],v=>patch({graph_style:v}))}
  <label className="lab-field"><span>Superscript units</span><input type="checkbox" checked={settings.unit_superscript} onChange={e=>patch({unit_superscript:e.target.checked})}/></label>
 </div>)}
 {card('Classic separators',<ClassicSeparators settings={settings} onChange={patch}/>)}
 {card('Metrics & Order',<><p className="lab-note">Toggle groups or individual readings. Use arrows to reorder top-level groups. Readings can be moved between groups in the Builder.</p>
  <div className="lab-metrics">{layout.root.children.map((n,i)=><div key={n.id} className="lab-metric-row"><label><input type="checkbox" checked={n.visible} onChange={e=>groupVisibility(n.id,e.target.checked)}/><b>{n.name}</b></label><div><button aria-label={'Move '+n.name+' earlier'} disabled={i===0} onClick={()=>swap(n.id,-1)}>↑</button><button aria-label={'Move '+n.name+' later'} disabled={i===layout.root.children.length-1} onClick={()=>swap(n.id,1)}>↓</button></div></div>)}</div>
  <div className="lab-token-list">{all.filter(n=>n.kind==='metric').map(n=><label key={n.id}><input type="checkbox" checked={n.visible} onChange={e=>groupVisibility(n.id,e.target.checked)}/>{catalog[n.token]||n.name}</label>)}</div>
  <div className="lab-add">{select('Add reading',token,Object.keys(catalog).filter(k=>!included.has(k)).length?Object.keys(catalog).filter(k=>!included.has(k)):[token],T)}<button onClick={addToken} disabled={included.has(token)}>Add reading</button></div>
 </>)}
 {card('Colors & Fonts',<><div className="lab-grid">
  {range('Global font size',settings.fontsize,12,28,v=>patch({fontsize:v}))}
  {select('Global font weight',settings.font_weight,weights,v=>patch({font_weight:v}))}
  <label className="lab-field"><span>Use bundled font</span><input type="checkbox" checked={settings.sans} onChange={e=>patch({sans:e.target.checked})}/></label>
  {select('Background mode',settings.background.mode,['solid','linear','radial'],v=>patchBackground({mode:v}))}
  {colorInput('Background',settings.background.color,v=>patchBackground({color:v}))}
  {settings.background.mode==='linear'&&range('Gradient angle',settings.background.angle,0,360,v=>patchBackground({angle:v}))}
  {settings.background.mode!=='solid'&&settings.background.stops.map((s:any,i:number)=><React.Fragment key={i}>{colorInput('Gradient stop '+(i+1),s.color,(value)=>patchBackground({stops:settings.background.stops.map((x:any,k:number)=>k===i?{...x,color:value}:x)}))}</React.Fragment>)}
  <label className="lab-field"><span>Background outline</span><input type="checkbox" checked={settings.background.outline_enabled} onChange={e=>patchBackground({outline_enabled:e.target.checked})}/></label>
  {settings.background.outline_enabled&&<>{colorInput('Outline',settings.background.outline_color,v=>patchBackground({outline_color:v}))}{range('Outline thickness',settings.background.outline_width,1,6,v=>patchBackground({outline_width:v}))}{range('Outline opacity',settings.background.outline_opacity,0,100,v=>patchBackground({outline_opacity:v}))}</>}
 </div><h4>Category palette</h4><div className="lab-colors">{Object.entries(settings.colors).map(([key,value])=>colorInput(key,value as string,v=>patch({colors:{...settings.colors,[key]:v}})))}</div>
 <h4>Individual metric colors and font weights</h4><label className="lab-field"><span>Filter</span><input value={filter} placeholder="Search metrics..." onChange={e=>Filter(e.target.value)}/></label>
 <div className="lab-tokens">{Object.entries(catalog).filter(([key,label])=>!isGraph(key)&&key!=='separator'&&(key+' '+label).toLowerCase().includes(filter.toLowerCase())).map(([key,label])=><div className="lab-token-row" key={key}><span>{label}</span>{colorInput('Override',settings.token_colors[key]||settings.colors[key.split('.')[0]]||settings.colors.text,v=>patch({token_colors:{...settings.token_colors,[key]:v}}))}{select('Weight',settings.token_weights[key]||'inherit',['inherit',...weights],v=>{const next={...settings.token_weights};if(v==='inherit')delete next[key];else next[key]=v;patch({token_weights:next})})}<button onClick={()=>{const colors={...settings.token_colors},weights={...settings.token_weights};delete colors[key];delete weights[key];patch({token_colors:colors,token_weights:weights})}}>Reset</button></div>)}</div>
 <h4>Custom category labels</h4><div className="lab-grid">{Object.entries({fps:'FPS',cpu:'CPU',gpu:'GPU',ram:'RAM',vram:'VRAM',battery:'Battery',draw:'DRAW',tdp:'TDP'}).map(([key,name])=><label className="lab-field" key={key}><span>{name}</span><input maxLength={24} value={settings.custom_labels[key]||''} placeholder={name} onChange={e=>{const next={...settings.custom_labels};const v=Array.from(e.target.value).filter(c=>c.charCodeAt(0)>=32&&c.charCodeAt(0)!==127&&c!=='='&&c!==',').join('').slice(0,24);if(v.trim())next[key]=v;else delete next[key];patch({custom_labels:next})}}/></label>)}</div>
 </>)}
 {card('Saved Styles',<><p className="lab-note">Browser styles are local presets. To transfer a design to the device, use Export JSON in the Builder.</p>
  <div className="lab-add"><label className="lab-field"><span>Style name</span><input maxLength={24} value={styleName} onChange={e=>N(e.target.value)}/></label><button onClick={saveStyle}>Save current style</button></div>
  <div className="lab-add">{select('Saved styles',activeStyle,Object.keys(styles),Selected)}<button disabled={!styles[activeStyle]} onClick={loadStyle}>Load</button><button disabled={!styles[activeStyle]} onClick={()=>{const next={...styles};delete next[activeStyle];onStyles(next);Selected(Object.keys(next)[0]||'')}}>Delete</button></div>
  {Object.keys(styles).length>0&&<label className="lab-field"><span>Rename selected style</span><input value={styles[activeStyle]?.name||''} onChange={e=>{if(!styles[activeStyle])return;onStyles({...styles,[activeStyle]:{...styles[activeStyle],name:e.target.value.slice(0,24)}})}}/></label>}
 </>)}
 {card('Device & Diagnostics (simulated)',<p className="lab-note">Activation commands, native renderer, Decky controller navigation, TDP readback and system diagnostics require a real SteamOS / Decky backend. No live device controls are available in the browser.</p>)}
 </section>;
}
