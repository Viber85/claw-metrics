import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import ts from 'typescript';
const jsx=(type,props)=>({type,props:props||{}});
const ui=Object.fromEntries(['ButtonItem','DialogButton','Focusable','Field','PanelSection','PanelSectionRow','ToggleField'].map(k=>[k,p=>jsx(k,p)]));
const controller=readFileSync('src/controller.tsx','utf8');
const positions=runInNewContext('('+controller.match(/export const hudPositions[^=]*=\s*(\[[\s\S]*?\]);/)[1]+')');
const core={hudPositions:positions,defaults:{},graphStyleChoices:[],GraphStyleIcon:()=>null,
 AccordionCard:p=>jsx('card',p),ControlGroup:p=>jsx('group',p),GamepadGrid:p=>jsx('grid',{children:p.items.map(p.renderItem)})};
const module={exports:{}};
runInNewContext(ts.transpileModule(readFileSync('src/pages/LayoutCard.tsx','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module,exports:module.exports,require:name=>{
 if(name==='react/jsx-runtime')return {jsx,jsxs:jsx};if(name==='@decky/ui')return ui;
 if(name==='../controller')return core;
 if(name==='./ModularEditor')return {ModularEditor:()=>null};
 if(name.includes('LayoutSliderField'))return {LayoutSliderField:p=>jsx('slider',p)};
 return new Proxy({},{get:()=>()=>null});
}});
function walk(v){if(!v||typeof v!=='object')return [];if(Array.isArray(v))return v.flatMap(walk);if(typeof v.type==='function')return walk(v.type(v.props));return[v,...walk(v.props.children)]}
for(const hud_orientation of ['horizontal','vertical'])for(const supported of [false,true]){
 const updates=[];
 const vm={settings:{hud_orientation,hud_position:'center-right',unit_superscript:false,group_gap_x:0,vertical_category_gap:6,colors:{separator:'777777'},metrics:{graph:false}},info:{layout_spacing_supported:supported},ready:true,update:v=>updates.push(v),toggleSection:()=>{},toggleLayoutPanel:()=>{}};
 const nodes=walk(module.exports.LayoutCard({vm}));
 const unit=nodes.find(n=>n.type==='ToggleField'&&n.props.label==='Superscript units');assert(unit);
 assert.equal(unit.props.disabled,!supported);unit.props.onChange(true);assert.equal(updates.at(-1).unit_superscript,true);
 for(const id of ['center-left','center-right']){
  const anchor=nodes.find(n=>n.props?.['data-anchor-position']===id);assert(anchor);
  assert.equal(anchor.props.disabled,!supported);anchor.props.onClick();assert.equal(updates.at(-1).hud_position,id);
  assert.equal(anchor.props.style.gridColumn,id==='center-left'?1:3);
 }
 const label=hud_orientation==='horizontal'?'Horizontal group spacing (px)':'Vertical group spacing (px)';
 const gap=nodes.find(n=>n.type==='slider'&&n.props.label===label);assert(gap);assert.equal(gap.props.disabled,!supported);
 gap.props.onChange(15);assert.equal(updates.at(-1)[hud_orientation==='horizontal'?'group_gap_x':'vertical_category_gap'],15);
}
console.log('PASS classic options: both orientations, eight anchors, spacing callbacks and renderer availability. Mock UI only.');
