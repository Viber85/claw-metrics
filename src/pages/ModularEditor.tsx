import {useEffect,useState} from 'react';
import {callable,openFilePicker,FileSelectionType} from '@decky/api';
import {ButtonItem,ConfirmModal,DialogButton,Field,PanelSectionRow,ToggleField,showModal} from '@decky/ui';
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
 const chooseTemplate=(id:'horizontal'|'vertical')=>{
  const label=id==='horizontal'?'Horizontal':'Vertical';
  const dialog=showModal(<ConfirmModal strTitle={'Start from '+label+'?'}
   strDescription="Replace the current editable layout with a fresh template? Your current layout will be lost unless you export it first. The classic renderer remains available as fallback."
   strOKButtonText="Use template" strCancelButtonText="Cancel"
   onCancel={()=>dialog.Close()}
   onOK={()=>{dialog.Close();void action(async()=>{const value=await preset(id);update({modular_layout:value,modular_enabled:true});Message(label+' template loaded. Open Layout builder to customize it.');});}}/>);
 };

 const action=async(fn:()=>Promise<void>)=>{Busy(true);Message('');try{await fn()}catch(error){Message(String(error))}finally{Busy(false)}};
 return <ControlGroup open={open} onToggle={()=>Open(!open)} title="Layout builder" summary={settings.modular_enabled?'Customizable layout enabled':'Classic renderer active'}>
  <PanelSectionRow><Field label="STARTING TEMPLATES" description="Horizontal and Vertical are the only built-in starting points. After choosing one, customize any group or reading in the builder. Existing colors, fonts and sensor settings remain separate."/></PanelSectionRow>
  {!canEdit&&ready&&<PanelSectionRow><Field label="Native renderer unavailable" description="Reinstall this plugin version to restore its bundled renderer."/></PanelSectionRow>}
  <PanelSectionRow><ToggleField label="Use editable renderer (test)" checked={settings.modular_enabled} disabled={!canEdit||busy||!doc} onChange={value=>update({modular_enabled:value})}/></PanelSectionRow>
  <PanelSectionRow><GamepadGrid className="claw-tiles" columns={2} items={([['horizontal','↔ Horizontal'],['vertical','↕ Vertical']] as Array<['horizontal'|'vertical',string]>)} renderItem={([id,label])=><DialogButton key={id} disabled={!canEdit||busy} style={{minWidth:0,whiteSpace:'normal',minHeight:56,background:"#1c3450",border:"1px solid #456987",borderRadius:8}} onClick={()=>chooseTemplate(id)}>{label}</DialogButton>}/></PanelSectionRow>
  <PanelSectionRow><Field label="NON-DESTRUCTIVE EDITING" description="The builder edits a draft. Apply saves the new layout; Cancel leaves your saved layout unchanged. Export JSON before replacing your template." /></PanelSectionRow>
  <PanelSectionRow><ButtonItem layout="below" disabled={!canEdit||busy} onClick={()=>void action(async()=>{const file=await openFilePicker(FileSelectionType.FILE,home,true,false);if(!file?.realpath&&!file?.path)return;const value=await importLayout(file.realpath||file.path);update({modular_layout:value,modular_enabled:true});Message('Layout imported. Settings are saving.')})}>Import DevLab JSON</ButtonItem></PanelSectionRow>
  <PanelSectionRow><ButtonItem layout="below" disabled={!canEdit||busy||!doc} onClick={()=>void action(async()=>{const value=await exportLayout(doc);Message('Layout saved: '+value.path)})}>Export current layout</ButtonItem></PanelSectionRow>
  {doc&&<PanelSectionRow><ButtonItem layout="below" disabled={!canEdit||busy} onClick={()=>{const dialog=showModal(<Builder initial={doc} settings={settings} onApply={value=>{dialog.Close();void dialog.ClosedPromise.then(()=>update({modular_layout:value,modular_enabled:true}));}} closeModal={()=>dialog.Close()}/>,undefined,{popupWidth:window.innerWidth,popupHeight:window.innerHeight});}}>Open Layout builder</ButtonItem></PanelSectionRow>}
  {message&&<PanelSectionRow><div role="status" style={{overflowWrap:'anywhere',fontSize:12,padding:'6px 0'}}>{message}</div></PanelSectionRow>}
 </ControlGroup>
}
