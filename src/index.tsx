import { useEffect, useRef, useState } from "react";
import { callable, definePlugin } from "@decky/api";
import {
  ButtonItem,
  ColorPickerModal,
  showModal,
  DialogButton,
  Focusable,
  Field,
  PanelSection,
  PanelSectionRow,
  SliderField,
  ToggleField,
} from "@decky/ui";
import { FaChartLine, FaCopy } from "react-icons/fa";

type Group = "fps" | "frametime" | "cpu" | "gpu" | "ram" | "vram" | "battery" | "draw" | "time";
type FontWeight = "light" | "regular" | "bold";
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
function hslStringToHex(value: string): string | null {
  const match = value.match(/^hsla?\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%(?:\s*,\s*[\d.]+)?\s*\)$/);
  if (!match) return null;
  const hue = Number(match[1]), saturation = Number(match[2]), lightness = Number(match[3]);
  if (![hue, saturation, lightness].every(Number.isFinite)) return null;
  const h = ((hue % 360) + 360) % 360, s = Math.max(0, Math.min(100, saturation)) / 100,
    l = Math.max(0, Math.min(100, lightness)) / 100;
  const a = s * Math.min(l, 1 - l);
  const channel = (n: number) => {
    const k = (n + h / 30) % 12;
    return Math.round(255 * (l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1))))
      .toString(16).padStart(2, "0").toUpperCase();
  };
  return channel(0) + channel(8) + channel(4);
}
type Settings = Record<Group, boolean> & {
  enabled: boolean; fontsize: number; opacity: number; power: boolean; tdp: boolean;
  sans: boolean; rounding: number; offset_x: number; offset_y: number; padding_y: number;
  padding_x: number; element_gap: number; table_gap: number; graph_width: number;
  inner_gap: number; inline_metrics: boolean; fps_bold: boolean; font_weight: FontWeight; order: Group[];
  metrics: Record<string, boolean>;
  colors: ColorSettings;
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
  colors: {...defaultColors},
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
  const [expanded, setExpanded] = useState<Group | null>(null);
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

  const openColorPicker = (key: ColorKey, label: string) => {
    const [h, sat, light] = rgbToHsl(current.current.colors[key] ?? defaultColors[key]);
    const dialog = showModal(<ColorPickerModal
      title={label} defaultH={h} defaultS={sat} defaultL={light} defaultA={1}
      closeModal={() => dialog.Close()}
      onConfirm={(hsl: string) => {
        const hex = hslStringToHex(hsl);
        if (hex) update({colors: {...current.current.colors, [key]: hex}});
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
      <PanelSection title="Claw Metrics · v0.2.4-test.7">
        {toggle("enabled", "Uključi prikaz")}
        <PanelSectionRow><Field label="Status" description={status} /></PanelSectionRow>
      </PanelSection>
      <PanelSection title="ELEMENTS">
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
                <DialogButton disabled={!ready} onClick={() => setExpanded(open ? null : key)}
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
        <PanelSectionRow><Field label="TDP · Panel de Control" description="Očitanje primijenjenog limita još nije dostupno." disabled /></PanelSectionRow>
      </PanelSection>
      <PanelSection title="APPEARANCE">
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below" onClick={() => update({sans: true, fontsize: 18, opacity: 80, rounding: 10, offset_x: 8, offset_y: 8, padding_y: 8})}>Primijeni izgled prijedloga</ButtonItem></PanelSectionRow>
        {toggle("sans", "Sans-serif font")}
        <PanelSectionRow><Field label="Font" description={settings.sans
          ? (info?.condensed_fonts_ready
              ? "Barlow Semi Condensed · Light / Regular / Bold dostupni"
              : "Preuzimanje iz službenog Google Fonts izvora nije uspjelo ili još traje. Privremeno ostaje postojeći Claw Sans. Ponovno pokreni Decky kada budeš online.")
          : "MangoHud zadani font"} /></PanelSectionRow>
        <PanelSectionRow><Field label="Debljina fonta" description="Odaberi Light za tanji izgled, Regular za čitljivost ili Bold za naglašenu cijelu traku. FPS može zasebno biti Bold. Promjena fonta može zahtijevati ponovno pokretanje igre." /></PanelSectionRow>
        <PanelSectionRow>
          <div style={{display: "flex", gap: 6, flexWrap: "wrap"}}>
            {(["light", "regular", "bold"] as FontWeight[]).map(weight => (
              <DialogButton key={weight} disabled={!ready || !settings.sans} onClick={() => update({font_weight: weight})}
                style={{minWidth: 84, padding: "8px", background: settings.font_weight === weight ? "#22678d" : "#303e4f",
                  fontWeight: weight === "bold" ? 700 : weight === "light" ? 300 : 400}}>
                {weight === "light" ? "Light" : weight === "regular" ? "Regular" : "Bold"}
              </DialogButton>
            ))}
          </div>
        </PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" disabled={!ready} onClick={() => {void refresh();}}>
          Provjeri dostupnost fonta
        </ButtonItem></PanelSectionRow>
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
        <PanelSectionRow><ToggleField label="FPS broj Bold (stvarni font kad je dostupan)"
          checked={settings.fps_bold} disabled={!ready || !info?.layout_spacing_supported}
          onChange={(v: boolean) => update({fps_bold: v})} /></PanelSectionRow>
        <PanelSectionRow><SliderField label="Širina frametime grafa (px)" value={settings.graph_width} min={80} max={200} step={5} showValue
          disabled={!ready || !info?.layout_spacing_supported} onChange={(value: number) => update({graph_width: value})} /></PanelSectionRow>
        <PanelSectionRow><ButtonItem disabled={!ready || !info?.layout_spacing_supported} layout="below"
          onClick={() => update({padding_x: 5, element_gap: 4, table_gap: 2, graph_width: 110, inner_gap: 4, inline_metrics: true, fps_bold: true})}>
          Test: kompaktan prikaz (graf 110px, razmaci 4/2px)
        </ButtonItem></PanelSectionRow>
        <PanelSectionRow><Field label="Položaj i padding" description="Ručni položaj od lijevog i gornjeg ruba. Padding povećava razmak gore/dolje; bočni razmak u standardnom MangoHudu je fiksan. Ako je red širi od igre, smanji font ili odaberi kompaktan raspored — pomak ne smanjuje širinu." /></PanelSectionRow>
        <PanelSectionRow><Field label="Napomena" description="Broj uključenih podataka i font moraju stati u širinu igre. Ako red izlazi iz ekrana, smanji tekst ili isključi dodatne senzore. FPS se ne može zasebno povećati u ovom MangoHud rendereru." /></PanelSectionRow>
      </PanelSection>
      <PanelSection title="BOJE / COLORS">
        <PanelSectionRow><Field label="Birač boja" description="Odaberi element i prilagodi nijansu, zasićenost i svjetlinu kontrolerom. Nazivi kategorija, brojčane vrijednosti i separatori imaju odvojene boje. Promjene se spremaju za oba MangoHud profila." /></PanelSectionRow>
        {colorRows.map(([key, label]) => (
          <PanelSectionRow key={key}>
            <ButtonItem layout="below" disabled={!ready} onClick={() => openColorPicker(key, label)}>
              <span style={{display: "inline-flex", alignItems: "center", gap: 9}}>
                <span style={{display: "inline-block", width: 22, height: 22, borderRadius: 5,
                  border: "1px solid #a9b6c8", background: "#" + (settings.colors?.[key] ?? defaultColors[key])}} />
                <span>{label}</span>
                <span style={{opacity: 0.7, fontSize: 12}}>#{settings.colors?.[key] ?? defaultColors[key]}</span>
              </span>
            </ButtonItem>
          </PanelSectionRow>
        ))}
        <PanelSectionRow><ButtonItem layout="below" disabled={!ready} onClick={() => update({colors: {...defaultColors}})}>
          Vrati zadane boje
        </ButtonItem></PanelSectionRow>
      </PanelSection>
      <PanelSection title="ACTIVATION">
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
        {info?.layout_spacing_supported && <PanelSectionRow>
          <ButtonItem layout="below" disabled={rendererBusy} onClick={() => { void verifyRenderer(); }}>
            Provjeri koristi li igra eksperimentalni renderer
          </ButtonItem>
        </PanelSectionRow>}
        {info?.layout_spacing_supported && <PanelSectionRow>
          <Field label="Stvarno učitana biblioteka" description={rendererStatus} />
        </PanelSectionRow>}
        <PanelSectionRow><Field label="Siguran povratak"
          description="Ako testna komanda blokira pokretanje igre, vrati staru launch komandu iz 0.2.3. Ne mijenja SteamOS ni Panel de Control." /></PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" onClick={() => { void refresh(); }}>Provjeri vezu / ponovno učitaj</ButtonItem></PanelSectionRow>
        <PanelSectionRow><Field label="Primjena" description="Nakon spremanja ponovno pokreni igru. Launch komanda ostaje ista. Sistemski Steam overlay drži isključenim." /></PanelSectionRow>
      </PanelSection>
    </>
  );
}

export default definePlugin(() => ({
  name: "Claw Metrics",
  titleView: <div>Claw Metrics</div>,
  content: <Content />,
  icon: <FaChartLine />,
}));
