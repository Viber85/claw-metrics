import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import ts from 'typescript';
const jsx=(type,props)=>({type,props:props||{}}),state=[];let cursor=0,applied,appliedAppearance,closed=false,saveStyleHandler,styleSettings={},picker;
const ui=Object.fromEntries(['ConfirmModal','ModalRoot','DialogButton','DropdownItem','Focusable','TextField','ToggleField'].map(k=>[k,p=>jsx(k,p)]));
ui.showModal=value=>{picker=value;return {Close(){},ClosedPromise:Promise.resolve()}};
function load(path,require=()=>{throw Error('Unexpected import')}){const module={exports:{}};runInNewContext(ts.transpileModule(readFileSync(path,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,jsx:ts.JsxEmit.ReactJSX}}).outputText,{module,exports:module.exports,require,structuredClone,console});return module.exports}
const model=load('src/modular/model.ts');
const styles=load('src/style-presets.ts');
const {Builder,previewCanvasSize}=load('src/modular/Builder.tsx',name=>{
 if(name==='react')return {useEffect:()=>{},useRef:initial=>({current:initial??null}),useState:initial=>{const i=cursor++;if(!(i in state))state[i]=typeof initial==='function'?initial():initial;return[state[i],next=>state[i]=typeof next==='function'?next(state[i]):next]}};
 if(name==='react/jsx-runtime')return {jsx,jsxs:jsx};
 if(name==='@decky/ui')return ui;
 if(name==='./model')return model;
 if(name==='../style-presets')return styles;
 if(name==='./Hud')return {ModularHud:'preview',initialData:{}};
 if(name==='./preview-fonts')return {previewFontCSS:'@font-face{font-family:ClawPreviewBarlow}'};
 if(name.includes('LayoutSliderField'))return {LayoutSliderField:p=>jsx('slider',p)};
 if(name.includes('controller'))return {OpaqueColorPicker:'color',graphStyleChoices:[{id:'line',label:'Line'},{id:'bars',label:'Histogram'}]};
 throw Error(name);
});
const initial=JSON.parse(readFileSync('assets/modular/two-rows.json'));
function walk(v){if(!v||typeof v!=='object')return [];if(Array.isArray(v))return v.flatMap(walk);if(typeof v.type==='function')return walk(v.type(v.props));return[v,...walk(v.props.children)]}
function renderTree(){cursor=0;return Builder({initial,settings:{rounding:10,opacity:80,graph_style:'line',...styleSettings},onSaveStyle:saveStyleHandler,onApply:(d,a)=>{applied=d;appliedAppearance=a},closeModal:()=>closed=true})}
function render(){return walk(renderTree())}
const text=v=>Array.isArray(v)?v.map(text).join(''):v&&typeof v==='object'?text(v.props?.children):String(v??'');
const control=(type,label)=>{const found=render().find(n=>n.type===type&&(n.props.label===label||text(n.props.children)===label));assert(found,`${type}: ${label}`);return found.props};
const section=(label)=>{const found=render().find(n=>n.type==='DialogButton'&&n.props.className==='claw-builder-accordion-button'&&text(n.props.children).includes(label));assert(found,`section: ${label}`);found.props.onClick()};
const draft=()=>state[1];
assert(render().some(n=>n.props?.className==='claw-builder-stage'));
const previewCSS=render().find(n=>n.type==='style'&&typeof n.props.children==='string'&&n.props.children.includes('.claw-builder-page')).props.children;
assert(previewCSS.includes('grid-template-rows:clamp(106px,13dvh,126px)'),'horizontal preview must be compact and leave room for properties');
assert(previewCSS.includes('overflow:auto;overscroll-behavior:contain'),'preview must scroll in both axes without scrolling routed page');
assert(previewCSS.includes('touch-action:pan-x pan-y'),'touch must pan the large virtual screen');
const previewStage=render().find(n=>n.props?.className==='claw-builder-stage');
assert.equal(previewStage.props.tabIndex,0,'preview can receive keyboard focus for scrolling');
assert.equal(previewStage.props.role,'region');
const safeCanvas=walk(previewStage).find(n=>n.props?.className==='claw-builder-screen');
assert(safeCanvas,'game canvas is nested inside the scrollable viewport');
assert.equal(safeCanvas.props.style.padding,10,'UI camera gutter is not overlay padding');
assert.equal(safeCanvas.props.style.width,760,'a fitting overlay must not force 1280px of scrolling');
assert.equal(safeCanvas.props.style.height,100,'a fitting overlay must not force 800px of scrolling');
assert(safeCanvas.props.style.width>1280*.45,'screen and margin are both part of scroll width');
const gameCanvas=walk(previewStage).find(n=>n.props?.className==='claw-builder-game-screen');
assert.equal(gameCanvas.props.style.overflow,'hidden','virtual camera has real clipping bounds');
assert.deepEqual(JSON.parse(JSON.stringify(previewCanvasSize({width:760,height:100},{width:250,height:35},.45,{x:12,y:12}))),{width:760,height:100},'fitting overlay must not scroll');
const oversized=previewCanvasSize({width:760,height:100},{width:980,height:145},.45,{x:12,y:12});
assert(oversized.width>760&&oversized.height>100,'only oversized overlay grows scrollable canvas');
let moved;let previewPrevented=false,previewStopped=false;
const host={scrollWidth:900,clientWidth:760,scrollHeight:200,clientHeight:100,scrollBy:v=>{moved=v}};
previewStage.props.onKeyDown({key:'ArrowDown',target:host,currentTarget:host,preventDefault(){previewPrevented=true},stopPropagation(){previewStopped=true}});
assert.equal(moved.top,60,'keyboard Down pans stage without touching the layout');
assert(previewPrevented&&previewStopped);
const noScroll={scrollWidth:760,clientWidth:760,scrollHeight:100,clientHeight:100,scrollBy:()=>{throw Error('No scroll expected')}};
previewStage.props.onKeyDown({key:'ArrowDown',target:noScroll,currentTarget:noScroll,preventDefault(){throw Error('Do not consume gamepad arrows without overflow')},stopPropagation(){}});
console.log('PASS compact scrollable preview: top/bottom safe margin, scaled screen bounds, touch and keyboard panning.');
const legacyTdp=model.flatten(initial.root).find(n=>n.token==='tdp.value');
assert(legacyTdp,'original layouts still contain the legacy combined TDP');
const upgraded=model.splitLegacyTdp(initial);
const converted=model.find(upgraded.root,legacyTdp.id);
assert.equal(converted.kind,'group');
assert.deepEqual(Array.from(converted.children,n=>n.token),['tdp.label','tdp.reading']);
assert.equal(JSON.stringify(model.splitLegacyTdp(initial)),JSON.stringify(model.splitLegacyTdp(initial)),'conversion has repeatable IDs and clean Cancel');
assert.equal(model.flatten(draft().root).some(n=>n.token==='tdp.value'),false,'editor opens legacy layouts as separate controls');
assert.equal(model.flatten(draft().root).some(n=>n.token==='tdp.label'),true);
assert.equal(model.flatten(draft().root).some(n=>n.token==='tdp.reading'),true);
console.log('PASS independent TDP editor controls and deterministic legacy-layout conversion.');
assert(render().some(n=>n.type==='style'&&n.props.children.includes('height:calc(100dvh - 80px)')),'page reserves Steam top/bottom chrome');
assert(render().some(n=>n.type==='style'&&n.props.children.includes('.claw-builder{width:100%;height:100%;min-height:0')),'inner editor stays within the routed page');
assert(!render().some(n=>n.type==='ModalRoot'),'the editor is a routed page, not a Steam modal');
assert(render().some(n=>n.props?.className==='claw-builder-page'));
assert.equal(applied,undefined);
// Inspect the native Focusable hierarchy, not just CSS classes. This catches
// the missing parent row which formerly flattened both columns into a column.
// It does not simulate Steam's navigation engine or establish device behavior.
function navigation(v,scopes=[]){
 if(!v||typeof v!=='object')return [];
 if(Array.isArray(v))return v.flatMap(child=>navigation(child,scopes));
 if(typeof v.type==='function')return navigation(v.type(v.props),scopes);
 const next=v.type==='Focusable'?[...scopes,v]:scopes;
 return [{node:v,scopes},...navigation(v.props.children,next)];
}
function navClass(name){const result=navigation(renderTree()).find(({node})=>node.props.className===name);assert(result,name);return result}
function scope(name,flow,parent){
 const {node,scopes}=navClass(name);
 assert.equal(node.type,'Focusable',`${name} must register native navigation`);
 assert.equal(node.props['flow-children'],flow,name);
 if(parent)assert.equal(scopes.at(-1)?.props.className,parent,`${name} nearest navigation parent`);
}
function checkNavigation(orientation){
 assert.equal(navClass('claw-builder').node.props['data-orientation'],orientation);
 // Zoom consumes Left/Right as a native slider: Down must still reach the
 // controls panel even when the preview is visually beside it.
 scope('claw-builder','column','claw-builder-page');
 scope('claw-builder-preview','column','claw-builder');
 scope('claw-builder-panel','column','claw-builder');
 scope('claw-builder-menu','row','claw-builder-panel');
 scope('claw-builder-navigator','column','claw-builder-menu');
 scope('claw-builder-properties','column','claw-builder-menu');
 scope('claw-builder-property-scroll','column','claw-builder-properties');
 scope('claw-builder-actions','row','claw-builder-properties');
 scope('claw-builder-fields','row','claw-builder-card-body');
 scope('claw-builder-tree','column','claw-builder-card-body');
 const treeButton=navClass('claw-builder-tree-select');
 assert.equal(treeButton.scopes.at(-1).props.className,'claw-builder-tree-row');
 assert.equal(treeButton.scopes.at(-2).props.className,'claw-builder-tree');
}
checkNavigation('horizontal');
const horizontalDraft=state[1];
state[1]=model.validate(JSON.parse(readFileSync('assets/modular/vertical.json')));
checkNavigation('vertical');state[1]=horizontalDraft;
const rootButton=navClass('claw-builder-tree-select').node;
assert(walk(rootButton).some(n=>n.type==='strong'&&text(n.props.children)===initial.root.name),'root group name is bold');
console.log('PASS editor navigation hierarchy: horizontal/vertical templates, left/right sibling panels and control rows; mock structure only.');

