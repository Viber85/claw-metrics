export type ReportSession = {id:string;state:string;started_at:number;samples:number};
const endedStates=new Set(['stopped','interrupted','overlay_unloaded','plugin_unloaded','size_limit']);
/** Latest ended session by its recorded start time; never select a live recording. */
export function latestReportSession(sessions:ReportSession[]|undefined):ReportSession|undefined {
 return sessions?.filter(s=>endedStates.has(s.state)&&typeof s.id==='string'&&s.id.length>0&&Number.isFinite(s.started_at))
  .sort((a,b)=>b.started_at-a.started_at)[0];
}
