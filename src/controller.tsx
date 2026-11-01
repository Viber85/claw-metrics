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
import type {SectionKey} from "./components/AccordionCard";

export type Group = "fps" | "frametime" | "cpu" | "gpu" | "ram" | "vram" | "battery" | "tdp" | "draw" | "time";
export type FontWeight = "light" | "regular" | "semibold" | "bold";
export type GraphStyle = "area" | "line" | "bars" | "dual";
export type HudOrientation = "horizontal" | "vertical";
export type HudPosition = "top-left" | "top-center" | "top-right" | "bottom-left" | "bottom-center" | "bottom-right";
export const hudPositions: {id:HudPosition; label:string; icon:string; column:number; row:number}[] = [
  {id:"top-left",label:"Top left",icon:"↖",column:1,row:1},
  {id:"top-center",label:"Top center",icon:"↑",column:2,row:1},
  {id:"top-right",label:"Top right",icon:"↗",column:3,row:1},
  {id:"bottom-left",label:"Bottom left",icon:"↙",column:1,row:2},
  {id:"bottom-center",label:"Bottom center",icon:"↓",column:2,row:2},
  {id:"bottom-right",label:"Bottom right",icon:"↘",column:3,row:2},
];

// Actual silhouettes of the four native frametime render modes.
// They are the primary symbols in the gamepad grid; no letter shortcuts.
export function GraphStyleIcon({kind}:{kind:GraphStyle}) {
  const isArea = kind === "area" || kind === "dual";
  return <svg width={46} height={35} viewBox="0 0 48 34" aria-hidden="true"
    style={{display:"block",flexShrink:0,overflow:"visible"}}>
    <path d="M3 30 H45" fill="none" stroke="#7090a7" strokeWidth={1} strokeOpacity={0.55}/>
    {isArea && <path d="M3 25 L11 19 L19 23 L28 9 L36 16 L45 5 L45 30 L3 30 Z"
      fill="#39dabe" fillOpacity={kind === "area" ? 0.88 : 0.19} />}
    {kind === "bars" ? <>
      <rect x={4} y={18} width={6} height={12} rx={0.7} fill="#39dabe"/>
      <rect x={14} y={11} width={6} height={19} rx={0.7} fill="#39dabe"/>
      <rect x={24} y={16} width={6} height={14} rx={0.7} fill="#39dabe"/>
      <rect x={34} y={4} width={6} height={26} rx={0.7} fill="#39dabe"/>
    </> : kind !== "area" && <polyline points="3,25 11,19 19,23 28,9 36,16 45,5"
      fill="none" stroke={kind === "dual" ? "#77eaff" : "#39dabe"} strokeWidth={kind === "dual" ? 2.8 : 2.3}
      strokeLinecap="round" strokeLinejoin="round"/>}
  </svg>;
}
export const graphStyleChoices: {id:GraphStyle;label:string}[] = [
  {id:"area",label:"Filled area"},
  {id:"line",label:"Line"},
  {id:"bars",label:"Histogram"},
  {id:"dual",label:"Line + fill"},
];

export {GamepadGrid} from "./components/GamepadGrid";

export type WeightSelection = "inherit" | FontWeight;
export type StyleCategory = "global" | "fps" | "cpu" | "gpu" | "ram" | "vram" | "battery" | "time" | "tdp" | "draw" | "values";
export type TokenKey = "fps.label" | "fps.value" | "fps.ms" | "cpu.label" | "cpu.load" | "cpu.temp" | "cpu.clock" | "cpu.power" | "gpu.label" | "gpu.load" | "gpu.temp" | "gpu.clock" | "gpu.power" | "gpu.junction" | "gpu.fan" | "gpu.voltage" | "ram.label" | "ram.value" | "vram.label" | "vram.value" | "vram.temp" | "vram.clock" | "battery.label" | "battery.value" | "battery.time" | "battery.power" | "time.value" | "tdp.value";
export type MetricToken = {key: TokenKey; label: string; defaultColor: ColorKey};
export const tokenGroups: Record<Exclude<StyleCategory, "global">, MetricToken[]> = {
  fps: [{key:"fps.label", label:"FPS label", defaultColor:"fps_label"}, {key:"fps.value", label:"FPS value", defaultColor:"fps_value"}, {key:"fps.ms", label:"Frametime (ms)", defaultColor:"text"}],
  cpu: [{key:"cpu.label", label:"CPU label", defaultColor:"cpu"}, {key:"cpu.load", label:"Load (%)", defaultColor:"text"}, {key:"cpu.temp", label:"Temperature (°C)", defaultColor:"text"}, {key:"cpu.clock", label:"Clock (MHz)", defaultColor:"text"}, {key:"cpu.power", label:"Power (W)", defaultColor:"text"}],
  gpu: [{key:"gpu.label", label:"GPU label", defaultColor:"gpu"}, {key:"gpu.load", label:"Load (%)", defaultColor:"text"}, {key:"gpu.temp", label:"Temperature (°C)", defaultColor:"text"}, {key:"gpu.clock", label:"Clock (MHz)", defaultColor:"text"}, {key:"gpu.power", label:"Power (W)", defaultColor:"text"}, {key:"gpu.junction", label:"Junction temperature", defaultColor:"text"}, {key:"gpu.fan", label:"Fan speed", defaultColor:"text"}, {key:"gpu.voltage", label:"Voltage", defaultColor:"text"}],
  ram: [{key:"ram.label", label:"RAM label", defaultColor:"ram"}, {key:"ram.value", label:"Usage (GiB)", defaultColor:"text"}],
  vram: [{key:"vram.label", label:"VRAM label", defaultColor:"vram"}, {key:"vram.value", label:"Usage (GiB)", defaultColor:"text"}, {key:"vram.temp", label:"Memory temperature", defaultColor:"text"}, {key:"vram.clock", label:"Memory clock", defaultColor:"text"}],
  battery: [{key:"battery.label", label:"Battery label", defaultColor:"battery"}, {key:"battery.value", label:"Battery (%) / icon", defaultColor:"text"}, {key:"battery.time", label:"Remaining time", defaultColor:"text"}],
  time: [{key:"time.value", label:"Clock", defaultColor:"time"}],
  draw: [{key:"battery.power",label:"DRAW",defaultColor:"draw"}],
  tdp: [{key:"tdp.value",label:"TDP limit (W)",defaultColor:"tdp"}],
  values: [],
};
tokenGroups.values=Object.entries(tokenGroups).filter(([key])=>!["time","draw","tdp","values"].includes(key)).flatMap(([,tokens])=>tokens.filter(token=>!token.key.endsWith(".label")));
export const weightOptions: WeightSelection[] = ["inherit", "light", "regular", "semibold", "bold"];
export const weightLabel: Record<WeightSelection, string> = {
  inherit: "Global", light: "Light", regular: "Regular", semibold: "SemiBold", bold: "Bold",
};
export const styleTabs: [StyleCategory,string][] = [
  ["global","Global"],["fps","FPS"],["cpu","CPU"],["gpu","GPU"],
  ["ram","RAM"],["vram","VRAM"],["battery","Battery"],["time","Clock"],["tdp","TDP"],["draw","DRAW"],["values","Values"],
];
export type SavedStyle = Partial<Record<"fontsize"|"opacity"|"rounding"|"padding_x"|"padding_y"|"offset_x"|"offset_y"|"element_gap"|"table_gap"|"inner_gap"|"graph_width"|"vertical_width"|"vertical_value_gap"|"vertical_category_gap"|"vertical_graph_width"|"vertical_graph_height",number>> & {
  sans?:boolean; inline_metrics?:boolean; graph_style?:GraphStyle; hud_orientation?:HudOrientation; version?:number;
  groups?: Partial<Record<Group, boolean>>; metrics?: Record<string, boolean>;
  colors: ColorSettings; font_weight: FontWeight; fps_bold: boolean;
  token_weights: Partial<Record<TokenKey, FontWeight>>;
  token_colors: Partial<Record<TokenKey, string>>;
};

