import {useEffect,useState} from 'react';
import {callable,openFilePicker,FileSelectionType} from '@decky/api';
import {ButtonItem,DialogButton,Field,PanelSectionRow,ToggleField,showModal} from '@decky/ui';
import {GamepadGrid} from '../components/GamepadGrid';
import {ControlGroup} from '../components/ControlGroup';
import {Builder} from '../modular/Builder';
import type {ClawController} from '../controller';
const preset=callable<[string],any>('get_modular_preset');
const importLayout=callable<[string],any>('import_modular_layout');
const exportLayout=callable<[any],{path:string}>('export_modular_layout');
const getInfo=callable<[],{home:string}>('get_modular_info');
export function ModularEditor({vm}:{vm:ClawController}){
 const {settings,ready,update}=vm;const [busy,Busy]=useState(false),[message,Message]=useState(''),[home,Home]=useState('/home'),[open,Open]=useState(true);
 useEffect(()=>{if(ready)void getInfo().then(v=>Home(v.home)).catch(()=>{});},[ready]);
 const canEdit=ready&&vm.info?.layout_spacing_supported!==false;
 const doc=settings.modular_layout;
 const action=async(fn:()=>Promise<void>)=>{Busy(true);Message('');try{await fn()}catch(error){Message(String(error))}finally{Busy(false)}};
 return <ControlGroup open={open} onToggle={()=>Open(!open)} title="Modular layout" summary={settings.modular_enabled?'Modular layout selected':'Classic layout selected'}>
  <PanelSectionRow><Field label="Modular renderer" description="Choose a starting layout, then open Layout builder to arrange groups and readings. Fonts, colors and graph style use your plugin settings."/></PanelSectionRow>
  {!canEdit&&ready&&<PanelSectionRow><Field label="Native renderer unavailable" description="Reinstall this plugin version to restore its bundled renderer."/></PanelSectionRow>}
  <PanelSectionRow><ToggleField label="Use modular layout" checked={settings.modular_enabled} disabled={!canEdit||busy||!doc} onChange={value=>update({modular_enabled:value})}/></PanelSectionRow>
  <PanelSectionRow><GamepadGrid className="claw-tiles" columns={2} items={[['two-rows','Two rows'],['graph-focus','Graph focus']]} renderItem={([id,label])=><DialogButton key={id} disabled={!canEdit||busy} style={{minWidth:0,whiteSpace:'normal'}} onClick={()=>void action(async()=>{const value=await preset(id);update({modular_layout:value,modular_enabled:true})})}>{label}</DialogButton>}/></PanelSectionRow>
  <PanelSectionRow><ButtonItem layout="below" disabled={!canEdit||busy} onClick={()=>void action(async()=>{const file=await openFilePicker(FileSelectionType.FILE,home,true,false);if(!file?.realpath&&!file?.path)return;const value=await importLayout(file.realpath||file.path);update({modular_layout:value,modular_enabled:true});Message('Layout imported. Settings are saving.')})}>Import DevLab JSON</ButtonItem></PanelSectionRow>
  <PanelSectionRow><ButtonItem layout="below" disabled={!canEdit||busy||!doc} onClick={()=>void action(async()=>{const value=await exportLayout(doc);Message('Layout saved: '+value.path)})}>Export current layout</ButtonItem></PanelSectionRow>
  {doc&&<PanelSectionRow><ButtonItem layout="below" disabled={!canEdit||busy} onClick={()=>{const dialog=showModal(<Builder initial={doc} settings={settings} onApply={value=>update({modular_layout:value,modular_enabled:true})} closeModal={()=>dialog.Close()}/>);}}>Open Layout builder</ButtonItem></PanelSectionRow>}
  {message&&<PanelSectionRow><div role="status" style={{overflowWrap:'anywhere',fontSize:12,padding:'6px 0'}}>{message}</div></PanelSectionRow>}
 </ControlGroup>
}
