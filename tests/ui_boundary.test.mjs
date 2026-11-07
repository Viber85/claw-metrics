import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import ts from 'typescript';
const events=[];let closed=0;
class Component{constructor(props){this.props=props}}
const module={exports:{}};
runInNewContext(ts.transpileModule(readFileSync('src/components/UiBoundary.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,jsx:ts.JsxEmit.ReactJSX}}).outputText,{
 module,exports:module.exports,console:{error(){}},
 require:name=>name==='react'?{Component}:name==='react/jsx-runtime'?{jsx:(type,props)=>({type,props}),jsxs:(type,props)=>({type,props})}:
 name==='@decky/ui'?{Focusable:'focus',DialogButton:'button',Navigation:{CloseSideMenus(){closed++}}}:{traceEditor:(...args)=>events.push(args)}
});
const boundary=new module.exports.UiBoundary({children:'working panel'});
assert.equal(boundary.render(),'working panel');
boundary.state=module.exports.UiBoundary.getDerivedStateFromError();boundary.componentDidCatch(new Error('render failed'));
const fallback=boundary.render();assert.equal(fallback.type,'focus');
assert(events.some(row=>row[0]==='ui_error'&&row[1].includes('render failed')));
fallback.props.children.find(node=>node.type==='button').props.onClick();assert.equal(closed,1);
let prevented=false,stopped=false;fallback.props.onCancelButton({preventDefault(){prevented=true},stopPropagation(){stopped=true}});
assert(prevented&&stopped);assert.equal(closed,2);
console.log('PASS UI fallback: render error is recorded, visible close action and guarded Cancel. Actual Steam input focus untested.');
