import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {build} from 'esbuild';
const temp=mkdtempSync(join(tmpdir(),'claw-design-'));
try{
 const output=join(temp,'design.mjs');await build({entryPoints:['src/modular/design.ts'],bundle:true,platform:'node',format:'esm',outfile:output});
 const {parseDesign,createDesign,designDefaults}=await import(pathToFileURL(output));
 const layout=JSON.parse(readFileSync('assets/modular/horizontal.json','utf8'));
 const look={...designDefaults(),fontsize:24,token_weights:{'cpu.temp':'bold'},token_colors:{'gpu.temp':'#123abc'},custom_labels:{cpu:'Processor'}};
 layout.paddingX=19;layout.paddingY=7;layout.root.children[0].fontWeight='light';
 const design=createDesign(layout,look),text=JSON.stringify(design);
 const backend=spawnSync('python',['-c','import sys,json;from claw_design import load_design;print(json.dumps(load_design(sys.stdin.read())))'],{input:text,encoding:'utf8'});
 assert.equal(backend.status,0,backend.stderr);assert.deepEqual(parseDesign(text),{layout:JSON.parse(backend.stdout).layout,appearance:JSON.parse(backend.stdout).appearance});
 assert.deepEqual(parseDesign(JSON.stringify(layout)).appearance,{});
 assert.throws(()=>parseDesign(JSON.stringify({...design,version:2})),/v1/);
 assert.throws(()=>createDesign(layout,{...look,fontsize:100}),/number/);
 assert.throws(()=>createDesign(layout,{...look,colors:{text:'invalid'}}),/color/);
 assert.throws(()=>parseDesign(' '.repeat(1024*1024+1)),/1 MiB/);
 const filtered=createDesign(layout,{...look,command:'no',config_path:'/tmp/x',enabled:false});assert(!('command' in filtered.appearance));assert(!('enabled' in filtered.appearance));
 console.log('PASS portable design: browser/Python parity, font/colors/labels/insets, legacy import, version/size/type rejection and operational-setting exclusion.');
}finally{rmSync(temp,{recursive:true,force:true})}
