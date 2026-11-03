import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import ts from 'typescript';
const doc=JSON.parse(readFileSync('assets/modular/horizontal.json','utf8'));
const vertical=JSON.parse(readFileSync('assets/modular/vertical.json','utf8'));
const state=[],updates=[],calls=[];let cursor=0,failImport=false;
const jsx=(type,props)=>({type,props:props||{}});
const ui=Object.fromEntries(['ButtonItem','DialogButton','Field','PanelSectionRow','ToggleField','ConfirmModal'].map(k=>[k,p=>jsx(k==='ButtonItem'||k==='DialogButton'?'button':k,p)]));
let modal;ui.showModal=value=>{modal=value;return {Close(){}}};
const api={FileSelectionType:{FILE:0},openFilePicker:async()=>({realpath:'/tmp/import.json'}),callable:route=>async(...args)=>{
 calls.push([route,args]);
 if(route==='get_modular_preset')return structuredClone(args[0]==='vertical'?vertical:doc);
 if(route==='get_modular_info')return {home:'/home/test'};
 if(route==='import_modular_layout'){if(failImport)throw new Error('Invalid JSON');return structuredClone(doc)}
 if(route==='export_modular_layout')return {path:'/home/test/export.json'};
 throw new Error(route);
}};
const source=ts.transpileModule(readFileSync('src/pages/ModularEditor.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,jsx:ts.JsxEmit.ReactJSX}}).outputText;
const module={exports:{}};
runInNewContext(source,{module,exports:module.exports,require:name=>{
 if(name==='react')return {useEffect:()=>{},useState:initial=>{const i=cursor++;if(!(i in state))state[i]=initial;return [state[i],next=>state[i]=typeof next==='function'?next(state[i]):next]}};
 if(name==='react/jsx-runtime')return {jsx,jsxs:jsx};
 if(name==='@decky/api')return api;
 if(name==='@decky/ui')return ui;
 if(name.includes('modular/Builder'))return {Builder:'Builder'};
 if(name.includes('LayoutSliderField'))return {LayoutSliderField:p=>jsx('slider',p)};
 if(name.includes('GamepadGrid'))return {GamepadGrid:p=>jsx('grid',{children:p.items.map(p.renderItem)})};
 if(name.includes('ControlGroup'))return {ControlGroup:p=>jsx('group',p)};
 throw new Error(name);
},JSON});
const vm={ready:true,settings:{modular_enabled:false,modular_layout:null},update:value=>{updates.push(value);vm.settings={...vm.settings,...value}}};
function walk(value){if(!value||typeof value!=='object')return [];if(Array.isArray(value))return value.flatMap(walk);if(typeof value.type==='function')return walk(value.type(value.props));return [value,...walk(value.props.children)]}
function render(){cursor=0;return walk(module.exports.ModularEditor({vm}))}
const text=value=>Array.isArray(value)?value.map(text).join(''):value&&typeof value==='object'?text(value.props?.children):String(value??'');
const button=label=>{const value=render().find(n=>n.type==='button'&&text(n.props.children)===label);assert(value,'Missing '+label);return value};
assert(button('Export current layout').props.disabled);
button('↔ Horizontal').props.onClick();assert.equal(vm.settings.modular_layout,null);
modal.props.onCancel();assert.equal(vm.settings.modular_layout,null);
button('↔ Horizontal').props.onClick();modal.props.onOK();await new Promise(setImmediate);
assert(vm.settings.modular_enabled);assert.equal(vm.settings.modular_layout.root.id,doc.root.id);
button('Open Layout builder').props.onClick();assert(modal);
const draft=structuredClone(modal.props.initial);draft.root.gap=13;
assert.equal(vm.settings.modular_layout.root.gap,doc.root.gap);
modal.props.onApply(draft);assert.equal(vm.settings.modular_layout.root.gap,13);
button('Export current layout').props.onClick();await new Promise(setImmediate);
assert.equal(calls.findLast(([route])=>route==='export_modular_layout')[1][0].root.gap,13);
const before=JSON.stringify(vm.settings.modular_layout);failImport=true;
button('Import DevLab JSON').props.onClick();await new Promise(setImmediate);
assert.equal(JSON.stringify(vm.settings.modular_layout),before);
assert(render().some(n=>n.props.role==='status'&&text(n.props.children).includes('Invalid JSON')));
failImport=false;button('Import DevLab JSON').props.onClick();await new Promise(setImmediate);
assert.equal(vm.settings.modular_layout.root.gap,doc.root.gap);
button('↕ Vertical').props.onClick();modal.props.onOK();await new Promise(setImmediate);
assert.equal(vm.settings.modular_layout.root.axis,'column');
const toggle=render().find(n=>n.type==='ToggleField'&&n.props.label==='Use editable renderer (test)');toggle.props.onChange(false);assert(!vm.settings.modular_enabled);
console.log('PASS modular UI: preset selection, group edit, export latest document, rejected import retention, valid import and legacy toggle. Mock controls do not establish gamepad navigation.');
