import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import ts from 'typescript';
const jsx=(type,props)=>({type,props:props||{}});
const metrics={exports:{}};runInNewContext(ts.transpileModule(readFileSync('src/modular/fps-font-metrics.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:metrics,exports:metrics.exports});
let graphHost=null,capturedLayoutEffect,fitted={};
const fakeDocument={fonts:{ready:Promise.resolve()}};
const module={exports:{}};
runInNewContext(ts.transpileModule(readFileSync('src/modular/Hud.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module,exports:module.exports,require:name=>name==='./fps-font-metrics'?metrics.exports:name==='react/jsx-runtime'?{jsx,jsxs:jsx}:name==='react'?{useLayoutEffect:effect=>{capturedLayoutEffect=effect},useRef:()=>({current:graphHost}),useState:initial=>[typeof initial==='function'?initial():initial,next=>{fitted=typeof next==='function'?next(fitted):next}]}:{},console,document:fakeDocument});
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
const line={...structuredClone(gpu.children[1]),id:'test-line',name:'Separator line',token:'separator',axis:'column',width:48,height:4,color:'#ABCDEF',cornerRadius:2,separatorOpacity:40};
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
assert.equal(module.exports.readingReference('54°C','888°C'),'88°C','temperature no longer reserves an invisible third digit');
assert.equal(module.exports.readingReference('12.6 GiB','888.8 GiB'),'88.8 GiB','RAM reserves its current precision only');
assert.equal(module.exports.readingReference('3500 MHz','8888 MHz'),'8888 MHz','clock remains stable for equal digit count');
assert.equal(module.exports.readingReference('','88:88'),'88:88','plugged battery keeps its reference');
const tempReservation=walk(temperature).find(n=>n.type===module.exports.ReservedReading);
assert(tempReservation,'temperature includes the reference component');
assert.equal(tempReservation.props.reference,'88°C','temperature reserves only its two live digits');
const hiddenTemp=module.exports.ReservedReading(tempReservation.props);
assert.equal(hiddenTemp.props['aria-hidden'],'true');
assert.equal(hiddenTemp.props.children[0].props.children.props.children[0].props.children,'88','temperature reservation keeps exactly two digits');
assert.equal(temperature.props.style.paddingLeft,0,'reading has no implicit inset');
settings.unit_superscript=false;
const separator=nodes.find(n=>n.props?.['data-node-id']==='test-line');
const lineStyle=walk(separator).find(n=>n.type==='span').props.style;
assert.equal(lineStyle.width,4);
assert.equal(lineStyle.height,48);
assert.equal(lineStyle.borderRadius,2);
assert.equal(lineStyle.background,'rgba(171,205,239,0.4)');
const inherited=structuredClone(line);inherited.id='global-separator';inherited.color='';inherited.separatorOpacity=undefined;gpu.children.push(inherited);
nodes=walk(ModularHud({layout,settings:{...settings,colors:{...settings.colors,separator:'AA7733'}},data:{gpu:72},selected:'none',onSelect:()=>{}}));
assert.equal(walk(nodes.find(n=>n.props?.['data-node-id']==='global-separator')).find(n=>n.type==='span').props.style.background,'rgba(170,119,51,1)');
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

const {fpsBox,FpsValue}=module.exports;
for(const weight of ['light','regular','semibold','bold'])for(const sans of [false,true]){
 const a=fpsBox('84',weight,sans),b=fpsBox('11',weight,sans),c=fpsBox('100',weight,sans);
 assert.equal(a.width,b.width);assert.equal(a.height,b.height);assert(c.width>a.width);
 const value=FpsValue({value:'84',weight,sans});assert.equal(value.type,'svg');assert.equal(value.props['data-fps-ink'],'true');
 assert.equal(value.props.style.display,'block');assert.equal(value.props.style.overflow,'visible');
 assert.equal(value.props.width,`${a.width/a.metrics.lineUnits}em`);assert.equal(value.props.height,`${a.height/a.metrics.lineUnits}em`);
}
const fpsElement=groupNodes.find(n=>n.props?.['data-node-id']===fps.id);assert.equal(fpsElement.props.style.outlineOffset,0);
console.log('PASS tight FPS preview: same-font SVG ink bounds, fixed digit cells, actual digit count and accurate selection outline.');

const fontModule={exports:{}};
runInNewContext(ts.transpileModule(fonts,{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:fontModule,exports:fontModule.exports});
const adjusted=fontModule.exports.previewFontCSS;
assert.equal((adjusted.match(/size-adjust:83\.33333333333334%/g)||[]).length,4);
assert(adjusted.includes('size-adjust:85.90604026845638%'));
const nativeHost=groupNodes.find(n=>n.props?.className==='modular-hud');
assert.equal(nativeHost.props.style.fontKerning,'none');assert.equal(nativeHost.props.style.letterSpacing,0);
for(const face of Object.values(metrics.exports.fpsFontMetrics))assert(face.lineUnits>face.units);
console.log('PASS preview font scale: STB ascent/descent sizing, no kerning, matching FPS em geometry; browser/ImGui parity is checked separately.');

const reservation=module.exports.ReservedReading({token:'cpu.clock',value:'3500 MHz',reference:'8888 MHz',superscript:true});
assert.equal(reservation.props.style.display,'grid');assert.equal(reservation.props.style.visibility,'hidden');
assert.equal(reservation.props.children.length,3);
assert.equal(reservation.props.children[1].props.children.props.children[0].props.children,'0000');
for(const layer of reservation.props.children){assert.equal(layer.props.style.gridArea,'1 / 1');assert.equal(layer.props.style.display,'flex');}
console.log('PASS reservation layers: live/reference intrinsic maximum and no inherited inline line strut.');

const styled=JSON.parse(readFileSync('assets/modular/vertical.json'));
const styledCpu=styled.root.children.find(n=>n.name==='CPU');styledCpu.cornerRadius=1000;styledCpu.fontWeight='semibold';
const styledLoad=styledCpu.children.find(n=>n.token==='cpu.load');styledLoad.fontWeight='bold';
styledCpu.children.push({...structuredClone(styledLoad),id:'independent-copy',fontWeight:'light'});
function styledPreview(){return walk(ModularHud({layout:styled,settings:{...settings,sans:true,font_weight:'regular',token_weights:{'cpu.label':'regular'}},data:module.exports.initialData,selected:'none',onSelect:()=>{}}))}
let styledNodes=styledPreview();
const byId=id=>styledNodes.find(n=>n.props?.['data-node-id']===id);
assert.equal(byId(styledCpu.id).props.style.borderRadius,1000);
assert.equal(byId(styledCpu.children.find(n=>n.token==='cpu.label').id).props.style.fontWeight,600,'group overrides plugin token styling');
assert.equal(byId(styledLoad.id).props.style.fontWeight,700,'reading overrides group');
assert.equal(byId('independent-copy').props.style.fontWeight,300,'duplicate token can have an independent face');
delete styledLoad.fontWeight;styledNodes=styledPreview();assert.equal(byId(styledLoad.id).props.style.fontWeight,600);
delete styledCpu.fontWeight;styledNodes=styledPreview();assert.equal(byId(styledCpu.children.find(n=>n.token==='cpu.label').id).props.style.fontWeight,400,'automatic restores plugin styling');
console.log('PASS preview radius and font inheritance: group/plugin precedence and independent duplicate readings.');

let fontReadyResolve;fakeDocument.fonts.ready=new Promise(resolve=>{fontReadyResolve=resolve});
const sibling={offsetWidth:160};const autoGraph={dataset:{nodeId:'font-graph',padding:'7'}};
autoGraph.parentElement={children:[sibling,autoGraph]};graphHost={querySelectorAll:()=>[autoGraph]};
ModularHud({layout:styled,settings,data:module.exports.initialData,selected:'none',onSelect:()=>{}});
const stopFontPass=capturedLayoutEffect();assert.equal(fitted['font-graph'],146);
sibling.offsetWidth=220;fontReadyResolve();await new Promise(setImmediate);
assert.equal(fitted['font-graph'],206,'auto graph remeasures when the selected font face finishes loading');stopFontPass();
fakeDocument.fonts.ready=new Promise(resolve=>{fontReadyResolve=resolve});
ModularHud({layout:styled,settings,data:module.exports.initialData,selected:'none',onSelect:()=>{}});
const stopUnmounted=capturedLayoutEffect();stopUnmounted();sibling.offsetWidth=300;fontReadyResolve();await new Promise(setImmediate);
assert.equal(fitted['font-graph'],206,'font completion after unmount cannot update the preview');graphHost=null;
console.log('PASS font loading: guarded auto-graph width refresh and no update after unmount.');
