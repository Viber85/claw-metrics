import type {ReactNode} from "react";
import {DialogButton} from "@decky/ui";
import {FaChevronDown,FaChevronRight} from "react-icons/fa";

export function ControlGroup({title,summary,open,onToggle,children}:{
 title:string;summary:string;open:boolean;onToggle:()=>void;children:ReactNode;
}) {
 return <div className="claw-control-group" style={{margin:"7px 0",minWidth:0,
   border:"1px solid #2d3744",borderRadius:9,background:"#101820",overflow:"hidden"}}>
   <DialogButton aria-expanded={open} onClick={onToggle}
     style={{display:"block",width:"100%",margin:0,minWidth:0,minHeight:57,
       padding:"10px 9px",background:open?"#1b2b40":"#17212c",
       border:"none",borderRadius:0,textAlign:"left"}}>
     <span style={{display:"flex",gap:9,alignItems:"center",justifyContent:"space-between"}}>
       <span style={{minWidth:0,display:"flex",flexDirection:"column",gap:3}}>
         <strong style={{fontSize:13,color:"#f3f8ff"}}>{title}</strong>
         <span style={{fontSize:11.5,color:"#aab4c1",lineHeight:1.3}}>{summary}</span>
       </span>{open?<FaChevronDown/>:<FaChevronRight/>}
     </span>
   </DialogButton>
   {open && <div style={{padding:"10px 7px 12px",borderTop:"1px solid #2c3743"}}>
     {children}
   </div>}
 </div>;
}
