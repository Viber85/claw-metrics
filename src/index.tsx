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

import {styleLayoutFrom, independentColors, styleModified} from "./style-presets";
import {metricName, relatedLabel, cleanName, groupNames} from "./metric-names";

type Group = "fps" | "frametime" | "cpu" | "gpu" | "ram" | "vram" | "battery" | "tdp" | "draw" | "time";
type FontWeight = "light" | "regular" | "semibold" | "bold";
type WeightSelection = "inherit" | FontWeight;
type StyleCategory = "global" | "fps" | "cpu" | "gpu" | "ram" | "vram" | "battery" | "time" | "tdp" | "draw" | "values";
type TokenKey = "fps.label" | "fps.value" | "fps.ms" | "cpu.label" | "cpu.load" | "cpu.temp" | "cpu.clock" | "cpu.power" | "gpu.label" | "gpu.load" | "gpu.temp" | "gpu.clock" | "gpu.power" | "gpu.junction" | "gpu.fan" | "gpu.voltage" | "ram.label" | "ram.value" | "vram.label" | "vram.value" | "vram.temp" | "vram.clock" | "battery.label" | "battery.value" | "battery.time" | "battery.power" | "time.value" | "tdp.value";
type MetricToken = {key: TokenKey; label: string; defaultColor: ColorKey};
const tokenGroups: Record<Exclude<StyleCategory, "global">, MetricToken[]> = {
  fps: [{key:"fps.label", label:"FPS naziv", defaultColor:"fps_label"}, {key:"fps.value", label:"FPS broj", defaultColor:"fps_value"}, {key:"fps.ms", label:"Frametime (ms)", defaultColor:"text"}],
  cpu: [{key:"cpu.label", label:"CPU naziv", defaultColor:"cpu"}, {key:"cpu.load", label:"Opterećenje (%)", defaultColor:"text"}, {key:"cpu.temp", label:"Temperatura (°C)", defaultColor:"text"}, {key:"cpu.clock", label:"Takt (MHz)", defaultColor:"text"}, {key:"cpu.power", label:"Potrošnja (W)", defaultColor:"text"}],
  gpu: [{key:"gpu.label", label:"GPU naziv", defaultColor:"gpu"}, {key:"gpu.load", label:"Opterećenje (%)", defaultColor:"text"}, {key:"gpu.temp", label:"Temperatura (°C)", defaultColor:"text"}, {key:"gpu.clock", label:"Takt (MHz)", defaultColor:"text"}, {key:"gpu.power", label:"Potrošnja (W)", defaultColor:"text"}, {key:"gpu.junction", label:"Junction temperatura", defaultColor:"text"}, {key:"gpu.fan", label:"Ventilator", defaultColor:"text"}, {key:"gpu.voltage", label:"Napon", defaultColor:"text"}],
  ram: [{key:"ram.label", label:"RAM naziv", defaultColor:"ram"}, {key:"ram.value", label:"Zauzeće (GiB)", defaultColor:"text"}],
  vram: [{key:"vram.label", label:"VRAM naziv", defaultColor:"vram"}, {key:"vram.value", label:"Zauzeće (GiB)", defaultColor:"text"}, {key:"vram.temp", label:"Temperatura memorije", defaultColor:"text"}, {key:"vram.clock", label:"Takt memorije", defaultColor:"text"}],
  battery: [{key:"battery.label", label:"BATT naziv", defaultColor:"battery"}, {key:"battery.value", label:"Baterija (%) / ikona", defaultColor:"text"}, {key:"battery.time", label:"Preostalo vrijeme", defaultColor:"text"}],
  time: [{key:"time.value", label:"Sat", defaultColor:"time"}],
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
  ["ram","RAM"],["vram","VRAM"],["battery","Battery"],["time","Clock"],["tdp","TDP"],["draw","DRAW"],["values","Vrijednosti"],
];
type SavedStyle = Partial<Record<"fontsize"|"opacity"|"rounding"|"padding_x"|"padding_y"|"offset_x"|"offset_y"|"element_gap"|"table_gap"|"inner_gap"|"graph_width",number>> & {
  sans?:boolean; inline_metrics?:boolean; version?:number;
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
  ["text", "Vrijednosti"], ["time", "Clock"], ["tdp", "TDP"], ["draw", "DRAW"], ["separator", "Separatori između grupa"],
  ["fps_label", "FPS"],
  ["cpu", "CPU naziv"], ["gpu", "GPU naziv"], ["ram", "RAM naziv"],
  ["vram", "VRAM naziv"], ["battery", "BATT naziv"], ["graph", "Frametime graf"],
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
  return (
    <ConfirmModal strTitle={title} bAllowFullSize onCancel={closeModal}
      onOK={() => { onConfirm(preview); closeModal(); }}>
      <div style={{padding: "8px 4px 14px"}}>
        <div style={{display: "flex", alignItems: "center", gap: 12, marginBottom: 12}}>
          <div style={{height: 48, width: 48, borderRadius: 5,
            backgroundColor: "#" + preview, border: "1px solid #8794a4"}} />
          <div>
            <div>#{preview}</div>
            <div style={{fontSize: 12, opacity: 0.7}}>Neprozirna RGB boja (alpha 100%)</div>
          </div>
        </div>
        <SliderField showValue editableValue label="Nijansa (Hue)"
          value={h} min={0} max={360} step={1} onChange={setH} />
        <SliderField showValue editableValue label="Zasićenost (Saturation)"
          value={s} min={0} max={100} step={1} onChange={setS} />
        <SliderField showValue editableValue label="Svjetlina (Lightness)"
          value={l} min={0} max={100} step={1} onChange={setL} />
      </div>
    </ConfirmModal>
  );
}
const groupIcons: Record<string, ReactNode> = {global:<FaPalette/>,fps:<FaTachometerAlt/>,cpu:<FaMicrochip/>,gpu:<FaDesktop/>,ram:<FaMemory/>,vram:<FaMemory/>,battery:<FaBatteryThreeQuarters/>,time:<FaClock/>,tdp:<FaBolt/>,draw:<FaBolt/>,values:<FaHashtag/>};
function RenameMetricModal({name,original,onConfirm,onCancel}:any){
 const [value,setValue]=useState(name);
 return <ConfirmModal strTitle="Promijeni naziv metrike" onCancel={onCancel}
   onOK={()=>onConfirm(cleanName(value))}>
  <div className="claw-rename-modal" style={{padding:"8px 2px",minWidth:0}}>
    <TextField label="Naziv stavke" focusOnMount placeholder={original}
      value={value} onChange={(event)=>setValue(event.currentTarget.value.slice(0,24))}
      description="Odaberi polje tipkom A za SteamOS tipkovnicu. Maksimalno 24 znaka." />
    <p className="description" style={{fontSize:12,lineHeight:1.4,margin:"12px 0"}}>
      Naziv se koristi u Metrics, Colors & Font i HUD prikazu. Prazan naziv vraća zadani naziv.
    </p>
    <DialogButton style={{width:"100%",margin:0,minWidth:0}} onClick={()=>setValue("")}>
      Vrati zadani naziv
    </DialogButton>
  </div>
 </ConfirmModal>;
}

