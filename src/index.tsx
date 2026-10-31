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
  ToggleField,
} from "@decky/ui";
import { FaChartLine, FaChartBar, FaDesktop, FaThLarge, FaPalette, FaPlayCircle, FaSlidersH, FaChevronDown, FaChevronRight, FaCopy } from "react-icons/fa";

type Group = "fps" | "frametime" | "cpu" | "gpu" | "ram" | "vram" | "battery" | "draw" | "time";
type FontWeight = "light" | "regular" | "semibold" | "bold";
type WeightSelection = "inherit" | FontWeight;
type StyleCategory = "global" | "fps" | "cpu" | "gpu" | "ram" | "vram" | "battery" | "time";
type TokenKey = "fps.label" | "fps.value" | "fps.ms" | "cpu.label" | "cpu.load" | "cpu.temp" | "cpu.clock" | "cpu.power" | "gpu.label" | "gpu.load" | "gpu.temp" | "gpu.clock" | "gpu.power" | "gpu.junction" | "gpu.fan" | "gpu.voltage" | "ram.label" | "ram.value" | "vram.label" | "vram.value" | "vram.temp" | "vram.clock" | "battery.label" | "battery.value" | "battery.time" | "battery.power" | "time.value";
type MetricToken = {key: TokenKey; label: string; defaultColor: ColorKey};
const tokenGroups: Record<Exclude<StyleCategory, "global">, MetricToken[]> = {
  fps: [{key:"fps.label", label:"FPS naziv", defaultColor:"fps_label"}, {key:"fps.value", label:"FPS broj", defaultColor:"fps_value"}, {key:"fps.ms", label:"Frametime (ms)", defaultColor:"text"}],
  cpu: [{key:"cpu.label", label:"CPU naziv", defaultColor:"cpu"}, {key:"cpu.load", label:"Opterećenje (%)", defaultColor:"text"}, {key:"cpu.temp", label:"Temperatura (°C)", defaultColor:"text"}, {key:"cpu.clock", label:"Takt (MHz)", defaultColor:"text"}, {key:"cpu.power", label:"Potrošnja (W)", defaultColor:"text"}],
  gpu: [{key:"gpu.label", label:"GPU naziv", defaultColor:"gpu"}, {key:"gpu.load", label:"Opterećenje (%)", defaultColor:"text"}, {key:"gpu.temp", label:"Temperatura (°C)", defaultColor:"text"}, {key:"gpu.clock", label:"Takt (MHz)", defaultColor:"text"}, {key:"gpu.power", label:"Potrošnja (W)", defaultColor:"text"}, {key:"gpu.junction", label:"Junction temperatura", defaultColor:"text"}, {key:"gpu.fan", label:"Ventilator", defaultColor:"text"}, {key:"gpu.voltage", label:"Napon", defaultColor:"text"}],
  ram: [{key:"ram.label", label:"RAM naziv", defaultColor:"ram"}, {key:"ram.value", label:"Zauzeće (GiB)", defaultColor:"text"}],
  vram: [{key:"vram.label", label:"VRAM naziv", defaultColor:"vram"}, {key:"vram.value", label:"Zauzeće (GiB)", defaultColor:"text"}, {key:"vram.temp", label:"Temperatura memorije", defaultColor:"text"}, {key:"vram.clock", label:"Takt memorije", defaultColor:"text"}],
  battery: [{key:"battery.label", label:"BATT naziv", defaultColor:"battery"}, {key:"battery.value", label:"Baterija (%) / ikona", defaultColor:"text"}, {key:"battery.time", label:"Preostalo vrijeme", defaultColor:"text"}, {key:"battery.power", label:"Baterija (W)", defaultColor:"text"}],
  time: [{key:"time.value", label:"Sat", defaultColor:"text"}],
};
const weightOptions: WeightSelection[] = ["inherit", "light", "regular", "semibold", "bold"];
const weightLabel: Record<WeightSelection, string> = {
  inherit: "Global", light: "Light", regular: "Regular", semibold: "SemiBold", bold: "Bold",
};
const styleTabs: [StyleCategory,string][] = [
  ["global","Global"],["fps","FPS"],["cpu","CPU"],["gpu","GPU"],
  ["ram","RAM"],["vram","VRAM"],["battery","Battery"],["time","Clock"],
];
type SavedStyle = {
  colors: ColorSettings; font_weight: FontWeight; fps_bold: boolean;
  token_weights: Partial<Record<TokenKey, FontWeight>>;
  token_colors: Partial<Record<TokenKey, string>>;
};

