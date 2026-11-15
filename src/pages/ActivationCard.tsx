import { ButtonItem, Field, PanelSectionRow } from "@decky/ui";
import { FaCopy, FaPlayCircle } from "react-icons/fa";
import * as Core from "../controller";

const { AccordionCard } = Core;

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
        </AccordionCard>
  );
}