assert(!render().some(n=>n.type==='ConfirmModal'),'the builder uses its own right-panel actions');
assert(render().some(n=>n.props?.className==='claw-builder-actions'));
assert(!render().some(n=>n.type==='strong'&&text(n.props.children)==='Preview'));
assert(!render().some(n=>n.type==='DialogButton'&&text(n.props.children).includes('Guides')));
assert.equal(control('slider','Zoom (%)').max,100);
assert.equal(control('slider','Zoom (%)').value,90);
control('slider','Zoom (%)').onChange(100);assert.equal(control('slider','Zoom (%)').value,100);
assert(!render().some(n=>n.type==='DialogButton'&&text(n.props.children)==='Fit'));
assert(render().some(n=>n.type==='style'&&n.props.children.includes('grid-template-columns:minmax(0,1fr) 188px')),'zoom controls have a reserved column outside the preview');
const graph=model.flatten(initial.root).find(n=>n.token==='graph');
assert(graph);
render().find(n=>n.type==='preview').props.onSelect(graph.id);
section('Appearance');
control('DropdownItem','Graph style').onChange({data:'bars'});
assert.equal(render().find(n=>n.type==='preview').props.settings.graph_style,'bars');
assert.equal(appliedAppearance,undefined);
control('DialogButton','Undo').onClick();
assert.equal(render().find(n=>n.type==='preview').props.settings.graph_style,'line');
section('Selected element');
control('DialogButton','Place graph below · left').onClick();
assert.equal(draft().root.axis,'column');
assert.equal(draft().root.children[0].axis,'row');
assert.equal(draft().root.children.at(-1).id,graph.id);
assert.equal(draft().root.children.at(-1).selfAlign,'start');
assert.equal(model.flatten(draft().root).filter(n=>n.id===graph.id).length,1);
assert(model.isHorizontalLayout(draft()));
assert(render().some(n=>n.props?.['data-orientation']==='horizontal'),'horizontal preview stays wide after placement');
render().find(n=>n.type==='preview').props.onSelect(graph.id);
section('Appearance');
const fitGraph=control('ToggleField','Match readings width');assert.equal(fitGraph.checked,true,'placing graph below enables content matching');fitGraph.onChange(false);
assert.equal(model.find(draft().root,graph.id).width,180,'manual graph width remains editable');control('ToggleField','Match readings width').onChange(true);
assert.equal(model.find(draft().root,graph.id).width,0,'auto graph width is represented explicitly in the layout');
assert.equal(model.validate(draft()).root.children.at(-1).width,0,'auto width survives layout validation');
control('DialogButton','Undo').onClick();
assert.equal(model.find(draft().root,graph.id).width,180,'Undo restores the manual width setting');
control('DialogButton','Undo').onClick();
assert.equal(model.find(draft().root,graph.id).width,0,'Undo restores the placed graph fit mode');
control('DialogButton','Undo').onClick();
assert.equal(draft().root.axis,initial.root.axis);
assert.equal(model.parent(draft().root,graph.id).id,model.parent(initial.root,graph.id).id);
const firstGroup=initial.root.children.find(n=>n.kind==='group');
assert(firstGroup);
assert(!render().some(n=>n.props?.className==='claw-builder-tree-select'&&text(n.props.children).includes(firstGroup.children[0].name)),'nested groups begin collapsed');
render().find(n=>n.props?.className==='claw-builder-tree-select'&&text(n.props.children).includes(firstGroup.name)).props.onClick();
assert(render().some(n=>n.props?.className==='claw-builder-tree-select'&&text(n.props.children).includes(firstGroup.children[0].name)),'group expands');
for(const row of render().filter(n=>n.props?.className==='claw-builder-tree-select')){
 const groupRow=row.props['aria-expanded']!==undefined;
 assert.equal(walk(row).some(n=>n.type==='strong'),groupRow,'only group names are bold, including nested groups');
}
assert(render().some(n=>n.type==='style'&&n.props.children.includes('font-weight:400!important}.claw-builder-tree-select strong{font-weight:700}')),'readings retain regular weight regardless of native button defaults');