type ColorKey = "text" | "separator" | "fps_label" | "fps_value" | "cpu" | "gpu" | "ram" | "vram" | "battery" | "graph";
type ColorSettings = Record<ColorKey, string>;
const defaultColors: ColorSettings = {
  text: "F0F2F5", separator: "777C87", fps_label: "30E5A0", fps_value: "30E5A0",
  cpu: "37C9EF", gpu: "8BDA62", ram: "B077DF", vram: "D76AB8",
  battery: "30E5A0", graph: "30E5A0",
};
const colorRows: [ColorKey, string][] = [
  ["text", "Vrijednosti, sat i DRAW"], ["separator", "Separatori između grupa"],
  ["fps_label", "FPS naziv"], ["fps_value", "FPS broj"],
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
type Settings = Record<Group, boolean> & {
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
const order: Group[] = ["fps", "frametime", "cpu", "gpu", "ram", "vram", "battery", "draw", "time"];
const groups: Record<Group, {label: string; color: string; metrics: [string, string][]; always?: string; note?: string}> = {
  fps: {label: "FPS", color: "#30e5a0", metrics: [], always: "FPS", note: "MangoHud koristi istu glavnu veličinu fonta za FPS i ostale vrijednosti."},
  frametime: {label: "Frametime", color: "#30e5a0", metrics: [["fps_ms", "Frametime (ms)"], ["graph", "Frametime graph"]], note: "Broj u ms prati FPS blok; strelice premještaju graf. Za ms uključi i FPS."},
  gpu: {label: "GPU", color: "#8bda62", always: "GPU load", metrics: [["gpu_temp", "GPU temp"], ["gpu_junction_temp", "GPU junction temp"], ["gpu_core_clock", "GPU clock"], ["gpu_mem_clock", "VRAM clock"], ["gpu_mem_temp", "VRAM temp"], ["gpu_power", "GPU watts"], ["gpu_fan", "GPU fan"], ["gpu_voltage", "GPU voltage"]], note: "VRAM clock/temp prikazuju se u VRAM bloku i traže uključen VRAM. Ostali senzori ovise o dostupnosti na Z2 Extremeu."},
  cpu: {label: "CPU", color: "#37c9ef", always: "CPU load", metrics: [["cpu_temp", "CPU temp"], ["cpu_mhz", "CPU clock"], ["cpu_power", "CPU watts"]]},
  ram: {label: "RAM", color: "#b077df", always: "RAM usage", metrics: []},
  vram: {label: "VRAM", color: "#d76ab8", always: "VRAM usage", metrics: [], note: "MangoHud za VRAM koristi podatke GPU bloka; uključi i GPU."},
  battery: {label: "Battery", color: "#30e5a0", always: "Battery level", metrics: [["battery_icon", "Battery icon (replaces %)"], ["battery_time", "Remaining time"]], note: "Ikona i postotak su alternativni načini prikaza u ovom MangoHud rendereru."},
  draw: {label: "DRAW", color: "#ee6279", metrics: [], always: "Battery discharge watts", note: "Ukupno pražnjenje baterije. Na punjaču ili bez senzora prikazuje DRAW --, a ne izmišljenu potrošnju."},
  time: {label: "Clock", color: "#f0f2f5", metrics: [], always: "Clock · 24 h"},
};

type Info = {
  layout_spacing_supported: boolean;
  experimental_launch_option: string;
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
    <div data-section={id} style={{
      background: "#111e30",
      border: open ? "1px solid #04b7ed" : "1px solid #395579",
      borderLeft: open ? "4px solid #08d3fa" : "4px solid #8b65e7",
      borderRadius: 12,
      overflow: "hidden",
      marginBottom: 10,
      boxShadow: open ? "0 0 15px #0285ca55" : "none",
    }}>
      <DialogButton onClick={onToggle} style={{
        width: "100%", display: "flex", alignItems: "center",
        textAlign: "left", margin: 0, padding: "12px 10px",
        background: open ? "#073858" : "#14243b",
        border: "none", borderRadius: 0, minHeight: 66, whiteSpace: "normal",
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
  const [rendererStatus, setRendererStatus] = useState("Nije provjereno. Pokreni igru za test.");
  const [rendererBusy, setRendererBusy] = useState(false);
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
  const copyLaunchCommand = async (experimental = false) => {
    const command = experimental ? info?.experimental_launch_option : info?.launch_option;
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
      title={token.label} hex={hex} closeModal={() => dialog.Close()}
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
      colors: {...d.colors}, font_weight: d.font_weight, fps_bold: d.fps_bold,
      token_weights: {...d.token_weights}, token_colors: {...d.token_colors},
    };
    update({style_presets: {...d.style_presets, [slot]: preset}});
  };
  const loadPreset = (slot: string) => {
    const preset = current.current.style_presets?.[slot];
    if (!preset) return;
    update({colors: {...preset.colors}, font_weight: preset.font_weight,
      fps_bold: preset.fps_bold, token_weights: {...preset.token_weights},
      token_colors: {...preset.token_colors}});
  };

  const openColorPicker = (key: ColorKey, label: string) => {
    const dialog = showModal(<OpaqueColorPicker
      title={label} hex={current.current.colors[key] ?? defaultColors[key]}
      closeModal={() => dialog.Close()}
      onConfirm={(hex: string) => update({colors: {...current.current.colors, [key]: hex}})}
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
      <PanelSection title="Claw Metrics · v0.2.4-test.10">
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
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below" onClick={() => update({sans: true, fontsize: 18, opacity: 80, rounding: 10, offset_x: 8, offset_y: 8, padding_y: 8})}>Primijeni izgled prijedloga</ButtonItem></PanelSectionRow>
        {([ ["fontsize", "Veličina teksta", 12, 28, 1], ["opacity", "Pozadina (%)", 0, 100, 5],
          ["rounding", "Zaobljenost rubova", 0, 20, 1], ["padding_y", "Dodatni padding gore/dolje (px)", 0, 24, 1],
          ["offset_x", "X — lijevo/desno (px)", -1920, 1920, 1], ["offset_y", "Y — gore/dolje (px)", -1200, 1200, 1] ] as const).map(([key, label, min, max, step]) =>
          <PanelSectionRow key={key}><SliderField label={label} value={settings[key]} min={min} max={max} step={step} showValue disabled={!ready}
            onChange={(value: number) => update({[key]: value})} /></PanelSectionRow>)}
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below" onClick={() => update({offset_x: 8, offset_y: 8})}>Vrati položaj na X=8, Y=8</ButtonItem></PanelSectionRow>
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below" onClick={() => update({fontsize: 12, offset_x: 8, offset_y: 8, padding_y: 4, metrics: {...current.current.metrics, cpu_mhz: false, gpu_core_clock: false}})}>Uži red: manji font i bez MHz</ButtonItem></PanelSectionRow>
        <PanelSectionRow><Field label="Bočni padding i razmak" description={info?.layout_spacing_supported
          ? "Biblioteka je instalirana. Ove kontrole rade SAMO uz testnu Vulkan launch komandu iz ACTIVATION, ne uz običnu komandu. Nakon promjene ponovno pokreni igru. Oznaka FPS* potvrđuje da se testna konfiguracija učitala."
          : "U stock MangoHud 0.8.1 bočni padding (5 px) i razmak elemenata (8 px) nisu podesivi. Kontrole su zaključane dok ne provjerimo siguran renderer, bez promjene postojeće verzije."} /></PanelSectionRow>
        <PanelSectionRow><SliderField label="Padding lijevo i desno (px)" value={settings.padding_x} min={0} max={24} step={1} showValue
          disabled={!ready || !info?.layout_spacing_supported} onChange={(value: number) => update({padding_x: value})} /></PanelSectionRow>
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
        <PanelSectionRow><ButtonItem disabled={!ready || !info?.layout_spacing_supported} layout="below"
          onClick={() => update({padding_x: 5, element_gap: 4, table_gap: 2, graph_width: 110, inner_gap: 4, inline_metrics: true, fps_bold: true})}>
          Test: kompaktan prikaz (graf 110px, razmaci 4/2px)
        </ButtonItem></PanelSectionRow>
        <PanelSectionRow><Field label="Položaj i padding" description="Ručni položaj od lijevog i gornjeg ruba. Padding povećava razmak gore/dolje; bočni razmak u standardnom MangoHudu je fiksan. Ako je red širi od igre, smanji font ili odaberi kompaktan raspored — pomak ne smanjuje širinu." /></PanelSectionRow>
        <PanelSectionRow><Field label="Napomena" description="Broj uključenih podataka i font moraju stati u širinu igre. Ako red izlazi iz ekrana, smanji tekst ili isključi dodatne senzore. FPS se ne može zasebno povećati u ovom MangoHud rendereru." /></PanelSectionRow>

        </AccordionCard>
        <AccordionCard id="metrics" title="Metrics" subtitle="Prikazane metrike i njihov redoslijed"
          icon={<FaChartBar />} open={openSection === "metrics"} onToggle={() => toggleSection("metrics")}>
        <PanelSectionRow><div style={{fontSize: 13, color: "#b8c7d5", marginBottom: 12}}>
          Reorder with the arrows. Items with a chevron have their own settings.
        </div></PanelSectionRow>
        {visible.map((key, index) => {
          const group = groups[key];
          const open = expanded === key;
          const total = group.metrics.length + (group.always ? 1 : 0);
          const count = group.metrics.filter(([id]) => settings.metrics[id]).length + (group.always ? 1 : 0);
          return <PanelSectionRow key={key}>
            <div style={{background: "#17212ee8", borderRadius: 10, marginBottom: 6, overflow: "hidden", border: open ? "1px solid #18adf1" : "1px solid #334152"}}>
              <Focusable style={{display: "flex", alignItems: "center", gap: 4, padding: 5}} flow-children="row">
                <DialogButton disabled={!ready} onClick={() => expandMetric(open ? null : key)}
                  style={{flex: 1, minWidth: 0, margin: 0, padding: "8px 5px", textAlign: "left", background: "transparent", color: "#f2f7fc", fontSize: 15}}>
                  <span style={{color: "#42bfff", marginRight: 7}}>{open ? "⌄" : "›"}</span>
                  <span style={{fontWeight: 700}}>{group.label}</span>
                  {total > 1 && <span style={{float: "right", color: "#9bbad0", fontSize: 12}}>{count}/{total}</span>}
                </DialogButton>
                <DialogButton style={smallButton} disabled={!ready || index === 0} onClick={() => move(key, -1)}><span title="Move up">⌃</span></DialogButton>
                <DialogButton style={smallButton} disabled={!ready || index === visible.length - 1} onClick={() => move(key, 1)}><span title="Move down">⌄</span></DialogButton>
                <DialogButton style={smallButton} disabled={!ready} onClick={() => update({[key]: false})}><span title="Hide element">×</span></DialogButton>
              </Focusable>
              {open && <div style={{borderLeft: `3px solid ${group.color}`, margin: "4px 9px 12px", paddingLeft: 8}}>
                <div style={{fontSize: 12, lineHeight: 1.5, color: "#b4c9d8", margin: "8px 0"}}>
                  Toggle the metrics in this block; they show together on one row.
                </div>
                <div style={{fontSize: 12, color: "#70cdf7", margin: "12px 0 6px", letterSpacing: 0.5}}>GROUP METRICS</div>
                {group.always && <Field label={group.always} padding="compact"><span style={{fontSize: 11, color: "#4acbff", background: "#123e59", borderRadius: 12, padding: "3px 7px"}}>Always</span></Field>}
                {group.metrics.map(([id, label]) => <ToggleField key={id} label={label} checked={settings.metrics[id]} disabled={!ready}
                  onChange={(checked: boolean) => metric(id, checked)} />)}
                {group.note && <div style={{fontSize: 11, lineHeight: 1.5, color: "#a6b6c6", marginTop: 10}}>{group.note}</div>}
              </div>}
            </div>
          </PanelSectionRow>;
        })}
        {hidden.length > 0 && <PanelSectionRow><Field label="ADD ELEMENT" description="Vrati skrivenu grupu u red." /></PanelSectionRow>}
        {hidden.map(key => <PanelSectionRow key={key}><ButtonItem disabled={!ready} layout="below" onClick={() => update({[key]: true})}>+ {groups[key].label}</ButtonItem></PanelSectionRow>)}


        </AccordionCard>
        <AccordionCard id="colors" title="Colors & Font" subtitle="Paleta, separatori, Light / Regular / SemiBold / Bold"
          icon={<FaPalette />} open={openSection === "colors"} onToggle={() => toggleSection("colors")}>
          <PanelSectionRow><Field label="BOJE & FONT"
            description="Globalne postavke ili zasebne postavke naziva i vrijednosti svake metrike." /></PanelSectionRow>
          <div style={{display:"flex",gap:5,flexWrap:"wrap",padding:"5px 0 12px"}}>
            {styleTabs.map(([key,name])=><DialogButton key={key} disabled={!ready}
              onClick={()=>chooseStyleCategory(key)}
              style={{minWidth:78,margin:0,padding:8,
                background:styleCategory===key?"#087daf":"#263d5b",
                border:styleCategory===key?"1px solid #29dcff":"1px solid #476687"}}>
              {name}
            </DialogButton>)}
          </div>
          {styleCategory==="global" ? <>
          <PanelSectionRow><Field label="GLOBALNO" description="Font i zadane boje koje ostale vrijednosti nasljeđuju." /></PanelSectionRow>
          {toggle("sans", "Sans-serif font")}
          <PanelSectionRow><Field label="Barlow Semi Condensed" description={
            info?.condensed_fonts_ready ? "Light / Regular / SemiBold / Bold učitani."
              : "Fontovi nisu dostupni; koristi se Claw Sans."} /></PanelSectionRow>
          <PanelSectionRow><Field label="Osnovna debljina" description="Promjena osnovnog fonta može zahtijevati ponovno pokretanje igre." /></PanelSectionRow>
          <PanelSectionRow><div style={{display:"flex",gap:5,flexWrap:"wrap"}}>
            {(["light","regular","semibold","bold"] as FontWeight[]).map(weight=>
              <DialogButton key={weight} disabled={!ready || !settings.sans}
                onClick={()=>update({font_weight:weight})}
                style={{minWidth:82,margin:0,background:settings.font_weight===weight?"#096e9e":"#23364c",
                  fontWeight:weight==="bold"?700:weight==="semibold"?600:weight==="light"?300:400}}>
                {weightLabel[weight]}
              </DialogButton>)}
          </div></PanelSectionRow>
          <PanelSectionRow><ToggleField label="FPS Bold (ako nije ručno postavljen)"
            checked={settings.fps_bold} disabled={!ready} onChange={v=>update({fps_bold:v})}/></PanelSectionRow>
          {colorRows.map(([key,label])=><PanelSectionRow key={key}>
            <ButtonItem layout="below" disabled={!ready} onClick={()=>openColorPicker(key,label)}>
              <span style={{display:"inline-flex",alignItems:"center",gap:8}}>
                <span style={{width:20,height:20,borderRadius:5,background:"#"+(settings.colors[key]??defaultColors[key]),border:"1px solid #b8c7d9"}}/>
                {label}
              </span>
            </ButtonItem>
          </PanelSectionRow>)}
          <PanelSectionRow><ButtonItem disabled={!ready} layout="below"
            onClick={()=>update({colors:{...defaultColors}})}>Vrati zadane boje</ButtonItem></PanelSectionRow>
          <PanelSectionRow><Field label="MOJI STILOVI"
            description="Tri spremišta za vlastite kombinacije fontova i boja. Spremanje ne mijenja postojeću konfiguraciju." /></PanelSectionRow>
          {(["1","2","3"] as const).map(slot=><PanelSectionRow key={slot}>
            <div style={{display:"flex",gap:6}}>
              <DialogButton disabled={!ready} onClick={()=>savePreset(slot)}
                style={{flex:1,margin:0}}>Spremi {slot}</DialogButton>
              <DialogButton disabled={!ready||!settings.style_presets?.[slot]}
                onClick={()=>loadPreset(slot)} style={{flex:1,margin:0}}>Učitaj {slot}</DialogButton>
            </div>
          </PanelSectionRow>)}
          </> : <>
          <PanelSectionRow><Field label={styleCategory.toUpperCase()}
            description="Svaka stavka ima svoju boju i težinu fonta. Global znači naslijedi osnovnu postavku." /></PanelSectionRow>
          {tokenGroups[styleCategory as Exclude<StyleCategory,"global">].map(token=>(
            <div key={token.key} style={{padding:"8px 4px",marginBottom:8,
              background:"#1a2c43",border:"1px solid #375878",borderRadius:8}}>
              <div style={{fontWeight:700,fontSize:13,marginBottom:5}}>{token.label}</div>
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
          <Field label="EKSPERIMENTALNI prikaz – samo Vulkan 64-bit"
            description={info.experimental_launch_option} />
        </PanelSectionRow>}
        {info?.layout_spacing_supported && <PanelSectionRow>
          <ButtonItem layout="below" onClick={() => { void copyLaunchCommand(true); }}>
            <FaCopy style={{marginRight: 8}} /> Kopiraj testnu komandu (Vulkan 64-bit)
          </ButtonItem>
        </PanelSectionRow>}
        <PanelSectionRow><Field label="Siguran povratak"
          description="Ako testna komanda blokira pokretanje igre, vrati staru launch komandu iz 0.2.3. Ne mijenja SteamOS ni Panel de Control." /></PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" onClick={() => { void refresh(); }}>Provjeri vezu / ponovno učitaj</ButtonItem></PanelSectionRow>
        <PanelSectionRow><Field label="Primjena" description="Nakon spremanja ponovno pokreni igru. Launch komanda ostaje ista. Sistemski Steam overlay drži isključenim." /></PanelSectionRow>

        </AccordionCard>
        <AccordionCard id="advanced" title="Advanced" subtitle="Dijagnostika, senzori i tehničke informacije"
          icon={<FaSlidersH />} open={openSection === "advanced"} onToggle={() => toggleSection("advanced")}>
        <PanelSectionRow><Field label="TDP · Panel de Control" description="Očitanje primijenjenog limita još nije dostupno." disabled /></PanelSectionRow>
        {info?.layout_spacing_supported && <PanelSectionRow>
          <ButtonItem layout="below" disabled={rendererBusy} onClick={() => { void verifyRenderer(); }}>
            Provjeri koristi li igra eksperimentalni renderer
          </ButtonItem>
        </PanelSectionRow>}
        {info?.layout_spacing_supported && <PanelSectionRow>
          <Field label="Stvarno učitana biblioteka" description={rendererStatus} />
        </PanelSectionRow>}

          <PanelSectionRow><Field label="Stanje konfiguracije" description={info?.config_path ?? "Nije učitano"} /></PanelSectionRow>
          <PanelSectionRow><Field label="TDP" description={info?.tdp_note ?? "Nije dostupno očitanje Panel de Control limita."} /></PanelSectionRow>
          <PanelSectionRow><Field label="DRAW" description={info?.power_note ?? "Očitavanje ovisi o baterijskom senzoru."} /></PanelSectionRow>
          <PanelSectionRow><ButtonItem layout="below" disabled={!ready} onClick={() => { void refresh(); }}>Ponovno učitaj status</ButtonItem></PanelSectionRow>
        </AccordionCard>
      </div>
    </>
  );
}

export default definePlugin(() => ({
  name: "Claw Metrics",
  titleView: <div>Claw Metrics</div>,
  content: <Content />,
  icon: <FaChartLine />,
}));