export type ColorKey = "text" | "separator" | "fps_label" | "fps_value" | "cpu" | "gpu" | "ram" | "vram" | "battery" | "graph" | "time" | "tdp" | "draw";
export type ColorSettings = Record<ColorKey, string>;
export const defaultColors: ColorSettings = {
  text: "F0F2F5", separator: "777C87", fps_label: "30E5A0", fps_value: "30E5A0",
  cpu: "37C9EF", gpu: "8BDA62", ram: "B077DF", vram: "D76AB8",
  battery: "30E5A0", graph: "30E5A0", time:"F0F2F5", draw:"F0F2F5", tdp:"FFBD69",
};
export const colorRows: [ColorKey, string][] = [
  ["text", "Values"], ["time", "Clock"], ["tdp", "TDP"], ["draw", "DRAW"], ["separator", "Group separators"],
  ["fps_label", "FPS"],
  ["cpu", "CPU label"], ["gpu", "GPU label"], ["ram", "RAM label"],
  ["vram", "VRAM label"], ["battery", "Battery label"], ["graph", "Frametime graph"],
];

// Decky picker uses HSL sliders; MangoHud accepts 6-digit RGB without '#'.
export function rgbToHsl(hex: string): [number, number, number] {
  const parts = [0, 2, 4].map(i => parseInt(hex.slice(i, i + 2), 16) / 255);
  const [r, g, b] = parts;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0, s = 0;
  const l = (max + min) / 2, diff = max - min;
  if (diff) {
    s = diff / (1 - Math.abs(2 * l - 1));
    switch (max) {
      case r: h = ((g - b) / diff) % 6; break;
      case g: h = (b - r) / diff + 2; break;
      default: h = (r - g) / diff + 4;
    }
    h = ((h * 60) + 360) % 360;
  }
  return [Math.round(h), Math.round(s * 100), Math.round(l * 100)];
}
export function hslToHex(hue: number, saturation: number, lightness: number): string {
  // This plugin only stores opaque 24-bit RGB. Alpha is not supported by
  // MangoHud label/separator settings; never add a fourth channel.
  const h = ((hue % 360) + 360) % 360;
  const s = Math.max(0, Math.min(100, saturation)) / 100;
  const l = Math.max(0, Math.min(100, lightness)) / 100;
  const a = s * Math.min(l, 1 - l);
  const channel = (n: number) => {
    const k = (n + h / 30) % 12;
    return Math.round(255 * (l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1))))
      .toString(16).padStart(2, "0").toUpperCase();
  };
  return channel(0) + channel(8) + channel(4);
}