render().find(n=>n.props?.className==='claw-builder-tree-select'&&text(n.props.children).includes(firstGroup.name)).props.onClick();
assert(!render().some(n=>n.props?.className==='claw-builder-tree-select'&&text(n.props.children).includes(firstGroup.children[0].name)),'group collapses without deleting contents');
assert(!render().some(n=>n.props?.className==='claw-builder-tree-toggle'),'no separate tree toggle');
render().find(n=>n.type==='preview').props.onSelect(firstGroup.children[0].id);
assert(render().some(n=>n.props?.className==='claw-builder-tree-select'&&text(n.props.children).includes(firstGroup.children[0].name)),'selecting an element in preview reopens its group');
render().find(n=>n.props?.className==='claw-builder-tree-select'&&text(n.props.children).includes(initial.root.name)).props.onClick();
render().find(n=>n.props?.className==='claw-builder-tree-select'&&text(n.props.children).includes(initial.root.name)).props.onClick();
render().find(n=>n.props?.className==='claw-builder-tree-select'&&text(n.props.children).includes(firstGroup.name)).props.onClick();
control('DropdownItem','Element vertical alignment').onChange({data:'end'});
assert.equal(draft().root.children[0].selfAlign,'end');
render().find(n=>n.props?.className==='claw-builder-tree-select'&&text(n.props.children).includes(initial.root.name)).props.onClick();
assert(render().some(n=>n.props?.['data-orientation']==='horizontal'));
control('DropdownItem','Direction').onChange({data:'column'});
assert(render().some(n=>n.props?.['data-orientation']==='vertical'));
assert(render().some(n=>n.props?.className==='claw-builder-stage'));
control('DropdownItem','Direction').onChange({data:'row'});
section('Appearance');
assert(render().some(n=>n.props?.className==='claw-builder-stage'),'preview remains mounted while editing');
control('slider','Corner radius').onChange(14);
control('slider','Overlay background opacity (%)').onChange(52);
assert.equal(render().find(n=>n.type==='preview').props.settings.rounding,14);
assert.equal(render().find(n=>n.type==='preview').props.settings.opacity,52);
const units=control('ToggleField','Superscript units (°C, MHz, GiB, ms, W, %)');
assert.equal(units.checked,false);
units.onChange(true);
assert.equal(render().find(n=>n.type==='preview').props.settings.unit_superscript,true);
control('DialogButton','Undo').onClick();assert.equal(render().find(n=>n.type==='preview').props.settings.unit_superscript,false);
control('DialogButton','Redo').onClick();assert.equal(render().find(n=>n.type==='preview').props.settings.unit_superscript,true);
section('Group spacing');
control('slider','Horizontal spacing between groups (px)').onChange(23);assert.equal(draft().root.gap,23);assert.equal(applied,undefined);assert.notEqual(initial.root.gap,23);
control('DialogButton','Undo').onClick();assert.equal(draft().root.gap,initial.root.gap);
control('DialogButton','Redo').onClick();assert.equal(draft().root.gap,23);
control('DialogButton','+ Group').onClick();let newGroup=draft().root.children.at(-1);assert.equal(newGroup.name,'New group');
assert(render().some(n=>n.props?.className==='claw-builder-stage'),'preview remains mounted after adding');
assert(control('DialogButton','+ Reading'),'element list remains available while editing');control('DialogButton','+ Reading').onClick();assert.equal(model.find(draft().root,newGroup.id).children.length,1);
control('DropdownItem','Move to group').onChange({data:initial.root.id});assert.equal(model.find(draft().root,newGroup.id).children.length,0);
control('DialogButton','Move earlier').onClick();assert.equal(draft().root.children.at(-1).id,newGroup.id);
control('DialogButton','Delete element').onClick();assert.equal(model.flatten(draft().root).length,model.flatten(initial.root).length+1);
render().find(n=>n.type==='preview').props.onSelect(newGroup.id);
control('DropdownItem','Reading').onChange({data:'separator'});
control('DialogButton','+ Reading').onClick();
assert.equal(draft().root.children.at(-1).children[0].token,'separator');
assert.equal(draft().root.children.at(-1).children[0].height,2);
assert(control('DialogButton','Separator color'),'separator options open immediately when selected');
control('slider','Line thickness (px)').onChange(4);
control('DropdownItem','Separator orientation').onChange({data:'column'});
control('slider','Line length (px)').onChange(27);
control('slider','Line corner radius (px)').onChange(2);
control('slider','Line opacity (%)').onChange(36);
const editedLine=draft().root.children.at(-1).children[0];
assert.deepEqual([editedLine.axis,editedLine.width,editedLine.cornerRadius,editedLine.separatorOpacity],['column',27,2,36]);
assert.equal(draft().root.children.at(-1).children[0].height,4);
const cyclic=model.move(draft(),draft().root.id,newGroup.id);assert.deepEqual(cyclic,draft());
control('DialogButton','Cancel').onClick();assert.equal(closed,false,'dirty Cancel must not discard silently');assert.equal(applied,undefined);
assert.equal(picker.type,ui.ConfirmModal);assert.equal(picker.props.strTitle,'Unsaved overlay changes');
assert.equal(picker.props.strOKButtonText,'Apply layout');
picker.props.onCancel();assert.equal(closed,false,'Keep editing must not exit');
control('DialogButton','Cancel').onClick();picker.props.children.props.onClick();
await new Promise(setImmediate);assert(closed,'Discard changes explicitly closes a dirty editor');
closed=false;control('DialogButton','Apply layout').onClick();assert.equal(closed,false);assert.equal(applied.root.gap,23);assert.equal(applied.root.children.at(-1).name,'New group');
assert.equal(appliedAppearance.rounding,14);assert.equal(appliedAppearance.opacity,52);
assert.equal(appliedAppearance.unit_superscript,true);
assert.throws(()=>model.validate({...initial,x:NaN}));
console.log('PASS builder: draft isolation, undo/redo, add, move, reorder, delete, cycle protection, cancel and apply. Mock UI only.');

