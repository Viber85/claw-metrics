import {Navigation} from '@decky/ui';
import {callable} from '@decky/api';
import type {BuilderAppearance,BuilderStyleStore} from './Builder';
import type {Layout} from './model';

export const EDITOR_PATH='/claw-metrics/editor';
const record=callable<[string,string],{ok:boolean}>('record_ui_event');
export function traceEditor(event:string,detail=''){
 void record(event,detail.slice(0,400)).catch(()=>{});
}
export type EditorPageProps={initial:Layout;settings:any;
 onApply:(layout:Layout,appearance:BuilderAppearance,slot?:string)=>unknown;
 onSaveStyle:(slot:string,layout:Layout,appearance:BuilderAppearance,name:string)=>Promise<BuilderStyleStore>};
let routeAvailable=true;
export function setEditorRouteAvailable(available:boolean){routeAvailable=available}
export function editorRouteAvailable(){return routeAvailable}
let serial=0;
let active:{id:number;props:EditorPageProps;leaving:boolean;mount:number;pending?:()=>unknown}|undefined;
export function currentEditorPage(){return active}
export function openEditorPage(props:EditorPageProps){
 if(!routeAvailable){traceEditor('ui_error','Editor route unavailable');return;}
 if(active)return; // Never stack editor navigation entries.
 active={id:++serial,props,leaving:false,mount:0};traceEditor('editor_open');
 Navigation.Navigate(EDITOR_PATH);Navigation.CloseSideMenus();
}
export function leaveEditorPage(id:number,pending?:()=>unknown){
 if(!active||active.id!==id||active.leaving)return;
 active.leaving=true;active.pending=pending;
 traceEditor('editor_exit_request',pending?'apply':'cancel');
 Navigation.NavigateBack();
}
export function releaseEditorPage(id:number){
 if(!active||active.id!==id)return;
 const {pending}=active;active=undefined;traceEditor('editor_unmount');
 // Apply only AFTER React has unmounted the routed page. No modal close
 // promise, arbitrary animation timer or forced DOM focus is involved.
 if(pending)void Promise.resolve().then(()=>{traceEditor('editor_apply_start');return pending()})
  .then(()=>traceEditor('editor_apply_done')).catch(error=>traceEditor('ui_error',String(error)));
}
export function mountEditorPage(id:number){
 if(!active||active.id!==id)return ()=>{};
 const generation=++active.mount;traceEditor('editor_mount');
 return ()=>{void Promise.resolve().then(()=>{
  // React's development effect replay must not discard a remounted page.
  if(active?.id===id&&active.mount===generation)releaseEditorPage(id);
 })};
}
export function disposeEditorPage(){
 const wasOpen=Boolean(active&&!active.leaving);active=undefined;
 if(wasOpen){traceEditor('editor_dispose');Navigation.NavigateBack()}
}
