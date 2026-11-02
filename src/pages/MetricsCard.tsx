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

type Settings = Core.Settings;
const { GamepadGrid, groupIcons, order, groups, AccordionCard } = Core;

/** Standalone metrics presentation; all mutable state is owned by the Decky controller. */
export function MetricsCard({vm}:{vm:Core.ClawController}) {
  const { info, settings, expanded, openSection, toggleSection, expandMetric, ready, update, renameMetric, named, related, move, metric, visible, hidden, smallButton } = vm;
  return (
<AccordionCard id="metrics" title="Metrics" subtitle="Displayed metrics and their order"
          icon={<FaChartBar />} open={openSection === "metrics"} onToggle={() => toggleSection("metrics")}>
        <PanelSectionRow><div style={{fontSize: 12, color: "#b8c7d5", marginBottom: 8}}>
          Select a metric to edit its readings, order or label.
        </div></PanelSectionRow>
        <Focusable flow-children="column" className="claw-metric-rows">
        {Array.from({length:Math.ceil(visible.length/3)},(_,rowIndex)=>{
          const row=visible.slice(rowIndex*3,rowIndex*3+3);
          return <Focusable key={rowIndex} flow-children="column" className="claw-metric-row">
          <GamepadGrid items={row} columns={3} className="claw-tiles claw-metric-tiles"
          renderItem={(key) => {
            const group = groups[key];
            const open = expanded === key;
            const total = group.metrics.length + (group.always ? 1 : 0);
            const count = group.metrics.filter(([id]) => settings.metrics[id]).length + (group.always ? 1 : 0);
            return <DialogButton key={key} data-metric={key} className="metric-card claw-control-button"
              disabled={!ready} aria-pressed={open}
                aria-label={"Metric settings: " + named(key)}
                onClick={() => expandMetric(open ? null : key)}
                style={{width:"100%",minWidth:0,minHeight:62,margin:0,padding:"7px 3px",
                  background:open?"#183c6b":"#18222e",
                  border:open?"2px solid #3b8cff":"1px solid #354252",
                  borderRadius:8,color:"#f2f7fc"}}>
                <span style={{display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",
                  gap:4,width:"100%",minWidth:0}}>
                  <span aria-hidden="true" style={{fontSize:15,color:group.color,lineHeight:1}}>{groupIcons[key]}</span>
                  <span style={{fontSize:12,fontWeight:600,lineHeight:1.15,overflowWrap:"anywhere",
                    textAlign:"center",width:"100%",minWidth:0}}>{named(key)}</span>
                  {total>1 && <span style={{fontSize:10,color:"#aab4c1",lineHeight:1}}>{count}/{total}</span>}
                </span>
              </DialogButton>;
          }}/>
        {expanded && row.includes(expanded) && settings[expanded] && (() => {
          const key=expanded;
          const group=groups[key];
          const index=visible.indexOf(key);
          return <div className="metric-detail" style={{border:"1px solid #303b48",
            borderLeft:"3px solid "+group.color,borderRadius:8,background:"#111820",
            padding:"9px 7px",marginTop:9,minWidth:0}}>
            <div style={{fontWeight:700,fontSize:13,marginBottom:7,color:"#f1f7fc"}}>{named(key)} · Settings</div>
            <Focusable style={{display:"flex",gap:5,alignItems:"center",flexWrap:"wrap"}} flow-children="row">
              <DialogButton className="claw-control-button" aria-label={"Rename: "+named(key)} disabled={!ready}
                onClick={()=>renameMetric(key)} style={smallButton}><FaPen aria-hidden="true"/></DialogButton>
              <DialogButton className="claw-control-button" aria-label={"Move earlier: "+named(key)} disabled={!ready || index<=0}
                onClick={()=>move(key,-1)} style={smallButton}>←</DialogButton>
              <DialogButton className="claw-control-button" aria-label={"Move later: "+named(key)} disabled={!ready || index===visible.length-1}
                onClick={()=>move(key,1)} style={smallButton}>→</DialogButton>
              <DialogButton className="claw-control-button" aria-label={"Hide: "+named(key)} disabled={!ready}
                onClick={()=>{expandMetric(null);update({[key]:false});}}
                style={{...smallButton,minWidth:74,width:74,fontSize:12}}>Hide</DialogButton>
            </Focusable>
            {group.always && <Field label={related(group.always)} padding="compact">
              <span style={{fontSize:11,color:"#4acbff"}}>Always on</span>
            </Field>}
            {group.metrics.map(([id,label])=><ToggleField key={id} label={related(label)}
              checked={settings.metrics[id]} disabled={!ready || (["fps_average","fps_low1","ram_game","ram_swap"].includes(id) && !info?.layout_spacing_supported)}
              onChange={(checked:boolean)=>metric(id,checked)}/>)}
            {group.note && <div style={{fontSize:11,lineHeight:1.4,color:"#a6b6c6",marginTop:8}}>
              {related(group.note)}
            </div>}
          </div>;
        })()}
          </Focusable>;
        })}
        </Focusable>
        {hidden.length > 0 && <>
          <PanelSectionRow><Field label="ADD METRIC" description="Restore a hidden metric group." /></PanelSectionRow>
          <GamepadGrid items={hidden} columns={3} className="claw-tiles claw-hidden-metric-tiles"
            renderItem={(key)=><DialogButton key={key} className="claw-control-button" disabled={!ready}
              aria-label={"Show metric: "+named(key)}
              onClick={()=>update({[key]:true})}
              style={{minWidth:0,width:"100%",minHeight:52,margin:0,padding:"6px 3px",
                background:"#16202c",border:"1px dashed #42536a",borderRadius:8}}>
              <span style={{display:"flex",alignItems:"center",justifyContent:"center",
                flexDirection:"column",gap:4,minWidth:0}}>
                <span aria-hidden="true" style={{fontSize:14,color:groups[key].color}}>{groupIcons[key]}</span>
                <span style={{fontSize:11,overflowWrap:"anywhere",textAlign:"center"}}>+ {named(key)}</span>
              </span>
            </DialogButton>}/>
        </>}

        </AccordionCard>
  );
}