// CPU/GPU separation edits the containing row/column, preserving internal gaps.
state.length=0;
const cpu=model.flatten(initial.root).find(n=>n.name==='CPU');
const container=model.parent(initial.root,cpu.id);
render().find(n=>n.type==='preview').props.onSelect(cpu.id);section('Group spacing');
control('slider',`Horizontal spacing · ${container.name} (px)`).onChange(31);
assert.equal(model.find(draft().root,container.id).gap,31);
assert.equal(model.find(draft().root,cpu.id).gap,cpu.gap);
control('DialogButton','Undo').onClick();assert.equal(model.find(draft().root,container.id).gap,container.gap);
control('DialogButton','Redo').onClick();assert.equal(model.find(draft().root,container.id).gap,31);
render().find(n=>n.type==='preview').props.onSelect(container.id);
control('DropdownItem','Direction').onChange({data:'column'});
render().find(n=>n.type==='preview').props.onSelect(cpu.id);section('Group spacing');
assert(!render().some(n=>n.type==='slider'&&n.props.label===`Horizontal spacing · ${container.name} (px)`));
control('slider',`Vertical spacing · ${container.name} (px)`).onChange(27);
assert.equal(model.find(draft().root,container.id).gap,27);
assert.equal(model.find(draft().root,cpu.id).gap,cpu.gap);
control('slider','Horizontal spacing inside group (px)').onChange(11);
assert.equal(model.find(draft().root,cpu.id).gap,11);
assert.equal(model.find(draft().root,container.id).gap,27);
control('DialogButton','Apply layout').onClick();assert.equal(model.parent(applied.root,cpu.id).gap,27);
// Editing CPU also exposes its grandparent column and outer FPS/readings row.
const ancestors=model.spacingAncestors(draft().root,cpu.id);
assert(ancestors.some(n=>n.axis==='row')&&ancestors.some(n=>n.axis==='column'));
for(const ancestor of ancestors){
 const label=`${ancestor.axis==='row'?'Horizontal':'Vertical'} spacing · ${ancestor.name} (px)`;
 const field=control('slider',label);assert.equal(field.min,0);assert.equal(field.max,240);assert.equal(field.step,1);
 field.onChange(240);assert.equal(model.find(draft().root,ancestor.id).gap,240);
 field.onChange(0);assert.equal(model.find(draft().root,ancestor.id).gap,0);
 assert.equal(model.find(draft().root,cpu.id).gap,11,'outer gaps do not change reading spacing');
}
section('Appearance');
assert(!render().some(n=>n.type==='slider'&&n.props.label==='Group padding'));
assert(model.flatten(draft().root).filter(n=>n.kind==='group').every(n=>n.padding===0));
const padded=structuredClone(initial);for(const node of model.flatten(padded.root))if(node.kind==='group')node.padding=67;
const migrated=model.validate(padded);assert(model.flatten(migrated.root).filter(n=>n.kind==='group').every(n=>n.padding===0));
assert.equal(padded.root.padding,67,'legacy migration does not mutate imported data');
assert.equal(model.group('Padded',[],{padding:50}).padding,0,'new groups have no padding');
assert.throws(()=>model.validate({...initial,root:{...initial.root,gap:241}}));
control('DialogButton','Apply layout').onClick();assert(model.flatten(applied.root).filter(n=>n.kind==='group').every(n=>n.padding===0));
console.log('PASS group spacing: all row/column ancestors, independent internal gaps, 0–240 px, zero default insets, undo/redo and Apply.');

