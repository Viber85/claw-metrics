// Appearance only: sensor selection, metric names/order and other slots are not overwritten.
export const styleLayoutKeys = ['sans','fontsize','fps_scale','center_horizontal','hud_position','opacity','rounding','padding_x','padding_y','offset_x','offset_y','element_gap','table_gap','inner_gap','graph_width','graph_style','inline_metrics'] as const;
export function styleLayoutFrom(value:any){
 const result:any={};
 for(const key of styleLayoutKeys){
  const v=value?.[key];
  if(key==='sans'||key==='inline_metrics'||key==='center_horizontal'){if(typeof v==='boolean')result[key]=v}
  else if(key==='hud_position'){if(['top-left','top-center','top-right','bottom-left','bottom-center','bottom-right'].includes(v))result[key]=v}
  else if(key==='graph_style'){if(['area','line','bars','dual'].includes(v))result[key]=v}
  else if(typeof v==='number'&&Number.isFinite(v))result[key]=v;
 }
 if(result.hud_position)result.center_horizontal=result.hud_position.endsWith('center');
 else if(result.center_horizontal===true)result.hud_position='top-center';
 return result;
}
export function independentColors(colors:any,defaults:any){return {...defaults,...colors,time:colors?.time??colors?.text??defaults.text,draw:colors?.draw??colors?.text??defaults.text}}
function stable(value:any):any {if(Array.isArray(value))return value.map(stable);if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(k=>[k,stable(value[k])]));return value}
export function styleModified(preset:any,current:any){
 if(!preset)return false;
 const savedLayout=styleLayoutFrom(preset), activeLayout=styleLayoutFrom(current);
 for(const key of Object.keys(savedLayout)){
  if(JSON.stringify(stable(savedLayout[key]))!==JSON.stringify(stable(activeLayout[key])))return true;
 }
 for(const key of ['font_weight','colors','token_weights','token_colors']){
  if(JSON.stringify(stable(preset[key]??{}))!==JSON.stringify(stable(current[key]??{})))return true;
 }
 return false;
}
