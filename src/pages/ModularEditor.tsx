import {useEffect,useState} from 'react';
import {callable,openFilePicker,FileSelectionType} from '@decky/api';
import {ConfirmModal,DialogButton,Field,PanelSectionRow,ToggleField,showModal} from '@decky/ui';
import {GamepadGrid} from '../components/GamepadGrid';
import {ControlGroup} from '../components/ControlGroup';
import {Builder} from '../modular/Builder';
import {isHorizontalLayout,validate, type Layout} from '../modular/model';
import type {ClawController} from '../controller';
const preset=callable<[string],any>('get_modular_preset');
const importLayout=callable<[string],any>('import_modular_layout');
const getInfo=callable<[],{home:string}>('get_modular_info');
export function ModularEditor({vm}:{vm:ClawController}){
 const {settings,ready,update}=vm;const [busy,Busy]=useState(false),[message,Message]=useState(''),[home,Home]=useState('/home'),[open,Open]=useState(true);
 useEffect(()=>{if(ready)void getInfo().then(v=>Home(v.home)).catch(()=>{});},[ready]);
 const canEdit=ready&&vm.info?.layout_spacing_supported!==false;
 const doc=settings.modular_layout;
 const openBuilder=(layout:Layout)=>{const editor=showModal(<Builder initial={layout} settings={settings} onApply={value=>{editor.Close();void editor.ClosedPromise.then(()=>update({modular_layout:value,modular_enabled:true}));}} closeModal={()=>editor.Close()}/>,undefined,{popupWidth:window.innerWidth,popupHeight:window.innerHeight});};
 const chooseTemplate=(id:'horizontal'|'vertical')=>{
  const label=id==='horizontal'?'Horizontal':'Vertical';
  const dialog=showModal(<ConfirmModal strTitle={'Start from '+label+'?'}
   strDescription="Replace the current editable layout with a fresh template? Save the current overlay as a style first if you want to keep it."
   strOKButtonText="Use template" strCancelButtonText="Cancel"
   onCancel={()=>dialog.Close()}
   onOK={()=>{dialog.Close();void dialog.ClosedPromise.then(()=>action(async()=>{const value=validate(await preset(id));if(value.root.axis!==(id==='horizontal'?'row':'column'))throw new Error(label+' template has the wrong direction.');update({modular_layout:value,modular_enabled:true});Message(label+' template loaded.');openBuilder(value);}));}}/>);
 };

 const action=async(fn:()=>Promise<void>)=>{Busy(true);Message('');try{await fn()}catch(error){Message(String(error))}finally{Busy(false)}};
 return <ControlGroup open={open} onToggle={()=>Open(!open)} title="Layout builder" summary={settings.modular_enabled?'Customizable layout enabled':'Classic renderer active'}>
  <PanelSectionRow><Field label="TEMPLATES" description="Choose a starting layout, then edit its groups and readings."/></PanelSectionRow>
  {!canEdit&&ready&&<PanelSectionRow><Field label="Native renderer unavailable" description="Reinstall this plugin version to restore its bundled renderer."/></PanelSectionRow>}
  <PanelSectionRow><ToggleField label="Use editable renderer (test)" checked={settings.modular_enabled} disabled={!canEdit||busy||!doc} onChange={value=>update({modular_enabled:value})}/></PanelSectionRow>
  <PanelSectionRow><GamepadGrid className="claw-tiles claw-modular-templates" columns={2} items={([['horizontal','↔ Horizontal'],['vertical','↕ Vertical']] as Array<['horizontal'|'vertical',string]>)} renderItem={([id,label])=><DialogButton key={id} aria-label={id+' template'} disabled={!canEdit||busy} style={{minWidth:0,minHeight:38,padding:'5px 4px',fontSize:12,background:"#1c3450",border:"1px solid #456987",borderRadius:8}} onClick={()=>chooseTemplate(id)}>{label}</DialogButton>}/></PanelSectionRow>
  <PanelSectionRow><Field label="CURRENT OVERLAY" description={doc?`${isHorizontalLayout(doc)?'Horizontal':'Vertical'} · Save it in Colors & Font → Styles to keep it for later.`:'Choose a template to begin.'}/></PanelSectionRow>
  <PanelSectionRow><div className="claw-modular-actions"><DialogButton disabled={!canEdit||busy||!doc} onClick={()=>doc&&openBuilder(doc)}>Edit overlay</DialogButton><DialogButton disabled={!canEdit||busy} onClick={()=>void action(async()=>{const file=await openFilePicker(FileSelectionType.FILE,home,true,false);if(!file?.realpath&&!file?.path)return;const value=await importLayout(file.realpath||file.path);update({modular_layout:value,modular_enabled:true});Message('Layout imported. Settings are saving.')})}>Import JSON</DialogButton></div></PanelSectionRow>
  {message&&<PanelSectionRow><div role="status" style={{overflowWrap:'anywhere',fontSize:12,padding:'6px 0'}}>{message}</div></PanelSectionRow>}
 </ControlGroup>
}
