// Uses the actual preview JSX, embedded fonts and a real headless browser.
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {runInNewContext} from 'node:vm';
import ts from 'typescript';
const [input,output,browser]=process.argv.slice(2);
const cases=JSON.parse(readFileSync(input,'utf8'));
const jsx=(type,props)=>({type,props:props||{}});
function load(file,require=()=>{}){
 const module={exports:{}};
 runInNewContext(ts.transpileModule(readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module,exports:module.exports,require});return module.exports;
}
const metrics=load('src/modular/fps-font-metrics.ts');
const {previewFontCSS}=load('src/modular/preview-fonts.ts');
const {ModularHud,initialData}=load('src/modular/Hud.tsx',name=>{
 if(name==='./fps-font-metrics')return metrics;
 if(name==='react/jsx-runtime')return {jsx,jsxs:jsx};
 if(name==='react')return {useLayoutEffect:()=>{},useRef:()=>({current:null}),useState:init=>[typeof init==='function'?init():init,()=>{}]};
 throw Error(name);
});
const escape=v=>String(v).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const unitless=new Set(['opacity','fontWeight','lineHeight','flexShrink','flexGrow','zIndex','order']);
function html(node){
 if(node===null||node===undefined||typeof node==='boolean')return '';
 if(Array.isArray(node))return node.map(html).join('');
 if(typeof node!=='object')return escape(node);
 if(typeof node.type==='function')return html(node.type(node.props));
 if(typeof node.type!=='string')return html(node.props.children);
 const attrs=Object.entries(node.props).filter(([key,val])=>key!=='children'&&key!=='key'&&!key.startsWith('on')&&val!==undefined).map(([key,value])=>{
  if(key==='style')value=Object.entries(value).filter(([,v])=>v!==undefined).map(([k,v])=>`${k.replace(/[A-Z]/g,c=>'-'+c.toLowerCase())}:${typeof v==='number'&&!unitless.has(k)?v+'px':v}`).join(';');
  return `${key==='className'?'class':key}="${escape(value)}"`;
 }).join(' ');
 return `<${node.type} ${attrs}>${html(node.props.children)}</${node.type}>`;
}
const rendered=cases.map((item,index)=>{
 const settings={enabled:true,sans:true,fontsize:item.size,font_weight:item.weight,unit_superscript:item.units,colors:{text:'FFFFFF'},background:{mode:'solid',color:'#446688',stops:[]},opacity:100,rounding:10};
 return `<section class="parity-case" id="case-${index}">${html(ModularHud({layout:item.layout,settings,data:initialData,selected:'',onSelect:()=>{},editing:false}))}</section>`;
}).join('');
const script=`(async()=>{await document.fonts.ready;await new Promise(requestAnimationFrame);const cases=${JSON.stringify(cases)};const failures=[];let maxError=0;for(let i=0;i<cases.length;i++){const host=document.getElementById('case-'+i),origin=host.getBoundingClientRect();for(const node of host.querySelectorAll('[data-node-id]')){const r=node.getBoundingClientRect(),expected=cases[i].boxes[node.dataset.nodeId],actual=[r.x-origin.x,r.y-origin.y,r.width,r.height];for(let axis=0;axis<4;axis++){const error=Math.abs(actual[axis]-expected[axis]);maxError=Math.max(maxError,error);if(error>.6)failures.push({case:i,id:node.dataset.nodeId,axis,expected:expected[axis],actual:actual[axis]});}}}document.body.dataset.parity=btoa(JSON.stringify({maxError,failures}));})();`;
writeFileSync(output,`<!doctype html><meta charset="utf-8"><style>${previewFontCSS}*{box-sizing:border-box}body{margin:0}.parity-case{position:relative;width:1280px;height:800px}.hud-node{white-space:nowrap;min-width:0}</style>${rendered}<script>${script}</script>`);
const dom=execFileSync(browser,['--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--virtual-time-budget=3000','--dump-dom','file://'+output],{encoding:'utf8',maxBuffer:10000000,timeout:45000,stdio:['ignore','pipe','pipe']});
const encoded=dom.match(/data-parity="([^"]+)"/);if(!encoded)throw Error('Browser did not finish font loading/geometry checks');
const result=JSON.parse(Buffer.from(encoded[1],'base64').toString());
if(result.failures.length){console.error(JSON.stringify(result.failures.sort((a,b)=>Math.abs(b.actual-b.expected)-Math.abs(a.actual-a.expected)).slice(0,16),null,2));throw Error(`${result.failures.length} preview/native coordinate mismatches; max ${result.maxError}px`);}
console.log(`PASS real browser / ImGui padding parity: ${cases.length} cases; max coordinate error ${result.maxError.toFixed(3)}px.`);