export type OpaqueColorPickerProps = {
  title: string; hex: string; closeModal: () => void; onConfirm: (hex: string) => void;
};
export function OpaqueColorPicker({title, hex, closeModal, onConfirm}: OpaqueColorPickerProps) {
  const [initialH, initialS, initialL] = rgbToHsl(hex);
  const [h, setH] = useState(initialH);
  const [s, setS] = useState(initialS);
  const [l, setL] = useState(initialL);
  const preview = hslToHex(h, s, l);
  const [hexOverride, setHexOverride] = useState<string|null>(null);
  const hexValue = hexOverride ?? preview;
  const validHex = /^#?[0-9A-Fa-f]{6}$/.test(hexValue);
  const chosen = validHex ? hexValue.replace(/^#/, "").toUpperCase() : preview;
  return (
    <ConfirmModal strTitle={title} bAllowFullSize onCancel={closeModal}
      onOK={() => { onConfirm(chosen); closeModal(); }}>
      <div style={{padding: "8px 4px 14px"}}>
        <div style={{display: "flex", alignItems: "center", gap: 12, marginBottom: 12}}>
          <div style={{height: 48, width: 48, borderRadius: 5,
            backgroundColor: "#" + chosen, border: "1px solid #8794a4"}} />
          <div>
            <div>#{chosen}</div>
            <div style={{fontSize: 12, opacity: 0.7}}>Opaque RGB color (100% alpha)</div>
          </div>
        </div>
        <TextField label="HEX color (#RRGGBB)" value={hexValue}
          onChange={event=>setHexOverride(event.currentTarget.value.slice(0,7))}
          description={validHex?"Exact RGB color. Edit with SteamOS keyboard.":"Invalid HEX — the slider color will be used."}/>
        <SliderField showValue editableValue label="Hue"
          value={h} min={0} max={360} step={1}
          onChange={v=>{setH(v);setHexOverride(null);}} />
        <SliderField showValue editableValue label="Saturation"
          value={s} min={0} max={100} step={1}
          onChange={v=>{setS(v);setHexOverride(null);}} />
        <SliderField showValue editableValue label="Lightness"
          value={l} min={0} max={100} step={1}
          onChange={v=>{setL(v);setHexOverride(null);}} />
      </div>
    </ConfirmModal>
  );
}
export const groupIcons: Record<string, ReactNode> = {global:<FaPalette/>,fps:<FaTachometerAlt/>,cpu:<FaMicrochip/>,gpu:<FaDesktop/>,ram:<FaMemory/>,vram:<FaMemory/>,battery:<FaBatteryThreeQuarters/>,time:<FaClock/>,tdp:<FaBolt/>,draw:<FaBolt/>,values:<FaHashtag/>};
export function RenameStyleModal({value,slot,onConfirm,onCancel}:{
  value:string; slot:string; onConfirm:(value:string)=>void; onCancel:()=>void;
}) {
  const [text,setText]=useState(value);
  return <ConfirmModal strTitle={"Rename style "+slot} onCancel={onCancel}
    onOK={()=>onConfirm(cleanName(text))}>
    <div style={{padding:"10px 4px"}}>
      <TextField label="Style name" focusOnMount value={text} placeholder={"Style "+slot}
        description="Up to 24 characters. Clear to restore the default style name."
        onChange={e=>setText(e.currentTarget.value.slice(0,24))}/>
    </div>
  </ConfirmModal>;
}
export function RenameMetricModal({name,original,onConfirm,onCancel}:any){
 const [value,setValue]=useState(name);
 return <ConfirmModal strTitle="Rename metric" onCancel={onCancel}
   onOK={()=>onConfirm(cleanName(value))}>
  <div className="claw-rename-modal" style={{padding:"8px 2px",minWidth:0}}>
    <TextField label="Metric label" focusOnMount placeholder={original}
      value={value} onChange={(event)=>setValue(event.currentTarget.value.slice(0,24))}
      description="Press A to edit with the SteamOS keyboard. Maximum 24 characters." />
    <p className="description" style={{fontSize:12,lineHeight:1.4,margin:"12px 0"}}>
      The label is used in Metrics, Colors & Font and the HUD. Leave empty to restore the default.
    </p>
    <DialogButton style={{width:"100%",margin:0,minWidth:0}} onClick={()=>setValue("")}>
      Use default label
    </DialogButton>
  </div>
 </ConfirmModal>;
}

export type Settings = Record<Group, boolean> & {
  active_style: string|null; style_names: Record<string,string>;
  custom_labels: Record<string,string>;
  enabled: boolean; fontsize: number; fps_scale: number; center_horizontal: boolean; hud_position: HudPosition; hud_orientation: HudOrientation; vertical_width: number; vertical_value_gap: number; vertical_category_gap: number; vertical_graph_width: number; vertical_graph_height: number; opacity: number; power: boolean; tdp: boolean;
  sans: boolean; rounding: number; offset_x: number; offset_y: number; padding_y: number;
  padding_x: number; element_gap: number; table_gap: number; graph_width: number; graph_style: GraphStyle;
  inner_gap: number; inline_metrics: boolean; fps_bold: boolean; font_weight: FontWeight; order: Group[];
  metrics: Record<string, boolean>;
  colors: ColorSettings;
  token_weights: Partial<Record<TokenKey, FontWeight>>;
  token_colors: Partial<Record<TokenKey, string>>;
  style_presets: Record<string, SavedStyle>;
};
export const order: Group[] = ["fps", "frametime", "cpu", "gpu", "ram", "vram", "battery", "tdp", "draw", "time"];
export const groups: Record<Group, {label: string; color: string; metrics: [string, string][]; always?: string; note?: string}> = {
  fps: {label: "FPS", color: "#30e5a0", metrics: [], always: "FPS", note: "The base font size is shared by the FPS label and other values."},
  frametime: {label: "Frametime", color: "#30e5a0", metrics: [["fps_ms", "Frametime (ms)"], ["graph", "Frametime graph"]], note: "The ms value follows the FPS block. Enable FPS to display milliseconds."},
  gpu: {label: "GPU", color: "#8bda62", always: "GPU load", metrics: [["gpu_temp", "GPU temp"], ["gpu_junction_temp", "GPU junction temp"], ["gpu_core_clock", "GPU clock"], ["gpu_mem_clock", "VRAM clock"], ["gpu_mem_temp", "VRAM temp"], ["gpu_power", "GPU watts"], ["gpu_fan", "GPU fan"], ["gpu_voltage", "GPU voltage"]], note: "VRAM clock and temperature appear in the VRAM block. Other sensors depend on Z2 Extreme hardware support."},
  cpu: {label: "CPU", color: "#37c9ef", always: "CPU load", metrics: [["cpu_temp", "CPU temp"], ["cpu_mhz", "CPU clock"], ["cpu_power", "CPU watts"]]},
  ram: {label: "RAM", color: "#b077df", always: "RAM usage", metrics: []},
  vram: {label: "VRAM", color: "#d76ab8", always: "VRAM usage", metrics: [], note: "VRAM readings use the GPU data source. Enable GPU as well."},
  battery: {label: "Battery", color: "#30e5a0", always: "Battery level", metrics: [["battery_icon", "Battery icon (replaces %)"], ["battery_time", "Remaining time"]], note: "Battery icon and percentage are alternative display formats."},
  tdp: {label: "TDP", color: "#ffbd69", metrics: [], always: "Configured TDP limit", note: "Read-only: RyzenAdj STAPM or MSI firmware PL1. Displays TDP -- when unavailable; does not control power."},
  draw: {label: "DRAW", color: "#ee6279", metrics: [], always: "Battery discharge watts", note: "Total battery discharge. Displays DRAW -- while charging or when a sensor is unavailable."},
  time: {label: "Clock", color: "#f0f2f5", metrics: [], always: "Clock · 24 h"},
};

export type TdpStatus = { readable:boolean; watts:number|null; source:string; description:string };
export type Info = {
  layout_spacing_supported: boolean;
  experimental_launch_option: string;
  short_launch_option: string;
  short_launcher_ready: boolean;
  experimental_config_readable: boolean;
  font_path: string;
  font_ready: boolean;
  condensed_fonts_ready: boolean;
  config_readable: boolean;
  config_path: string;
  launch_option: string;
  tdp_note: string;
  power_note: string;
};

export const defaults: Settings = {
  active_style:null, style_names:{}, custom_labels: {},
  enabled: true, fontsize: 18, fps_scale: 100, center_horizontal: false, hud_position: "top-left", hud_orientation:"horizontal", vertical_width:0, vertical_value_gap:8, vertical_category_gap:6, vertical_graph_width:0, vertical_graph_height:28, opacity: 80, fps: true, frametime: true,
  cpu: true, gpu: true, ram: true, vram: true, battery: true, draw: true,
  power: true, time: true, tdp: false, sans: true, rounding: 10, offset_x: 8, offset_y: 0, padding_y: 0,
  padding_x: 5, element_gap: 8, table_gap: 4, graph_width: 150, graph_style: "line",
  inner_gap: 4, inline_metrics: true, fps_bold: true, font_weight: "regular", order,
  metrics: {fps_ms: true, graph: true, cpu_temp: true, cpu_mhz: true, cpu_power: true,
    gpu_temp: true, gpu_junction_temp: false, gpu_core_clock: true, gpu_mem_clock: false,
    gpu_mem_temp: false, gpu_power: true, gpu_fan: false, gpu_voltage: false,
    battery_icon: false, battery_time: true},
  colors: {...defaultColors}, token_weights: {}, token_colors: {}, style_presets: {},
};

// Callable methods are provided by the Decky Python backend.
export const load = callable<[], Settings>("get_settings");
export const save = callable<[Settings], { ok: boolean; config_path: string }>("save_settings");
export const getInfo = callable<[], Info>("get_info");
export const getTdpStatus = callable<[], TdpStatus>("get_tdp_status");
export const setTdpGameContext = callable<[string | null], {ok: boolean}>("set_tdp_game_context");

export function readActivePdcProfileKey(): string | null | undefined {
  try {
    const app = Router?.MainRunningApp as
      { appid?: number | string; display_name?: string; app_type?: number } | undefined;
    if (!app?.appid) return null;
    const raw = String(app.appid);
    if (app.app_type === 1073741824 || Number(raw) >= 2147483648) {
      const name = app.display_name?.trim().toLowerCase().replace(/\s+/g, " ");
      return name ? "ns:" + name : raw;
    }
    return raw;
  } catch {
    return undefined;
  }
}

export type RendererStatus = {
  native_loaded: boolean; native_processes: number; stock_processes: number;
  layer_requests: number; config_requests: number; path_requests: number;
  processes_seen: number; environments_read: number;
  manifest_in_user_location: boolean; reason: string;
};
export const getRendererStatus = callable<[], RendererStatus>("get_renderer_status");

export type GithubRelease = {
  version:string;tag:string;notes:string;
  asset_url:string;sha256:string;release_url:string;
};
export type GithubUpdateInfo = {
  ok:boolean; current?:string; available:boolean; latest:GithubRelease|null;
  error?:string; source?:string;
};
export type DeckyHttpResponse = {status:number;body:string};
export const GITHUB_RELEASES_API = "https://api.github.com/repos/ikorljan-droid/claw-metrics/releases?per_page=30";
export const checkUpdates = callable<[], GithubUpdateInfo>("check_updates");
export const getInstalledVersion = callable<[], {version:string}>("get_installed_version");
export const validateGithubReleases = callable<[string],GithubUpdateInfo>("validate_github_releases");

// Decky Loader handles ZIP download, SHA-256 verification, unloading and
// reinstalling its plugins. This is a guarded loader-internal API, not part
// of @decky/api. Do not copy/unzip a plugin from its own privileged backend.
export type LoaderInstaller = {
  callable?: (route:string) => (...args:unknown[]) => Promise<unknown>;
};
export function deckyInstaller(): LoaderInstaller|null {
  return (window as Window & {DeckyBackend?:LoaderInstaller}).DeckyBackend ?? null;
}

export function withTimeout<T>(request: Promise<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("Backend did not respond (10 s). Restart Decky Loader.")), 10000);
    request.then(resolve, reject).finally(() => clearTimeout(timer));
  });
}

