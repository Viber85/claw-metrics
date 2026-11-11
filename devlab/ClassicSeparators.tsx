import {Fragment} from 'react';
import {rgba} from '../src/modular/Hud';
import type {Settings,SeparatorOrientation} from '../src/controller';

const readings=[['fps_label','FPS','120'],['cpu','CPU','36%  54°C'],
  ['gpu','GPU','72%  52°C'],['ram','RAM','12.6 GiB']] as const;
const orientations=['auto','horizontal','vertical','off'] as const;
const title=(value:string)=>value[0].toUpperCase()+value.slice(1);
type RangeKey='separator_length'|'separator_height'|'separator_thickness'|'separator_rounding'|'separator_opacity';
type Appearance=Pick<Settings,RangeKey|'colors'|'background'|'fontsize'|'opacity'|'rounding'|'separator_orientation'|'hud_orientation'>;

export function ClassicSeparators({settings,onChange}:{settings:Partial<Appearance>;onChange:(v:Partial<Appearance>)=>void}){
 const {hud_orientation='horizontal',separator_orientation='auto',separator_length=0,
  separator_height=100,separator_thickness=2,separator_rounding=0,separator_opacity=100,
  fontsize=18,colors,background,opacity=80,rounding=10}=settings;
 const strip=hud_orientation==='horizontal';
 const vertical=separator_orientation==='vertical'||(separator_orientation==='auto'&&strip);
 const contentWidth=Math.min(420,Math.max(260,fontsize*15))-10;
 const automatic=vertical?fontsize*.85*separator_height/100:strip?fontsize*.85:contentWidth;
 const length=separator_length||automatic;
 const color=colors?.separator||'777C87';
 const range=(key:RangeKey,label:string,value:number,min:number,max:number,step=1)=>
  <label className="lab-field"><span>{label} <b>{value}</b></span>
   <input aria-label={label} type="range" value={value} min={min} max={max} step={step}
    onChange={e=>onChange({[key]:e.currentTarget.valueAsNumber})}/></label>;

 return <>
  <div className="lab-grid">
   <label className="lab-field"><span>Classic HUD orientation</span>
    <select value={hud_orientation} onChange={e=>onChange({hud_orientation:e.currentTarget.value as Appearance['hud_orientation']})}>
     <option value="horizontal">Horizontal</option><option value="vertical">Vertical</option>
    </select>
   </label>
   <label className="lab-field"><span>Classic separator orientation</span>
    <select value={separator_orientation} onChange={e=>onChange({separator_orientation:e.currentTarget.value as SeparatorOrientation})}>
     {orientations.map(value=><option key={value} value={value}>{title(value)}</option>)}
    </select>
   </label>
   {separator_orientation!=='off'&&<>
    {range('separator_length','Separator length (px, 0 = auto)',separator_length,0,1000)}
    {range('separator_thickness','Separator thickness (px)',separator_thickness,1,20)}
    {range('separator_rounding','Separator corner radius (px)',separator_rounding,0,10)}
    {range('separator_opacity','Separator opacity (%)',separator_opacity,0,100)}
    {separator_length===0&&vertical&&range('separator_height','Automatic height (%)',separator_height,50,150,5)}
    <label className="lab-field"><span>Classic separator color</span>
     <input type="color" value={'#'+color} onChange={e=>{if(colors)onChange({colors:{...colors,separator:e.currentTarget.value.slice(1).toUpperCase()}})}}/>
    </label>
   </>}
  </div>
  <div className="classic-preview" aria-label="Classic HUD preview">
   <div className="classic-preview-hud" style={{flexDirection:strip?'row':'column',alignItems:strip?'center':'stretch',
    width:strip?'max-content':Math.max(contentWidth,!vertical&&separator_orientation!=='off'?length:0)+10,
    background:rgba(background?.color||'161820',opacity),fontSize:fontsize,borderRadius:rounding}}>
    {readings.map(([token,label,value],index)=><Fragment key={token}>
     {index>0&&separator_orientation!=='off'&&<div className="classic-preview-divider" style={{
      width:vertical?separator_thickness:length,height:vertical?length:separator_thickness,
      borderRadius:separator_rounding,background:rgba(color,separator_opacity)}}/>}
     <div className="classic-preview-reading" style={{color:'#'+(colors?.text||'F0F2F5')}}>
      <span style={{color:'#'+(colors?.[token]||'F0F2F5')}}>{label}</span> {value}
     </div>
    </Fragment>)}
   </div>
  </div>
 </>;
}
