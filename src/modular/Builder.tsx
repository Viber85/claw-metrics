import {useEffect,useRef,useState, type ReactNode} from 'react';
import {ConfirmModal,DialogButton,DropdownItem,Focusable,TextField,ToggleField,showModal} from '@decky/ui';
import {OpaqueColorPicker} from '../controller';
import {LayoutSliderField} from '../components/LayoutSliderField';
import {ModularHud,initialData} from './Hud';
import {anchors,catalog,find,flatten,group,metric,move,parent,validate,type Layout,type Node} from './model';

export function Builder({initial,settings,onApply,closeModal}:{initial:Layout;settings:any;onApply:(doc:Layout)=>void;closeModal?:()=>void}) {
 const [layout,L]=useState(()=>validate(initial)),[selected,S]=useState(initial.root.id),[token,T]=useState('fps.average'),[past,P]=useState<Layout[]>([]),[future,F]=useState<Layout[]>([]),[error,E]=useState(''),[guides,G]=useState(true);
 const stage=useRef<HTMLDivElement>(null),[zoom,Z]=useState(.2);
 useEffect(()=>{const element=stage.current;if(!element)return;const resize=()=>Z(element.clientWidth/1280);const observer=new ResizeObserver(resize);observer.observe(element);resize();return()=>observer.disconnect()},[]);
 const active=find(layout.root,selected)||layout.root,all=flatten(layout.root),owner=parent(layout.root,active.id);
 const commit=(next:Layout)=>{try{const valid=validate(next);if(JSON.stringify(valid)===JSON.stringify(layout))return;P([...past.slice(-39),layout]);F([]);L(valid);E('')}catch(e){E(String(e))}};
 const patch=(values:Partial<Node>)=>{const next=structuredClone(layout);Object.assign(find(next.root,active.id)!,values);commit(next)};
 const add=(kind:'group'|'metric')=>{const next=structuredClone(layout),target=find(next.root,active.kind==='group'?active.id:owner!.id)!;const child=kind==='group'?group('New group',[],{padding:4}):metric(token);target.children.push(child);commit(next);S(child.id)};
 const shift=(delta:number)=>{if(owner){const index=owner.children.findIndex(n=>n.id===active.id)+delta;if(index>=0&&index<owner.children.length)commit(move(layout,active.id,owner.id,index))}};
 const button=(label:string,fn:()=>void,disabled=false)=><DialogButton disabled={disabled} onClick={fn} style={{minWidth:0,width:'100%',whiteSpace:'normal'}}>{label}</DialogButton>;
 const select=(label:string,value:string,options:{data:string;label:string}[],fn:(s:string)=>void)=><DropdownItem label={label} selectedOption={value} rgOptions={options} onChange={o=>fn(String(o.data))}/>;
 const slider=(label:string,value:number,min:number,max:number,fn:(v:number)=>void)=><LayoutSliderField label={label} value={value} min={min} max={max} step={1} onChange={fn}/>;
 const colors=(label:string,key:'color'|'background')=><div>{button(label,()=>{const dialog=showModal(<OpaqueColorPicker title={label} hex={(active[key]||'#ffffff').replace('#','')} closeModal={()=>dialog.Close()} onConfirm={hex=>patch({[key]:'#'+hex.replace('#','')})}/>);})}{button(key==='color'?'Use plugin color':active.id===layout.root.id?'Use plugin background':'Transparent',()=>patch({[key]:''}),!active[key])}</div>;
 const tree=(n:Node,depth=0):ReactNode=><div key={n.id}>{<DialogButton aria-pressed={active.id===n.id} onClick={()=>S(n.id)} style={{width:'100%',minWidth:0,whiteSpace:'normal',textAlign:'left',paddingLeft:10+depth*12,background:active.id===n.id?'#233d5d':'transparent'}}>{n.kind==='group'?(n.axis==='row'?'↔ ':'↕ '):'· '}{n.name}{!n.visible?' · hidden':''}</DialogButton>}{n.children.map(c=>tree(c,depth+1))}</div>;
 return <ConfirmModal strTitle="Build your overlay" strDescription="Arrange groups and individual readings. Preview uses sample values." bAllowFullSize strOKButtonText="Apply layout" strCancelButtonText="Cancel" onOK={()=>onApply(validate(layout))} onCancel={closeModal}>
 <style>{`.claw-builder{width: min(84vw,1050px);max-width:100%;color:#e9eef5}.claw-builder *{box-sizing:border-box}.claw-builder-workspace{display:grid;grid-template-columns:minmax(0,1fr) minmax(260px,.8fr);gap:16px;max-height:62vh;overflow:auto}.claw-builder-card{background:#121922;border:1px solid #2b3544;border-radius:10px;padding:12px;min-width:0}.claw-builder h3{font-size:15px;margin:8px 0}.claw-builder small{color:#95a6bc;font-size:11px}.claw-builder-tree{max-height:260px;overflow:auto}.claw-builder-tools{display:flex;gap:6px;margin:10px 0}.claw-builder-stage{position:relative;height:170px;overflow:hidden;border-radius:8px;background:linear-gradient(150deg,#587687,#172c38 75%)}.claw-builder-screen{position:absolute;width:1280px;height:800px;transform:scale(.2);transform-origin:top left}.claw-builder .modular-hud{width:max-content}.claw-builder .hud-node{white-space:nowrap;min-width:0}.claw-builder-inspector>div{margin-bottom:10px}.claw-builder button:focus{background-color:#365270!important}.claw-builder-error{color:#ffb9b9;padding:8px}@media(max-width:750px){.claw-builder-workspace{grid-template-columns:1fr}}`}</style>
 <div className="claw-builder">
 <Focusable className="claw-builder-tools" flow-children="row">
 {button('Undo',()=>{const prev=past[past.length-1];if(prev){F([layout,...future]);P(past.slice(0,-1));L(prev)}},!past.length)}
 {button('Redo',()=>{const next=future[0];if(next){P([...past,layout]);F(future.slice(1));L(next)}},!future.length)}
 {button(guides?'Guides on':'Guides off',()=>G(!guides))}
 </Focusable>
 <Focusable className="claw-builder-workspace" flow-children="row">
 <Focusable flow-children="column" className="claw-builder-card">
 <h3>Live preview</h3><small>Sample data · HTML preview · 1280 × 800</small>
 <div ref={stage} className="claw-builder-stage" style={{height:800*zoom}}><div className="claw-builder-screen" style={{transform:`scale(${zoom})`}}><ModularHud layout={layout} settings={{...settings,enabled:true}} data={initialData} selected={active.id} onSelect={S} editing={guides}/></div></div>
 <h3>Layout structure</h3><small>Select a group or reading to edit it.</small>
 <Focusable flow-children="column" className="claw-builder-tree">{tree(layout.root)}</Focusable>
 <h3>Add an element</h3>{select('Reading',token,Object.entries(catalog).map(([data,label])=>({data,label})),T)}
 <Focusable className="claw-builder-tools" flow-children="row">{button('+ Group',()=>add('group'),all.length>=96)}{button('+ Element',()=>add('metric'),all.length>=96)}</Focusable>
 <small>{all.length}/96 elements · changes apply when saved</small>
 </Focusable>
 <Focusable flow-children="column" className="claw-builder-card claw-builder-inspector">
 <small>{active.kind==='group'?'GROUP':'ELEMENT'} · Layout builder</small><h3>{active.name}</h3>
 <TextField label="Name" value={active.name} onChange={e=>patch({name:e.target.value.slice(0,80)})}/>
 <ToggleField label="Visible" checked={active.visible} onChange={visible=>patch({visible})}/>
 {active.kind==='group'?<>
 {select('Direction',active.axis,[{data:'row',label:'Row →'},{data:'column',label:'Column ↓'}],axis=>patch({axis:axis as Node['axis']}))}
 {select('Cross-axis alignment',active.align,['start','center','end'].map(data=>({data,label:data})),align=>patch({align:align as Node['align']}))}
 {slider('Group gap',active.gap,0,80,gap=>patch({gap}))}{slider('Group padding',active.padding,0,80,padding=>patch({padding}))}
 </>:<>{select('Reading',active.token,Object.entries(catalog).map(([data,label])=>({data,label})),token=>patch({token,name:catalog[token]}))}{active.token==='graph'&&<>{slider('Graph width',active.width,40,1000,width=>patch({width}))}{slider('Graph height',active.height,16,240,height=>patch({height}))}</>}{colors('Color override','color')}</>}
 {slider('Element scale (%)',active.scale,50,250,scale=>patch({scale}))}
 {colors('Group / element background','background')}
 {active.background&&slider('Background opacity (%)',active.opacity,0,100,opacity=>patch({opacity}))}
 <ToggleField label="Outline" checked={active.outline} onChange={outline=>patch({outline})}/>
 {owner&&<>
 {select('Move to group',owner.id,all.filter(n=>n.kind==='group'&&!find(active,n.id)).map(n=>({data:n.id,label:n.name})),id=>commit(move(layout,active.id,id)))}
 <Focusable flow-children="row" className="claw-builder-tools">{button('Move earlier',()=>shift(-1),owner.children[0].id===active.id)}{button('Move later',()=>shift(1),owner.children[owner.children.length-1].id===active.id)}</Focusable>
 {button(active.kind==='group'?'Delete group & contents':'Delete element',()=>{const next=structuredClone(layout),p=parent(next.root,active.id)!;p.children=p.children.filter(c=>c.id!==active.id);commit(next);S(p.id)})}
 </>}
 <h3>Position on screen</h3>{select('Anchor',layout.anchor,anchors.map(data=>({data,label:data})),anchor=>commit({...layout,anchor}))}
 {slider('Horizontal offset',layout.x,0,2000,x=>commit({...layout,x}))}{slider('Vertical offset',layout.y,0,2000,y=>commit({...layout,y}))}
 </Focusable></Focusable>{error&&<div role="alert" className="claw-builder-error">{error}</div>}
 </div></ConfirmModal>;
}
