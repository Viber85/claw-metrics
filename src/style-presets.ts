// Appearance only: sensor selection, metric names/order and other slots are not overwritten.
export const styleLayoutKeys = ['sans','fontsize','opacity','rounding','padding_x','padding_y','offset_x','offset_y','element_gap','table_gap','inner_gap','graph_width','inline_metrics'] as const;
export function styleLayoutFrom(value:any){
 const result:any={};
 for(const key of styleLayoutKeys){
  const v=value?.[key];
  if(key==='sans'||key==='inline_metrics'){if(typeof v==='boolean')result[key]=v}
  else if(typeof v==='number'&&Number.isFinite(v))result[key]=v;
 }
 return result;
}
export function independentColors(colors:any,defaults:any){return {...defaults,...colors,time:colors?.time??colors?.text??defaults.text,draw:colors?.draw??colors?.text??defaults.text}}
function stable(value:any):any {if(Array.isArray(value))return value.map(stable);if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(k=>[k,stable(value[k])]));return value}
export function styleModified(preset:any,current:any){
 if(!preset)return false;
 for(const key of [...Object.keys(styleLayoutFrom(preset)),'font_weight','colors','token_weights','token_colors']){
  if(JSON.stringify(stable(preset[key]??{}))!==JSON.stringify(stable(current[key]??{})))return true;
 }
 return false;
}
