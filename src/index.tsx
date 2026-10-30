import { useEffect, useState } from "react";
import { callable, definePlugin } from "@decky/api";
import {
  ButtonItem,
  Field,
  PanelSection,
  PanelSectionRow,
  SliderField,
  ToggleField,
} from "@decky/ui";
import { FaChartLine } from "react-icons/fa";

type Settings = {
  enabled: boolean;
  fontsize: number;
  opacity: number;
  fps: boolean;
  frametime: boolean;
  cpu: boolean;
  gpu: boolean;
  ram: boolean;
  vram: boolean;
  battery: boolean;
  power: boolean;
  time: boolean;
  tdp: boolean;
};

type Info = {
  config_path: string;
  launch_option: string;
  tdp_note: string;
  power_note: string;
};

const defaults: Settings = {
  enabled: true,
  fontsize: 18,
  opacity: 65,
  fps: true,
  frametime: true,
  cpu: true,
  gpu: true,
  ram: true,
  vram: true,
  battery: true,
  power: true,
  time: true,
  tdp: false,
};

// Callable methods are provided by the Decky Python backend.
const load = callable<[], Settings>("get_settings");
const save = callable<[Settings], { ok: boolean; config_path: string }>("save_settings");
const getInfo = callable<[], Info>("get_info");

function Content() {
  const [settings, setSettings] = useState<Settings>(defaults);
  const [info, setInfo] = useState<Info | null>(null);
  const [status, setStatus] = useState("Učitavanje…");

  useEffect(() => {
    Promise.all([load(), getInfo()])
      .then(([saved, details]) => {
        setSettings(saved);
        setInfo(details);
        setStatus("Spremno");
      })
      .catch((error: unknown) => {
        setStatus("Greška pri učitavanju: " + String(error));
      });
  }, []);

  const update = (patch: Partial<Settings>) => {
    const next = { ...settings, ...patch };
    setSettings(next);
    setStatus("Spremanje…");
    save(next)
      .then(() => {
        setStatus("Spremljeno. Za primjenu u igri možda je potreban restart igre.");
      })
      .catch((error: unknown) => {
        setStatus("Greška pri spremanju: " + String(error));
      });
  };

  const toggle = (key: keyof Settings, label: string) => (
    <PanelSectionRow>
      <ToggleField
        label={label}
        checked={Boolean(settings[key])}
        onChange={(checked: boolean) => update({ [key]: checked })}
      />
    </PanelSectionRow>
  );

  return (
    <>
      <PanelSection title="Claw Metrics · v0.1.1">
        {toggle("enabled", "Uključi prikaz")}
        <PanelSectionRow>
          <Field label="Status" description={status} />
        </PanelSectionRow>
      </PanelSection>

      <PanelSection title="Metrike">
        {toggle("fps", "FPS")}
        {toggle("frametime", "Frametime (ms) + graf")}
        {toggle("cpu", "CPU · % · MHz · °C")}
        {toggle("gpu", "GPU · % · MHz · °C")}
        {toggle("ram", "RAM · GB")}
        {toggle("vram", "VRAM · GB")}
        {toggle("battery", "Baterija · % · vrijeme")}
        {toggle("power", "CPU/GPU power · W")}
        {toggle("time", "Sat")}
        <PanelSectionRow>
          <Field
            label="TDP (Panel de Control)"
            description="Očitavanje primijenjenog limita još nije implementirano."
          />
        </PanelSectionRow>
      </PanelSection>

      <PanelSection title="Izgled">
        <PanelSectionRow>
          <SliderField
            label="Veličina fonta"
            value={settings.fontsize}
            min={12}
            max={28}
            step={1}
            showValue
            onChange={(value: number) => update({ fontsize: value })}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <SliderField
            label="Pozadina (%)"
            value={settings.opacity}
            min={0}
            max={100}
            step={5}
            showValue
            onChange={(value: number) => update({ opacity: value })}
          />
        </PanelSectionRow>
      </PanelSection>

      <PanelSection title="Testna aktivacija">
        <PanelSectionRow>
          <Field
            label="Steam Launch Options"
            description={info?.launch_option ?? "Učitavanje…"}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <Field
            label="Važno"
            description="Ova verzija samo generira zaseban MangoHud profil. Automatski SteamOS Game Mode overlay bez Launch Options još nije implementiran."
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem layout="below" onClick={() => { void getInfo().then(setInfo); }}>
            Osvježi informacije
          </ButtonItem>
        </PanelSectionRow>
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
