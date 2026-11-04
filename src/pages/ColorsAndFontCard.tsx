import {BackgroundEditor} from "./BackgroundEditor";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { callable, definePlugin } from "@decky/api";
import {
  ButtonItem,
  ConfirmModal,
  showModal,
  DialogButton,
  Focusable,
  Field,
  PanelSection,
  PanelSectionRow,
  SliderField,
  TextField,
  Router,
  ToggleField,
} from "@decky/ui";
import { FaChartLine, FaChartBar, FaDesktop, FaThLarge, FaPalette, FaPlayCircle, FaSlidersH, FaChevronDown, FaChevronRight, FaPlay, FaDownload, FaCopy, FaPen, FaTachometerAlt, FaMicrochip, FaMemory, FaBatteryThreeQuarters, FaClock, FaBolt, FaHashtag } from "react-icons/fa";

import {styleLayoutFrom, styleMetricSnapshotFrom, styleMetricUpdatesFrom, independentColors, styleModified} from "../style-presets";
import {metricName, relatedLabel, cleanName, groupNames} from "../metric-names";
import * as Core from "../controller";
import {styleSlotIds} from "../style-presets";

type FontWeight = Core.FontWeight;
type StyleCategory = Core.StyleCategory;
const { GamepadGrid, tokenGroups, weightLabel, styleTabs, defaultColors, colorRows, groupIcons, groups, save, AccordionCard } = Core;

