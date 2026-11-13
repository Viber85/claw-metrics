import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import ts from 'typescript';
const navigation=[],events=[];
const module={exports:{}};
runInNewContext(ts.transpileModule(readFileSync('src/modular/editor-page.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,{
 module,exports:module.exports,Promise,
 require:name=>name==='@decky/ui'?{Navigation:{Navigate:p=>navigation.push(['open',p]),CloseSideMenus:()=>navigation.push(['close-qam']),NavigateBack:()=>navigation.push(['back'])}}:
 {callable:()=>async(...args)=>events.push(args)}
});
const {openEditorPage,currentEditorPage,leaveEditorPage,mountEditorPage,releaseEditorPage,disposeEditorPage}=module.exports;
let applied=0;
const props={initial:{},settings:{},onApply:()=>applied++,onSaveStyle:async()=>({presets:{},names:{}})};
for(let cycle=0;cycle<100;cycle++){
 openEditorPage(props);const session=currentEditorPage();
 const count=navigation.length;openEditorPage(props);assert.equal(navigation.length,count,'duplicate editor open is ignored');
 const unmount=mountEditorPage(session.id);
 const before=applied;leaveEditorPage(session.id,cycle%2?()=>props.onApply():undefined);
 const backCount=navigation.filter(n=>n[0]==='back').length;
 leaveEditorPage(session.id,()=>applied++);assert.equal(navigation.filter(n=>n[0]==='back').length,backCount);
 assert.equal(applied,before,'Apply cannot run while the routed editor is mounted');
 unmount();await new Promise(setImmediate);
 assert.equal(currentEditorPage(),undefined);assert.equal(applied,before+(cycle%2));
 releaseEditorPage(session.id);assert.equal(applied,before+(cycle%2),'late cleanup cannot apply twice');
}
openEditorPage(props);let session=currentEditorPage();
const firstCleanup=mountEditorPage(session.id);firstCleanup();
const realCleanup=mountEditorPage(session.id);await new Promise(setImmediate);
assert(currentEditorPage(),'React effect replay must not discard the live page');
realCleanup();await new Promise(setImmediate);assert.equal(currentEditorPage(),undefined,'Steam Back/unmount discards an unapplied draft');
openEditorPage(props);session=currentEditorPage();leaveEditorPage(session.id,()=>applied++);
const before=applied;disposeEditorPage();releaseEditorPage(session.id);await new Promise(setImmediate);
assert.equal(applied,before,'plugin unload discards pending Apply');
assert(events.some(e=>e[0]==='editor_apply_done'));
console.log('PASS 100 routed editor cycles: QAM closes on open, one Back, Apply after unmount, Cancel/back discard, replay guard and unload cleanup. No real Steam focus validation.');
// Render the real Game Mode route component and verify that its Builder receives
// the top-safe inset. Do not add this inset to shared DevLab components.
const routeModule={exports:{}},routeLeaves=[];
const fakeSession={id:42,props:{initial:{},settings:{},onApply:()=>{},onSaveStyle:async()=>({presets:{},names:{}})}};
const element=(type,props)=>({type,props});
runInNewContext(ts.transpileModule(readFileSync('src/pages/EditorPage.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,jsx:ts.JsxEmit.ReactJSX}}).outputText,{
 module:routeModule,exports:routeModule.exports,
 require:name=>name==='react'?{useEffect:()=>{}}:name==='react/jsx-runtime'?{jsx:element,jsxs:element}:
 name==='@decky/ui'?{DialogButton:'button',Navigation:{NavigateBack(){}}}:
 name==='../modular/Builder'?{Builder:'MockBuilder'}:
 name==='../components/UiBoundary'?{UiBoundary:'MockBoundary'}:
 name==='../modular/editor-page'?{currentEditorPage:()=>fakeSession,leaveEditorPage:(...a)=>routeLeaves.push(a),mountEditorPage:()=>()=>{}}:
 (()=>{throw Error('Unknown EditorPage dependency '+name)})()
});
assert.equal(routeModule.exports.STEAMOS_TOP_SAFE_INSET,56);
const route=routeModule.exports.EditorPage();
assert.equal(route.type,'MockBoundary');
const routedBuilder=route.props.children;
assert.equal(routedBuilder.type,'MockBuilder');
assert.equal(routedBuilder.props.topSafeInset,56,'route explicitly reserves SteamOS top status bar');
routedBuilder.props.closeModal();
assert.deepEqual(routeLeaves[0],[42,undefined],'closing the editor retains routed navigation');
console.log('PASS SteamOS route-only top safe area: Builder receives 56px without changing DevLab rendering.');