state.length=0;section('Position on screen');
const anchorOptions=control('DropdownItem','Anchor').rgOptions;
for(const key of ['center-left','center-right'])assert(anchorOptions.some(option=>option.data===key));
control('DropdownItem','Anchor').onChange({data:'center-left'});
assert.equal(draft().anchor,'center-left');assert.equal(draft().y,0,'new center anchor starts exactly at mid-height');
assert.equal(control('slider','Vertical offset from center').min,-2000);
control('slider','Vertical offset from center').onChange(-35);
control('DropdownItem','Anchor').onChange({data:'center-right'});
assert.equal(draft().y,-35,'switching edges retains the offset from center');
control('DialogButton','Apply layout').onClick();assert.equal(applied.anchor,'center-right');assert.equal(applied.y,-35);
control('DialogButton','Undo').onClick();assert.equal(draft().anchor,'center-left');assert.equal(draft().y,-35);
control('DialogButton','Redo').onClick();assert.equal(draft().anchor,'center-right');
control('DropdownItem','Anchor').onChange({data:'top-left'});
assert.equal(draft().y,0,'legacy edge margins stay non-negative');
console.log('PASS center-edge anchors: both choices, exact initial center, signed offsets, save and undo/redo.');

// Text Enter stays inside the editor for both a group and a reading.
state.length=0;closed=false;applied=undefined;
for(const id of [initial.root.id,graph.id]){
 render().find(n=>n.type==='preview').props.onSelect(id);
 control('TextField','Name').onChange({target:{value:'Renamed '+id}});
 for(const handler of ['onKeyDownCapture','onKeyUpCapture']){
  let prevented=false,stopped=false;
  render().find(n=>n.props?.className==='claw-builder').props[handler]({key:'Enter',target:{tagName:'INPUT',type:'text'},preventDefault(){prevented=true},stopPropagation(){stopped=true}});
  assert(prevented&&stopped);assert.equal(closed,false);assert.equal(applied,undefined);
 }
 assert.equal(model.find(draft().root,id).name,'Renamed '+id);
}
console.log('PASS editor Enter: group/reading names remain edited without closing or applying.');

