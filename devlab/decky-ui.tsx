import React from 'react';
import {createRoot} from 'react-dom/client';
export const DialogButton=({children,...p}:any)=><button {...p}>{children}</button>;
export const Focusable=({children,'flow-children':flow,onGamepadDirection,onCancelButton,onOKButton,...p}:any)=><div {...p}>{children}</div>;
export const TextField=({label,value,onChange,...p}:any)=><label className="web-field">{label}<input value={value} onChange={onChange} {...p}/></label>;
export const ToggleField=({label,checked,onChange,disabled}:any)=><label className="web-field">{label}<input type="checkbox" checked={checked} disabled={disabled} onChange={e=>onChange(e.target.checked)}/></label>;
export const DropdownItem=({label,selectedOption,rgOptions,onChange,disabled}:any)=><label className="web-field">{label}<select disabled={disabled} value={selectedOption} onChange={e=>onChange(rgOptions.find((v:any)=>String(v.data)===e.target.value))}>{rgOptions.map((v:any)=><option key={v.data} value={v.data}>{v.label}</option>)}</select></label>;
export const SliderField=({value,min,max,step,onChange,disabled}:any)=><input aria-label="Adjust value" type="range" min={min} max={max} step={step} value={value} disabled={disabled} onChange={e=>onChange(Number(e.target.value))}/>;
export function showModal(element:any){const host=document.createElement('div');host.className='web-modal';document.body.append(host);const root=createRoot(host);root.render(element);return {Close(){root.unmount();host.remove()}}}
