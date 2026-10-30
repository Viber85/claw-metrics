import React, {useEffect, useState} from 'react';
import {definePlugin, callable} from '@decky/api';
import {PanelSection, PanelSectionRow, ToggleField, SliderField, ButtonItem, Field} from '@decky/ui';
import {Activity} from 'lucide-react';

type Settings = {
 enabled:boolean; fontsize:number; opacity:number; fps:boolean; frametime:boolean;
 cpu:boolean;gpu:boolean;ram:boolean;vram:boolean;battery:boolean;power:boolean;time:boolean;tdp:boolean;
};
const defaults:Settings={enabled:true,fontsize:18,opacity:65,fps:true,frametime:true,cpu:true,gpu:true,ram:true,vram:true,battery:true,power:true,time:true,tdp:false};
const load=callable<[],Settings>('get_settings');
const save=callable<[Settings],{ok:boolean;config_path:string}>('save_settings');
const getInfo=callable<[],{config_path:string;launch_option:string;tdp_note:string;power_note:string}>('get_info');

function Content(){
 const [settings,setSettings]=useState<Settings>(defaults);
 const [info,setInfo]=useState<{config_path:string;launch_option:string;tdp_note:string;power_note:string}|null>(null);
 const [status,setStatus]=useState('Učitavanje...');
 useEffect(()=>{Promise.all([load(),getInfo()]).then(([s,i])=>{setSettings(s);setInfo(i);setStatus('Spremno');}).catch(e=>setStatus('Greška: '+String(e)));},[]);
 const update=(patch:Partial<Settings>)=>{
   const next={...settings,...patch};setSettings(next);setStatus('Spremanje...');
   save(next).then(()=>setStatus('Spremljeno · za primjenu u igri možda treba ponovno pokrenuti igru')).catch(e=>setStatus('Greška: '+String(e)));
 };
 const toggle=(key:keyof Settings,title:string)=>(
  <PanelSectionRow><ToggleField label={title} checked={Boolean(settings[key])} onChange={(v:boolean)=>update({[key]:v})}/></PanelSectionRow>
 );
 return <>
  <PanelSection title="Claw Metrics · v0.1">
   {toggle('enabled','Prikaz overlaya')}
   <PanelSectionRow><Field label="Status" description={status}/></PanelSectionRow>
  </PanelSection>
  <PanelSection title="Metrike">
   {toggle('fps','FPS')}{toggle('frametime','Frametime (ms) + graf')}
   {toggle('cpu','CPU · % · MHz · °C')}{toggle('gpu','GPU · % · MHz · °C')}
   {toggle('ram','RAM · GB')}{toggle('vram','VRAM · GB')}
   {toggle('battery','Baterija · % · vrijeme · ikona')}
   {toggle('power','CPU/GPU power · W')}
   {toggle('time','Sat')}
   <PanelSectionRow><Field label="TDP (Panel de Control)" description="Planirano: stvarni primijenjeni limit još nije dostupan u ovoj verziji."/></PanelSectionRow>
  </PanelSection>
  <PanelSection title="Izgled">
   <PanelSectionRow><SliderField label="Veličina fonta" value={settings.fontsize} min={12} max={28} step={1} showValue onChange={(v:number)=>update({fontsize:v})}/></PanelSectionRow>
   <PanelSectionRow><SliderField label="Pozadina (%)" value={settings.opacity} min={0} max={100} step={5} showValue onChange={(v:number)=>update({opacity:v})}/></PanelSectionRow>
  </PanelSection>
  <PanelSection title="Aktivacija u igri">
   <PanelSectionRow><Field label="Launch options" description={info?.launch_option??'Učitavanje...'}/></PanelSectionRow>
   <PanelSectionRow><Field label="Napomena" description="Za prvu verziju dodaj gornju naredbu u Steam Launch Options igre. Na nekim SteamOS sustavima Gamescope već pokreće MangoHud; u tom slučaju konfiguraciju treba spojiti s postojećom integracijom."/></PanelSectionRow>
   <PanelSectionRow><ButtonItem layout="below" onClick={()=>{getInfo().then(setInfo);}}>Osvježi putanju</ButtonItem></PanelSectionRow>
  </PanelSection>
 </>;
}
export default definePlugin(()=>({name:'Claw Metrics',title:<div>Claw Metrics</div>,content:<Content/>,icon:<Activity/>}));