type Settings = Record<Group, boolean> & {
  active_style: string|null;
  custom_labels: Record<string,string>;
  enabled: boolean; fontsize: number; opacity: number; power: boolean; tdp: boolean;
  sans: boolean; rounding: number; offset_x: number; offset_y: number; padding_y: number;
  padding_x: number; element_gap: number; table_gap: number; graph_width: number;
  inner_gap: number; inline_metrics: boolean; fps_bold: boolean; font_weight: FontWeight; order: Group[];
  metrics: Record<string, boolean>;
  colors: ColorSettings;
  token_weights: Partial<Record<TokenKey, FontWeight>>;
  token_colors: Partial<Record<TokenKey, string>>;
  style_presets: Record<string, SavedStyle>;
};
const order: Group[] = ["fps", "frametime", "cpu", "gpu", "ram", "vram", "battery", "tdp", "draw", "time"];
const groups: Record<Group, {label: string; color: string; metrics: [string, string][]; always?: string; note?: string}> = {
  fps: {label: "FPS", color: "#30e5a0", metrics: [], always: "FPS", note: "MangoHud koristi istu glavnu veličinu fonta za FPS i ostale vrijednosti."},
  frametime: {label: "Frametime", color: "#30e5a0", metrics: [["fps_ms", "Frametime (ms)"], ["graph", "Frametime graph"]], note: "Broj u ms prati FPS blok; strelice premještaju graf. Za ms uključi i FPS."},
  gpu: {label: "GPU", color: "#8bda62", always: "GPU load", metrics: [["gpu_temp", "GPU temp"], ["gpu_junction_temp", "GPU junction temp"], ["gpu_core_clock", "GPU clock"], ["gpu_mem_clock", "VRAM clock"], ["gpu_mem_temp", "VRAM temp"], ["gpu_power", "GPU watts"], ["gpu_fan", "GPU fan"], ["gpu_voltage", "GPU voltage"]], note: "VRAM clock/temp prikazuju se u VRAM bloku i traže uključen VRAM. Ostali senzori ovise o dostupnosti na Z2 Extremeu."},
  cpu: {label: "CPU", color: "#37c9ef", always: "CPU load", metrics: [["cpu_temp", "CPU temp"], ["cpu_mhz", "CPU clock"], ["cpu_power", "CPU watts"]]},
  ram: {label: "RAM", color: "#b077df", always: "RAM usage", metrics: []},
  vram: {label: "VRAM", color: "#d76ab8", always: "VRAM usage", metrics: [], note: "MangoHud za VRAM koristi podatke GPU bloka; uključi i GPU."},
  battery: {label: "Battery", color: "#30e5a0", always: "Battery level", metrics: [["battery_icon", "Battery icon (replaces %)"], ["battery_time", "Remaining time"]], note: "Ikona i postotak su alternativni načini prikaza u ovom MangoHud rendereru."},
  tdp: {label: "TDP", color: "#ffbd69", metrics: [], always: "Postavljeni TDP limit", note: "Samo očitanje: RyzenAdj STAPM ili MSI firmware PL1. Ako očitanje nije moguće, prikazuje TDP --. Ne upravlja potrošnjom."},
  draw: {label: "DRAW", color: "#ee6279", metrics: [], always: "Battery discharge watts", note: "Ukupno pražnjenje baterije. Na punjaču ili bez senzora prikazuje DRAW --, a ne izmišljenu potrošnju."},
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
  active_style:null, custom_labels: {},
  enabled: true, fontsize: 18, opacity: 80, fps: true, frametime: true,
  cpu: true, gpu: true, ram: true, vram: true, battery: true, draw: true,
  power: true, time: true, tdp: false, sans: true, rounding: 10, offset_x: 8, offset_y: 8, padding_y: 8,
  padding_x: 5, element_gap: 8, table_gap: 4, graph_width: 150,
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
  return (
    <div data-section={id} data-selected={open ? "true" : "false"} style={{
      background: "#111e30",
      width: "100%", maxWidth: "100%", minWidth: 0, boxSizing: "border-box",
      border: open ? "2px solid #ffffff" : "1px solid #395579",
      borderLeft: open ? "4px solid #08d3fa" : "4px solid #8b65e7",
      borderRadius: 12,
      overflow: "hidden",
      marginBottom: 10,
      boxShadow: open ? "inset 0 0 0 1px #ffffff, 0 0 15px #0285ca55" : "none",
    }}>
      {/* Keep the selection border INSIDE the header: Decky can override DialogButton borders. */}
      <div className="claw-accordion-header" style={{position:"relative",width:"100%",minWidth:0,
        maxWidth:"100%",boxSizing:"border-box"}}>
        <DialogButton onClick={onToggle} aria-pressed={open} style={{
          width: "100%", minWidth: 0, boxSizing: "border-box",
          display: "flex", alignItems: "center",
          textAlign: "left", margin: 0, padding: "12px 10px",
          background: open ? "#073858" : "#14243b",
          border: "none", borderRadius: 0, minHeight: 66, whiteSpace: "normal",
          outline: open ? "2px solid #ffffff" : "none", outlineOffset: "-3px",
        }}>
          <span style={{display: "flex", alignItems: "center", gap: 10, width: "100%", minWidth: 0}}>
            <span style={{display: "flex", alignItems: "center", justifyContent: "center",
              background: open ? "#075b83" : "#203551", borderRadius: 8, minWidth: 36, height: 36,
              fontSize: 20, color: open ? "#42e0ff" : "#acd7fe"}}>{icon}</span>
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
        {/* Painted over the Decky button so Steam focus styling cannot hide the white outline.
            Pointer events are disabled to preserve controller navigation and click behavior. */}
        <div aria-hidden="true" className="claw-accordion-selection-ring"
          style={{position:"absolute",inset:3,zIndex:2,pointerEvents:"none",
            boxSizing:"border-box",borderRadius:8,
            border:open?"2px solid #ffffff":"2px solid transparent",
            boxShadow:open?"0 0 0 1px rgba(255,255,255,0.50)":"none"}} />
      </div>
      {open && <div style={{padding: "10px 8px 12px", borderTop: "1px solid #235b81"}}>
        {children}
      </div>}
    </div>
  );
}