export {AccordionCard} from "./components/AccordionCard";
export type {SectionKey,AccordionCardProps} from "./components/AccordionCard";

export type LayoutPanel = "position" | "size" | "spacing" | "frametime";
export type AdvancedPanel = "updates" | "diagnostics" | "backup";
export {ControlGroup} from "./components/ControlGroup";

// Decky can remount Content after backend saves. Keep navigation state
// outside the React instance, so saving never jumps back to Metrics.
export let lastOpenSection: SectionKey | null = "metrics";
export let lastExpandedMetric: Group | null = null;
export let lastStyleCategory: StyleCategory | null = "global";
// Persist expanded subcard choices across Decky remounts, just like Metrics
// and Colors & Font. Null means every subcard is collapsed.
export let lastLayoutPanel: LayoutPanel | null = "position";
export let lastAdvancedPanel: AdvancedPanel | null = "updates";

export function useClawController() {
  const [settings, setSettings] = useState<Settings>(defaults);
  const [info, setInfo] = useState<Info | null>(null);
  const [status, setStatus] = useState("Loading…");
  const [copyStatus, setCopyStatus] = useState("");
  const [connecting,setConnecting] = useState(true);
  const [connectionError,setConnectionError] = useState("");
  const connectionAttempt = useRef(0);
  const [layoutPanel,setLayoutPanel]=useState<LayoutPanel | null>(()=>lastLayoutPanel);
  const [advancedPanel,setAdvancedPanel]=useState<AdvancedPanel | null>(()=>lastAdvancedPanel);
  const toggleLayoutPanel=(id:LayoutPanel)=>{
    const next=lastLayoutPanel===id?null:id;
    lastLayoutPanel=next;
    setLayoutPanel(next);
  };
  const toggleAdvancedPanel=(id:AdvancedPanel)=>{
    const next=lastAdvancedPanel===id?null:id;
    lastAdvancedPanel=next;
    setAdvancedPanel(next);
  };
  const [showTechnical,setShowTechnical] = useState(false);
  const [rendererStatus, setRendererStatus] = useState("Not checked. Start a game to verify.");
  const [tdpStatus, setTdpStatus] = useState("TDP has not been checked.");
  const [rendererBusy, setRendererBusy] = useState(false);
  const [updateBusy, setUpdateBusy] = useState(false);
  const [updateStatus, setUpdateStatus] = useState("Check manually for updates.");
  const [installedVersion,setInstalledVersion] = useState<string|null>(null);
  const [installedVersionError,setInstalledVersionError] = useState("");
  const [updateFallback, setUpdateFallback] = useState<string|null>(null);
  const requestGithubInstall = (release:GithubRelease) => {
    const installer=deckyInstaller();
    if (!installer || typeof installer.callable !== "function") {
      setUpdateFallback(release.asset_url);
      setUpdateStatus("Decky install API unavailable. Use Decky Settings → Developer → Install Plugin from URL.");
      return;
    }
    try {
      // Decky opens its OWN confirmation modal; the plugin may unload while
      // the installer runs, so do not wait to declare the install successful.
      const launch=installer.callable("utilities/install_plugin");
      if (typeof launch !== "function") throw new Error("Installation API is not supported.");
      setUpdateStatus("Update request sent to Decky. Confirm installation in its dialog.");
      void launch(release.asset_url, "Claw Metrics", release.version,
                  release.sha256, 2 /* UPDATE */).catch((error:unknown)=>{
        setUpdateFallback(release.asset_url);
        setUpdateStatus("Installation request failed: "+String(error));
      });
    } catch(error) {
      setUpdateFallback(release.asset_url);
      setUpdateStatus("Installation API unavailable: "+String(error));
    }
  };
  const confirmGithubInstall = (release:GithubRelease) => {
    const dialog=showModal(<ConfirmModal strTitle={"Claw Metrics "+release.tag}
      strOKButtonText="Install" onCancel={()=>dialog.Close()}
      onOK={()=>{ dialog.Close(); requestGithubInstall(release); }}>
      <div style={{padding:"8px 4px",minWidth:0,maxWidth:"100%"}}>
        <p style={{fontSize:13,margin:"0 0 8px"}}>
          A new version is available. Review the changes before installing.
        </p>
        <div style={{fontSize:12,opacity:.8,marginBottom:8}}>Changes in {release.tag}:</div>
        <div style={{fontSize:12,lineHeight:1.45,whiteSpace:"pre-wrap",
          overflowWrap:"anywhere",maxHeight:230,overflowY:"auto",
          background:"#10283a",padding:10,borderRadius:8}}>{release.notes}</div>
        <p style={{fontSize:12,opacity:.83,marginBottom:0}}>
          Decky will download the ZIP, verify its SHA-256 checksum, and reload
          the plugin. If the new interface does not appear, reload Claw Metrics
          in Decky Settings → Plugins or restart Decky Loader. Restart a running
          game to load the updated Vulkan renderer; no device reboot is needed.
        </p>
      </div>
    </ConfirmModal>);
  };
  const checkGithubRelease = async () => {
    if (updateBusy) return;
    setUpdateBusy(true);
    setUpdateFallback(null);
    setUpdateStatus("Checking GitHub releases…");
    try {
      let result:GithubUpdateInfo|null=null;
      let deckyError="";
      // Prefer the same HTTPS client/certificate handling Decky uses for
      // plugin installation. This avoids SteamOS-specific urllib failures.
      const loader=deckyInstaller();
      if (typeof loader?.callable === "function") {
        try {
          const request=loader.callable("utilities/http_request");
          const http=await withTimeout(request("GET",GITHUB_RELEASES_API,{
            headers:{"Accept":"application/vnd.github+json",
              "X-GitHub-Api-Version":"2022-11-28"},
          },8)) as DeckyHttpResponse;
          if (!http || typeof http.status !== "number" || typeof http.body !== "string") {
            throw new Error("Decky returned an invalid HTTPS response.");
          }
          if (http.status!==200) {
            throw new Error("GitHub API: HTTP "+http.status+
              (http.status===403||http.status===429?" (rate limit)":""));
          }
          // The Python backend validates each asset URL/digest. The frontend
          // must not install arbitrary URLs returned by a remote service.
          result=await withTimeout(validateGithubReleases(http.body));
          if (!result.ok) throw new Error(result.error||"Invalid GitHub release data.");
        } catch(error) {
          deckyError=String(error);
          result=null;
        }
      } else {
        deckyError="Decky network API unavailable.";
      }
      if (!result) {
        // Compatibility fallback for older Decky builds. All exceptions are
        // returned as data, so the UI never displays 'Python Exception'.
        const fallback=await withTimeout(checkUpdates());
        if (!fallback.ok) {
          const details=[deckyError,"Python HTTPS: "+(fallback.error||"unknown error")]
            .filter(Boolean).join(" · ");
          throw new Error(details);
        }
        result=fallback;
      }
      if (!result.available || !result.latest) {
        setUpdateStatus("Installed version "+(result.current||"unknown")+
          " is up to date. No newer test release.");
      } else {
        setUpdateStatus("New version available: "+result.latest.tag+
          " (installed: "+result.current+").");
        confirmGithubInstall(result.latest);
      }
    } catch(error) {
      setUpdateStatus("Update check failed: "+String(error).slice(0,420));
    } finally {
      setUpdateBusy(false);
    }
  };
  const verifyTdp = async () => {
    try { const result=await withTimeout(getTdpStatus());setTdpStatus(result.description); }
    catch(error) {setTdpStatus("TDP check failed: "+String(error));}
  };
  const verifyRenderer = async () => {
    setRendererBusy(true);
    setRendererStatus("Checking running game processes…");
    try {
      const result = await withTimeout(getRendererStatus());
      setRendererStatus(
        (result.native_loaded ? "ACTIVE" : "NIJE ACTIVE") +
        " · native: " + result.native_processes +
        " · stock MangoHud: " + result.stock_processes +
        " · layer requests: " + result.layer_requests +
        " · test config: " + result.config_requests +
        " · Vulkan path: " + result.path_requests +
        " · process access: " + result.environments_read + "/" + result.processes_seen +
        " · manifest: " + (result.manifest_in_user_location ? "DA" : "NE") +
        ". " + result.reason
      );
    } catch (error) {
      setRendererStatus("Check failed: " + String(error));
    } finally {
      setRendererBusy(false);
    }
  };
  const [expanded, setExpanded] = useState<Group | null>(() => lastExpandedMetric);
  const [openSection, setOpenSection] = useState<SectionKey | null>(() => lastOpenSection);
  const [styleCategory, setStyleCategory] = useState<StyleCategory | null>(() => lastStyleCategory);
  const toggleSection = (id: SectionKey) => {
    const next = lastOpenSection === id ? null : id;
    lastOpenSection = next;
    setOpenSection(next);
  };
  const expandMetric = (key: Group | null) => {
    lastExpandedMetric = key;
    setExpanded(key);
  };
  const [ready, setReady] = useState(false);

  const current = useRef<Settings>(defaults);
  const queue = useRef<Promise<void>>(Promise.resolve());
  const revision = useRef(0);

  const refresh = async ():Promise<boolean> => {
    const attempt=++connectionAttempt.current;
    const started=revision.current;
    setConnecting(true);
    setStatus("Connecting to backend…");
    try {
      // Core settings must not depend on optional renderer diagnostics.
      // Previous Promise.all([load(),getInfo()]) disabled EVERY control if
      // getInfo failed or timed out, even when settings were fully available.
      const saved=await withTimeout(load());
      if(attempt!==connectionAttempt.current)return false;
      if(!saved || !Array.isArray(saved.order) || !saved.metrics || !saved.colors)
        throw new Error("The backend returned incomplete settings.");
      if(revision.current===started){
        current.current=saved;
        setSettings(saved);
      }
      setReady(true);
      setConnectionError("");
      setStatus("Settings connected.");
      try {
        const details=await withTimeout(getInfo());
        if(attempt!==connectionAttempt.current)return true;
        setInfo(details);
        setStatus(details.config_readable
          ? "Backend connected · game profile ready."
          : "Settings connected; the game configuration is not readable.");
      } catch(error){
        // Never lock working Metrics/Layout/Colors for an optional failure.
        if(attempt===connectionAttempt.current){
          setInfo(null);
          setStatus("Settings connected; renderer information unavailable: "+String(error));
        }
      }
      return true;
    } catch(error){
      if(attempt===connectionAttempt.current){
        setReady(false);
        setInfo(null);
        const message="Connection error: "+String(error);
        setConnectionError(message);
        setStatus(message);
      }
      return false;
    } finally {
      if(attempt===connectionAttempt.current)setConnecting(false);
    }
  };
  useEffect(()=>{
    let cancelled=false;
    void (async()=>{
      if(await refresh() || cancelled)return;
      // Decky may still be restarting its Python process after an update.
      await new Promise<void>(resolve=>setTimeout(resolve,1800));
      if(!cancelled)await refresh();
    })();
    return ()=>{cancelled=true;};
  },[]);

  useEffect(()=>{
    if(!ready)return;
    let cancelled=false;
    // Read the version from the installed ZIP's package.json through Python,
    // not from a hard-coded UI string or the newest GitHub release.
    void withTimeout(getInstalledVersion()).then(result=>{
      if(cancelled)return;
      if(typeof result?.version !== "string" || !result.version.trim())
        throw new Error("Invalid installed package version.");
      setInstalledVersion(result.version);
      setInstalledVersionError("");
    }).catch(error=>{
      if(cancelled)return;
      setInstalledVersion(null);
      setInstalledVersionError("Unable to read installed version: "+String(error));
    });
    return ()=>{cancelled=true;};
  },[ready]);

  const update = (patch: Partial<Settings>) => {
    const next = { ...current.current, ...patch };
    current.current = next;
    const id = ++revision.current;
    setSettings(next);
    setStatus("Saving…");
    queue.current = queue.current.then(async () => {
      try {
        const result = await withTimeout(save(next));
        if (!result.ok) throw new Error("Backend did not confirm the save.");
        if (id === revision.current) setStatus("Saved. Restart the game to apply changes.");
      } catch (error) {
        if (id === revision.current) setStatus("Save failed: " + String(error));
      }
    });
  };

  // Copy synchronously from a button click: SteamOS Game Mode often does
  // not expose the modern Clipboard API to Decky panels.
  const copyLaunchCommand = async (experimental: boolean | "short" = false) => {
    const command = experimental === "short" ? info?.short_launch_option
      : experimental ? info?.experimental_launch_option : info?.launch_option;
    if (!command) {
      setCopyStatus("Launch command unavailable.");
      return;
    }

    let copied = false;
    const input = document.createElement("textarea");
    input.value = command;
    input.readOnly = true;
    input.style.position = "fixed";
    input.style.left = "-9999px";
    input.style.top = "-9999px";
    document.body.appendChild(input);
    try {
      input.focus();
      input.select();
      copied = document.execCommand("copy");
    } catch (error) {
      console.warn("Claw Metrics: execCommand copy failed", error);
    } finally {
      input.remove();
    }

    if (!copied && navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(command);
        copied = true;
      } catch (error) {
        console.warn("Claw Metrics: Clipboard API copy failed", error);
      }
    }
    setCopyStatus(
      copied
        ? "Copied! Paste into Steam Launch Options."
        : "Copy failed. Check clipboard permissions in SteamOS Game Mode."
    );
  };

  const renameMetric = (key:Group) => {
    const restoreFocus=()=>requestAnimationFrame(()=>{(document.querySelector('[data-metric="'+key+'"]') as HTMLElement)?.focus()});
    const dialog=showModal(<RenameMetricModal name={metricName(current.current,key)} original={groups[key].label}
      onCancel={()=>{dialog.Close();restoreFocus()}} onConfirm={(value:string)=>{
        const labels={...current.current.custom_labels};
        if(!value || value===groups[key].label) delete labels[key];else labels[key]=value;
        update({custom_labels:labels}); dialog.Close();restoreFocus();
      }}/>);
  };
  const named=(key:string)=>key==="values"?"Values":metricName(settings,key);
  const tokenTitle=(token:MetricToken)=>{
    const group=token.key==="battery.power"?"draw":token.key.split(".")[0];
    const key=group==="time"?"time":group;
    if(token.key.endsWith(".label")||token.key.endsWith(".value")||token.key==="battery.power")return named(key);
    return (styleCategory==="values"?named(key)+" · ":"")+relatedLabel(settings,token.label).replace(/\s+(label|value)\b/gi,"");
  };
  const styleTitle=(slot:string)=>settings.style_names?.[slot] || ("Style "+slot);
  const renameStyle=(slot:string)=>{
    const dialog=showModal(<RenameStyleModal value={settings.style_names?.[slot]??""}
      slot={slot} onCancel={()=>dialog.Close()} onConfirm={value=>{
        const names={...current.current.style_names};
        if(value) names[slot]=value; else delete names[slot];
        update({style_names:names});dialog.Close();
      }}/>);
  };
  const confirmAction=(title:string,description:string,action:()=>void)=>{
    const dialog=showModal(<ConfirmModal strTitle={title} strOKButtonText="Confirm"
      onCancel={()=>dialog.Close()} onOK={()=>{dialog.Close();action();}}>
      <div style={{padding:"8px 4px",fontSize:13,lineHeight:1.5}}>{description}</div>
    </ConfirmModal>);
  };
  const loadedPreset=settings.active_style?settings.style_presets?.[settings.active_style]:null;
  const presetDirty=loadedPreset?styleModified({...loadedPreset,colors:independentColors(loadedPreset.colors,defaultColors)},settings):false;
  const related=(label:string)=>relatedLabel(settings,label);
  const chooseStyleCategory = (id: StyleCategory) => {
    // Match Metrics: pressing the already expanded card closes its editor.
    const next = lastStyleCategory === id ? null : id;
    lastStyleCategory = next;
    setStyleCategory(next);
  };
  const cycleTokenWeight = (key: TokenKey) => {
    const old: WeightSelection = current.current.token_weights?.[key] ?? "inherit";
    const next = weightOptions[(weightOptions.indexOf(old) + 1) % weightOptions.length];
    const updated = {...current.current.token_weights};
    if (next === "inherit") delete updated[key];
    else updated[key] = next;
    update({token_weights: updated});
  };
  const openTokenColorPicker = (token: MetricToken) => {
    const hex = current.current.token_colors?.[token.key] ??
      current.current.colors[token.defaultColor] ?? defaultColors[token.defaultColor];
    const dialog = showModal(<OpaqueColorPicker
      title={tokenTitle(token)} hex={hex} closeModal={() => dialog.Close()}
      onConfirm={(value: string) => update({
        token_colors: {...current.current.token_colors, [token.key]: value}
      })}
    />);
  };
  const resetTokenColor = (key: TokenKey) => {
    const next = {...current.current.token_colors};
    delete next[key];
    update({token_colors: next});
  };
  const savePreset = (slot: string) => {
    const d = current.current;
    const preset: SavedStyle = {
      version:3, ...styleLayoutFrom(d),
      // Save BOTH the main cards and individual sensor switches per style.
      ...styleMetricSnapshotFrom(d),
      colors: {...d.colors}, font_weight: d.font_weight, fps_bold: d.fps_bold,
      token_weights: {...d.token_weights}, token_colors: {...d.token_colors},
    };
    update({style_presets: {...d.style_presets, [slot]: preset},active_style:slot});
  };
  const loadPreset = (slot: string) => {
    const preset = current.current.style_presets?.[slot];
    if (!preset) return;
    // Old appearance-only styles have no group/sensor snapshot. Keep the
    // current metric selection until the user saves those slots again.
    update({...styleLayoutFrom(preset),...styleMetricUpdatesFrom(preset,current.current),
      active_style:slot,colors: independentColors(preset.colors,defaultColors),
      font_weight:preset.font_weight,fps_bold:preset.fps_bold,
      token_weights:{...preset.token_weights},token_colors:{...preset.token_colors}});
  };

  const paletteLabel = (key:ColorKey,label:string) => {
    const category:Partial<Record<ColorKey,Group>>={fps_label:"fps",cpu:"cpu",gpu:"gpu",ram:"ram",vram:"vram",battery:"battery",graph:"frametime",time:"time",tdp:"tdp",draw:"draw"};
    return category[key]?named(category[key]!):related(label);
  };
  const openColorPicker = (key: ColorKey, label: string) => {
    const dialog = showModal(<OpaqueColorPicker
      title={paletteLabel(key,label)} hex={current.current.colors[key] ?? defaultColors[key]}
      closeModal={() => dialog.Close()}
      onConfirm={(hex: string) => {
        const token_colors={...current.current.token_colors};
        const changed=new Set<ColorKey>(key==="fps_label"?["fps_label","fps_value"]:[key]);
        // Global color changes must not silently erase individually set colors.
        update({colors:{...current.current.colors,[key]:hex,...(key==="fps_label"?{fps_value:hex}:{})}});
      }}
    />);
  };

  const toggle = (key: "enabled" | "sans", label: string) => (
    <PanelSectionRow><ToggleField label={label} checked={settings[key]} disabled={!ready}
      onChange={(value: boolean) => update({[key]: value})} /></PanelSectionRow>
  );
  const move = (key: Group, direction: number) => {
    const next = [...current.current.order];
    const visible = next.filter(id => current.current[id]);
    const at = visible.indexOf(key);
    const other = visible[at + direction];
    if (!other) return;
    const a = next.indexOf(key), b = next.indexOf(other);
    [next[a], next[b]] = [next[b], next[a]];
    update({order: next});
  };
  const metric = (key: string, value: boolean) => update({metrics: {...current.current.metrics, [key]: value}});
  const visible = settings.order.filter(key => settings[key]);
  const hidden = settings.order.filter(key => !settings[key]);
  const smallButton = {minWidth: 40, width: 40, minHeight:40, padding: "7px 0", margin: 0, fontSize: 17, borderRadius: 6};

  // One central controller owns settings, Decky RPC and navigation state.
  // Cards only render this model; they never mount separate backend sessions.
  return { settings, setSettings, info, setInfo, status, setStatus, copyStatus, setCopyStatus, connecting, setConnecting, connectionError, setConnectionError, connectionAttempt, layoutPanel, setLayoutPanel, toggleLayoutPanel, advancedPanel, setAdvancedPanel, toggleAdvancedPanel, showTechnical, setShowTechnical, rendererStatus, setRendererStatus, tdpStatus, setTdpStatus, rendererBusy, setRendererBusy, updateBusy, setUpdateBusy, updateStatus, setUpdateStatus, updateFallback, setUpdateFallback, requestGithubInstall, confirmGithubInstall, checkGithubRelease, verifyTdp, verifyRenderer, installedVersion, installedVersionError, expanded, setExpanded, openSection, setOpenSection, styleCategory, setStyleCategory, toggleSection, expandMetric, ready, setReady, current, queue, revision, refresh, update, copyLaunchCommand, renameMetric, named, tokenTitle, styleTitle, renameStyle, confirmAction, loadedPreset, presetDirty, related, chooseStyleCategory, cycleTokenWeight, openTokenColorPicker, resetTokenColor, savePreset, loadPreset, paletteLabel, openColorPicker, toggle, move, metric, visible, hidden, smallButton };
}

export type ClawController = ReturnType<typeof useClawController>;
