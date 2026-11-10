import rules from '../../assets/overlay-design-rules.json';
import {validate,type Layout} from './model';
export type OverlayDesign={schema:'claw-overlay-design';version:1;layout:Layout;appearance:Record<string,any>};
export const designDefaults=()=>structuredClone(rules.defaults);
export function validateAppearance(value:any):Record<string,any>{
 if(!value||typeof value!=='object'||Array.isArray(value))throw Error('Expected appearance settings');
 const out:any=designDefaults();
 const number=(v:any,lo:number,hi:number)=>{if(typeof v!=='number'||!Number.isInteger(v)||v<lo||v>hi)throw Error('Invalid appearance number');return v};
 const color=(v:any)=>{if(typeof v!=='string'||!/^#?[0-9a-f]{6}$/i.test(v))throw Error('Invalid appearance color');return v.replace('#','').toUpperCase()};
 for(const [key,[lo,hi]] of Object.entries(rules.ranges))if(key in value)out[key]=number(value[key],lo,hi);
 for(const [key,choices] of Object.entries(rules.enums))if(key in value){if(!(choices as string[]).includes(value[key]))throw Error('Invalid '+key);out[key]=value[key]}
 for(const key of rules.booleans)if(key in value){if(typeof value[key]!=='boolean')throw Error('Invalid '+key);out[key]=value[key]}
 for(const [key,allowed] of [['colors',rules.colors],['token_colors',rules.tokens],['token_weights',rules.tokens],['custom_labels',rules.labels]] as [string,string[]][]){
  if(!(key in value))continue;const map=value[key];if(!map||typeof map!=='object'||Array.isArray(map))throw Error('Invalid '+key);
  for(const [token,raw] of Object.entries(map)){if(!allowed.includes(token))continue;let v:any=raw;
   if(key==='token_weights'){if(!rules.enums.font_weight.includes(v))throw Error('Invalid token weight')}
   else if(key==='custom_labels'){if(typeof v!=='string'||Array.from(v).length>24||/[\x00-\x1f\x7f=,]/.test(v))throw Error('Invalid label');v=v.replace(/\s+/g,' ').trim();if(!v)continue}
   else v=color(v);out[key][token]=v;
  }
 }
 if('background' in value){const b=value.background,t=out.background;if(!b||typeof b!=='object'||Array.isArray(b))throw Error('Invalid background');
  for(const k of ['color','outline_color'])if(k in b)t[k]=color(b[k]);
  if('mode' in b){if(!['solid','linear','radial'].includes(b.mode))throw Error('Invalid background mode');t.mode=b.mode}
  if('outline_enabled' in b){if(typeof b.outline_enabled!=='boolean')throw Error('Invalid outline');t.outline_enabled=b.outline_enabled}
  for(const [k,lo,hi] of [['angle',0,360],['outline_width',1,6],['outline_opacity',0,100],['center_x',0,100],['center_y',0,100],['radius',1,200]] as [string,number,number][])if(k in b)t[k]=number(b[k],lo,hi);
  if('stops' in b){if(!Array.isArray(b.stops)||b.stops.length<2||b.stops.length>8)throw Error('Expected 2–8 gradient stops');t.stops=b.stops.map((s:any)=>({position:number(s.position,0,100),color:color(s.color)})).sort((a:any,b:any)=>a.position-b.position)}
 }
 return out;
}
export function parseDesign(text:string):{layout:Layout;appearance:Record<string,any>}{
 if(new TextEncoder().encode(text).length>1024*1024)throw Error('Design exceeds 1 MiB');const v=JSON.parse(text);
 if(v?.schema==='claw-modular-layout')return {layout:validate(v),appearance:{}};
 if(v?.schema!=='claw-overlay-design'||v.version!==1)throw Error('Expected claw-overlay-design v1');
 return {layout:validate(v.layout),appearance:validateAppearance(v.appearance)};
}
export function createDesign(layout:Layout,settings:any):OverlayDesign{return {schema:'claw-overlay-design',version:1,layout:validate(layout),appearance:validateAppearance(settings)}}
export function serializeDesign(layout:Layout,settings:any){return JSON.stringify(createDesign(layout,settings),null,2)+'\n'}
