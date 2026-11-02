import {SessionDiagnostics} from "./SessionDiagnostics";
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
const { AccordionCard, ControlGroup } = Core;

/** Standalone advanced presentation; all mutable state is owned by the Decky controller. */
export function AdvancedCard({vm}:{vm:Core.ClawController}) {
  const { info, status, installedVersion, installedVersionError, advancedPanel, toggleAdvancedPanel, showTechnical, setShowTechnical, rendererStatus, tdpStatus, rendererBusy, updateBusy, updateStatus, updateFallback, checkGithubRelease, verifyTdp, verifyRenderer, openSection, toggleSection, ready, refresh, copyLaunchCommand } = vm;
  return (
<AccordionCard id="advanced" title="Advanced" subtitle="Updates and troubleshooting"
          icon={<FaSlidersH />} open={openSection === "advanced"} onToggle={() => toggleSection("advanced")}>
          <ControlGroup title="Updates" summary="Installed version · GitHub releases"
            open={advancedPanel==="updates"} onToggle={()=>toggleAdvancedPanel("updates")}>
            <PanelSectionRow><Field label="Installed version"
              description={installedVersion
                ? "Claw Metrics "+installedVersion
                : installedVersionError || (ready?"Reading installed package…":"Waiting for backend connection…")} /></PanelSectionRow>
        <PanelSectionRow><Field label="GitHub updates"
          description="Check for releases and confirm installation through Decky Loader." /></PanelSectionRow>
        <PanelSectionRow><ButtonItem disabled={!ready || updateBusy}
          layout="below" onClick={()=>{ void checkGithubRelease(); }}>
          <FaDownload style={{marginRight:8}} />
          {updateBusy ? "Checking GitHub…" : "Check for updates"}
        </ButtonItem></PanelSectionRow>
        <PanelSectionRow><Field label="Update status" description={updateStatus} /></PanelSectionRow>
        {updateFallback && <PanelSectionRow><Field label="Manual install via Decky Settings → Developer"
          description={updateFallback} /></PanelSectionRow>}

          </ControlGroup>
          <ControlGroup title="Diagnostics" summary="Session recorder · TDP · renderer"
            open={advancedPanel==="diagnostics"} onToggle={()=>toggleAdvancedPanel("diagnostics")}>
        <SessionDiagnostics ready={ready}/>
        <PanelSectionRow><Field label="TDP limit (read-only)" description="Read-only TDP limit from the active profile. Panel de Control still manages TDP." /></PanelSectionRow>
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below" onClick={() => { void verifyTdp(); }}>
          Check TDP sensor
        </ButtonItem></PanelSectionRow>
        <PanelSectionRow><Field label="TDP diagnostic source" description={tdpStatus} /></PanelSectionRow>
        {info?.layout_spacing_supported && <PanelSectionRow>
          <ButtonItem layout="below" disabled={rendererBusy} onClick={() => { void verifyRenderer(); }}>
            Check game renderer
          </ButtonItem>
        </PanelSectionRow>}
        {info?.layout_spacing_supported && <PanelSectionRow>
          <Field label="Loaded renderer library" description={rendererStatus} />
        </PanelSectionRow>}

          {showTechnical && <>
          <PanelSectionRow><Field label="Configuration path" description={info?.config_path ?? "Not loaded"} /></PanelSectionRow>
          <PanelSectionRow><Field label="TDP" description={info?.tdp_note ?? "TDP -- · no verified reading."} /></PanelSectionRow>
          <PanelSectionRow><Field label="DRAW" description={info?.power_note ?? "Reading depends on the battery sensor."} /></PanelSectionRow>
          </>}
          <PanelSectionRow><ButtonItem layout="below" disabled={!ready} onClick={() => { void refresh(); }}>Refresh status</ButtonItem></PanelSectionRow>

          <PanelSectionRow><ButtonItem layout="below"
            onClick={()=>setShowTechnical(!showTechnical)}>
            {showTechnical?"Hide technical details":"Show technical details"}
          </ButtonItem></PanelSectionRow>
          </ControlGroup>
          <ControlGroup title="Backup launch commands" summary="Only for troubleshooting"
            open={advancedPanel==="backup"} onToggle={()=>toggleAdvancedPanel("backup")}>

          <PanelSectionRow><Field label="Extended Vulkan command (backup)"
            description={info?.experimental_launch_option ?? "Unavailable"} /></PanelSectionRow>
          <PanelSectionRow><ButtonItem disabled={!info?.experimental_launch_option} layout="below"
            onClick={()=>{ void copyLaunchCommand(true); }}>
            <FaCopy style={{marginRight:8}}/> Copy extended Vulkan command
          </ButtonItem></PanelSectionRow>
          <PanelSectionRow><Field label="Stock MangoHud (without Claw renderer)"
            description={info?.launch_option ?? "Unavailable"} /></PanelSectionRow>
          <PanelSectionRow><ButtonItem disabled={!info?.launch_option} layout="below"
            onClick={()=>{ void copyLaunchCommand(); }}>
            <FaCopy style={{marginRight:8}}/> Copy stock launch command
          </ButtonItem></PanelSectionRow>


          </ControlGroup>
        </AccordionCard>
  );
}