state.length=0;closed=false;applied=undefined;
styleSettings={style_presets:{'1':{}},style_names:{'1':'Existing'}};
let styleCalls=[];
saveStyleHandler=async(slot,doc,appearance,name)=>{
 styleCalls.push({slot,doc:structuredClone(doc),appearance:{...appearance},name});
 return {presets:{'1':{},[slot]:{}},names:{'1':'Existing',[slot]:name}};
};
control('TextField','Name').onChange({target:{value:'Unsaved editor draft'}});
control('DialogButton','Save style').onClick();
scope('claw-builder-save-style','column','claw-builder-properties');
assert.equal(control('DropdownItem','Style slot').selectedOption,'new');
assert(control('DropdownItem','Style slot').rgOptions.some(x=>x.data==='1'&&x.label==='Existing'));
control('TextField','Style name').onChange({target:{value:'From editor'}});
control('DialogButton','Save new style').onClick();await new Promise(setImmediate);
assert.equal(styleCalls[0].slot,'2');assert.equal(styleCalls[0].doc.root.name,'Unsaved editor draft');
assert.equal(styleCalls[0].name,'From editor');assert.equal(closed,false);assert.equal(applied,undefined);
assert.equal(control('DropdownItem','Style slot').selectedOption,'2');
assert(render().some(n=>n.props?.role==='status'&&text(n.props.children)==='Saved: From editor'));
control('DropdownItem','Style slot').onChange({data:'1'});
assert.equal(control('TextField','Style name').value,'Existing');
control('DialogButton','Overwrite style').onClick();await new Promise(setImmediate);
assert.equal(styleCalls[1].slot,'1');assert.equal(styleCalls[1].doc.root.name,'Unsaved editor draft');
saveStyleHandler=async()=>{throw new Error('Offline')};
control('DialogButton','Overwrite style').onClick();await new Promise(setImmediate);
assert(render().some(n=>n.props?.role==='status'&&text(n.props.children).includes('Offline')));
assert.equal(closed,false);assert.equal(applied,undefined);
control('DialogButton','Cancel').onClick();assert.equal(closed,false);picker.props.children.props.onClick();await new Promise(setImmediate);assert.equal(closed,true);
console.log('PASS editor Save style: new/overwrite shared slots, latest draft, names, error/retry and no implicit Apply or close.');
 
