import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import ts from 'typescript';
const jsx=(type,props)=>({type,props:props||{}});
const module={exports:{}};
runInNewContext(ts.transpileModule(readFileSync('src/modular/Hud.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module,exports:module.exports,require:name=>name==='react/jsx-runtime'?{jsx,jsxs:jsx}:name==='react'?{useLayoutEffect:()=>{},useRef:()=>({current:null}),useState:initial=>[typeof initial==='function'?initial():initial,()=>{}]}:{},console});
const {ModularHud,unitParts,readingText}=module.exports;
assert.equal(unitParts('cpu.temp','54°C').join('|'),'54|°C');
assert.equal(unitParts('gpu.clock','1750 MHz').join('|'),'1750|MHz');
assert.equal(unitParts('ram.value','12.6 GiB').join('|'),'12.6|GiB');
assert.equal(unitParts('fps.ms','11.9 ms').join('|'),'11.9|ms');
assert.equal(unitParts('gpu.temp','--').join('|'),'--|');
for(const enabled of [false,true])for(const [token,value,unit] of [['cpu.power','8.6 W','W'],['battery.power','DRAW 27 W','W'],['tdp.value','TDP 28 W','W'],['ram.value','12.6 GiB','GiB'],['gpu.clock','1750 MHz','MHz'],['fps.ms','11.9 ms','ms']]){
 const output=readingText(token,value,enabled);
 assert.equal(output.props.style.columnGap,'.14em');
 assert(!output.props.children[0].props.children.endsWith(' '));
 assert.equal(output.props.children[1].props.children,unit);
 assert.equal(output.props.children[1].props.style.fontSize,enabled?'.7em':'1em');
}
const layout=JSON.parse(readFileSync('assets/modular/horizontal.json'));
const gpu=layout.root.children.find(n=>n.name==='GPU');
gpu.align='center';gpu.children[1].selfAlign='start';
const line={...structuredClone(gpu.children[1]),id:'test-line',name:'Separator line',token:'separator',width:160,height:2,color:'#ABCDEF'};
gpu.children.push(line);
const settings={enabled:true,sans:true,fontsize:18,font_weight:'regular',fps_scale:100,colors:{text:'F0F2F5',graph:'30E5A0'},background:{mode:'solid',color:'#111820',stops:[]},opacity:80,rounding:6,graph_style:'line'};
function walk(n){if(!n||typeof n!=='object')return [];if(Array.isArray(n))return n.flatMap(walk);return[n,...walk(n.props?.children)]}
let nodes=walk(ModularHud({layout,settings,data:{gpu:72},selected:'none',onSelect:()=>{}}));
assert.equal(nodes.find(n=>n.props?.className==='modular-hud').props.style.fontFamily,'ClawPreviewBarlow');
settings.fps_scale=200;
const fps=layout.root.children.find(n=>n.name==='FPS').children.find(n=>n.token==='fps.value');
nodes=walk(ModularHud({layout,settings,data:{gpu:72},selected:'none',onSelect:()=>{}}));
assert.equal(nodes.find(n=>n.props?.['data-node-id']===fps.id).props.style.fontSize,`${fps.scale/100}em`,'native modular text size uses node scale, without classic FPS multiplier');
const reading=nodes.find(n=>n.props?.['data-node-id']===gpu.children[1].id);
assert.equal(walk(reading).find(n=>n.type==='span'&&n.props.style?.textAlign).props.style.textAlign,'start','individual metric aligns its ink left inside the reserved width');
settings.unit_superscript=true;
nodes=walk(ModularHud({layout,settings,data:{gpu:72,gpuTemp:52},selected:'none',onSelect:()=>{}}));
const temperature=nodes.find(n=>n.props?.['data-node-id']===gpu.children.find(n=>n.token==='gpu.temp').id);
assert(walk(temperature).some(n=>n.type==='span'&&n.props.style?.fontSize==='.7em'&&n.props.children==='°C'));
settings.unit_superscript=false;
const separator=nodes.find(n=>n.props?.['data-node-id']==='test-line');
assert.equal(walk(separator).find(n=>n.type==='span').props.style.height,2);
assert.equal(walk(separator).find(n=>n.type==='span').props.style.background,'#ABCDEF');
const inherited=structuredClone(line);inherited.id='global-separator';inherited.color='';gpu.children.push(inherited);
nodes=walk(ModularHud({layout,settings:{...settings,colors:{...settings.colors,separator:'AA7733'}},data:{gpu:72},selected:'none',onSelect:()=>{}}));
assert.equal(walk(nodes.find(n=>n.props?.['data-node-id']==='global-separator')).find(n=>n.type==='span').props.style.background,'#AA7733');
settings.sans=false;
nodes=walk(ModularHud({layout,settings,data:{gpu:72},selected:'none',onSelect:()=>{}}));
assert.equal(nodes.find(n=>n.props?.className==='modular-hud').props.style.fontFamily,'ClawPreviewSans');
const fonts=readFileSync('src/modular/preview-fonts.ts','utf8');
for(const weight of [300,400,600,700])assert(fonts.includes(`font-weight:${weight}`));
assert.equal((fonts.match(/data:font\/woff2;base64,/g)||[]).length,5);
console.log('PASS modular preview: bundled native font faces, individual left text alignment, separator geometry and color.');

for(const anchor of ['center-left','center-right'])for(const y of [-25,0,25]){
 const placed={...layout,anchor,x:18,y};
 const host=walk(ModularHud({layout:placed,settings,data:{gpu:72},selected:'none',onSelect:()=>{}})).find(n=>n.props?.className==='modular-hud');
 assert.equal(host.props.style.top,`calc(50% + ${y}px)`);
 assert.equal(host.props.style.transform,'translateY(-50%)');
 assert.equal(host.props.style[anchor==='center-left'?'left':'right'],18);
 assert.equal(host.props.style.bottom,undefined);
}

const tdpNode=(function find(n){return n.token==='tdp.value'?n:n.children.map(find).find(Boolean)})(layout.root);
const tdpSettings={...settings,sans:true,token_colors:{'tdp.label':'FFAC12','tdp.value':'DDEEFF'},token_weights:{'tdp.label':'bold','tdp.value':'light'},custom_labels:{tdp:'Power Limit'}};
for(const enabled of [false,true]){
 const output=walk(ModularHud({layout,settings:{...tdpSettings,unit_superscript:enabled},data:{tdp:20},selected:'none',onSelect:()=>{}}));
 const row=output.find(n=>n.props?.['data-node-id']===tdpNode.id);
 assert.equal(row.props.style.color,'#DDEEFF');assert.equal(row.props.style.fontWeight,300);
 const title=walk(row).find(n=>n.props?.['data-tdp-part']==='label');
 assert.equal(title.props.style.color,'#FFAC12');assert.equal(title.props.style.fontWeight,700);assert.equal(title.props.children,'Power Limit');
 assert.equal(walk(row).filter(n=>n.props?.children==='Power Limit').length,1);
}
console.log('PASS modular TDP preview: independent category/value colors and weights, custom title and both unit modes.');

// Raw older layouts also preview without group insets before normalization.
for(const node of [layout.root,gpu])node.padding=77;
layout.root.gap=240;gpu.gap=0;
nodes=walk(ModularHud({layout,settings,data:{gpu:72},selected:'none',onSelect:()=>{}}));
assert.equal(nodes.find(n=>n.props?.['data-node-id']===layout.root.id).props.style.padding,0);
assert.equal(nodes.find(n=>n.props?.['data-node-id']===gpu.id).props.style.padding,0);
assert.equal(nodes.find(n=>n.props?.['data-node-id']===layout.root.id).props.style.gap,240);
assert.equal(nodes.find(n=>n.props?.['data-node-id']===gpu.id).props.style.gap,0);
console.log('PASS preview: legacy group padding ignored and independent parent/internal gaps retained.');

const {batteryTime}=module.exports;
for(const status of ['Charging','Full','Not charging'])for(const hours of [0,-1,2.25,Infinity,NaN]){
 const result=batteryTime(1,status,hours);assert.equal(result.plugged,true);assert.equal(result.text,'');
}
for(const hours of [0,-1,100,1e30,Infinity,NaN])assert.equal(batteryTime(1,'Discharging',hours).text,'--');
assert.equal(batteryTime(1,'Discharging',2.25).text,'02:15');assert.equal(batteryTime(1,'Unknown',2.25).text,'--');
assert.equal(batteryTime(0,'Charging',Infinity).plugged,false);
for(const token of ['fps.label','cpu.label','gpu.label','ram.label','vram.label','battery.label','time.value','fps.average','fps.low1','battery.time']){
 const row=readingText(token,'88',true);assert.equal(row.props.style.height,'1.18em');assert.equal(row.props.children[0].props.style.paddingTop,'.18em');
}
const battery=modelBattery(layout.root);
function modelBattery(n){return n.token==='battery.time'?n:n.children.map(modelBattery).find(Boolean)}
if(!battery){gpu.children.push({...line,id:'battery-time-test',token:'battery.time',padding:0});}
const charging=walk(ModularHud({layout,settings,data:{batteryStatus:'Charging',batteryHours:Infinity},selected:'none',onSelect:()=>{}}));
const plugged=charging.find(n=>n.props?.['data-node-id']===(battery?.id||'battery-time-test'));
assert(walk(plugged).some(n=>n.type===module.exports.Plug));
assert(!textOf(plugged).includes('Infinity'));assert(!textOf(plugged).includes('-2147483648'));
function textOf(n){return typeof n==='string'?n:Array.isArray(n)?n.map(textOf).join(''):n&&typeof n==='object'?textOf(n.props?.children):''}
console.log('PASS battery preview: plugged/full/charge-limit, safe unavailable estimates and common label/value line boxes.');

assert.equal(batteryTime(1,'Unknown',Infinity,true).plugged,true);assert.equal(batteryTime(1,'Discharging',2.25,true).plugged,true);

const paddedNodes=walk(ModularHud({layout:{...layout,paddingX:27,paddingY:13},settings:{...settings,rounding:1000},data:{},selected:'none',onSelect:()=>{}}));
const overlayNode=paddedNodes.find(n=>n.props?.['data-node-id']===layout.root.id);
assert.equal(overlayNode.props.style.paddingLeft,27);assert.equal(overlayNode.props.style.paddingRight,27);
assert.equal(overlayNode.props.style.paddingTop,13);assert.equal(overlayNode.props.style.paddingBottom,13);
assert.equal(overlayNode.props.style.borderRadius,1000);
assert.equal(paddedNodes.find(n=>n.props?.['data-node-id']===gpu.id).props.style.paddingLeft,0);

gpu.paddingX=19;gpu.paddingY=7;gpu.outline=true;gpu.outlineWidth=4;gpu.outlineOpacity=35;gpu.outlineColor='#FFAACC';
const groupNodes=walk(ModularHud({layout,settings,data:{},selected:'none',onSelect:()=>{}}));
const groupNode=groupNodes.find(n=>n.props?.['data-node-id']===gpu.id);
assert.equal(groupNode.props.style.paddingLeft,19);assert.equal(groupNode.props.style.paddingTop,7);
assert.equal(groupNode.props.style.boxShadow,'inset 0 0 0 4px rgba(255,170,204,0.35)');
