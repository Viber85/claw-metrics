import { useEffect, useRef, useState } from "react";
import { callable, definePlugin } from "@decky/api";
import {
  ButtonItem,
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
type Settings = Record<Group, boolean> & {
  enabled: boolean; fontsize: number; opacity: number; power: boolean; tdp: boolean;
  renderer: boolean; center: boolean; auto_fit: boolean; fps_fontsize: number; padding_x: number;
  sans: boolean; rounding: number; offset_x: number; offset_y: number; padding_y: number; order: Group[];
  metrics: Record<string, boolean>;
};
const order: Group[] = ["fps", "frametime", "cpu", "gpu", "ram", "vram", "battery", "draw", "time"];
const groups: Record<Group, {label: string; color: string; metrics: [string, string][]; always?: string; note?: string}> = {
  fps: {label: "FPS", color: "#30e5a0", metrics: [], always: "FPS", note: "Neovisna veličina FPS broja dostupna je uz uključeni Claw renderer."},
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
  renderer_ready: boolean;
  renderer_note: string;
  stock_launch_option: string;
  font_path: string;
  font_ready: boolean;
  config_readable: boolean;
  config_path: string;
  launch_option: string;
  tdp_note: string;
  power_note: string;
};

const defaults: Settings = {
  enabled: true, fontsize: 18, opacity: 80, fps: true, frametime: true,
  cpu: true, gpu: true, ram: true, vram: true, battery: true, draw: true,
  power: true, time: true, tdp: false, renderer: false, center: true, auto_fit: true, fps_fontsize: 28, padding_x: 12, sans: true, rounding: 10, offset_x: 8, offset_y: 8, padding_y: 8, order,
  metrics: {fps_ms: true, graph: true, cpu_temp: true, cpu_mhz: true, cpu_power: true,
    gpu_temp: true, gpu_junction_temp: false, gpu_core_clock: true, gpu_mem_clock: false,
    gpu_mem_temp: false, gpu_power: true, gpu_fan: false, gpu_voltage: false,
    battery_icon: false, battery_time: true},
};

// Callable methods are provided by the Decky Python backend.
const load = callable<[], Settings>("get_settings");
const save = callable<[Settings], { ok: boolean; config_path: string; info: Info }>("save_settings");
const getInfo = callable<[], Info>("get_info");

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
        if (id === revision.current) {
          setInfo(result.info);
          setStatus("Spremljeno. Ponovno pokreni igru za sigurnu primjenu.");
        }
      } catch (error) {
        if (id === revision.current) setStatus("Greška pri spremanju: " + String(error));
      }
    });
  };

  // Copy synchronously from a button click: SteamOS Game Mode often does
  // not expose the modern Clipboard API to Decky panels.
  const copyLaunchCommand = async () => {
    const command = info?.launch_option;
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

  const toggle = (key: "enabled" | "sans" | "renderer" | "center" | "auto_fit", label: string, unavailable = false) => (
    <PanelSectionRow><ToggleField label={label} checked={settings[key]} disabled={!ready || unavailable}
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
      <PanelSection title="Claw Metrics · v0.3.0">
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
                {key === "fps" && <SliderField label="FPS broj — veličina fonta (px)" value={settings.fps_fontsize} min={12} max={64} step={1} showValue disabled={!ready || !settings.renderer || !info?.renderer_ready}
                  onChange={(value: number) => update({fps_fontsize: value})} />}
                {group.note && <div style={{fontSize: 11, lineHeight: 1.5, color: "#a6b6c6", marginTop: 10}}>{group.note}</div>}
              </div>}
            </div>
          </PanelSectionRow>;
        })}
        {hidden.length > 0 && <PanelSectionRow><Field label="ADD ELEMENT" description="Vrati skrivenu grupu u red." /></PanelSectionRow>}
        {hidden.map(key => <PanelSectionRow key={key}><ButtonItem disabled={!ready} layout="below" onClick={() => update({[key]: true})}>+ {groups[key].label}</ButtonItem></PanelSectionRow>)}
        <PanelSectionRow><Field label="TDP · Panel de Control" description="Očitanje primijenjenog limita još nije dostupno." disabled /></PanelSectionRow>
      </PanelSection>
      <PanelSection title="CLAW RENDERER">
        {toggle("renderer", "Koristi Claw renderer", !info?.renderer_ready && !settings.renderer)}
        <PanelSectionRow><Field label="Nativni paket" description={info?.renderer_note ?? "Učitavanje…"} /></PanelSectionRow>
        <PanelSectionRow><Field label="Aktivacija u igri" description="Za prvi prelazak kopiraj NOVU launch naredbu iz odjeljka ACTIVATION i ponovno pokreni igru. Prekidač ne mijenja Steam Launch Options automatski. Sistemski MangoHud ostaje netaknut." /></PanelSectionRow>
        <PanelSectionRow><ButtonItem disabled={!ready || !info?.renderer_ready} layout="below" onClick={() => update({renderer: true, sans: true, center: true, auto_fit: true, fontsize: 18, fps_fontsize: 28, padding_x: 12, padding_y: 8, offset_x: 0, offset_y: 8, opacity: 80, rounding: 12})}>Claw renderer + izgled prijedloga</ButtonItem></PanelSectionRow>
      </PanelSection>
      <PanelSection title="APPEARANCE">
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below" onClick={() => update({sans: true, fontsize: 18, opacity: 80, rounding: 10, offset_x: settings.renderer && settings.center ? 0 : 8, offset_y: 8, padding_y: 8, padding_x: 12, fps_fontsize: 28})}>Primijeni izgled prijedloga</ButtonItem></PanelSectionRow>
        {toggle("sans", "Sans-serif font")}
        {toggle("center", "Automatsko centriranje", !settings.renderer || !info?.renderer_ready)}
        {toggle("auto_fit", "Prilagodi red širini igre", !settings.renderer || !info?.renderer_ready)}
        <PanelSectionRow><SliderField label="Padding lijevo/desno (px)" value={settings.padding_x} min={0} max={40} step={1} showValue disabled={!ready || !settings.renderer || !info?.renderer_ready}
          onChange={(value: number) => update({padding_x: value})} /></PanelSectionRow>
        <PanelSectionRow><Field label="Font" description={settings.sans ? (info?.font_ready ? "Claw Sans · provjeren i spremljen uz profil" : "Font nije spreman — ponovno pokreni Decky Loader") : "MangoHud zadani font"} /></PanelSectionRow>
        {([ ["fontsize", "Veličina teksta", 12, 28, 1], ["opacity", "Pozadina (%)", 0, 100, 5],
          ["rounding", "Zaobljenost rubova", 0, 20, 1], ["padding_y", settings.renderer ? "Padding gore/dolje (px)" : "Dodatni padding gore/dolje (px)", 0, 40, 1],
          ["offset_x", settings.renderer && settings.center ? "X — pomak od centra (px)" : "X — lijevo/desno (px)", -1920, 1920, 1], ["offset_y", "Y — gore/dolje (px)", -1200, 1200, 1] ] as const).map(([key, label, min, max, step]) =>
          <PanelSectionRow key={key}><SliderField label={label} value={settings[key]} min={min} max={max} step={step} showValue disabled={!ready}
            onChange={(value: number) => update({[key]: value})} /></PanelSectionRow>)}
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below" onClick={() => update({offset_x: settings.renderer && settings.center ? 0 : 8, offset_y: 8})}>Vrati položaj</ButtonItem></PanelSectionRow>
        <PanelSectionRow><ButtonItem disabled={!ready} layout="below" onClick={() => update({fontsize: 12, offset_x: 8, offset_y: 8, padding_y: 4, metrics: {...current.current.metrics, cpu_mhz: false, gpu_core_clock: false}})}>Uži red: manji font i bez MHz</ButtonItem></PanelSectionRow>
        <PanelSectionRow><Field label="Položaj i padding" description={settings.renderer ? "Padding djeluje na sve četiri strane. Uz centriranje X pomiče red od centra. Automatsko prilagođavanje smanjuje cijeli red samo kada ne stane u širinu igre." : "Stock MangoHud: ručni položaj od lijevog i gornjeg ruba, podesiv samo vertikalni padding. Za bočni padding, centriranje i FPS font uključi Claw renderer."} /></PanelSectionRow>
        <PanelSectionRow><Field label="Napomena" description="Broj uključenih podataka i font moraju stati u širinu igre. Ako red izlazi iz ekrana, smanji tekst ili isključi dodatne senzore. Neovisni FPS font podešava se u ELEMENTS → FPS uz uključen Claw renderer." /></PanelSectionRow>
      </PanelSection>
      <PanelSection title="ACTIVATION">
        <PanelSectionRow><Field label="Steam Launch Options" description={info?.launch_option ?? "Učitavanje…"} /></PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" disabled={!info?.launch_option} onClick={() => { void copyLaunchCommand(); }}>
          <FaCopy style={{marginRight: 8}} /> Kopiraj launch komandu
        </ButtonItem></PanelSectionRow>
        {copyStatus && <PanelSectionRow><Field label="Međuspremnik" description={copyStatus} /></PanelSectionRow>}
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
