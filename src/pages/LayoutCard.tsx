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
  TextField,
  Router,
  ToggleField,
} from "@decky/ui";
import { FaChartLine, FaChartBar, FaDesktop, FaThLarge, FaPalette, FaPlayCircle, FaSlidersH, FaChevronDown, FaChevronRight, FaPlay, FaDownload, FaCopy, FaPen, FaTachometerAlt, FaMicrochip, FaMemory, FaBatteryThreeQuarters, FaClock, FaBolt, FaHashtag } from "react-icons/fa";

import {styleLayoutFrom, styleMetricSnapshotFrom, styleMetricUpdatesFrom, independentColors, styleModified} from "../style-presets";
import {metricName, relatedLabel, cleanName, groupNames} from "../metric-names";
import * as Core from "../controller";
import {ModularEditor} from "./ModularEditor";
import {LayoutSliderField} from "../components/LayoutSliderField";


const { hudPositions, GraphStyleIcon, graphStyleChoices, GamepadGrid, defaults, AccordionCard, ControlGroup } = Core;

/** Standalone layout presentation; all mutable state is owned by the Decky controller. */
export function LayoutCard({vm}:{vm:Core.ClawController}) {
  const { settings, info, layoutPanel, toggleLayoutPanel, openSection, toggleSection, ready, update, confirmAction, openColorPicker, hidden } = vm;
  return (
<AccordionCard id="layout" title="Layout" subtitle="Orientation, position, size and spacing"
          icon={<FaThLarge />} open={openSection === "layout"} onToggle={() => toggleSection("layout")}>
          <ModularEditor vm={vm}/>
          {!settings.modular_enabled && <>
          <PanelSectionRow><Field label="Classic HUD orientation"
            description="Choose a horizontal strip or vertical stack. Restart the running game to apply." /></PanelSectionRow>
          <GamepadGrid items={([
            {id:"horizontal",label:"Horizontal",symbol:"↔"},
            {id:"vertical",label:"Vertical",symbol:"↕"}
          ] as const)} columns={2} className="claw-tiles claw-orientation-tiles"
            renderItem={choice=><DialogButton key={choice.id}
              disabled={!ready} className="claw-control-button"
              aria-label={choice.label+" HUD"} aria-pressed={settings.hud_orientation===choice.id}
              onClick={()=>update({hud_orientation:choice.id})}
              style={{width:"100%",minWidth:0,margin:0,minHeight:55,padding:"7px 4px",
                background:settings.hud_orientation===choice.id?"#0b597b":"#1c3450",
                border:settings.hud_orientation===choice.id?"2px solid #31cefa":"1px solid #456987",
                borderRadius:8,color:"#f2f8ff"}}>
              <span style={{display:"flex",flexDirection:"column",gap:4,alignItems:"center"}}>
                <span style={{fontSize:18}} aria-hidden="true">{choice.symbol}</span>
                <span style={{fontSize:12,fontWeight:600}}>{choice.label}</span>
              </span>
            </DialogButton>}/>
          {settings.hud_orientation==="vertical" && <PanelSectionRow>
            <Field label="Vertical preview"
              description="Uses native Claw Stacked layout: FPS at top, compact two-column metric rows with automatic value wrapping and a frametime graph at the bottom. Stock MangoHud keeps its original three-column fallback. FPS scaling and graph styles are available in this native preview; Both orientations support all six graph modes; Vertical also has independent graph width and height."/>
          </PanelSectionRow>}
          <ControlGroup title="Position" summary="8 anchors · X / Y offsets"
            open={layoutPanel==="position"} onToggle={()=>toggleLayoutPanel("position")}>
        <PanelSectionRow><Field label="HUD position"
          description="Choose a screen-edge anchor, including the vertical center of the left or right edge."/></PanelSectionRow>
        {/* Steam's navigation tree must match the visual 3×3 anchor grid: column
            movement between horizontal rows, row movement within each.
            A single flow-children="row" prevents D-pad up/down navigation. */}
        <Focusable flow-children="column" style={{display:"flex",flexDirection:"column",
          gap:5,padding:"0 4px 12px",maxWidth:"100%",boxSizing:"border-box"}}>
          {(["top","center","bottom"] as const).map((edge)=>
            <Focusable key={edge} flow-children="row" style={{display:"grid",
              gridTemplateColumns:"repeat(3,minmax(0,1fr))",gap:5,
              width:"100%",minWidth:0,maxWidth:"100%",boxSizing:"border-box"}}>
              {hudPositions.filter((anchor)=>anchor.id.startsWith(edge)).map((anchor)=>{
                const selected=settings.hud_position===anchor.id;
                return <DialogButton key={anchor.id} className="claw-hud-anchor" data-anchor-position={anchor.id}
                  aria-label={anchor.label} aria-pressed={selected}
                  disabled={!ready || (anchor.id.startsWith("center-") && !info?.layout_spacing_supported) || (settings.hud_orientation==="horizontal" && anchor.id.endsWith("center") && !info?.layout_spacing_supported)}
                  onClick={()=>update({hud_position:anchor.id,center_horizontal:anchor.id.endsWith("center")})}
                  style={{gridColumn:anchor.column,margin:0,padding:"4px 2px",minWidth:0,minHeight:54,
                    border:selected?"2px solid #31cefa":"1px solid #43607a",
                    borderRadius:8,background:selected?"#0b4c70":"#162b40",
                    color:selected?"#f6fcff":"#bfd5e7",outline:"none",boxShadow:"none"}}>
                  <span style={{display:"flex",flexDirection:"column",alignItems:"center",
                    justifyContent:"center",gap:2,lineHeight:1.1,width:"100%"}}>
                    <span aria-hidden="true" style={{fontSize:19,fontWeight:700}}>{anchor.icon}</span>
                    <span style={{fontSize:11.5,fontWeight:selected?700:500,
                      textAlign:"center"}}>{anchor.label}</span>
                  </span>
                </DialogButton>;
              })}
            </Focusable>
          )}
        </Focusable>
        <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="X offset (px)"
          value={settings.offset_x} min={-1920} max={1920} step={1} showValue
          disabled={!ready || settings.hud_position.endsWith("center")}
          onChange={(value:number)=>update({offset_x:value})}/></div></PanelSectionRow>
        <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Y offset (px)" value={settings.offset_y}
           min={-1200} max={1200} step={1} showValue disabled={!ready}
           onChange={value=>update({offset_y:value})}/></div></PanelSectionRow>
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below"
           onClick={()=>update({offset_x:0,offset_y:0})}>Reset X / Y offsets</ButtonItem></PanelSectionRow>

          </ControlGroup>
          <ControlGroup title="Size & appearance" summary="Text · FPS scale · background"
            open={layoutPanel==="size"} onToggle={()=>toggleLayoutPanel("size")}>
        <PanelSectionRow><ToggleField label="Superscript units" checked={settings.unit_superscript}
          disabled={!ready || !info?.layout_spacing_supported} onChange={unit_superscript=>update({unit_superscript})}/></PanelSectionRow>
        {([ ["fontsize", "Text size", 12, 28, 1], ["opacity", "Background opacity (%)", 0, 100, 5],
          ["rounding", "Corner radius", 0, 20, 1] ] as const).map(([key, label, min, max, step]) =>
          <PanelSectionRow key={key}><div className="claw-layout-slider"><LayoutSliderField label={label} value={settings[key]} min={min} max={max} step={step} showValue disabled={!ready}
            onChange={(value: number) => update({[key]: value})} /></div></PanelSectionRow>)}

        {settings.hud_orientation==="vertical" && <>
          <PanelSectionRow><ToggleField label="Automatic vertical width"
            checked={settings.vertical_width===0} disabled={!ready}
            onChange={(enabled:boolean)=>update({vertical_width:enabled?0:240})}/></PanelSectionRow>
          {settings.vertical_width>0 && <PanelSectionRow>
            <div className="claw-layout-slider"><LayoutSliderField label="Vertical HUD width (px)"
              value={settings.vertical_width} min={160} max={420} step={10} showValue disabled={!ready}
              onChange={(value:number)=>update({vertical_width:value})}/></div>
          </PanelSectionRow>}
          <PanelSectionRow><Field label="Width behavior"
            description="With the Claw renderer, Auto chooses a compact font-dependent width. Fixed width changes the stacked rows and graph together. Long values may need extra room." /></PanelSectionRow>
        </>}
        <PanelSectionRow><Field label="FPS value scale"
          description="Scales the FPS number only. In Vertical, the FPS header expands without changing CPU/GPU text size." /></PanelSectionRow>
        <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label={"FPS scale · "+settings.fps_scale+"%"}
          value={settings.fps_scale} min={100} max={200} step={10} showValue
          disabled={!ready || !info?.layout_spacing_supported}
          onChange={(value:number)=>update({fps_scale:value})}/></div></PanelSectionRow>
        <div className="claw-fps-scale-preview" aria-label="FPS scale preview"
          style={{width:"100%",maxWidth:"100%",minWidth:0,boxSizing:"border-box",
            background:"#101c2e",border:"1px solid #385a77",borderRadius:8,
            overflow:"hidden",padding:"9px 7px",marginBottom:10}}>
          <span style={{display:"flex",alignItems:"center",gap:8,minWidth:0,
            whiteSpace:"nowrap",color:"#eaf4ff",lineHeight:1.2}}>
            <span style={{color:"#35e5a2",fontSize:12,flexShrink:0}}>FPS</span>
            <span style={{fontWeight:700,fontSize:Math.round(18*settings.fps_scale/100),
              flexShrink:0}}>60</span>
            <span style={{fontSize:12,color:"#a9bbcf",flexShrink:0}}>GPU 72%</span>
          </span>
        </div>

            <PanelSectionRow><Field label="Preview" description="Illustrative only: native game rendering may differ." /></PanelSectionRow>
          </ControlGroup>
          <ControlGroup title="Spacing" summary="Group spacing · padding · readings"
            open={layoutPanel==="spacing"} onToggle={()=>toggleLayoutPanel("spacing")}>
        <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Vertical padding (px)"
          value={settings.padding_y} min={0} max={24} step={1} showValue disabled={!ready}
          onChange={v=>update({padding_y:v})}/></div></PanelSectionRow>
        <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Horizontal padding (px)"
          value={settings.padding_x} min={0} max={24} step={1} showValue
          disabled={!ready || !info?.layout_spacing_supported}
          onChange={v=>update({padding_x:v})}/></div></PanelSectionRow>
        {settings.hud_orientation==="horizontal"&&<PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Horizontal group spacing (px)"
          value={settings.group_gap_x} min={0} max={60} step={1} showValue disabled={!ready || !info?.layout_spacing_supported}
          onChange={group_gap_x=>update({group_gap_x})}/></div></PanelSectionRow>}
        <PanelSectionRow><Field label="Element spacing" description={info?.layout_spacing_supported
          ? "Custom Claw renderer is available. Restart the game to apply spacing changes."
          : "The custom renderer is unavailable. Spacing controls are disabled."} /></PanelSectionRow>
        <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Element gap (px)" value={settings.element_gap} min={0} max={20} step={1} showValue
          disabled={!ready || !info?.layout_spacing_supported} onChange={(value: number) => update({element_gap: value})} /></div></PanelSectionRow>
        <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Column padding (px)" value={settings.table_gap} min={0} max={12} step={1} showValue
          disabled={!ready || !info?.layout_spacing_supported} onChange={(value: number) => update({table_gap: value})} /></div></PanelSectionRow>
        <PanelSectionRow><ToggleField label="Even spacing across inline metrics"
          checked={settings.inline_metrics} disabled={!ready || !info?.layout_spacing_supported || settings.hud_orientation==="vertical"}
          onChange={(v: boolean) => update({inline_metrics: v})} /></PanelSectionRow>
        {settings.hud_orientation==="horizontal" ? <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Within-group gap (px)" value={settings.inner_gap} min={0} max={16} step={1} showValue
          disabled={!ready || !info?.layout_spacing_supported || !settings.inline_metrics}
          onChange={(value: number) => update({inner_gap: value})} /></div></PanelSectionRow>
        : <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Metric value gap (px)" value={settings.vertical_value_gap} min={0} max={16} step={1} showValue
          disabled={!ready || !info?.layout_spacing_supported}
          onChange={(value: number) => update({vertical_value_gap: value})} /></div></PanelSectionRow>}
        {settings.hud_orientation==="vertical" && <>
          <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Vertical group spacing (px)"
            value={settings.vertical_category_gap} min={0} max={20} step={1} showValue
            disabled={!ready || !info?.layout_spacing_supported}
            onChange={(value:number)=>update({vertical_category_gap:value})}/></div></PanelSectionRow>
          <PanelSectionRow><Field label="Group spacing"
            description="Adds space between FPS, CPU, GPU and other categories. Wrapped readings within a category stay together." /></PanelSectionRow>
        </>}


          </ControlGroup>
          {settings.hud_orientation==="horizontal" && <ControlGroup title="Separators" summary="Color · height · thickness"
            open={layoutPanel==="separators"} onToggle={()=>toggleLayoutPanel("separators")}>
            <PanelSectionRow><DialogButton className="claw-control-button" disabled={!ready || !info?.layout_spacing_supported}
              style={{width:"100%",minWidth:0,minHeight:36,padding:"5px 10px",display:"flex",alignItems:"center",gap:8}}
              onClick={()=>openColorPicker("separator","Separator color")}>
              <span aria-hidden="true" style={{width:16,height:16,flexShrink:0,borderRadius:3,
                border:"1px solid #bccbd9",background:"#"+settings.colors.separator}}/>Separator color
            </DialogButton></PanelSectionRow>
            <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Separator height (%)"
              value={settings.separator_height} min={50} max={150} step={5} showValue
              disabled={!ready || !info?.layout_spacing_supported}
              onChange={separator_height=>update({separator_height})}/></div></PanelSectionRow>
            <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Separator thickness (px)"
              value={settings.separator_thickness} min={1} max={6} step={1} showValue
              disabled={!ready || !info?.layout_spacing_supported}
              onChange={separator_thickness=>update({separator_thickness})}/></div></PanelSectionRow>
          </ControlGroup>}
          <ControlGroup title="Frametime graph" summary="Graph style and width"
            open={layoutPanel==="frametime"} onToggle={()=>toggleLayoutPanel("frametime")}>
            {settings.frametime && settings.metrics.graph ? <>
        <PanelSectionRow><Field label="Frametime graph style"
          description="Choose a graph style using the D-pad. Smooth Curve and Dual Layer work in both orientations, each with its own selection." /></PanelSectionRow>
        <GamepadGrid items={graphStyleChoices} columns={2}
          className="claw-tiles claw-graph-tiles" renderItem={(choice)=>{
            const selected=(settings.hud_orientation==="vertical" ? settings.vertical_graph_style : settings.graph_style)===choice.id;
            return <DialogButton key={choice.id} className="claw-control-button"
              aria-label={"Graph style: "+choice.label}
              aria-pressed={selected} disabled={!ready || !info?.layout_spacing_supported}
              onClick={()=>settings.hud_orientation==="vertical"
                  ? update({vertical_graph_style:choice.id})
                  : update({graph_style:choice.id})}
              style={{width:"100%",minWidth:0,margin:0,minHeight:84,padding:"8px 3px",
                background:selected?"#0b4c70":"#162b40",
                border:selected?"2px solid #31cefa":"1px solid #43607a",
                borderRadius:8,color:selected?"#f6fcff":"#bfd5e7"}}>
              <span style={{display:"flex",flexDirection:"column",alignItems:"center",
                justifyContent:"center",gap:6,width:"100%",minWidth:0}}>
                <GraphStyleIcon kind={choice.id}/>
                <span style={{fontSize:11.5,lineHeight:1.2,overflowWrap:"anywhere",
                  textAlign:"center",width:"100%",minWidth:0}}>{choice.label}</span>
              </span>
            </DialogButton>;
          }}/>
        {settings.hud_orientation==="horizontal" ? <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Frametime graph width (px)" value={settings.graph_width} min={80} max={200} step={5} showValue
          disabled={!ready || !info?.layout_spacing_supported} onChange={(value: number) => update({graph_width: value})} /></div></PanelSectionRow>
        : <>
          <PanelSectionRow><ToggleField label="Automatic graph width"
            checked={settings.vertical_graph_width===0} disabled={!ready || !info?.layout_spacing_supported}
            onChange={(enabled:boolean)=>update({vertical_graph_width:enabled?0:200})}/></PanelSectionRow>
          {settings.vertical_graph_width>0 && <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Vertical graph width (px)"
            value={settings.vertical_graph_width} min={80} max={420} step={5} showValue
            disabled={!ready || !info?.layout_spacing_supported}
            onChange={(value:number)=>update({vertical_graph_width:value})}/></div></PanelSectionRow>}
          <PanelSectionRow><div className="claw-layout-slider"><LayoutSliderField label="Vertical graph height (px)"
            value={settings.vertical_graph_height} min={16} max={120} step={2} showValue
            disabled={!ready || !info?.layout_spacing_supported}
            onChange={(value:number)=>update({vertical_graph_height:value})}/></div></PanelSectionRow>
          <PanelSectionRow><Field label="Graph dimensions" description="Width is capped at the HUD's available space. Height applies to all six Vertical graph styles." /></PanelSectionRow>
        </>}
            </> : <Field label="Graph disabled" description="Enable Frametime → Graph in Metrics to edit graph settings."/>}
          </ControlGroup>
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below"
          onClick={()=>confirmAction("Reset layout?",
            "Restores the default position, size, spacing and graph. Saved styles are not deleted.",
            ()=>update({
          hud_orientation:defaults.hud_orientation,vertical_width:defaults.vertical_width,fontsize:defaults.fontsize,fps_scale:defaults.fps_scale,
           center_horizontal:defaults.center_horizontal,hud_position:defaults.hud_position,
          opacity:defaults.opacity,rounding:defaults.rounding,
          padding_y:defaults.padding_y,padding_x:defaults.padding_x,offset_x:defaults.offset_x,offset_y:defaults.offset_y,
          element_gap:defaults.element_gap,table_gap:defaults.table_gap,inner_gap:defaults.inner_gap,group_gap_x:defaults.group_gap_x,unit_superscript:defaults.unit_superscript,
          vertical_value_gap:defaults.vertical_value_gap,vertical_category_gap:defaults.vertical_category_gap,vertical_graph_width:defaults.vertical_graph_width,vertical_graph_height:defaults.vertical_graph_height,
          graph_width:defaults.graph_width,separator_height:defaults.separator_height,separator_thickness:defaults.separator_thickness,
          graph_style:defaults.graph_style,vertical_graph_style:defaults.vertical_graph_style,inline_metrics:defaults.inline_metrics
        }))}>
            Reset layout to defaults
          </ButtonItem></PanelSectionRow>
         </>}
</AccordionCard>
  );
}
