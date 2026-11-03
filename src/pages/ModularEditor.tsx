import {useEffect,useState} from 'react';
import {callable,openFilePicker,FileSelectionType} from '@decky/api';
import {ButtonItem,DialogButton,Field,PanelSectionRow,ToggleField} from '@decky/ui';
import {LayoutSliderField} from '../components/LayoutSliderField';
import {GamepadGrid} from '../components/GamepadGrid';
import {ControlGroup} from '../components/ControlGroup';
import type {ClawController} from '../controller';
const preset=callable<[string],any>('get_modular_preset');
const importLayout=callable<[string],any>('import_modular_layout');
const exportLayout=callable<[any],{path:string}>('export_modular_layout');
const getInfo=callable<[],{home:string}>('get_modular_info');
function groups(root:any):any[]{return root?[...(root.kind==='group'?[root]:[]),...(root.children||[]).flatMap(groups)]:[]}
export function ModularEditor({vm}:{vm:ClawController}){
 const {settings,ready,update}=vm;const [busy,Busy]=useState(false),[message,Message]=useState(''),[selection,Selection]=useState(0),[home,Home]=useState('/home'),[open,Open]=useState(false);
 useEffect(()=>{if(ready)void getInfo().then(v=>Home(v.home)).catch(()=>{});},[ready]);
 const canEdit=ready&&vm.info?.layout_spacing_supported!==false;
 const doc=settings.modular_layout;const available=groups(doc?.root);const index=Math.min(selection,Math.max(0,available.length-1));const selected=available[index];
 const action=async(fn:()=>Promise<void>)=>{Busy(true);Message('');try{await fn()}catch(error){Message(String(error))}finally{Busy(false)}};
 const setDoc=(value:any)=>update({modular_layout:value});
 const change=(key:string,value:any)=>{if(!doc)return;setDoc({...doc,[key]:value})};
 const edit=(values:any)=>{if(!doc||!selected)return;const next=JSON.parse(JSON.stringify(doc));const target=groups(next.root).find(n=>n.id===selected.id);Object.assign(target,values);setDoc(next)};
 const sliders=(label:string,value:number,min:number,max:number,fn:(value:number)=>void)=><PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label={label} value={value} min={min} max={max} step={1} disabled={!canEdit||busy} onChange={fn}/></div></PanelSectionRow>;
 return <ControlGroup open={open} onToggle={()=>Open(!open)} title="Modular layout · preview" summary={settings.modular_enabled?'Modular layout selected':'Classic layout selected'}>
  <PanelSectionRow><Field label="Modular renderer" description="Restart the game once after updating this plugin. Arrange elements in DevLab, export layout JSON and import it here. Fonts, colors, background and graph style use your plugin settings. Geometry and visible elements come from the modular tree; legacy metric, position and padding controls apply when modular mode is off."/></PanelSectionRow>
  {!canEdit&&ready&&<PanelSectionRow><Field label="Native renderer unavailable" description="Reinstall this plugin version to restore its bundled renderer."/></PanelSectionRow>}
  <PanelSectionRow><ToggleField label="Use modular layout" checked={settings.modular_enabled} disabled={!canEdit||busy||!doc} onChange={value=>update({modular_enabled:value})}/></PanelSectionRow>
  <PanelSectionRow><GamepadGrid className="claw-tiles" columns={2} items={[['two-rows','Two rows'],['graph-focus','Graph focus']]} renderItem={([id,label])=><DialogButton key={id} disabled={!canEdit||busy} style={{minWidth:0,whiteSpace:'normal'}} onClick={()=>void action(async()=>{const value=await preset(id);update({modular_layout:value,modular_enabled:true});Selection(0)})}>{label}</DialogButton>}/></PanelSectionRow>
  <PanelSectionRow><ButtonItem layout="below" disabled={!canEdit||busy} onClick={()=>void action(async()=>{const file=await openFilePicker(FileSelectionType.FILE,home,true,false);if(!file?.realpath&&!file?.path)return;const value=await importLayout(file.realpath||file.path);update({modular_layout:value,modular_enabled:true});Selection(0);Message('Layout imported. Settings are saving.')})}>Import DevLab JSON</ButtonItem></PanelSectionRow>
  <PanelSectionRow><ButtonItem layout="below" disabled={!canEdit||busy||!doc} onClick={()=>void action(async()=>{const value=await exportLayout(doc);Message('Layout saved: '+value.path)})}>Export current layout</ButtonItem></PanelSectionRow>
  {doc&&<>
   <PanelSectionRow><Field label="Modular position" description="Changes apply while the game runs. A large layout can extend beyond the screen; use group scale or a smaller font to fit."/></PanelSectionRow>
   <PanelSectionRow><GamepadGrid className="claw-tiles" columns={3} items={['top-left','top-center','top-right','bottom-left','bottom-center','bottom-right']} renderItem={(anchor,i)=><DialogButton aria-label={"Modular "+anchor.replace(/-/g," ")} key={anchor} disabled={!canEdit||busy} aria-pressed={doc.anchor===anchor} style={{minWidth:0,whiteSpace:'normal',background:doc.anchor===anchor?'#2b69b3':undefined}} onClick={()=>change('anchor',anchor)}>{['↖','↑','↗','↙','↓','↘'][i]}</DialogButton>}/></PanelSectionRow>
   {sliders('Horizontal offset (px)',doc.x,0,2000,v=>change('x',v))}{sliders('Vertical offset (px)',doc.y,0,2000,v=>change('y',v))}
   <PanelSectionRow><DialogButton style={{whiteSpace:"normal",overflowWrap:"anywhere",minWidth:0,width:"100%"}} disabled={!canEdit||busy} onClick={()=>Selection((index+1)%available.length)}>Edit group: {selected?.name} · {index+1}/{available.length}</DialogButton></PanelSectionRow>
   {selected&&<>{selected.id!==doc.root.id&&<PanelSectionRow><ToggleField label="Show selected group" checked={selected.visible} disabled={!canEdit||busy} onChange={value=>edit({visible:value})}/></PanelSectionRow>}<PanelSectionRow><GamepadGrid className="claw-tiles" columns={2} items={['row','column']} renderItem={axis=><DialogButton key={axis} disabled={!canEdit||busy} aria-pressed={selected.axis===axis} style={{minWidth:0,background:selected.axis===axis?'#2b69b3':undefined}} onClick={()=>edit({axis})}>{axis==='row'?'Row →':'Column ↓'}</DialogButton>}/></PanelSectionRow>
    {sliders('Group scale (%)',selected.scale,50,250,v=>edit({scale:v}))}{sliders('Group gap (px)',selected.gap,0,80,v=>edit({gap:v}))}{sliders('Group padding (px)',selected.padding,0,80,v=>edit({padding:v}))}
   </>}
  </>}
  {message&&<PanelSectionRow><div role="status" style={{overflowWrap:'anywhere',fontSize:12,padding:'6px 0'}}>{message}</div></PanelSectionRow>}
 </ControlGroup>
}
