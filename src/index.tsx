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

import {styleLayoutFrom, styleMetricSnapshotFrom, styleMetricUpdatesFrom, independentColors, styleModified} from "./style-presets";
import {metricName, relatedLabel, cleanName, groupNames} from "./metric-names";
import {useClawController,readActivePdcProfileKey,setTdpGameContext} from "./controller";
import {OverlayCard} from "./pages/OverlayCard";
import {LayoutCard} from "./pages/LayoutCard";
import {MetricsCard} from "./pages/MetricsCard";
import {ColorsAndFontCard} from "./pages/ColorsAndFontCard";
import {ActivationCard} from "./pages/ActivationCard";
import {AdvancedCard} from "./pages/AdvancedCard";

/** Thin Decky shell: shared CSS, connection recovery and six independent cards. */
function Content(){
  const vm=useClawController();
  const {settings, setSettings, info, setInfo, status, setStatus, copyStatus, setCopyStatus, connecting, setConnecting, connectionError, setConnectionError, connectionAttempt, layoutPanel, setLayoutPanel, advancedPanel, setAdvancedPanel, showTechnical, setShowTechnical, rendererStatus, setRendererStatus, tdpStatus, setTdpStatus, rendererBusy, setRendererBusy, updateBusy, setUpdateBusy, updateStatus, setUpdateStatus, updateFallback, setUpdateFallback, requestGithubInstall, confirmGithubInstall, checkGithubRelease, verifyTdp, verifyRenderer, expanded, setExpanded, openSection, setOpenSection, styleCategory, setStyleCategory, toggleSection, expandMetric, ready, setReady, current, queue, revision, refresh, update, copyLaunchCommand, renameMetric, named, tokenTitle, styleTitle, renameStyle, confirmAction, loadedPreset, presetDirty, related, chooseStyleCategory, cycleTokenWeight, openTokenColorPicker, resetTokenColor, savePreset, loadPreset, paletteLabel, openColorPicker, toggle, move, metric, visible, hidden, smallButton}=vm;

  return (
    <>
      <style>{`
        [data-section="metrics"] .metric-card:focus-within {
          border-color: #ffffff !important; box-shadow: 0 0 0 1px #ffffff;
        }
        [data-section="metrics"] button:focus-visible {
          outline: 2px solid #ffffff !important; outline-offset: -3px;
          box-shadow: inset 0 0 0 1px #ffffff;
        }
        /* Match actual SteamOS D-pad focus flow to visible grid rows. */
        .claw-tiles {
          display: flex; flex-direction: column;
          gap: 6px; width: 100%; min-width: 0; padding: 4px 0 10px;
          box-sizing: border-box;
        }
        .claw-grid-row {
          display: grid; gap: 6px; width: 100%;
          max-width: 100%; min-width: 0; box-sizing: border-box;
        }
        .claw-grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .claw-grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .claw-tiles > *, .claw-tiles button, .claw-grid-row > * {
          min-width: 0 !important; max-width: 100%; box-sizing: border-box;
        }
        .claw-tiles button { white-space: normal !important; overflow-wrap: anywhere; }
         /* Each Layout slider uses exactly the available inset card width.
            A safe inset keeps headings, values and both thumb endpoints away
            from Decky's card edges. No clipping or fixed pixel track width. */
         [data-section="layout"] .claw-control-group,
         [data-section="layout"] .claw-control-group > div:last-child {
           width: 100%; max-width: 100%; min-width: 0; box-sizing: border-box;
         }
         [data-section="layout"] .claw-layout-slider {
           display: block; width: 100% !important; max-width: 100% !important;
           min-width: 0 !important; box-sizing: border-box !important;
           margin: 2px 0 8px !important; padding: 0 14px 0 10px !important;
         }
         [data-section="layout"] .claw-slider-control,
         [data-section="layout"] .claw-slider-native {
           display: block; width: 100%; max-width: 100%;
           min-width: 0; box-sizing: border-box;
         }
         [data-section="layout"] .claw-slider-heading {
           display: grid; width: 100%; max-width: 100%; min-width: 0;
           grid-template-columns: minmax(0, 1fr) minmax(48px, max-content);
           column-gap: 10px; align-items: baseline; box-sizing: border-box;
           padding: 0 0 4px 0;
         }
         [data-section="layout"] .claw-slider-label {
           min-width: 0; overflow-wrap: anywhere;
           white-space: normal; line-height: 1.25;
         }
         [data-section="layout"] .claw-slider-number {
           min-width: 48px; text-align: right; white-space: nowrap;
           overflow: visible; text-overflow: clip;
           font-variant-numeric: tabular-nums;
         }
         [data-section="layout"] .claw-slider-native > *,
         [data-section="layout"] .claw-slider-native :is(
           [class*="DialogSlider"], [class*="SliderControl"],
           [class*="SliderRoot"], [class*="SliderTrack"],
           [class*="sliderTrack"], [class*="SliderField"], input[type="range"]
         ) {
           min-width: 0 !important; max-width: 100% !important;
           box-sizing: border-box !important; flex-shrink: 1 !important;
         }
         [data-section="layout"] .claw-slider-native > * {
           width: 100% !important;
         }

         .claw-style-tiles .style-group-icon {
          display: inline-flex; align-items: center; justify-content: center;
          margin: 0 !important; color: #bceaff; font-size: 13px; line-height: 1;
        }
        .claw-metric-row { margin-bottom: 7px; width: 100%; min-width: 0; }
         .claw-style-row { margin-bottom: 7px; width: 100%; max-width: 100%; min-width: 0; box-sizing: border-box; }
         .claw-style-tiles { padding-bottom: 2px; }
         .claw-style-detail {
           margin: 8px 0 10px; padding: 9px 7px; width: 100%;
           min-width: 0; max-width: 100%; box-sizing: border-box;
           background: #102236; border: 1px solid #365d7c;
           border-left: 3px solid #29dcff; border-radius: 8px;
         }
        /* One accessible controller row per style token. */
         [data-section="colors"] .claw-style-detail {
           margin: 5px 0 7px; padding: 6px 5px;
         }
         [data-section="colors"] .claw-token-card {
           width: 100%; max-width: 100%; min-width: 0; box-sizing: border-box;
           padding: 6px 6px 7px; margin: 0 0 5px;
           background: #1a2c43; border: 1px solid #375878; border-radius: 7px;
         }
         [data-section="colors"] .claw-token-title {
           font-size: 12px; line-height: 1.2; font-weight: 700;
           color: #e7f5ff; margin: 0 0 5px; overflow-wrap: anywhere;
         }
         [data-section="colors"] .claw-token-controls {
           width: 100%; max-width: 100%; min-width: 0; box-sizing: border-box;
           display: flex; gap: 5px;
         }
         [data-section="colors"] .claw-token-controls > button {
           min-width: 0 !important; box-sizing: border-box;
         }
         .claw-metric-tiles { padding-bottom: 2px; }
        .claw-metric-tiles .metric-card:focus-within {
          outline: 2px solid #ffffff; outline-offset: -2px; border-radius: 8px;
        }
        .claw-metric-tiles button[aria-pressed="true"] {
          box-shadow: 0 0 0 1px #29dcff inset;
        }
        .claw-weight-tiles .claw-grid-row { min-height: 39px; }
        [data-section="colors"] .loaded-style-status {
          padding: 8px 9px; margin: 0 0 10px; background: #0b263b;
          border: 1px solid #306689; border-radius: 7px;
          font-size: 12px; color: #d8edff;
          width: 100%; min-width: 0; max-width: 100%; box-sizing: border-box;
          overflow-wrap: anywhere;
        }
        /* Two preset slots only; avoid Decky's intrinsic DialogButton min-width. */
        .claw-preset-list {
          display: grid; grid-template-columns: minmax(0, 1fr);
          gap: 8px; width: 100%; min-width: 0; max-width: 100%;
          padding: 0; margin: 0 0 8px; box-sizing: border-box;
        }
        .claw-preset-card {
          min-width: 0; max-width: 100%; box-sizing: border-box;
          border-radius: 9px; padding: 9px;
          background: #142840; border: 1px solid #365b7b;
        }
        .claw-preset-card[data-loaded="true"] {
          background: #093454; border-color: #26d6fa;
        }
        .claw-preset-actions {
          display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 7px; width: 100%; min-width: 0; margin-top: 8px;
          box-sizing: border-box;
        }
        .claw-preset-actions > button {
          width: 100% !important; max-width: 100% !important;
          min-width: 0 !important; margin: 0 !important;
          padding: 8px 3px !important; box-sizing: border-box;
          font-size: 12px !important; min-height: 38px;
          white-space: normal !important; overflow-wrap: anywhere;
        }
        .claw-preset-actions .claw-preset-label {
          display: inline-flex; align-items: center; justify-content: center;
          gap: 5px; width: 100%; min-width: 0;
          white-space: nowrap; font-size: 12px; line-height: 1.2;
        }
        .claw-preset-actions .claw-preset-label svg {
          display: block; flex: 0 0 auto;
          width: 12px; height: 12px;
        }
        /* Quiet SteamOS focus: use the open-card blue surface without a
           white ring or double outline. Supports DOM focus and .gpfocus. */
        [data-section] .claw-accordion-header > button,
        [data-section] .claw-accordion-header > button:focus,
        [data-section] .claw-accordion-header > button:focus-visible,
        [data-section] .claw-accordion-header > button.gpfocus,
        [data-section] .claw-accordion-header:has(.gpfocus) > button,
        [data-section][data-focused="true"] .claw-accordion-header > button {
          outline: none !important;
          box-shadow: none !important;
        }
        [data-section] .claw-accordion-header:focus-within > button,
        [data-section] .claw-accordion-header:has(.gpfocus) > button,
        [data-section] .claw-accordion-header:has([class*="gpfocus"]) > button,
        [data-section][data-focused="true"] .claw-accordion-header > button,
        [data-section][data-selected="true"] .claw-accordion-header > button {
          background: #073858 !important;
        }
        [data-section] .claw-accordion-header:focus-within .claw-accordion-icon,
        [data-section] .claw-accordion-header:has(.gpfocus) .claw-accordion-icon,
        [data-section] .claw-accordion-header:has([class*="gpfocus"]) .claw-accordion-icon,
        [data-section][data-focused="true"] .claw-accordion-icon,
        [data-section][data-selected="true"] .claw-accordion-icon {
          background: #075b83 !important;
          color: #42e0ff !important;
        }
        [data-section]:has(> .claw-accordion-header:focus-within),
        [data-section]:has(> .claw-accordion-header .gpfocus),
        [data-section]:has(> .claw-accordion-header [class*="gpfocus"]) {
          border-color: #2c709d !important;
          border-left-color: #08d3fa !important;
          box-shadow: 0 0 12px rgba(0,153,237,0.13) !important;
        }
        /* SteamOS controller focus can come from DOM :focus or Decky's
           .gpfocus class. Focus must be distinct from the saved anchor. */
        .claw-hud-anchor:focus,
        .claw-hud-anchor:focus-visible,
        .claw-hud-anchor.gpfocus,
        .claw-hud-anchor[class*="gpfocus"],
        .claw-hud-anchor:focus-within,
        .claw-hud-anchor:has(.gpfocus),
        .claw-hud-anchor:has([class*="gpfocus"]) {
          background: #0874a9 !important;
          border: 2px solid #ffffff !important;
          outline: 2px solid #31deff !important;
          outline-offset: -5px !important;
          color: #ffffff !important;
          box-shadow: 0 0 0 2px #31deff, 0 0 11px 2px rgba(0,200,255,0.58) !important;
        }
        .claw-hud-anchor:focus span,
        .claw-hud-anchor.gpfocus span,
        .claw-hud-anchor[class*="gpfocus"] span { color: #ffffff !important; }
        /* Identical focus semantics for Metrics, Colors & Font, graph styles. */
        .claw-control-button:focus,
        .claw-control-button:focus-visible,
        .claw-control-button.gpfocus,
        .claw-control-button[class*="gpfocus"],
        .claw-control-button:focus-within,
        .claw-control-button:has(.gpfocus),
        .claw-control-button:has([class*="gpfocus"]) {
          background: #0874a9 !important;
          border: 2px solid #ffffff !important;
          outline: 2px solid #31deff !important;
          outline-offset: -5px !important;
          color: #ffffff !important;
          box-shadow: 0 0 0 2px #31deff, 0 0 11px 2px rgba(0,200,255,0.58) !important;
        }
        .claw-control-button:focus span,
        .claw-control-button.gpfocus span,
        .claw-control-button[class*="gpfocus"] span { color: inherit; }
        .claw-rename-modal { max-width: 100%; overflow-wrap: anywhere; }
        .claw-rename-modal input { max-width: 100%; box-sizing: border-box; }
      `}</style>
      <PanelSection title="Claw Metrics · v0.2.4-test.60">
        <PanelSectionRow>
          <div style={{display: "flex", alignItems: "center", gap: 12, padding: "6px 2px 10px"}}>
            <div style={{background: "#084f75", border: "1px solid #14bcf9", color: "#3bdcff",
              width: 38, height: 38, borderRadius: 10, display: "flex", alignItems: "center",
              justifyContent: "center", fontSize: 22}}><FaChartBar /></div>
            <div style={{minWidth: 0}}>
              <div style={{fontSize: 18, fontWeight: 700, lineHeight: 1.2}}>Claw Metrics</div>
              <div style={{fontSize: 12, color: "#a7c4dd", marginTop: 3}}>Performance overlay · MSI Claw</div>
            </div>
          </div>
        </PanelSectionRow>
      </PanelSection>
      {!ready && <PanelSection title="Connection recovery">
        <PanelSectionRow>
          <Field label={connecting?"Connecting to Python backend…":"Backend not connected"}
            description={connectionError||"Checking the Decky backend after installation."}/>
        </PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" disabled={connecting}
          onClick={()=>{void refresh();}}>
          {connecting?"Connecting…":"Retry backend connection"}
        </ButtonItem></PanelSectionRow>
        <PanelSectionRow><Field label="If retry fails"
          description="Restart Decky Loader from Decky Settings. Do not delete saved Claw Metrics settings."/>
        </PanelSectionRow>
      </PanelSection>}
      <div style={{padding: "0 7px 14px"}}>
        <OverlayCard vm={vm}/>
        <LayoutCard vm={vm}/>
        <MetricsCard vm={vm}/>
        <ColorsAndFontCard vm={vm}/>
        <ActivationCard vm={vm}/>
        <AdvancedCard vm={vm}/>
      </div>
    </>
  );
}

export default definePlugin(() => {
  let stopped = false;
  let pending = false;
  const report = async () => {
    if (stopped || pending) return;
    const key = readActivePdcProfileKey();
    if (key === undefined) return;
    pending = true;
    try { await setTdpGameContext(key); }
    catch { /* Hardware probing continues even if Decky RPC is unavailable. */ }
    finally { pending = false; }
  };
  void report();
  const timer = setInterval(() => { void report(); }, 3000);
  return {
    name: "Claw Metrics",
    titleView: <div>Claw Metrics</div>,
    content: <Content />,
    icon: <FaChartLine />,
    onDismount() { stopped = true; clearInterval(timer); },
  };
});