// Decky can remount Content after backend saves. Keep navigation state
// outside the React instance, so saving never jumps back to Metrics.
let lastOpenSection: SectionKey | null = "metrics";
let lastExpandedMetric: Group | null = null;
let lastStyleCategory = "global";

function Content() {
  const [settings, setSettings] = useState<Settings>(defaults);
  const [info, setInfo] = useState<Info | null>(null);
  const [status, setStatus] = useState("Učitavanje…");
  const [copyStatus, setCopyStatus] = useState("");
  const [showLegacyCommand, setShowLegacyCommand] = useState(false);
  const [rendererStatus, setRendererStatus] = useState("Nije provjereno. Pokreni igru za test.");
  const [tdpStatus, setTdpStatus] = useState("TDP još nije provjeren.");
  const [rendererBusy, setRendererBusy] = useState(false);
  const verifyTdp = async () => {
    try { const result=await withTimeout(getTdpStatus());setTdpStatus(result.description); }
    catch(error) {setTdpStatus("Provjera TDP-a nije uspjela: "+String(error));}
  };
  const verifyRenderer = async () => {
    setRendererBusy(true);
    setRendererStatus("Provjeravam procese igre...");
    try {
      const result = await withTimeout(getRendererStatus());
      setRendererStatus(
        (result.native_loaded ? "AKTIVNO" : "NIJE AKTIVNO") +
        " · native: " + result.native_processes +
        " · obični MangoHud: " + result.stock_processes +
        " · zahtjev za slojem: " + result.layer_requests +
        " · testni config: " + result.config_requests +
        " · Vulkan path: " + result.path_requests +
        " · pristup procesima: " + result.environments_read + "/" + result.processes_seen +
        " · manifest: " + (result.manifest_in_user_location ? "DA" : "NE") +
        ". " + result.reason
      );
    } catch (error) {
      setRendererStatus("Provjera nije uspjela: " + String(error));
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
    setStatus("Provjera veze s backendom…");
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
        ? "Backend povezan · profil dostupan igri."
        : "Backend povezan, ali profil nije čitljiv. Ponovno pokreni Decky Loader.");
    } catch (error) {
      setStatus("Greška veze: " + String(error));
    }
  };
  useEffect(() => { void refresh(); }, []);

  const update = (patch: Partial<Settings>) => {
    const next = { ...current.current, ...patch };
    current.current = next;
    const id = ++revision.current;
    setSettings(next);
    setStatus("Spremanje…");
    queue.current = queue.current.then(async () => {
      try {
        const result = await withTimeout(save(next));
        if (!result.ok) throw new Error("Backend nije potvrdio spremanje.");
        if (id === revision.current) setStatus("Spremljeno. Ponovno pokreni igru za sigurnu primjenu.");
      } catch (error) {
        if (id === revision.current) setStatus("Greška pri spremanju: " + String(error));
      }
    });
  };

  // Copy synchronously from a button click: SteamOS Game Mode often does
  // not expose the modern Clipboard API to Decky panels.
  const copyLaunchCommand = async (experimental: boolean | "short" = false) => {
    const command = experimental === "short" ? info?.short_launch_option
      : experimental ? info?.experimental_launch_option : info?.launch_option;
    if (!command) {
      setCopyStatus("Naredba još nije dostupna.");
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
        ? "Kopirano! Zalijepi naredbu u Steam Launch Options."
        : "Kopiranje nije uspjelo. Provjeri dopušta li SteamOS kopiranje u Game Modeu."
    );
  };

  const renameMetric = (key:Group) => {
    const restoreFocus=()=>requestAnimationFrame(()=>{(document.querySelector('[data-metric="'+key+'"] button') as HTMLElement)?.focus()});
    const dialog=showModal(<RenameMetricModal name={metricName(current.current,key)} original={groups[key].label}
      onCancel={()=>{dialog.Close();restoreFocus()}} onConfirm={(value:string)=>{
        const labels={...current.current.custom_labels};
        if(!value || value===groups[key].label) delete labels[key];else labels[key]=value;
        update({custom_labels:labels}); dialog.Close();restoreFocus();
      }}/>);
  };
  const named=(key:string)=>key==="values"?"Vrijednosti":metricName(settings,key);
  const tokenTitle=(token:MetricToken)=>{
    const group=token.key==="battery.power"?"draw":token.key.split(".")[0];
    const key=group==="time"?"time":group;
    if(token.key.endsWith(".label")||token.key.endsWith(".value")||token.key==="battery.power")return named(key);
    return (styleCategory==="values"?named(key)+" · ":"")+relatedLabel(settings,token.label).replace(/\s+(naziv|broj)\b/gi,"");
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
      version:2, ...styleLayoutFrom(d),
      colors: {...d.colors}, font_weight: d.font_weight, fps_bold: d.fps_bold,
      token_weights: {...d.token_weights}, token_colors: {...d.token_colors},
    };
    update({style_presets: {...d.style_presets, [slot]: preset},active_style:slot});
  };
  const loadPreset = (slot: string) => {
    const preset = current.current.style_presets?.[slot];
    if (!preset) return;
    update({...styleLayoutFrom(preset),active_style:slot,colors: independentColors(preset.colors,defaultColors), font_weight: preset.font_weight,
      fps_bold: preset.fps_bold, token_weights: {...preset.token_weights},
      token_colors: {...preset.token_colors}});
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
        for(const tokens of Object.values(tokenGroups))for(const token of tokens){
          if(changed.has(token.defaultColor))delete token_colors[token.key];
        }
        update({colors:{...current.current.colors,[key]:hex,...(key==="fps_label"?{fps_value:hex}:{})},token_colors});
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
  const smallButton = {minWidth: 28, width: 28, padding: "6px 0", margin: 0, fontSize: 17, borderRadius: 6};

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
        /* Narrow QAM panel: fixed 3-column grid with no intrinsic button min-width. */
        .claw-tiles {
          display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 6px; width: 100%; min-width: 0; padding: 4px 0 10px;
          box-sizing: border-box;
        }
        .claw-tiles > *, .claw-tiles button {
          min-width: 0 !important; max-width: 100%; box-sizing: border-box;
        }
        .claw-tiles button { white-space: normal !important; overflow-wrap: anywhere; }
        .claw-style-tiles .style-group-icon {
          display: inline-flex; align-items: center; justify-content: center;
          margin: 0 !important; color: #bceaff; font-size: 13px; line-height: 1;
        }
        .claw-metric-tiles .metric-card:focus-within {
          outline: 2px solid #ffffff; outline-offset: -2px; border-radius: 8px;
        }
        .claw-metric-tiles button[aria-pressed="true"] {
          box-shadow: 0 0 0 1px #29dcff inset;
        }
        .claw-weight-tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
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
        /* Persistent selection, independent of Decky keyboard/controller focus. */
        [data-section][data-selected="true"] .claw-accordion-header > button {
          outline: 2px solid #ffffff !important;
          outline-offset: -3px !important;
        }
        .claw-rename-modal { max-width: 100%; overflow-wrap: anywhere; }
        .claw-rename-modal input { max-width: 100%; box-sizing: border-box; }
      `}</style>
      <PanelSection title="Claw Metrics · v0.2.4-test.21">
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
        <AccordionCard id="overlay" title="Overlay" subtitle="Uključi i provjeri prikaz na ekranu"
          icon={<FaDesktop />} open={openSection === "overlay"} onToggle={() => toggleSection("overlay")}>
          {toggle("enabled", "Uključi prikaz")}
          <PanelSectionRow><Field label="Status" description={status} /></PanelSectionRow>
          <PanelSectionRow><Field label="Profil" description={info?.config_readable
            ? "Konfiguracija je dostupna igri." : "Konfiguracija nije čitljiva ili se učitava."} /></PanelSectionRow>
        </AccordionCard>
        <AccordionCard id="layout" title="Layout" subtitle="Pozicija, veličina, širina i razmaci"
          icon={<FaThLarge />} open={openSection === "layout"} onToggle={() => toggleSection("layout")}>
        {([ ["fontsize", "Veličina teksta", 12, 28, 1], ["opacity", "Pozadina (%)", 0, 100, 5],
          ["rounding", "Zaobljenost rubova", 0, 20, 1], ["padding_y", "Dodatni padding gore/dolje (px)", 0, 24, 1],
          ["padding_x", "Padding lijevo i desno (px)", 0, 24, 1],
          ["offset_x", "X — lijevo/desno (px)", -1920, 1920, 1], ["offset_y", "Y — gore/dolje (px)", -1200, 1200, 1] ] as const).map(([key, label, min, max, step]) =>
          <PanelSectionRow key={key}><SliderField label={label} value={settings[key]} min={min} max={max} step={step} showValue disabled={!ready || (key==="padding_x" && !info?.layout_spacing_supported)}
            onChange={(value: number) => update({[key]: value})} /></PanelSectionRow>)}
        <PanelSectionRow><Field label="Bočni padding i razmak" description={info?.layout_spacing_supported
          ? "Biblioteka je instalirana. Ove kontrole rade SAMO uz testnu Vulkan launch komandu iz ACTIVATION, ne uz običnu komandu. Nakon promjene ponovno pokreni igru. Oznaka FPS* potvrđuje da se testna konfiguracija učitala."
          : "U stock MangoHud 0.8.1 bočni padding (5 px) i razmak elemenata (8 px) nisu podesivi. Kontrole su zaključane dok ne provjerimo siguran renderer, bez promjene postojeće verzije."} /></PanelSectionRow>
        <PanelSectionRow><SliderField label="Razmak između elemenata (px)" value={settings.element_gap} min={0} max={20} step={1} showValue
          disabled={!ready || !info?.layout_spacing_supported} onChange={(value: number) => update({element_gap: value})} /></PanelSectionRow>
        <PanelSectionRow><SliderField label="Padding stupaca (px)" value={settings.table_gap} min={0} max={12} step={1} showValue
          disabled={!ready || !info?.layout_spacing_supported} onChange={(value: number) => update({table_gap: value})} /></PanelSectionRow>
        <PanelSectionRow><ToggleField label="Jednaki razmaci: FPS, CPU, GPU, RAM, VRAM, BATT"
          checked={settings.inline_metrics} disabled={!ready || !info?.layout_spacing_supported}
          onChange={(v: boolean) => update({inline_metrics: v})} /></PanelSectionRow>
        <PanelSectionRow><SliderField label="Razmak unutar grupa (px)" value={settings.inner_gap} min={0} max={16} step={1} showValue
          disabled={!ready || !info?.layout_spacing_supported || !settings.inline_metrics}
          onChange={(value: number) => update({inner_gap: value})} /></PanelSectionRow>

        <PanelSectionRow><SliderField label="Širina frametime grafa (px)" value={settings.graph_width} min={80} max={200} step={5} showValue
          disabled={!ready || !info?.layout_spacing_supported} onChange={(value: number) => update({graph_width: value})} /></PanelSectionRow>
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below" onClick={()=>update({
          fontsize:defaults.fontsize,opacity:defaults.opacity,rounding:defaults.rounding,
          padding_y:defaults.padding_y,padding_x:defaults.padding_x,offset_x:defaults.offset_x,offset_y:defaults.offset_y,
          element_gap:defaults.element_gap,table_gap:defaults.table_gap,inner_gap:defaults.inner_gap,
          graph_width:defaults.graph_width,inline_metrics:defaults.inline_metrics
        })}>Vrati zadane postavke Layouta</ButtonItem></PanelSectionRow>
        <PanelSectionRow><Field label="Položaj i padding" description="Ručni položaj od lijevog i gornjeg ruba. Padding povećava razmak gore/dolje; bočni razmak u standardnom MangoHudu je fiksan. Ako je red širi od igre, smanji font ili razmake — pomak ne smanjuje širinu." /></PanelSectionRow>
        <PanelSectionRow><Field label="Napomena" description="Broj uključenih podataka i font moraju stati u širinu igre. Ako red izlazi iz ekrana, smanji tekst ili isključi dodatne senzore. FPS se ne može zasebno povećati u ovom MangoHud rendereru." /></PanelSectionRow>

        </AccordionCard>
        <AccordionCard id="metrics" title="Metrics" subtitle="Prikazane metrike i njihov redoslijed"
          icon={<FaChartBar />} open={openSection === "metrics"} onToggle={() => toggleSection("metrics")}>
        <PanelSectionRow><div style={{fontSize: 12, color: "#b8c7d5", marginBottom: 8}}>
          Odaberi karticu za detalje, preimenovanje, pomicanje i skrivanje. Tri metrike u redu.
        </div></PanelSectionRow>
        <div className="claw-tiles claw-metric-tiles">
          {visible.map(key => {
            const group = groups[key];
            const open = expanded === key;
            const total = group.metrics.length + (group.always ? 1 : 0);
            const count = group.metrics.filter(([id]) => settings.metrics[id]).length + (group.always ? 1 : 0);
            return <div key={key} className="metric-card" data-metric={key}>
              <DialogButton disabled={!ready} aria-pressed={open}
                aria-label={"Postavke metrike: " + named(key)}
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
                  {total>1 && <span style={{fontSize:10,color:"#a8c6d9",lineHeight:1}}>{count}/{total}</span>}
                </span>
              </DialogButton>
            </div>;
          })}
        </div>
        {expanded && settings[expanded] && (() => {
          const key=expanded;
          const group=groups[key];
          const index=visible.indexOf(key);
          return <div className="metric-detail" style={{border:"1px solid #365d7c",
            borderLeft:"3px solid "+group.color,borderRadius:8,background:"#102236",
            padding:"9px 7px",marginTop:9,minWidth:0}}>
            <div style={{fontWeight:700,fontSize:13,marginBottom:7,color:"#f1f7fc"}}>{named(key)} · Postavke</div>
            <Focusable style={{display:"flex",gap:5,alignItems:"center",flexWrap:"wrap"}} flow-children="row">
              <DialogButton aria-label={"Promijeni naziv: "+named(key)} disabled={!ready}
                onClick={()=>renameMetric(key)} style={smallButton}><FaPen aria-hidden="true"/></DialogButton>
              <DialogButton aria-label={"Pomakni gore: "+named(key)} disabled={!ready || index<=0}
                onClick={()=>move(key,-1)} style={smallButton}>⌃</DialogButton>
              <DialogButton aria-label={"Pomakni dolje: "+named(key)} disabled={!ready || index===visible.length-1}
                onClick={()=>move(key,1)} style={smallButton}>⌄</DialogButton>
              <DialogButton aria-label={"Sakrij: "+named(key)} disabled={!ready}
                onClick={()=>{expandMetric(null);update({[key]:false});}}
                style={{...smallButton,minWidth:66,width:66,fontSize:12}}>Sakrij</DialogButton>
            </Focusable>
            {group.always && <Field label={related(group.always)} padding="compact">
              <span style={{fontSize:11,color:"#4acbff"}}>Always</span>
            </Field>}
            {group.metrics.map(([id,label])=><ToggleField key={id} label={related(label)}
              checked={settings.metrics[id]} disabled={!ready}
              onChange={(checked:boolean)=>metric(id,checked)}/>)}
            {group.note && <div style={{fontSize:11,lineHeight:1.4,color:"#a6b6c6",marginTop:8}}>
              {related(group.note)}
            </div>}
          </div>;
        })()}
        {hidden.length > 0 && <>
          <PanelSectionRow><Field label="ADD ELEMENT" description="Vrati skrivenu grupu u red." /></PanelSectionRow>
          <div className="claw-tiles claw-hidden-metric-tiles">
            {hidden.map(key=><DialogButton key={key} disabled={!ready}
              aria-label={"Prikaži metriku: "+named(key)}
              onClick={()=>update({[key]:true})}
              style={{minWidth:0,width:"100%",minHeight:52,margin:0,padding:"6px 3px",
                background:"#162b3f",border:"1px dashed #50708e",borderRadius:8}}>
              <span style={{display:"flex",alignItems:"center",justifyContent:"center",
                flexDirection:"column",gap:4,minWidth:0}}>
                <span aria-hidden="true" style={{fontSize:14,color:groups[key].color}}>{groupIcons[key]}</span>
                <span style={{fontSize:11,overflowWrap:"anywhere",textAlign:"center"}}>+ {named(key)}</span>
              </span>
            </DialogButton>)}
          </div>
        </>}

        </AccordionCard>
        <AccordionCard id="colors" title="Colors & Font" subtitle="Paleta, separatori, Light / Regular / SemiBold / Bold"
          icon={<FaPalette />} open={openSection === "colors"} onToggle={() => toggleSection("colors")}>
          <PanelSectionRow><Field label="BOJE & FONT"
            description="Globalne postavke ili zasebne postavke naziva i vrijednosti svake metrike." /></PanelSectionRow>
          <div className="claw-tiles claw-style-tiles">
            {styleTabs.map(([key,name])=><DialogButton key={key} disabled={!ready}
              aria-pressed={styleCategory===key} aria-label={"Stil: "+(key==="global"?name:named(key))}
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
            </DialogButton>)}
          </div>
          {styleCategory==="global" ? <>
          <PanelSectionRow><Field label="GLOBALNO" description="Globalna debljina vrijedi za sve elemente. Promjena boje uklanja ručne boje povezanih elemenata; pojedinačne postavke možeš ponovno zadati nakon toga." /></PanelSectionRow>
          {toggle("sans", "Sans-serif font")}
          <PanelSectionRow><Field label="Barlow Semi Condensed" description={
            info?.condensed_fonts_ready ? "Light / Regular / SemiBold / Bold učitani."
              : "Fontovi nisu dostupni; koristi se Claw Sans."} /></PanelSectionRow>
          <PanelSectionRow><Field label="Osnovna debljina" description="Primjenjuje se na sve elemente i uklanja njihove ručne debljine fonta. Poslije ih možeš ponovno podesiti pojedinačno." /></PanelSectionRow>
          <div className="claw-tiles claw-weight-tiles">
            {(["light","regular","semibold","bold"] as FontWeight[]).map(weight=>
              <DialogButton key={weight} disabled={!ready || !settings.sans}
                aria-pressed={settings.font_weight===weight}
                onClick={()=>update({font_weight:weight,token_weights:{}})}
                style={{minWidth:0,width:"100%",minHeight:39,margin:0,padding:"7px 2px",
                  background:settings.font_weight===weight?"#096e9e":"#23364c",
                  border:"1px solid #406080",borderRadius:7,
                  fontSize:11,fontWeight:weight==="bold"?700:weight==="semibold"?600:weight==="light"?300:400}}>
                {weightLabel[weight]}
              </DialogButton>)}
          </div>
          <div className="claw-tiles claw-color-tiles">
            {colorRows.map(([key,label])=><DialogButton key={key} disabled={!ready}
              onClick={()=>openColorPicker(key,label)}
              aria-label={"Promijeni boju: "+paletteLabel(key,label)}
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
            </DialogButton>)}
          </div>
          <PanelSectionRow><ButtonItem disabled={!ready} layout="below"
            onClick={()=>update({colors:{...defaultColors}, token_colors:{}})}>Vrati zadane boje</ButtonItem></PanelSectionRow>
          <PanelSectionRow><Field label="MOJI STILOVI"
            description="Spremi ili učitaj cijeli izgled: boje, font, veličinu, položaj i razmake." /></PanelSectionRow>
          <div className="loaded-style-status" role="status">
            {loadedPreset?`Trenutno učitan: Stil ${settings.active_style}${presetDirty?" · izmijenjen":""}`:"Trenutno učitan: nijedan"}
          </div>
          <div className="claw-preset-list">
            {(["1","2"] as const).map(slot=>{
              const stored=Boolean(settings.style_presets?.[slot]);
              const active=stored && settings.active_style===slot;
              return <div className="claw-preset-card" data-loaded={active} key={slot}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",
                  gap:6,minWidth:0,flexWrap:"wrap"}}>
                  <span style={{fontWeight:700,fontSize:14,lineHeight:1.2}}>Stil {slot}</span>
                  <span style={{fontSize:11,color:active?"#61e4ff":"#a6bdd2"}}>
                    {active?(presetDirty?"Učitan · izmijenjen":"Učitan"):stored?"Spremljen":"Prazan"}
                  </span>
                </div>
                <div className="claw-preset-actions">
                  <DialogButton disabled={!ready||!stored} aria-pressed={active}
                    onClick={()=>loadPreset(slot)}
                    style={{background:active?"#e0f7ff":"#0874a5",
                      color:active?"#083957":"#ffffff",
                      border:"1px solid #3c91c0",borderRadius:7}}>
                    <span className="claw-preset-label"><FaPlay aria-hidden="true" /> Učitaj</span>
                  </DialogButton>
                  <DialogButton disabled={!ready} onClick={()=>savePreset(slot)}
                    style={{background:"#294968",border:"1px solid #507394",
                      borderRadius:7,color:"#ffffff"}}>
                    <span className="claw-preset-label"><FaDownload aria-hidden="true" /> Spremi</span>
                  </DialogButton>
                </div>
              </div>;
            })}
          </div>
          </> : <>
          <PanelSectionRow><Field label={named(styleCategory)}
            description="Svaka stavka ima svoju boju i težinu fonta. Global znači naslijedi osnovnu postavku." /></PanelSectionRow>
          {tokenGroups[styleCategory as Exclude<StyleCategory,"global">].map(token=>(
            <div key={token.key} style={{padding:"8px 4px",marginBottom:8,
              background:"#1a2c43",border:"1px solid #375878",borderRadius:8}}>
              <div style={{fontWeight:700,fontSize:13,marginBottom:5}}>{tokenTitle(token)}</div>
              <PanelSectionRow>
                <ButtonItem disabled={!ready} layout="below" onClick={()=>cycleTokenWeight(token.key)}>
                  <span style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}>
                    <span>Font: {weightLabel[settings.token_weights?.[token.key]??"inherit"]}</span>
                    <span style={{opacity:.7}}>Promijeni <FaChevronRight /></span>
                  </span>
                </ButtonItem>
              </PanelSectionRow>
              <PanelSectionRow><div style={{display:"flex",gap:5}}>
                <DialogButton disabled={!ready} onClick={()=>openTokenColorPicker(token)}
                  style={{flex:1,margin:0,padding:8}}>
                  <span style={{display:"flex",alignItems:"center",gap:7}}>
                    <span style={{width:17,height:17,borderRadius:4,
                      background:"#"+(settings.token_colors?.[token.key]??
                        settings.colors[token.defaultColor]??defaultColors[token.defaultColor]),
                      border:"1px solid #adc7e7"}}/>
                    {settings.token_colors?.[token.key]?"Vlastita boja":"Boja: globalna"}
                  </span>
                </DialogButton>
                <DialogButton disabled={!ready || !settings.token_colors?.[token.key]}
                  onClick={()=>resetTokenColor(token.key)}
                  style={{minWidth:70,padding:7,margin:0}}>Vrati</DialogButton>
              </div></PanelSectionRow>
            </div>
          ))}
          <PanelSectionRow><ButtonItem disabled={!ready} layout="below"
            onClick={()=>{
              const nw={...current.current.token_weights},nc={...current.current.token_colors};
              for(const t of tokenGroups[styleCategory as Exclude<StyleCategory,"global">]){
                delete nw[t.key]; delete nc[t.key];
              }
              update({token_weights:nw,token_colors:nc});
            }}>Vrati kategoriju na globalni izgled</ButtonItem></PanelSectionRow>
          </>}
        </AccordionCard>
        <AccordionCard id="activation" title="Activation" subtitle="Steam launch komanda i pokretanje"
          icon={<FaPlayCircle />} open={openSection === "activation"} onToggle={() => toggleSection("activation")}>
        <PanelSectionRow><Field label="Steam Launch Options" description={info?.launch_option ?? "Učitavanje…"} /></PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" disabled={!info?.launch_option} onClick={() => { void copyLaunchCommand(); }}>
          <FaCopy style={{marginRight: 8}} /> Kopiraj launch komandu
        </ButtonItem></PanelSectionRow>
        {copyStatus && <PanelSectionRow><Field label="Međuspremnik" description={copyStatus} /></PanelSectionRow>}
        {info?.layout_spacing_supported && <PanelSectionRow>
          <Field label="VAŽNO: Testni prikaz"
            description="Koristi testnu komandu u Steam Launch Options i ponovno pokreni igru. FPS* potvrđuje testnu KONFIGURACIJU, ali ne i izmijenjeni renderer. Dok igra radi, pritisni 'Provjeri koristi li igra eksperimentalni renderer'. Samo status AKTIVNO potvrđuje učitanu biblioteku. Test.3 koristi vlastiti naziv Vulkan sloja i dodatnu provjeru Steam Runtime okruženja." />
        </PanelSectionRow>}
        {info?.layout_spacing_supported && <PanelSectionRow>
          <Field label="Eksperimentalna konfiguracija"
            description={info.experimental_config_readable ? "Datoteka je spremljena. Ovo NE potvrđuje da je igra učitala eksperimentalni renderer." : "Datoteka nije čitljiva; ponovno pokreni Decky Loader."} />
        </PanelSectionRow>}
        {info?.layout_spacing_supported && <PanelSectionRow>
          <Field label="Kratka testna komanda (preporučeno)"
            description={info.short_launcher_ready
              ? info.short_launch_option
              : "Launcher nije spreman. Ponovno pokreni Decky Loader i osvježi status."} />
        </PanelSectionRow>}
        {info?.layout_spacing_supported && <PanelSectionRow>
          <ButtonItem disabled={!info.short_launcher_ready} layout="below"
            onClick={() => { void copyLaunchCommand("short"); }}>
            <FaCopy style={{marginRight: 8}} /> Kopiraj kratku testnu komandu
          </ButtonItem>
        </PanelSectionRow>}
        {info?.layout_spacing_supported && <PanelSectionRow>
          <Field label="Kratki launcher" description="Automatski postavlja iste Vulkan i MangoHud varijable kao stara testna komanda. Potrebno ga je jednom zalijepiti u Steam Launch Options za svaku igru. Ne uključuje globalno sve igre." />
        </PanelSectionRow>}
        {info?.layout_spacing_supported && <PanelSectionRow>
          <ButtonItem layout="below" onClick={() => setShowLegacyCommand(!showLegacyCommand)}>
            {showLegacyCommand ? "Sakrij dugu rezervnu komandu" : "Prikaži dugu rezervnu komandu"}
          </ButtonItem>
        </PanelSectionRow>}
        {info?.layout_spacing_supported && showLegacyCommand && <>
          <PanelSectionRow><Field label="Duga testna komanda (rezervna, Vulkan 64-bit)"
            description={info.experimental_launch_option} /></PanelSectionRow>
          <PanelSectionRow><ButtonItem layout="below"
            onClick={() => { void copyLaunchCommand(true); }}>
            <FaCopy style={{marginRight: 8}} /> Kopiraj testnu komandu (rezervna, duga)
          </ButtonItem></PanelSectionRow>
        </>}
        <PanelSectionRow><Field label="Siguran povratak"
          description="Ako testna komanda blokira pokretanje igre, vrati staru launch komandu iz 0.2.3. Ne mijenja SteamOS ni Panel de Control." /></PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" onClick={() => { void refresh(); }}>Provjeri vezu / ponovno učitaj</ButtonItem></PanelSectionRow>
        <PanelSectionRow><Field label="Primjena" description="Nakon spremanja ponovno pokreni igru. Launch komanda ostaje ista. Sistemski Steam overlay drži isključenim." /></PanelSectionRow>

        </AccordionCard>
        <AccordionCard id="advanced" title="Advanced" subtitle="Dijagnostika, senzori i tehničke informacije"
          icon={<FaSlidersH />} open={openSection === "advanced"} onToggle={() => toggleSection("advanced")}>
        <PanelSectionRow><Field label="TDP limit (read-only)" description="Ne mijenja TDP. Senzor očitava postavljeni limit; Panel de Control i dalje upravlja TDP-om." /></PanelSectionRow>
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below" onClick={() => { void verifyTdp(); }}>
          Provjeri TDP očitanje
        </ButtonItem></PanelSectionRow>
        <PanelSectionRow><Field label="Izvor TDP-a · dijagnostika" description={tdpStatus} /></PanelSectionRow>
        {info?.layout_spacing_supported && <PanelSectionRow>
          <ButtonItem layout="below" disabled={rendererBusy} onClick={() => { void verifyRenderer(); }}>
            Provjeri koristi li igra eksperimentalni renderer
          </ButtonItem>
        </PanelSectionRow>}
        {info?.layout_spacing_supported && <PanelSectionRow>
          <Field label="Stvarno učitana biblioteka" description={rendererStatus} />
        </PanelSectionRow>}

          <PanelSectionRow><Field label="Stanje konfiguracije" description={info?.config_path ?? "Nije učitano"} /></PanelSectionRow>
          <PanelSectionRow><Field label="TDP" description={info?.tdp_note ?? "TDP -- · nema potvrđenog očitanja."} /></PanelSectionRow>
          <PanelSectionRow><Field label="DRAW" description={info?.power_note ?? "Očitavanje ovisi o baterijskom senzoru."} /></PanelSectionRow>
          <PanelSectionRow><ButtonItem layout="below" disabled={!ready} onClick={() => { void refresh(); }}>Ponovno učitaj status</ButtonItem></PanelSectionRow>
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


