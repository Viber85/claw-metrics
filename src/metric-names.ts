export const groupNames:Record<string,string>={fps:'FPS',frametime:'Frametime',cpu:'CPU',gpu:'GPU',ram:'RAM',vram:'VRAM',battery:'Battery',tdp:'TDP',draw:'DRAW',time:'Clock'};
export function cleanName(value:string){return value.replace(/[\u0000-\u001f\u007f]/g,' ').replace(/\s+/g,' ').trim().slice(0,24)}
export function metricName(settings:any,key:string){return cleanName(String(settings.custom_labels?.[key]||''))||groupNames[key]||key}
export function relatedLabel(settings:any,text:string){return text.replace(/\b(Frametime|Battery|Clock|VRAM|BATT|TDP|DRAW|RAM|CPU|GPU|FPS)\b/g,name=>{const key:Record<string,string>={Frametime:'frametime',Battery:'battery',Clock:'time',BATT:'battery',TDP:'tdp',VRAM:'vram',RAM:'ram',DRAW:'draw',CPU:'cpu',GPU:'gpu',FPS:'fps'};return settings.custom_labels?.[key[name]]?metricName(settings,key[name]):name})}
export function hudName(settings:any,key:string,fallback:string){return settings.custom_labels?.[key]?metricName(settings,key):fallback}
