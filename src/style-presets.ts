// A style snapshots appearance + enabled metric groups/submetrics. Renamed labels and
// manual metric order remain global; legacy appearance-only styles stay compatible.
export const styleLayoutKeys = ['sans','fontsize','fps_scale','center_horizontal','hud_position','hud_orientation','vertical_width','vertical_value_gap','vertical_category_gap','vertical_graph_width','vertical_graph_height','vertical_graph_style','opacity','rounding','padding_x','padding_y','offset_x','offset_y','element_gap','table_gap','inner_gap','graph_width','graph_style','inline_metrics'] as const;
export function styleLayoutFrom(value:any){
 const result:any={};
 for(const key of styleLayoutKeys){
  const v=value?.[key];
  if(key==='sans'||key==='inline_metrics'||key==='center_horizontal'){if(typeof v==='boolean')result[key]=v}
  else if(key==='hud_position'){if(['top-left','top-center','top-right','bottom-left','bottom-center','bottom-right'].includes(v))result[key]=v}
  else if(key==='hud_orientation'){if(v==='horizontal'||v==='vertical')result[key]=v}
  else if(key==='graph_style'){if(['area','line','bars','dual','smooth','dual_layer'].includes(v))result[key]=v}
  else if(key==='vertical_graph_style'){if(['area','line','bars','dual','smooth','dual_layer'].includes(v))result[key]=v}
  else if(typeof v==='number'&&Number.isFinite(v))result[key]=v;
 }
 // Legacy vertical style slots stored only graph_style. Preserve their choice.
 if(result.hud_orientation==='vertical' && !result.vertical_graph_style && result.graph_style)
  result.vertical_graph_style=result.graph_style;
 if(result.hud_position)result.center_horizontal=result.hud_position.endsWith('center');
 else if(result.center_horizontal===true)result.hud_position='top-center';
 return result;
}
export const styleGroupKeys = ['fps','frametime','cpu','gpu','ram','vram','battery','tdp','draw','time'] as const;
export const styleMetricKeys = ['fps_average','fps_low1','ram_game','ram_swap','fps_ms','graph','cpu_temp','cpu_mhz','cpu_power','gpu_temp','gpu_junction_temp','gpu_core_clock','gpu_mem_clock','gpu_mem_temp','gpu_power','gpu_fan','gpu_voltage','battery_icon','battery_time'] as const;

// Only boolean values and known IDs are restored. An older style that has no
// groups/metrics fields must NOT unexpectedly reset a user's metric choices.
export function styleMetricSelectionsFrom(value:any){
 const groups:Record<string,boolean>={};
 const metrics:Record<string,boolean>={};
 for(const key of styleGroupKeys){
  if(typeof value?.groups?.[key]==='boolean')groups[key]=value.groups[key];
 }
 for(const key of styleMetricKeys){
  if(typeof value?.metrics?.[key]==='boolean')metrics[key]=value.metrics[key];
 }
 return {groups,metrics};
}
export function styleMetricSnapshotFrom(current:any){
 const groups:Record<string,boolean>={};
 const metrics:Record<string,boolean>={};
 for(const key of styleGroupKeys){
  if(typeof current?.[key]==='boolean')groups[key]=current[key];
 }
 for(const key of styleMetricKeys){
  if(typeof current?.metrics?.[key]==='boolean')metrics[key]=current.metrics[key];
 }
 return {groups,metrics};
}
export function styleMetricUpdatesFrom(preset:any,current:any){
 const saved=styleMetricSelectionsFrom(preset);
 return {...saved.groups,...(Object.keys(saved.metrics).length
  ? {metrics:{...current?.metrics,...saved.metrics}} : {})};
}
export function independentColors(colors:any,defaults:any){return {...defaults,...colors,time:colors?.time??colors?.text??defaults.text,draw:colors?.draw??colors?.text??defaults.text}}
function stable(value:any):any {if(Array.isArray(value))return value.map(stable);if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(k=>[k,stable(value[k])]));return value}
export function styleModified(preset:any,current:any){
 if(!preset)return false;
 const savedLayout=styleLayoutFrom(preset), activeLayout=styleLayoutFrom(current);
 for(const key of Object.keys(savedLayout)){
  if(JSON.stringify(stable(savedLayout[key]))!==JSON.stringify(stable(activeLayout[key])))return true;
 }
 const selected=styleMetricSelectionsFrom(preset);
 for(const [key,value] of Object.entries(selected.groups)){
  if(current?.[key]!==value)return true;
 }
 for(const [key,value] of Object.entries(selected.metrics)){
  if(current?.metrics?.[key]!==value)return true;
 }
 for(const key of ['font_weight','colors','token_weights','token_colors']){
  if(JSON.stringify(stable(preset[key]??{}))!==JSON.stringify(stable(current[key]??{})))return true;
 }
 return false;
}