// Clean cancel exits immediately; dirty B/Cancel offers Apply/Discard/Keep editing.
state.length=0;closed=false;applied=undefined;styleSettings={};
control('DialogButton','Cancel').onClick();
assert.equal(closed,true,'clean Cancel has no modal');
state.length=0;closed=false;applied=undefined;
control('TextField','Name').onChange({target:{value:'Modified via gamepad'}});
let prevented=false,stopped=false;
render().find(n=>n.props?.className==='claw-builder-page').props.onCancelButton({preventDefault(){prevented=true},stopPropagation(){stopped=true}});
assert(prevented&&stopped);assert.equal(closed,false,'B button must guard dirty edits');
assert.equal(picker.props.strTitle,'Unsaved overlay changes');
picker.props.onOK();await new Promise(setImmediate);
assert.equal(applied.root.name,'Modified via gamepad','Apply from prompt saves the draft');
assert.equal(closed,false,'routed editor Apply is responsible for navigation');

state.length=0;closed=false;applied=undefined;styleSettings={};
render().find(n=>n.type==='preview').props.onSelect(graph.id);section('Appearance');
assert(!render().some(n=>n.type==='slider'&&n.props.label==='Element scale (%)'));
assert(control('slider','Graph width'));assert(control('slider','Graph height'));
control('DialogButton','Graph color').onClick();picker.props.onConfirm('FF00FF');
assert.equal(model.find(draft().root,graph.id).color,'#FF00FF');
control('DialogButton','Apply layout').onClick();assert.equal(model.find(applied.root,graph.id).color,'#FF00FF');
const style=styles.styleSnapshotFrom({modular_layout:applied,modular_enabled:true});
assert.equal(model.find(style.modular_layout.root,graph.id).color,'#FF00FF');
control('DialogButton','Use plugin color').onClick();assert.equal(model.find(draft().root,graph.id).color,'');
render().find(n=>n.type==='preview').props.onSelect(initial.root.id);section('Appearance');
assert(control('slider','Element scale (%)'),'group text scaling remains available');
console.log('PASS graph editor: no ineffective scale slider; width/height retained; selected color survives Apply and style snapshot; reset inherits plugin color.');

state.length=0;section('Appearance');
assert.equal(control('slider','Corner radius').max,1000);
for(const label of ['Overlay horizontal padding (px)','Overlay vertical padding (px)']){
 const field=control('slider',label);assert.equal(field.min,0);assert.equal(field.max,160);assert.equal(field.step,1);
}
control('slider','Overlay horizontal padding (px)').onChange(27);
control('slider','Overlay vertical padding (px)').onChange(13);
assert.equal(draft().paddingX,27);assert.equal(draft().paddingY,13);
control('DialogButton','Pill shape').onClick();assert.equal(render().find(n=>n.type==='preview').props.settings.rounding,1000);
control('DialogButton','Undo').onClick();assert.equal(render().find(n=>n.type==='preview').props.settings.rounding,10);
control('DialogButton','Redo').onClick();assert.equal(render().find(n=>n.type==='preview').props.settings.rounding,1000);
control('DialogButton','Apply layout').onClick();assert.equal(applied.paddingX,27);assert.equal(applied.paddingY,13);assert.equal(appliedAppearance.rounding,1000);
render().find(n=>n.type==='preview').props.onSelect(cpu.id);section('Appearance');
assert(!render().some(n=>n.type==='slider'&&n.props.label.startsWith('Overlay horizontal padding')));
assert(!render().some(n=>n.type==='DialogButton'&&text(n.props.children)==='Pill shape'));
console.log('PASS Overlay insets: independent axes, root-only controls, Pill shape, undo/redo and Apply.');

