import {latestReportSession,type ReportSession} from "../session-reports";
import {useEffect, useState} from "react";
import {callable} from "@decky/api";
import {ButtonItem, Field, PanelSectionRow} from "@decky/ui";

type Session = ReportSession;
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
  const latest=latestReportSession(status?.sessions);
  const report=async()=>{
    setBusy(true);setMessage("Collecting available session logs…");
    try{
      const fresh=await getStatus();setStatus(fresh);
      const session=latestReportSession(fresh.sessions);
      if(!session)throw new Error("No ended session to export. Stop the current recording first.");
      const result=await exportReport(session.id);setMessage("Report saved: "+result.path+" · "+Math.ceil(result.bytes/1024)+" KiB. Open this path in Desktop Mode and attach the ZIP for analysis.");}
    catch(error){setMessage("Export failed: "+String(error));}finally{setBusy(false);}
  };
  return <>
    <PanelSectionRow><Field label="Crash Session Recorder" description="Recording starts automatically when the Claw overlay library is detected in a process (checked every 5 seconds), including with QAM closed. Ends after 3 consecutive checks without the overlay. Keeps up to 5 sessions (8 MiB telemetry each)."/></PanelSectionRow>
    <PanelSectionRow><ButtonItem layout="below" disabled={!ready||busy||!status} onClick={()=>{void record();}}>{status?.recording?"Stop recording":"Start recording manually"}</ButtonItem></PanelSectionRow>
    <PanelSectionRow><Field label={status?.recording?"Recording session":"Recorder status"} description={status?.error || status?.detection_error || (status?.paused?"Automatic recording paused until the overlay closes. ":"Waiting for overlay detection when idle. ")+"Interrupted sessions indicate an unclean end, not its cause. Missing sensors and unavailable previous-boot logs are reported. FPS is not sampled."}/></PanelSectionRow>
    <PanelSectionRow><Field label="Session for export" description={latest
      ? new Date(latest.started_at*1000).toLocaleString()+" · "+latest.state.replace(/_/g," ")+" · "+latest.samples+" samples"+
        (status?.recording?". A new session is recording; export uses this previous session.":"")
      : status?.recording?"The first session is recording. Stop it before exporting.":"No ended session available yet."}/></PanelSectionRow>
    <PanelSectionRow><ButtonItem layout="below" disabled={!ready||busy||!latest} onClick={()=>{void report();}}>Export Crash Report</ButtonItem></PanelSectionRow>
    <PanelSectionRow><Field label="Report privacy" description="Includes OS, kernel, overlay settings, game IDs, sensors and available system/Decky logs. Common credentials and home usernames are redacted. Review the ZIP before sharing. Upload is manual."/></PanelSectionRow>
    {message&&<PanelSectionRow><div style={{overflowWrap:"anywhere",fontSize:12,padding:"6px 0"}}>{message}</div></PanelSectionRow>}
  </>;
}
