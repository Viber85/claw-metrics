import {useEffect, useState} from "react";
import {callable} from "@decky/api";
import {ButtonItem, Field, PanelSectionRow} from "@decky/ui";

type Session = {id:string; state:string; started_at:number; samples:number};
type Status = {recording:boolean; sessions:Session[]; error:string; paused?:boolean; detection_error?:string};
const getStatus=callable<[],Status>("get_session_status");
const start=callable<[],Status>("start_session_recording");
const stop=callable<[],Status>("stop_session_recording");
const exportReport=callable<[string],{path:string;bytes:number}>("export_crash_report");

export function SessionDiagnostics({ready}:{ready:boolean}) {
  const [status,setStatus]=useState<Status>();
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState("");
  useEffect(()=>{
    if(!ready) return;
    let alive=true;
    const refresh=async()=>{try{const value=await getStatus();if(alive)setStatus(value);}catch(error){if(alive)setMessage(String(error));}};
    void refresh();
    const timer=setInterval(()=>{void refresh();},5000);
    return ()=>{alive=false;clearInterval(timer);};
  },[ready]);
  const record=async()=>{
    setBusy(true);setMessage("");
    try{setStatus(await (status?.recording?stop():start()));}
    catch(error){setMessage(String(error));}finally{setBusy(false);}
  };
  const report=async(id:string)=>{
    setBusy(true);setMessage("Collecting available session logs…");
    try{const result=await exportReport(id);setMessage("Report saved: "+result.path+" · "+Math.ceil(result.bytes/1024)+" KiB. Open this path in Desktop Mode and attach the ZIP for analysis.");}
    catch(error){setMessage("Export failed: "+String(error));}finally{setBusy(false);}
  };
  return <>
    <PanelSectionRow><Field label="Crash Session Recorder" description="Recording starts automatically when the Claw overlay library is detected in a process (checked every 5 seconds), including with QAM closed. Ends after 3 consecutive checks without the overlay. Keeps up to 5 sessions (8 MiB telemetry each)."/></PanelSectionRow>
    <PanelSectionRow><ButtonItem layout="below" disabled={!ready||busy||!status} onClick={()=>{void record();}}>{status?.recording?"Stop recording":"Start recording manually"}</ButtonItem></PanelSectionRow>
    <PanelSectionRow><Field label={status?.recording?"Recording session":"Recorder status"} description={status?.error || status?.detection_error || (status?.paused?"Automatic recording paused until the overlay closes. ":"Waiting for overlay detection when idle. ")+"Interrupted sessions indicate an unclean end, not its cause. Missing sensors and unavailable previous-boot logs are reported. FPS is not sampled."}/></PanelSectionRow>
    {status?.sessions.map(session=><PanelSectionRow key={session.id}>
      <Field label={new Date(session.started_at*1000).toLocaleString()} description={session.state+" · "+session.samples+" samples"}/>
      <ButtonItem layout="below" disabled={busy||status.recording} onClick={()=>{void report(session.id);}}>Export Crash Report</ButtonItem>
    </PanelSectionRow>)}
    <PanelSectionRow><Field label="Report privacy" description="Includes OS, kernel, overlay settings, game IDs, sensors and available system/Decky logs. Common credentials and home usernames are redacted. Review the ZIP before sharing. Upload is manual."/></PanelSectionRow>
    {message&&<PanelSectionRow><div style={{overflowWrap:"anywhere",fontSize:12,padding:"6px 0"}}>{message}</div></PanelSectionRow>}
  </>;
}
