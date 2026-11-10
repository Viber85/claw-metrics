import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM,VirtualConsole} from 'jsdom';
const errors=[],downloads=[];
const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e));
const dom=new JSDOM(readFileSync('devlab/public/index.html','utf8'),{url:'https://devlab.test/',runScripts:'dangerously',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){w.structuredClone=structuredClone;w.TextEncoder=TextEncoder;w.Blob=Blob;w.confirm=()=>true;w.URL.createObjectURL=blob=>{downloads.push(blob);return 'blob:devlab'};w.URL.revokeObjectURL=()=>{};w.HTMLAnchorElement.prototype.click=function(){};w.ResizeObserver=class{observe(){}disconnect(){}};}});
const wait=()=>new Promise(r=>setTimeout(r,50));
const {document}=dom.window;
const button=label=>{const el=[...document.querySelectorAll('button')].find(v=>v.textContent===label);assert(el,'Missing '+label);return el};
try{
 await wait();assert(document.querySelector('[aria-label="Overlay preview"]'));
 assert(document.querySelectorAll('.hud-node').length>8);
 button('Export JSON').click();await wait();assert.equal(downloads.length,1);
 let design=JSON.parse(await downloads[0].text());assert.equal(design.schema,'claw-overlay-design');assert.equal(design.version,1);assert.equal(design.appearance.fontsize,18);assert.equal(design.layout.root.axis,'row');
 assert.equal(JSON.parse(dom.window.localStorage.getItem('claw-devlab-design-v1')).schema,'claw-overlay-design');
 button('Vertical').click();await wait();assert.equal(document.querySelector('.claw-builder').dataset.orientation,'vertical');
 button('Export JSON').click();await wait();design=JSON.parse(await downloads[1].text());assert.equal(design.layout.root.axis,'column');
 // Exercise a real draft edit through the browser adapter, then export current state.
 const select=[...document.querySelectorAll('select')].find(s=>[...s.options].some(o=>o.textContent==='Row →'));
 if(select){select.value='row';select.dispatchEvent(new dom.window.Event('change',{bubbles:true}));await wait()}
 button('Export JSON').click();await wait();design=JSON.parse(await downloads[2].text());assert.equal(design.layout.root.axis,'row');
 assert.equal(errors.length,0,errors.map(e=>e.message).join('\n'));
 console.log('PASS DevLab integration: actual shared Builder mounts, horizontal/vertical templates, live draft edit, JSON download, local draft and no runtime errors. DOM test; no native controller or visual validation.');
}finally{dom.window.close()}
