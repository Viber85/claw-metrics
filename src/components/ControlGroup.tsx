import type {ReactNode} from "react";
import {DialogButton} from "@decky/ui";
import {FaChevronDown,FaChevronRight} from "react-icons/fa";

export function ControlGroup({title,summary,open,onToggle,children}:{
 title:string;summary:string;open:boolean;onToggle:()=>void;children:ReactNode;
}) {
 return <div className="claw-control-group" style={{margin:"7px 0",minWidth:0,
   border:"1px solid #355873",borderRadius:9,background:"#14253a",overflow:"hidden"}}>
   <DialogButton aria-expanded={open} onClick={onToggle}
     style={{display:"block",width:"100%",margin:0,minWidth:0,minHeight:57,
       padding:"10px 9px",background:open?"#16466a":"#172c43",
       border:"none",borderRadius:0,textAlign:"left"}}>
     <span style={{display:"flex",gap:9,alignItems:"center",justifyContent:"space-between"}}>
       <span style={{minWidth:0,display:"flex",flexDirection:"column",gap:3}}>
         <strong style={{fontSize:13,color:"#f3f8ff"}}>{title}</strong>
         <span style={{fontSize:11.5,color:"#afc5d7",lineHeight:1.3}}>{summary}</span>
       </span>{open?<FaChevronDown/>:<FaChevronRight/>}
     </span>
   </DialogButton>
   {open && <div style={{padding:"10px 7px 12px",borderTop:"1px solid #365b79"}}>
     {children}
   </div>}
 </div>;
}
