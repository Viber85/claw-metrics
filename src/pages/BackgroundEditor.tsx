import {useState} from "react";
import {ButtonItem,Field,PanelSectionRow,showModal,ToggleField} from "@decky/ui";
import {ControlGroup,OpaqueColorPicker,type ClawController,type OverlayBackground} from "../controller";
import {LayoutSliderField} from "../components/LayoutSliderField";

export function BackgroundEditor({vm}:{vm:ClawController}) {
 const [open,setOpen]=useState(false);
 const b=vm.settings.background;
 const patch=(value:Partial<OverlayBackground>)=>vm.update({background:{...vm.current.current.background,...value}});
 const color=(index?:number|"outline")=>{
  const hex=index==="outline"?b.outline_color:index===undefined?b.color:b.stops[index].color;
  const dialog=showModal(<OpaqueColorPicker title={index==="outline"?"Outline color":index===undefined?"Background color":"Gradient stop color"} hex={hex}
   closeModal={()=>dialog.Close()} onConfirm={hex=>{
    if(index==="outline")patch({outline_color:hex});
    else if(index===undefined)patch({color:hex});
    else patch({stops:vm.current.current.background.stops.map((s,i)=>i===index?{...s,color:hex}:s)});
   }}/>);
 };
 const preview=b.mode==="solid"?"#"+b.color:b.mode==="linear"
  ?`linear-gradient(${90+b.angle}deg,${b.stops.map(s=>`#${s.color} ${s.position}%`).join(",")})`
  :`radial-gradient(circle ${Math.hypot(260,64)*.5*b.radius/100}px at ${b.center_x}% ${b.center_y}%,${b.stops.map(s=>`#${s.color} ${s.position}%`).join(",")})`;
 const slider=(label:string,value:number,min:number,max:number,onChange:(n:number)=>void)=>min>=max?<Field label={label} description={String(value)}/>:<PanelSectionRow><div className="claw-background-slider claw-layout-slider"><LayoutSliderField label={label} value={value} min={min} max={max} step={1} onChange={onChange} disabled={!vm.ready}/></div></PanelSectionRow>;
 return <ControlGroup title="Background" summary="Solid color · linear or radial gradient" open={open} onToggle={()=>setOpen(!open)}>
  <div aria-label="Background preview" style={{position:"relative",height:64,borderRadius:10,overflow:"hidden",border:"1px solid #37414d",marginBottom:10,
   background:"repeating-conic-gradient(#202832 0% 25%,#10161e 0% 50%) 0 0 / 16px 16px"}}>
   <div style={{height:"100%",width:"100%",background:preview,opacity:vm.settings.opacity/100}}/>
   {b.outline_enabled&&<div style={{position:"absolute",inset:0,border:`${b.outline_width}px solid #${b.outline_color}`,borderRadius:10,boxSizing:"border-box",opacity:b.outline_opacity/100,pointerEvents:"none"}}/>}
  </div>
  {([['solid','Solid'],['linear','Linear gradient'],['radial','Radial / circular gradient']] as const).map(([mode,label])=><PanelSectionRow key={mode}>
   <ButtonItem layout="below" disabled={!vm.ready || (mode!=="solid"&&!vm.info?.layout_spacing_supported)} onClick={()=>patch({mode})}>
    {b.mode===mode?"✓ ":""}{label}
   </ButtonItem>
  </PanelSectionRow>)}
  {b.mode==="solid"?<PanelSectionRow><ButtonItem layout="below" disabled={!vm.ready} onClick={()=>color()}>Color · #{b.color}</ButtonItem></PanelSectionRow>:<>
   {b.mode==="linear"?slider("Direction (°)",b.angle,0,360,v=>patch({angle:v})): <>
    {slider("Center X (%)",b.center_x,0,100,v=>patch({center_x:v}))}
    {slider("Center Y (%)",b.center_y,0,100,v=>patch({center_y:v}))}
    {slider("Spread (%)",b.radius,1,200,v=>patch({radius:v}))}
   </>}
   <Field label="Gradient stops" description="Add up to 8 colors. Stop positions control the transitions."/>
   {b.stops.map((stop,index)=><div key={index} style={{width:"100%",maxWidth:"100%",minWidth:0,boxSizing:"border-box",padding:8,marginBottom:8,borderRadius:8,border:"1px solid #303b48",background:"#111820"}}>
    <ButtonItem layout="below" disabled={!vm.ready} onClick={()=>color(index)}>Stop {index+1} · #{stop.color}</ButtonItem>
    {slider("Position (%)",stop.position,b.stops[index-1]?.position??0,b.stops[index+1]?.position??100,
     value=>patch({stops:vm.current.current.background.stops.map((s,i)=>i===index?{...s,position:value}:s)}))}
    <ButtonItem layout="below" disabled={!vm.ready||b.stops.length<=2} onClick={()=>patch({stops:b.stops.filter((_,i)=>i!==index)})}>Remove stop</ButtonItem>
   </div>)}
   <PanelSectionRow><ButtonItem layout="below" disabled={!vm.ready||b.stops.length>=8} onClick={()=>{
    let insert=1,gap=-1;
    for(let i=1;i<b.stops.length;i++)if(b.stops[i].position-b.stops[i-1].position>gap){gap=b.stops[i].position-b.stops[i-1].position;insert=i;}
    const stops=[...b.stops];stops.splice(insert,0,{position:Math.round((stops[insert-1].position+stops[insert].position)/2),color:stops[insert-1].color});patch({stops});
   }}>Add color stop</ButtonItem></PanelSectionRow>
  </>}
  {slider("Background opacity (%)",vm.settings.opacity,0,100,value=>vm.update({opacity:value}))}
  <PanelSectionRow><ToggleField label="Outline" description="Rounded border with independent color and opacity."
   checked={b.outline_enabled} disabled={!vm.ready||!vm.info?.layout_spacing_supported} onChange={enabled=>patch({outline_enabled:enabled})}/></PanelSectionRow>
  {b.outline_enabled&&<>
   <PanelSectionRow><ButtonItem layout="below" disabled={!vm.ready} onClick={()=>color("outline")}>Outline color · #{b.outline_color}</ButtonItem></PanelSectionRow>
   {slider("Outline width (px)",b.outline_width,1,6,value=>patch({outline_width:value}))}
   {slider("Outline opacity (%)",b.outline_opacity,0,100,value=>patch({outline_opacity:value}))}
  </>}
  <Field label="Saved with styles" description="Background, opacity and gradient settings are stored when you save a style. Rounded corners follow Layout."/>
 </ControlGroup>;
}