/** Standalone colors presentation; all mutable state is owned by the Decky controller. */
export function ColorsAndFontCard({vm}:{vm:Core.ClawController}) {
  const { settings, info, status, openSection, styleCategory, toggleSection, ready, current, update, named, tokenTitle, styleTitle, renameStyle, confirmAction, loadedPreset, presetDirty, chooseStyleCategory, cycleTokenWeight, openTokenColorPicker, resetTokenColor, savePreset, addPreset, deletePreset, loadPreset, paletteLabel, openColorPicker, toggle, metric, visible, hidden } = vm;
  const [expandedStyle,setExpandedStyle]=useState<string|null>(settings.active_style);
  const savedSlots=styleSlotIds.filter(slot=>Boolean(settings.style_presets?.[slot]));
  return (
<AccordionCard id="colors" title="Colors & Font" subtitle="Palette, typography and saved styles"
          icon={<FaPalette />} open={openSection === "colors"} onToggle={() => toggleSection("colors")}>
          <PanelSectionRow><Field label="COLORS & FONT"
            description="Edit global appearance or individual metric elements." /></PanelSectionRow>
          <PanelSectionRow><Field label="SAVED STYLES"
            description="Save the current overlay builder layout, colors, typography and visible sensors in a style." /></PanelSectionRow>
          <div className="loaded-style-status" role="status">
            {loadedPreset?`Active: ${styleTitle(settings.active_style!)}${presetDirty?" · modified":""}`:"Active: none"}
          </div>
          <Focusable flow-children="column" className="claw-preset-list">
            {savedSlots.map(slot=>{
              const active=settings.active_style===slot;
              const expanded=expandedStyle===slot;
              return <div className="claw-preset-card" data-loaded={active} key={slot}>
                <DialogButton className="claw-preset-heading" aria-expanded={expanded} aria-label={`${styleTitle(slot)} · ${expanded?'collapse':'expand'}`} onClick={()=>setExpandedStyle(expanded?null:slot)}>
                  <span className="claw-preset-heading-name">{styleTitle(slot)}</span>
                  <span className="claw-preset-heading-status">{active?(presetDirty?"Loaded · modified":"Loaded"):"Saved"}</span>
                  <span aria-hidden="true">{expanded?'⌄':'›'}</span>
                </DialogButton>
                {expanded&&<>
                <Focusable flow-children="row" className="claw-preset-actions">
                  <DialogButton className="claw-control-button" disabled={!ready} aria-pressed={active}
                    onClick={()=>loadPreset(slot)}
                    style={{background:active?"#dceaff":"#196bd4",
                      color:active?"#12325c":"#ffffff",
                      border:"1px solid #3b78ba",borderRadius:7}}>
                    <span className="claw-preset-label"><FaPlay aria-hidden="true" /> Load</span>
                  </DialogButton>
                  <DialogButton className="claw-control-button" disabled={!ready} onClick={()=>{
                      confirmAction("Overwrite "+styleTitle(slot)+"?",
                        "This replaces its saved overlay layout, appearance and metric selection.",
                        ()=>savePreset(slot));
                    }}
                    style={{background:"#243344",border:"1px solid #43546a",
                      borderRadius:7,color:"#ffffff"}}>
                    <span className="claw-preset-label"><FaDownload aria-hidden="true" /> Save</span>
                  </DialogButton>
                </Focusable>
                <Focusable flow-children="row" className="claw-preset-actions claw-preset-secondary"><DialogButton className="claw-control-button" disabled={!ready}
                  onClick={()=>renameStyle(slot)} aria-label={"Rename "+styleTitle(slot)}
                  style={{background:"#1b2838",border:"1px solid #37485c"}}>
                  <FaPen style={{marginRight:6}}/> Rename
                </DialogButton><DialogButton className="claw-control-button" disabled={!ready}
                  onClick={()=>confirmAction("Delete "+styleTitle(slot)+"?","This removes the saved style. Your current overlay settings stay in place.",()=>{deletePreset(slot);setExpandedStyle(null);})}
                  style={{background:"#302331",border:"1px solid #67465b"}}>Delete</DialogButton></Focusable>
                </>}
              </div>;
            })}
            {!savedSlots.length&&<div className="claw-preset-empty">No saved styles yet.</div>}
            <DialogButton className="claw-preset-add" disabled={!ready||savedSlots.length>=styleSlotIds.length} onClick={()=>{const slot=styleSlotIds.find(id=>!settings.style_presets?.[id]);if(slot){addPreset();setExpandedStyle(slot)}}}>+ Add style</DialogButton>
          </Focusable>
          <BackgroundEditor vm={vm}/>
          <PanelSectionRow><Field label="APPEARANCE EDITOR" description="Select a metric to customize its colors and typography." /></PanelSectionRow>
          <Focusable flow-children="column" className="claw-style-rows">
            {Array.from({length:Math.ceil(styleTabs.length/3)},(_,rowIndex)=>{
              const row=styleTabs.slice(rowIndex*3,rowIndex*3+3);
              return <Focusable key={rowIndex} flow-children="column" className="claw-style-row">
                <GamepadGrid items={row} columns={3} className="claw-tiles claw-style-tiles"
            renderItem={([key,name])=><DialogButton key={key} className="claw-control-button" disabled={!ready}
              aria-pressed={styleCategory===key} aria-label={"Style: "+(key==="global"?name:named(key))}
              onClick={()=>chooseStyleCategory(key)}
              style={{minWidth:0,width:"100%",minHeight:49,margin:0,padding:"6px 3px",
                background:styleCategory===key?"#185fae":"#1d2835",
                border:styleCategory===key?"2px solid #3186f5":"1px solid #476687",
                borderRadius:8,color:"#eef5ff"}}>
              <span style={{display:"flex",flexDirection:"column",alignItems:"center",
                justifyContent:"center",gap:4,minWidth:0,width:"100%"}}>
                <span className="style-group-icon" aria-hidden="true">{groupIcons[key]}</span>
                <span style={{fontSize:11.5,lineHeight:1.2,overflowWrap:"anywhere",
                  textAlign:"center",width:"100%",minWidth:0}}>{key==="global"?name:named(key)}</span>
              </span>
            </DialogButton>}/>
                {styleCategory!==null && row.some(([key])=>key===styleCategory) && <div className="claw-style-detail">
          {styleCategory==="global" ? <>
          <PanelSectionRow><Field label="GLOBAL" description="Global settings apply by default. Custom element overrides remain until explicitly reset." /></PanelSectionRow>
          {toggle("sans", "Use bundled font")}
          <PanelSectionRow><Field label="Barlow Semi Condensed" description={
            info?.condensed_fonts_ready ? "Light / Regular / SemiBold / Bold loaded."
              : "Bundled weights unavailable; using Claw Sans."} /></PanelSectionRow>
          <PanelSectionRow><Field label="Base font weight" description="Default for all elements without a custom font weight." /></PanelSectionRow>
          <GamepadGrid items={(["light","regular","semibold","bold"] as FontWeight[])}
            columns={2} className="claw-tiles claw-weight-tiles" renderItem={(weight)=>
              <DialogButton key={weight} className="claw-control-button" disabled={!ready || !settings.sans}
                aria-pressed={settings.font_weight===weight}
                onClick={()=>update({font_weight:weight})}
                style={{minWidth:0,width:"100%",minHeight:39,margin:0,padding:"7px 2px",
                  background:settings.font_weight===weight?"#096e9e":"#23364c",
                  border:"1px solid #406080",borderRadius:7,
                  fontSize:11,fontWeight:weight==="bold"?700:weight==="semibold"?600:weight==="light"?300:400}}>
                {weightLabel[weight]}
              </DialogButton>}/>
          <GamepadGrid items={colorRows} columns={3} className="claw-tiles claw-color-tiles"
            renderItem={([key,label])=><DialogButton key={key} className="claw-control-button" disabled={!ready}
              onClick={()=>openColorPicker(key,label)}
              aria-label={"Change color: "+paletteLabel(key,label)}
              style={{minWidth:0,width:"100%",minHeight:51,margin:0,padding:"6px 3px",
                background:"#21354c",border:"1px solid #496783",borderRadius:8,color:"#e8f4ff"}}>
              <span style={{display:"flex",flexDirection:"column",alignItems:"center",
                gap:4,minWidth:0,width:"100%"}}>
                <span aria-hidden="true" style={{width:14,height:14,flexShrink:0,borderRadius:4,
                  background:"#"+(settings.colors[key]??defaultColors[key]),
                  border:"1px solid #b8c7d9"}}/>
                <span style={{fontSize:11,lineHeight:1.2,overflowWrap:"anywhere",
                  textAlign:"center",minWidth:0,width:"100%"}}>{paletteLabel(key,label)}</span>
              </span>
            </DialogButton>}/>
          <PanelSectionRow><ButtonItem disabled={!ready} layout="below"
            onClick={()=>confirmAction("Restore default colors?",
              "Reset the global palette. Individual custom colors will be preserved.",
              ()=>update({colors:{...defaultColors}}))}>Restore default colors</ButtonItem></PanelSectionRow>
          </> : <>
          <PanelSectionRow><Field label={named(styleCategory)}
            description="Each element can override color and font weight. Global inherits the default." /></PanelSectionRow>
          {tokenGroups[styleCategory as Exclude<StyleCategory,"global">].map(token=>(
            <div key={token.key} className="claw-token-card">
              <div className="claw-token-title">{tokenTitle(token)}</div>
              <Focusable flow-children="row" className="claw-token-controls"
                style={{display:"flex",gap:5,width:"100%",minWidth:0}}>
                <DialogButton className="claw-control-button claw-token-font"
                  disabled={!ready} aria-label={"Change font weight: "+tokenTitle(token)}
                  onClick={()=>cycleTokenWeight(token.key)}
                  style={{flex:"1.15 1 0",minWidth:0,maxWidth:"100%",margin:0,
                    padding:"6px 7px",minHeight:38,background:"#254765",
                    border:"1px solid #456c8c",borderRadius:7}}>
                  <span style={{display:"flex",justifyContent:"space-between",alignItems:"center",
                    gap:3,width:"100%",minWidth:0,fontSize:11.5}}>
                    <span style={{overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                      Font: {weightLabel[settings.token_weights?.[token.key]??"inherit"]}
                    </span>
                    <FaChevronRight style={{flexShrink:0,opacity:0.72}}/>
                  </span>
                </DialogButton>
                <DialogButton className="claw-control-button claw-token-color"
                  disabled={!ready} aria-label={"Change color: "+tokenTitle(token)}
                  onClick={()=>openTokenColorPicker(token)}
                  style={{flex:"1 1 0",minWidth:0,maxWidth:"100%",margin:0,
                    padding:"6px 6px",minHeight:38,background:"#254765",
                    border:"1px solid #456c8c",borderRadius:7}}>
                  <span style={{display:"flex",alignItems:"center",gap:5,
                    minWidth:0,fontSize:11.5,whiteSpace:"nowrap"}}>
                    <span aria-hidden="true" style={{flexShrink:0,width:15,height:15,
                      borderRadius:4,background:"#"+(settings.token_colors?.[token.key]??
                        settings.colors[token.defaultColor]??defaultColors[token.defaultColor]),
                      border:"1px solid #adc7e7"}}/>
                    <span style={{overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                      {settings.token_colors?.[token.key]?"Custom":"Global"}
                    </span>
                  </span>
                </DialogButton>
                <DialogButton className="claw-control-button claw-token-reset"
                  disabled={!ready || !settings.token_colors?.[token.key]}
                  aria-label={"Reset custom color: "+tokenTitle(token)}
                  onClick={()=>resetTokenColor(token.key)}
                  style={{flex:"0 0 52px",width:52,minWidth:0,maxWidth:52,margin:0,
                    padding:"6px 2px",minHeight:38,fontSize:11,
                    background:"#223a56",border:"1px solid #456682",borderRadius:7}}>
                  Reset
                </DialogButton>
              </Focusable>
            </div>
          ))}
          <PanelSectionRow><ButtonItem disabled={!ready} layout="below"
            onClick={()=>confirmAction("Reset category overrides?",
              "Clear custom colors and font weights for this category.",
              ()=>{
                const nw={...current.current.token_weights},nc={...current.current.token_colors};
                for(const t of tokenGroups[styleCategory as Exclude<StyleCategory,"global">]){
                  delete nw[t.key]; delete nc[t.key];
                }
                update({token_weights:nw,token_colors:nc});
              })}>Reset category overrides</ButtonItem></PanelSectionRow>
          </>}
                </div>}
              </Focusable>;
            })}
          </Focusable>
        </AccordionCard>
  );
}
