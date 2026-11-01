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

type Group = "fps" | "frametime" | "cpu" | "gpu" | "ram" | "vram" | "battery" | "tdp" | "draw" | "time";
type FontWeight = "light" | "regular" | "semibold" | "bold";
type GraphStyle = "area" | "line" | "bars" | "dual";
type HudPosition = "top-left" | "top-center" | "top-right" | "bottom-left" | "bottom-center" | "bottom-right";
const hudPositions: {id:HudPosition; label:string; icon:string; column:number; row:number}[] = [
  {id:"top-left",label:"Top left",icon:"↖",column:1,row:1},
  {id:"top-center",label:"Top center",icon:"↑",column:2,row:1},
  {id:"top-right",label:"Top right",icon:"↗",column:3,row:1},
  {id:"bottom-left",label:"Bottom left",icon:"↙",column:1,row:2},
  {id:"bottom-center",label:"Bottom center",icon:"↓",column:2,row:2},
  {id:"bottom-right",label:"Bottom right",icon:"↘",column:3,row:2},
];

// Actual silhouettes of the four native frametime render modes.
// They are the primary symbols in the gamepad grid; no letter shortcuts.
function GraphStyleIcon({kind}:{kind:GraphStyle}) {
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
const graphStyleChoices: {id:GraphStyle;label:string}[] = [
  {id:"area",label:"Filled area"},
  {id:"line",label:"Line"},
  {id:"bars",label:"Histogram"},
  {id:"dual",label:"Line + fill"},
];

/** Match the real SteamOS navigation tree to the visible grid.
 * The parent handles up/down, each row handles left/right. */
function GamepadGrid<T>({items, columns, className, renderItem}:{
  items:readonly T[]; columns:2|3; className:string;
  renderItem:(item:T,index:number)=>ReactNode;
}) {
  const rows:T[][]=[];
  for(let at=0;at<items.length;at+=columns) rows.push(items.slice(at,at+columns));
  return <Focusable flow-children="column" className={className}>
    {rows.map((row,rowIndex)=>
      <Focusable key={rowIndex} flow-children="row"
        className={"claw-grid-row claw-grid-cols-"+columns}>
        {row.map((item,colIndex)=>renderItem(item,rowIndex*columns+colIndex))}
      </Focusable>)}
  </Focusable>;
}
type WeightSelection = "inherit" | FontWeight;
type StyleCategory = "global" | "fps" | "cpu" | "gpu" | "ram" | "vram" | "battery" | "time" | "tdp" | "draw" | "values";
type TokenKey = "fps.label" | "fps.value" | "fps.ms" | "cpu.label" | "cpu.load" | "cpu.temp" | "cpu.clock" | "cpu.power" | "gpu.label" | "gpu.load" | "gpu.temp" | "gpu.clock" | "gpu.power" | "gpu.junction" | "gpu.fan" | "gpu.voltage" | "ram.label" | "ram.value" | "vram.label" | "vram.value" | "vram.temp" | "vram.clock" | "battery.label" | "battery.value" | "battery.time" | "battery.power" | "time.value" | "tdp.value";
type MetricToken = {key: TokenKey; label: string; defaultColor: ColorKey};
const tokenGroups: Record<Exclude<StyleCategory, "global">, MetricToken[]> = {
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
const weightOptions: WeightSelection[] = ["inherit", "light", "regular", "semibold", "bold"];
const weightLabel: Record<WeightSelection, string> = {
  inherit: "Global", light: "Light", regular: "Regular", semibold: "SemiBold", bold: "Bold",
};
const styleTabs: [StyleCategory,string][] = [
  ["global","Global"],["fps","FPS"],["cpu","CPU"],["gpu","GPU"],
  ["ram","RAM"],["vram","VRAM"],["battery","Battery"],["time","Clock"],["tdp","TDP"],["draw","DRAW"],["values","Values"],
];
type SavedStyle = Partial<Record<"fontsize"|"opacity"|"rounding"|"padding_x"|"padding_y"|"offset_x"|"offset_y"|"element_gap"|"table_gap"|"inner_gap"|"graph_width",number>> & {
  sans?:boolean; inline_metrics?:boolean; graph_style?:GraphStyle; version?:number;
  groups?: Partial<Record<Group, boolean>>; metrics?: Record<string, boolean>;
  colors: ColorSettings; font_weight: FontWeight; fps_bold: boolean;
  token_weights: Partial<Record<TokenKey, FontWeight>>;
  token_colors: Partial<Record<TokenKey, string>>;
};

type ColorKey = "text" | "separator" | "fps_label" | "fps_value" | "cpu" | "gpu" | "ram" | "vram" | "battery" | "graph" | "time" | "tdp" | "draw";
type ColorSettings = Record<ColorKey, string>;
const defaultColors: ColorSettings = {
  text: "F0F2F5", separator: "777C87", fps_label: "30E5A0", fps_value: "30E5A0",
  cpu: "37C9EF", gpu: "8BDA62", ram: "B077DF", vram: "D76AB8",
  battery: "30E5A0", graph: "30E5A0", time:"F0F2F5", draw:"F0F2F5", tdp:"FFBD69",
};
const colorRows: [ColorKey, string][] = [
  ["text", "Values"], ["time", "Clock"], ["tdp", "TDP"], ["draw", "DRAW"], ["separator", "Group separators"],
  ["fps_label", "FPS"],
  ["cpu", "CPU label"], ["gpu", "GPU label"], ["ram", "RAM label"],
  ["vram", "VRAM label"], ["battery", "Battery label"], ["graph", "Frametime graph"],
];

// Decky picker uses HSL sliders; MangoHud accepts 6-digit RGB without '#'.
function rgbToHsl(hex: string): [number, number, number] {
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
function hslToHex(hue: number, saturation: number, lightness: number): string {
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

type OpaqueColorPickerProps = {
  title: string; hex: string; closeModal: () => void; onConfirm: (hex: string) => void;
};
function OpaqueColorPicker({title, hex, closeModal, onConfirm}: OpaqueColorPickerProps) {
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
const groupIcons: Record<string, ReactNode> = {global:<FaPalette/>,fps:<FaTachometerAlt/>,cpu:<FaMicrochip/>,gpu:<FaDesktop/>,ram:<FaMemory/>,vram:<FaMemory/>,battery:<FaBatteryThreeQuarters/>,time:<FaClock/>,tdp:<FaBolt/>,draw:<FaBolt/>,values:<FaHashtag/>};
function RenameStyleModal({value,slot,onConfirm,onCancel}:{
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
function RenameMetricModal({name,original,onConfirm,onCancel}:any){
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

type Settings = Record<Group, boolean> & {
  active_style: string|null; style_names: Record<string,string>;
  custom_labels: Record<string,string>;
  enabled: boolean; fontsize: number; fps_scale: number; center_horizontal: boolean; hud_position: HudPosition; opacity: number; power: boolean; tdp: boolean;
  sans: boolean; rounding: number; offset_x: number; offset_y: number; padding_y: number;
  padding_x: number; element_gap: number; table_gap: number; graph_width: number; graph_style: GraphStyle;
  inner_gap: number; inline_metrics: boolean; fps_bold: boolean; font_weight: FontWeight; order: Group[];
  metrics: Record<string, boolean>;
  colors: ColorSettings;
  token_weights: Partial<Record<TokenKey, FontWeight>>;
  token_colors: Partial<Record<TokenKey, string>>;
  style_presets: Record<string, SavedStyle>;
};
const order: Group[] = ["fps", "frametime", "cpu", "gpu", "ram", "vram", "battery", "tdp", "draw", "time"];
const groups: Record<Group, {label: string; color: string; metrics: [string, string][]; always?: string; note?: string}> = {
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

type TdpStatus = { readable:boolean; watts:number|null; source:string; description:string };
type Info = {
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

const defaults: Settings = {
  active_style:null, style_names:{}, custom_labels: {},
  enabled: true, fontsize: 18, fps_scale: 100, center_horizontal: false, hud_position: "top-left", opacity: 80, fps: true, frametime: true,
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
const load = callable<[], Settings>("get_settings");
const save = callable<[Settings], { ok: boolean; config_path: string }>("save_settings");
const getInfo = callable<[], Info>("get_info");
const getTdpStatus = callable<[], TdpStatus>("get_tdp_status");
const setTdpGameContext = callable<[string | null], {ok: boolean}>("set_tdp_game_context");

function readActivePdcProfileKey(): string | null | undefined {
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

type RendererStatus = {
  native_loaded: boolean; native_processes: number; stock_processes: number;
  layer_requests: number; config_requests: number; path_requests: number;
  processes_seen: number; environments_read: number;
  manifest_in_user_location: boolean; reason: string;
};
const getRendererStatus = callable<[], RendererStatus>("get_renderer_status");

type GithubRelease = {
  version:string;tag:string;notes:string;
  asset_url:string;sha256:string;release_url:string;
};
type GithubUpdateInfo = {
  ok:boolean; current?:string; available:boolean; latest:GithubRelease|null;
  error?:string; source?:string;
};
type DeckyHttpResponse = {status:number;body:string};
const GITHUB_RELEASES_API = "https://api.github.com/repos/ikorljan-droid/claw-metrics/releases?per_page=30";
const checkUpdates = callable<[], GithubUpdateInfo>("check_updates");
const validateGithubReleases = callable<[string],GithubUpdateInfo>("validate_github_releases");

// Decky Loader handles ZIP download, SHA-256 verification, unloading and
// reinstalling its plugins. This is a guarded loader-internal API, not part
// of @decky/api. Do not copy/unzip a plugin from its own privileged backend.
type LoaderInstaller = {
  callable?: (route:string) => (...args:unknown[]) => Promise<unknown>;
};
function deckyInstaller(): LoaderInstaller|null {
  return (window as Window & {DeckyBackend?:LoaderInstaller}).DeckyBackend ?? null;
}

function withTimeout<T>(request: Promise<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("Backend ne odgovara (10 s). Ponovno pokreni Decky Loader.")), 10000);
    request.then(resolve, reject).finally(() => clearTimeout(timer));
  });
}

type SectionKey = "overlay" | "layout" | "metrics" | "colors" | "activation" | "advanced";
type AccordionCardProps = {
  id: SectionKey;
  title: string;
  subtitle: string;
  icon: ReactNode;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
};

function AccordionCard({id, title, subtitle, icon, open, onToggle, children}: AccordionCardProps) {
  const [focused, setFocused] = useState(false);
  const active = open || focused;
  return (
    <div data-section={id} data-selected={open ? "true" : "false"}
      data-focused={focused ? "true" : "false"} style={{
      background: active ? "#0d2945" : "#111e30",
      width: "100%", maxWidth: "100%", minWidth: 0, boxSizing: "border-box",
      border: active ? "1px solid #2c709d" : "1px solid #395579",
      borderLeft: active ? "4px solid #08d3fa" : "4px solid #8b65e7",
      borderRadius: 12,
      overflow: "hidden",
      marginBottom: 10,
      boxShadow: active ? "0 0 12px rgba(0,153,237,0.13)" : "none",
    }}>
      {/* Steam and Decky retain normal button navigation; highlight is in the background. */}
      <div className="claw-accordion-header"
        onFocusCapture={()=>setFocused(true)} onBlurCapture={()=>setFocused(false)}
        style={{position:"relative",width:"100%",minWidth:0,
        maxWidth:"100%",boxSizing:"border-box"}}>
        <DialogButton onClick={onToggle} aria-pressed={open} style={{
          width: "100%", minWidth: 0, boxSizing: "border-box",
          display: "flex", alignItems: "center",
          textAlign: "left", margin: 0, padding: "12px 10px",
          background: active ? "#073858" : "#14243b",
          border: "none", borderRadius: 0, minHeight: 66, whiteSpace: "normal",
          outline: "none", boxShadow: "none",
        }}>
          <span style={{display: "flex", alignItems: "center", gap: 10, width: "100%", minWidth: 0}}>
            <span className="claw-accordion-icon"
              style={{display: "flex", alignItems: "center", justifyContent: "center",
              background: active ? "#075b83" : "#203551", borderRadius: 8, minWidth: 36, height: 36,
              fontSize: 20, color: active ? "#42e0ff" : "#acd7fe"}}>{icon}</span>
            <span style={{display: "flex", flex: 1, minWidth: 0, flexDirection: "column", gap: 3}}>
              <span style={{fontWeight: 700, fontSize: 16, color: "#f1f7ff"}}>{title}</span>
              <span style={{fontWeight: 400, fontSize: 11, lineHeight: 1.35,
                color: "#a9c7e8", overflowWrap: "anywhere"}}>{subtitle}</span>
            </span>
            <span style={{display: "flex", color: "#9edbff", fontSize: 16, flexShrink: 0}}>
              {open ? <FaChevronDown /> : <FaChevronRight />}
            </span>
          </span>
        </DialogButton>
      </div>
      {open && <div style={{padding: "10px 8px 12px", borderTop: "1px solid #235b81"}}>
        {children}
      </div>}
    </div>
  );
}

type LayoutPanel = "position" | "size" | "spacing" | "frametime";
type AdvancedPanel = "updates" | "diagnostics" | "backup";
function ControlGroup({title,summary,open,onToggle,children}:{
 title:string;summary:string;open:boolean;onToggle:()=>void;children:ReactNode;
}) {
 return <div className="claw-control-group" style={{margin:"7px 0",minWidth:0,
   border:"1px solid #355873",borderRadius:9,background:"#14253a",overflow:"hidden"}}>
   <DialogButton aria-expanded={open} onClick={onToggle}
     style={{display:"block",width:"100%",margin:0,minWidth:0,minHeight:57,
       padding:"10px 9px",background:open?"#16466a":"#172c43",
       border:"none",borderRadius:0,textAlign:"left"}}>
     <span style={{display:"flex",gap:9,alignItems:"center",justifyContent:"space-between"}}>
       <span style={{minWidth:0,display:"flex",flexDirection:"column",gap:3}}>
         <strong style={{fontSize:13,color:"#f3f8ff"}}>{title}</strong>
         <span style={{fontSize:11.5,color:"#afc5d7",lineHeight:1.3}}>{summary}</span>
       </span>{open?<FaChevronDown/>:<FaChevronRight/>}
     </span>
   </DialogButton>
   {open && <div style={{padding:"10px 7px 12px",borderTop:"1px solid #365b79"}}>
     {children}
   </div>}
 </div>;
}
// Decky can remount Content after backend saves. Keep navigation state
// outside the React instance, so saving never jumps back to Metrics.
let lastOpenSection: SectionKey | null = "metrics";
let lastExpandedMetric: Group | null = null;
let lastStyleCategory = "global";

function Content() {
  const [settings, setSettings] = useState<Settings>(defaults);
  const [info, setInfo] = useState<Info | null>(null);
  const [status, setStatus] = useState("Loading…");
  const [copyStatus, setCopyStatus] = useState("");
  const [layoutPanel,setLayoutPanel]=useState<LayoutPanel>("position");
  const [advancedPanel,setAdvancedPanel]=useState<AdvancedPanel>("updates");
  const [showTechnical,setShowTechnical] = useState(false);
  const [rendererStatus, setRendererStatus] = useState("Not checked. Start a game to verify.");
  const [tdpStatus, setTdpStatus] = useState("TDP has not been checked.");
  const [rendererBusy, setRendererBusy] = useState(false);
  const [updateBusy, setUpdateBusy] = useState(false);
  const [updateStatus, setUpdateStatus] = useState("Check manually for updates.");
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
        setUpdateStatus("Installed version "+(result.current||"nepoznata")+
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
  const [styleCategory, setStyleCategory] = useState<StyleCategory>(() => lastStyleCategory as StyleCategory);
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

  const refresh = async () => {
    setStatus("Connecting to backend…");
    const started = revision.current;
    try {
      const [saved, details] = await withTimeout(Promise.all([load(), getInfo()]));
      if (revision.current === started) {
        current.current = saved;
        setSettings(saved);
      }
      setInfo(details);
      setReady(true);
      setStatus(details.config_readable
        ? "Backend connected · game profile ready."
        : "Backend connected, but the profile is unreadable. Restart Decky Loader.");
    } catch (error) {
      setStatus("Connection error: " + String(error));
    }
  };
  useEffect(() => { void refresh(); }, []);

  const update = (patch: Partial<Settings>) => {
    const next = { ...current.current, ...patch };
    current.current = next;
    const id = ++revision.current;
    setSettings(next);
    setStatus("Saving…");
    queue.current = queue.current.then(async () => {
      try {
        const result = await withTimeout(save(next));
        if (!result.ok) throw new Error("Backend nije potvrdio spremanje.");
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
    lastStyleCategory = id;
    setStyleCategory(id);
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
        .claw-style-tiles .style-group-icon {
          display: inline-flex; align-items: center; justify-content: center;
          margin: 0 !important; color: #bceaff; font-size: 13px; line-height: 1;
        }
        .claw-metric-row { margin-bottom: 7px; width: 100%; min-width: 0; }
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
      <PanelSection title="Claw Metrics · v0.2.4-test.43">
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
      <div style={{padding: "0 7px 14px"}}>
        <AccordionCard id="overlay" title="Overlay" subtitle="Display and connection status"
          icon={<FaDesktop />} open={openSection === "overlay"} onToggle={() => toggleSection("overlay")}>
          {toggle("enabled", "Enable overlay")}
          <PanelSectionRow><Field label="Connection & save status" description={status} /></PanelSectionRow>
          <PanelSectionRow><Field label="In-game renderer"
            description={rendererStatus} /></PanelSectionRow>
          <PanelSectionRow><ButtonItem layout="below" disabled={!ready || rendererBusy}
            onClick={()=>{void verifyRenderer();}}>Check running game</ButtonItem></PanelSectionRow>
          <PanelSectionRow><Field label="Game configuration" description={info?.config_readable
            ? "Configuration is ready for games." : "Configuration is unavailable or still loading."} /></PanelSectionRow>
        </AccordionCard>
        <AccordionCard id="layout" title="Layout" subtitle="Position, scale and spacing"
          icon={<FaThLarge />} open={openSection === "layout"} onToggle={() => toggleSection("layout")}>
          <ControlGroup title="Position" summary="6 anchors · X / Y offsets"
            open={layoutPanel==="position"} onToggle={()=>setLayoutPanel("position")}>
        <PanelSectionRow><Field label="HUD position"
          description="Choose one of six screen-edge anchors."/></PanelSectionRow>
        {/* Steam's navigation tree must match the visual 3×2 grid: column
            movement between two horizontal rows, row movement within each.
            A single flow-children="row" prevents D-pad up/down navigation. */}
        <Focusable flow-children="column" style={{display:"flex",flexDirection:"column",
          gap:5,padding:"0 4px 12px",maxWidth:"100%",boxSizing:"border-box"}}>
          {(["top","bottom"] as const).map((edge)=>
            <Focusable key={edge} flow-children="row" style={{display:"grid",
              gridTemplateColumns:"repeat(3,minmax(0,1fr))",gap:5,
              width:"100%",minWidth:0,maxWidth:"100%",boxSizing:"border-box"}}>
              {hudPositions.filter((anchor)=>anchor.id.startsWith(edge)).map((anchor)=>{
                const selected=settings.hud_position===anchor.id;
                return <DialogButton key={anchor.id} className="claw-hud-anchor" data-anchor-position={anchor.id}
                  aria-label={anchor.label} aria-pressed={selected}
                  disabled={!ready || (anchor.id.endsWith("center") && !info?.layout_spacing_supported)}
                  onClick={()=>update({hud_position:anchor.id,center_horizontal:anchor.id.endsWith("center")})}
                  style={{margin:0,padding:"4px 2px",minWidth:0,minHeight:54,
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
        <PanelSectionRow><SliderField label="X offset (px)"
          value={settings.offset_x} min={-1920} max={1920} step={1} showValue
          disabled={!ready || settings.hud_position.endsWith("center")}
          onChange={(value:number)=>update({offset_x:value})}/></PanelSectionRow>
        <PanelSectionRow><SliderField label="Y offset (px)" value={settings.offset_y}
           min={-1200} max={1200} step={1} showValue disabled={!ready}
           onChange={value=>update({offset_y:value})}/></PanelSectionRow>
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below"
           onClick={()=>update({offset_x:0,offset_y:0})}>Reset X / Y offsets</ButtonItem></PanelSectionRow>

          </ControlGroup>
          <ControlGroup title="Size & appearance" summary="Text · FPS scale · background"
            open={layoutPanel==="size"} onToggle={()=>setLayoutPanel("size")}>
        {([ ["fontsize", "Text size", 12, 28, 1], ["opacity", "Background opacity (%)", 0, 100, 5],
          ["rounding", "Corner radius", 0, 20, 1] ] as const).map(([key, label, min, max, step]) =>
          <PanelSectionRow key={key}><SliderField label={label} value={settings[key]} min={min} max={max} step={step} showValue disabled={!ready || (key==="padding_x" && !info?.layout_spacing_supported)}
            onChange={(value: number) => update({[key]: value})} /></PanelSectionRow>)}

        <PanelSectionRow><Field label="FPS value scale"
          description="Scales the FPS number only; other values retain their size." /></PanelSectionRow>
        <PanelSectionRow><SliderField label={"FPS scale · "+settings.fps_scale+"%"}
          value={settings.fps_scale} min={100} max={200} step={10} showValue
          disabled={!ready || !info?.layout_spacing_supported}
          onChange={(value:number)=>update({fps_scale:value})}/></PanelSectionRow>
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
          <ControlGroup title="Spacing" summary="Padding · element and column gaps"
            open={layoutPanel==="spacing"} onToggle={()=>setLayoutPanel("spacing")}>
        <PanelSectionRow><SliderField label="Vertical padding (px)"
          value={settings.padding_y} min={0} max={24} step={1} showValue disabled={!ready}
          onChange={v=>update({padding_y:v})}/></PanelSectionRow>
        <PanelSectionRow><SliderField label="Horizontal padding (px)"
          value={settings.padding_x} min={0} max={24} step={1} showValue
          disabled={!ready || !info?.layout_spacing_supported}
          onChange={v=>update({padding_x:v})}/></PanelSectionRow>
        <PanelSectionRow><Field label="Element spacing" description={info?.layout_spacing_supported
          ? "Custom Claw renderer is available. Restart the game to apply spacing changes."
          : "The custom renderer is unavailable. Spacing controls are disabled."} /></PanelSectionRow>
        <PanelSectionRow><SliderField label="Element gap (px)" value={settings.element_gap} min={0} max={20} step={1} showValue
          disabled={!ready || !info?.layout_spacing_supported} onChange={(value: number) => update({element_gap: value})} /></PanelSectionRow>
        <PanelSectionRow><SliderField label="Column padding (px)" value={settings.table_gap} min={0} max={12} step={1} showValue
          disabled={!ready || !info?.layout_spacing_supported} onChange={(value: number) => update({table_gap: value})} /></PanelSectionRow>
        <PanelSectionRow><ToggleField label="Even spacing across inline metrics"
          checked={settings.inline_metrics} disabled={!ready || !info?.layout_spacing_supported}
          onChange={(v: boolean) => update({inline_metrics: v})} /></PanelSectionRow>
        <PanelSectionRow><SliderField label="Within-group gap (px)" value={settings.inner_gap} min={0} max={16} step={1} showValue
          disabled={!ready || !info?.layout_spacing_supported || !settings.inline_metrics}
          onChange={(value: number) => update({inner_gap: value})} /></PanelSectionRow>


          </ControlGroup>
          <ControlGroup title="Frametime graph" summary="Graph style and width"
            open={layoutPanel==="frametime"} onToggle={()=>setLayoutPanel("frametime")}>
            {settings.frametime && settings.metrics.graph ? <>
        <PanelSectionRow><Field label="Frametime graph style"
          description="Select a visual style using the D-pad." /></PanelSectionRow>
        <GamepadGrid items={graphStyleChoices} columns={2}
          className="claw-tiles claw-graph-tiles" renderItem={(choice)=>{
            const selected=settings.graph_style===choice.id;
            return <DialogButton key={choice.id} className="claw-control-button"
              aria-label={"Graph style: "+choice.label}
              aria-pressed={selected} disabled={!ready || !info?.layout_spacing_supported}
              onClick={()=>update({graph_style:choice.id})}
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
        <PanelSectionRow><SliderField label="Frametime graph width (px)" value={settings.graph_width} min={80} max={200} step={5} showValue
          disabled={!ready || !info?.layout_spacing_supported} onChange={(value: number) => update({graph_width: value})} /></PanelSectionRow>
            </> : <Field label="Graph disabled" description="Enable Frametime → Graph in Metrics to edit graph settings."/>}
          </ControlGroup>
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below"
          onClick={()=>confirmAction("Reset layout?",
            "Restores the default position, size, spacing and graph. Saved styles are not deleted.",
            ()=>update({
          fontsize:defaults.fontsize,fps_scale:defaults.fps_scale,
           center_horizontal:defaults.center_horizontal,hud_position:defaults.hud_position,
          opacity:defaults.opacity,rounding:defaults.rounding,
          padding_y:defaults.padding_y,padding_x:defaults.padding_x,offset_x:defaults.offset_x,offset_y:defaults.offset_y,
          element_gap:defaults.element_gap,table_gap:defaults.table_gap,inner_gap:defaults.inner_gap,
          graph_width:defaults.graph_width,graph_style:defaults.graph_style,inline_metrics:defaults.inline_metrics
        }))}>
            Reset layout to defaults
          </ButtonItem></PanelSectionRow>
        </AccordionCard>
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
                  background:open?"#075783":"#172d44",
                  border:open?"2px solid #32d7ff":"1px solid #406586",
                  borderRadius:8,color:"#f2f7fc"}}>
                <span style={{display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",
                  gap:4,width:"100%",minWidth:0}}>
                  <span aria-hidden="true" style={{fontSize:15,color:group.color,lineHeight:1}}>{groupIcons[key]}</span>
                  <span style={{fontSize:12,fontWeight:600,lineHeight:1.15,overflowWrap:"anywhere",
                    textAlign:"center",width:"100%",minWidth:0}}>{named(key)}</span>
                  {total>1 && <span style={{fontSize:10,color:"#a8c6d9",lineHeight:1}}>{count} active</span>}
                </span>
              </DialogButton>;
          }}/>
        {expanded && row.includes(expanded) && settings[expanded] && (() => {
          const key=expanded;
          const group=groups[key];
          const index=visible.indexOf(key);
          return <div className="metric-detail" style={{border:"1px solid #365d7c",
            borderLeft:"3px solid "+group.color,borderRadius:8,background:"#102236",
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
              checked={settings.metrics[id]} disabled={!ready}
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
                background:"#162b3f",border:"1px dashed #50708e",borderRadius:8}}>
              <span style={{display:"flex",alignItems:"center",justifyContent:"center",
                flexDirection:"column",gap:4,minWidth:0}}>
                <span aria-hidden="true" style={{fontSize:14,color:groups[key].color}}>{groupIcons[key]}</span>
                <span style={{fontSize:11,overflowWrap:"anywhere",textAlign:"center"}}>+ {named(key)}</span>
              </span>
            </DialogButton>}/>
        </>}

        </AccordionCard>
        <AccordionCard id="colors" title="Colors & Font" subtitle="Palette, typography and saved styles"
          icon={<FaPalette />} open={openSection === "colors"} onToggle={() => toggleSection("colors")}>
          <PanelSectionRow><Field label="COLORS & FONT"
            description="Edit global appearance or individual metric elements." /></PanelSectionRow>
          <PanelSectionRow><Field label="SAVED STYLES"
            description="Presets save colors, typography, layout and visible sensors. Re-save legacy presets to capture metric choices." /></PanelSectionRow>
          <div className="loaded-style-status" role="status">
            {loadedPreset?`Active: ${styleTitle(settings.active_style!)}${presetDirty?" · modified":""}`:"Active: none"}
          </div>
          <Focusable flow-children="column" className="claw-preset-list">
            {(["1","2"] as const).map(slot=>{
              const stored=Boolean(settings.style_presets?.[slot]);
              const active=stored && settings.active_style===slot;
              return <div className="claw-preset-card" data-loaded={active} key={slot}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",
                  gap:6,minWidth:0,flexWrap:"wrap"}}>
                  <span style={{fontWeight:700,fontSize:14,lineHeight:1.2}}>{styleTitle(slot)}</span>
                  <span style={{fontSize:11,color:active?"#61e4ff":"#a6bdd2"}}>
                    {active?(presetDirty?"Loaded · modified":"Loaded"):stored?"Saved":"Empty"}
                    {stored && <span style={{display:"block",marginTop:3,fontSize:10}}>
                      {settings.style_presets[slot]?.groups
                        ? Object.values(settings.style_presets[slot].groups!).filter(Boolean).length+" active"
                        : "Legacy preset"}
                    </span>}
                  </span>
                </div>
                <Focusable flow-children="row" className="claw-preset-actions">
                  <DialogButton className="claw-control-button" disabled={!ready||!stored} aria-pressed={active}
                    onClick={()=>loadPreset(slot)}
                    style={{background:active?"#e0f7ff":"#0874a5",
                      color:active?"#083957":"#ffffff",
                      border:"1px solid #3c91c0",borderRadius:7}}>
                    <span className="claw-preset-label"><FaPlay aria-hidden="true" /> Load</span>
                  </DialogButton>
                  <DialogButton className="claw-control-button" disabled={!ready} onClick={()=>{
                      if(stored) confirmAction("Overwrite "+styleTitle(slot)+"?",
                        "This replaces saved layout, appearance and metric selection.",
                        ()=>savePreset(slot));
                      else savePreset(slot);
                    }}
                    style={{background:"#294968",border:"1px solid #507394",
                      borderRadius:7,color:"#ffffff"}}>
                    <span className="claw-preset-label"><FaDownload aria-hidden="true" /> Save</span>
                  </DialogButton>
                </Focusable>
                <DialogButton className="claw-control-button" disabled={!ready}
                  onClick={()=>renameStyle(slot)} aria-label={"Rename "+styleTitle(slot)}
                  style={{margin:"7px 0 0",width:"100%",minWidth:0,minHeight:38,
                    background:"#203b58",border:"1px solid #466681",fontSize:12}}>
                  <FaPen style={{marginRight:6}}/> Rename
                </DialogButton>
              </div>;
            })}
          </Focusable>
          <PanelSectionRow><Field label="APPEARANCE EDITOR" description="Select a metric to customize its colors and typography." /></PanelSectionRow>
          <GamepadGrid items={styleTabs} columns={3} className="claw-tiles claw-style-tiles"
            renderItem={([key,name])=><DialogButton key={key} className="claw-control-button" disabled={!ready}
              aria-pressed={styleCategory===key} aria-label={"Style: "+(key==="global"?name:named(key))}
              onClick={()=>chooseStyleCategory(key)}
              style={{minWidth:0,width:"100%",minHeight:49,margin:0,padding:"6px 3px",
                background:styleCategory===key?"#087daf":"#263d5b",
                border:styleCategory===key?"2px solid #29dcff":"1px solid #476687",
                borderRadius:8,color:"#eef5ff"}}>
              <span style={{display:"flex",flexDirection:"column",alignItems:"center",
                justifyContent:"center",gap:4,minWidth:0,width:"100%"}}>
                <span className="style-group-icon" aria-hidden="true">{groupIcons[key]}</span>
                <span style={{fontSize:11.5,lineHeight:1.2,overflowWrap:"anywhere",
                  textAlign:"center",width:"100%",minWidth:0}}>{key==="global"?name:named(key)}</span>
              </span>
            </DialogButton>}/>
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
            <div key={token.key} style={{padding:"8px 4px",marginBottom:8,
              background:"#1a2c43",border:"1px solid #375878",borderRadius:8}}>
              <div style={{fontWeight:700,fontSize:13,marginBottom:5}}>{tokenTitle(token)}</div>
              <PanelSectionRow>
                <ButtonItem disabled={!ready} layout="below" onClick={()=>cycleTokenWeight(token.key)}>
                  <span style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}>
                    <span>Font: {weightLabel[settings.token_weights?.[token.key]??"inherit"]}</span>
                    <span style={{opacity:.7}}>Change <FaChevronRight /></span>
                  </span>
                </ButtonItem>
              </PanelSectionRow>
              <PanelSectionRow><Focusable flow-children="row" style={{display:"flex",gap:5}}>
                <DialogButton className="claw-control-button" disabled={!ready} onClick={()=>openTokenColorPicker(token)}
                  style={{flex:1,margin:0,padding:8}}>
                  <span style={{display:"flex",alignItems:"center",gap:7}}>
                    <span style={{width:17,height:17,borderRadius:4,
                      background:"#"+(settings.token_colors?.[token.key]??
                        settings.colors[token.defaultColor]??defaultColors[token.defaultColor]),
                      border:"1px solid #adc7e7"}}/>
                    {settings.token_colors?.[token.key]?"Custom color":"Global color"}
                  </span>
                </DialogButton>
                <DialogButton className="claw-control-button" disabled={!ready || !settings.token_colors?.[token.key]}
                  onClick={()=>resetTokenColor(token.key)}
                  style={{minWidth:70,padding:7,margin:0}}>Reset</DialogButton>
              </Focusable></PanelSectionRow>
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
        </AccordionCard>
        <AccordionCard id="activation" title="Activation" subtitle="Launch Claw Metrics in games"
          icon={<FaPlayCircle />} open={openSection === "activation"} onToggle={() => toggleSection("activation")}>
          <PanelSectionRow><Field label="Steam Launch Options"
            description={info?.short_launcher_ready
              ? info.short_launch_option
              : "Launcher unavailable. Reload Decky and check the installation."} /></PanelSectionRow>
          <PanelSectionRow><ButtonItem layout="below" disabled={!info?.short_launcher_ready}
            onClick={()=>{ void copyLaunchCommand("short"); }}>
            <FaCopy style={{marginRight:8}} /> Copy launch command
          </ButtonItem></PanelSectionRow>
          {copyStatus && <PanelSectionRow><Field label="Clipboard" description={copyStatus}/></PanelSectionRow>}
          <PanelSectionRow><Field label="How to use"
            description="Paste into a game's Steam Launch Options. Restart the game after changes. Backup commands are in Advanced." /></PanelSectionRow>
        </AccordionCard>
        <AccordionCard id="advanced" title="Advanced" subtitle="Updates and troubleshooting"
          icon={<FaSlidersH />} open={openSection === "advanced"} onToggle={() => toggleSection("advanced")}>
          <ControlGroup title="Updates" summary="Installed version · GitHub releases"
            open={advancedPanel==="updates"} onToggle={()=>setAdvancedPanel("updates")}>
            <PanelSectionRow><Field label="Installed version" description="Claw Metrics 0.2.4-test.43" /></PanelSectionRow>
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
          <ControlGroup title="Diagnostics" summary="TDP sensor · renderer · configuration"
            open={advancedPanel==="diagnostics"} onToggle={()=>setAdvancedPanel("diagnostics")}>
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
            open={advancedPanel==="backup"} onToggle={()=>setAdvancedPanel("backup")}>

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