const currentCpu=model.find(draft().root,cpu.id);
control('slider','Horizontal padding (px)').onChange(19);
control('slider','Vertical padding (px)').onChange(7);
control('ToggleField','Outline').onChange(true);
control('slider','Outline thickness (px)').onChange(4);
control('slider','Outline opacity (%)').onChange(35);
assert.equal(model.find(draft().root,cpu.id).paddingX,19);assert.equal(model.find(draft().root,cpu.id).paddingY,7);
assert.equal(model.find(draft().root,cpu.id).outlineWidth,4);assert.equal(model.find(draft().root,cpu.id).outlineOpacity,35);
control('DialogButton','Undo').onClick();assert.equal(model.find(draft().root,cpu.id).outlineOpacity,undefined);
control('DialogButton','Redo').onClick();assert.equal(model.find(draft().root,cpu.id).outlineOpacity,35);
control('DialogButton','Apply layout').onClick();assert.equal(model.find(applied.root,cpu.id).paddingX,19);assert.equal(model.find(applied.root,cpu.id).outlineWidth,4);
assert.equal(model.parent(applied.root,cpu.id).gap,model.parent(draft().root,cpu.id).gap);
console.log('PASS group insets/outline: independent axes, separate opacity/thickness, undo/redo, Apply and unchanged sibling gaps.');

control('DialogButton','Outline color').onClick();picker.props.onConfirm('FFAACC');
assert.equal(model.find(draft().root,cpu.id).outlineColor,'#FFAACC');
control('DialogButton','Default outline color').onClick();assert.equal(model.find(draft().root,cpu.id).outlineColor,'');
const metricNode=model.flatten(draft().root).find(n=>n.kind==='metric'&&n.token==='cpu.load');
render().find(n=>n.type==='preview').props.onSelect(metricNode.id);section('Appearance');
assert.equal(control('slider','Horizontal padding (px)').value,0);assert.equal(control('slider','Vertical padding (px)').value,0);
control('slider','Horizontal padding (px)').onChange(11);control('slider','Vertical padding (px)').onChange(5);
assert.equal(model.find(draft().root,metricNode.id).paddingX,11);assert.equal(model.find(draft().root,metricNode.id).paddingY,5);
assert(!render().some(n=>n.props?.className==='claw-builder-accordion-button'&&text(n.props.children).includes('Position on screen')));
render().find(n=>n.type==='preview').props.onSelect(draft().root.id);
assert(render().some(n=>n.props?.className==='claw-builder-accordion-button'&&text(n.props.children).includes('Position on screen')));
control('DialogButton','Apply layout').onClick();assert.equal(model.find(applied.root,metricNode.id).paddingX,11);
console.log('PASS all elements have zero-default X/Y padding; global Position appears only for Overlay.');

state.length=0;closed=false;applied=undefined;styleSettings={sans:true};
const fontCpu=model.flatten(initial.root).find(n=>n.kind==='group'&&n.name==='CPU');
render().find(n=>n.type==='preview').props.onSelect(fontCpu.id);section('Appearance');
assert.equal(control('slider','Corner radius').value,0);
control('slider','Corner radius').onChange(1000);
control('DropdownItem','Font weight').onChange({data:'semibold'});
assert.equal(model.find(draft().root,fontCpu.id).cornerRadius,1000);
assert.equal(model.find(draft().root,fontCpu.id).fontWeight,'semibold');
control('DialogButton','Undo').onClick();assert.equal(model.find(draft().root,fontCpu.id).fontWeight,undefined);
control('DialogButton','Redo').onClick();assert.equal(model.find(draft().root,fontCpu.id).fontWeight,'semibold');
const localReading=fontCpu.children.find(n=>n.token==='cpu.load');
render().find(n=>n.type==='preview').props.onSelect(localReading.id);section('Appearance');
assert(!render().some(n=>n.type==='slider'&&n.props.label==='Corner radius'));
control('DropdownItem','Font weight').onChange({data:'bold'});
control('DialogButton','Apply layout').onClick();
assert.equal(model.find(applied.root,localReading.id).fontWeight,'bold');
assert.equal(model.find(applied.root,fontCpu.id).cornerRadius,1000);
let appearanceSave;
saveStyleHandler=async(slot,doc)=>{appearanceSave=doc;return{presets:{[slot]:{}},names:{[slot]:'Rounded'}}};
control('DialogButton','Save style').onClick();control('DialogButton','Save new style').onClick();await new Promise(setImmediate);
assert.equal(model.find(appearanceSave.root,fontCpu.id).cornerRadius,1000);
assert.equal(model.find(appearanceSave.root,localReading.id).fontWeight,'bold');
control('DropdownItem','Font weight').onChange({data:'inherit'});
assert.equal(model.find(draft().root,localReading.id).fontWeight,undefined);
render().find(n=>n.type==='preview').props.onSelect(graph.id);section('Appearance');
assert(!render().some(n=>n.type==='DropdownItem'&&n.props.label==='Font weight'));
console.log('PASS group radius and per-item font: controls, automatic reset, undo/redo, Apply and Save style.');
