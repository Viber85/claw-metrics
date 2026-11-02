// Regression for the native Steam Item contract: a blank label does not remove
// the fixed inline children column. Request below/max explicitly, keep callbacks.
// This is not a test of SteamOS's native DOM or controller navigation.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import ts from 'typescript';
const source=readFileSync('src/components/LayoutSliderField.tsx','utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
const NativeSlider=()=>{};
const module={exports:{}};
const jsx=(type,props)=>({type,props});
runInNewContext(compiled,{module,exports:module.exports,require:id=>{
 if(id==='@decky/ui')return {SliderField:NativeSlider};
 if(id==='react/jsx-runtime')return {jsx,jsxs:jsx};
 throw Error(id);
}});
const walk=node=>node&&typeof node==='object'?[node,...[node.props?.children].flat().flatMap(walk)]:[];
for(const value of [0,50,100]){
 let changed;
 const tree=module.exports.LayoutSliderField({label:'Position (%)',value,min:0,max:100,step:1,onChange:v=>changed=v});
 const node=walk(tree).find(n=>n.type===NativeSlider);
 assert.equal(node.props.layout,'below');
 assert.equal(node.props.childrenContainerWidth,'max');
 assert.equal(node.props.showValue,false);
 assert.equal(node.props.value,value);
 node.props.onChange(100-value);assert.equal(changed,100-value);
 assert.equal(walk(tree).find(n=>n.type==='output').props.children,String(value));
}
const background=readFileSync('src/pages/BackgroundEditor.tsx','utf8');
assert.match(background,/<PanelSectionRow><div className="claw-background-slider claw-layout-slider">/);
console.log('Shared slider: full-width Decky contract, endpoint callbacks, complete numeric label and Background inset row passed; device geometry remains untested.');
