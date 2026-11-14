import { useEffect, useState } from "react";
import { callable } from "@decky/api";
import { ButtonItem, Field, PanelSectionRow } from "@decky/ui";
import { FaCopy, FaPlayCircle } from "react-icons/fa";
import * as Core from "../controller";

const { AccordionCard } = Core;

type FrameGenStatus = {
  state: "ready" | "enabled" | "setup" | "update" | "unavailable";
  message: string;
};
const getFrameGen = callable<[], FrameGenStatus>("get_framegen_status");
const setFrameGen = callable<[boolean], FrameGenStatus>("set_framegen_enabled");

function FrameGenActivation({launcherReady}: {launcherReady: boolean}) {
  const [status, setStatus] = useState<FrameGenStatus>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let mounted = true;
    void getFrameGen().then(
      result => { if (mounted) setStatus(result); },
      () => { if (mounted) setStatus({state:"unavailable", message:"Could not read the Steam game installation."}); },
    );
    return () => { mounted = false; };
  }, []);

  const enabled = status?.state === "enabled";
  const unavailable = status?.state === "unavailable";
  const description = !status ? "Looking for the Steam installation…"
    : unavailable ? status.message
    : enabled ? "Adapter enabled. Start the game with Better Overlay's usual launch command."
    : status.state === "update" ? "Steam replaced the adapter. Enable it again to use the updated AMD DLL."
    : "Adds FSR FPS metrics by installing an adapter in the game folder and backing up the AMD DLL.";

  async function change(enable: boolean) {
    setError("");
    setBusy(true);
    try {
      const result = await setFrameGen(enable);
      if (result.state === "unavailable") setError(result.message);
      else setStatus(result);
    } catch {
      setError("Frame Gen setup failed. Try again after closing the game.");
    } finally {
      setBusy(false);
    }
  }

  return <>
    <PanelSectionRow><Field label="Clair Obscur · Internal FSR" description={description}/></PanelSectionRow>
    {status && !unavailable && <PanelSectionRow>
      <ButtonItem layout="below" disabled={busy || (!enabled && !launcherReady)}
        onClick={() => void change(!enabled)}>
        {busy ? "Updating adapter…" : enabled ? "Restore original AMD DLL" : "Enable FSR metrics"}
      </ButtonItem>
    </PanelSectionRow>}
    {status?.state === "setup" && <PanelSectionRow>
      <ButtonItem layout="below" disabled={busy} onClick={() => void change(false)}>Restore original AMD DLL</ButtonItem>
    </PanelSectionRow>}
    {error && <PanelSectionRow><Field label="Frame Gen setup" description={error}/></PanelSectionRow>}
  </>;
}

/** Standalone activation presentation; all mutable state is owned by the Decky controller. */
export function ActivationCard({vm}:{vm:Core.ClawController}) {
  const { info, copyStatus, openSection, toggleSection, copyLaunchCommand } = vm;
  return (
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
          {openSection === "activation" && <FrameGenActivation launcherReady={Boolean(info?.short_launcher_ready)}/>}
        </AccordionCard>
  );
}
