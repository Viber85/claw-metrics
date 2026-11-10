import {useState} from 'react';
export type GraphStyle='line'|'area'|'bars'|'dual'|'smooth'|'dual_layer';
export const graphStyleChoices=['line','area','bars','dual','smooth','dual_layer'].map(id=>({id,label:id.replaceAll('_',' ')}));
export function OpaqueColorPicker({title,hex,onConfirm,closeModal}:any){const [value,V]=useState('#'+hex);return <section role="dialog" aria-modal="true" aria-label={title}><h2>{title}</h2><input aria-label="Color" type="color" value={value} onChange={e=>V(e.target.value)}/><button onClick={()=>{onConfirm(value.slice(1));closeModal()}}>Use color</button><button onClick={closeModal}>Cancel</button></section>}
