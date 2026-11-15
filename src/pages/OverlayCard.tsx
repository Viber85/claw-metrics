import {
  ButtonItem,
  Field,
  PanelSectionRow,
} from "@decky/ui";
import { FaDesktop } from "react-icons/fa";

import * as Core from "../controller";


const { AccordionCard } = Core;

/** Standalone overlay presentation; all mutable state is owned by the Decky controller. */
export function OverlayCard({vm}:{vm:Core.ClawController}) {
  const { info, status, rendererStatus, rendererBusy, verifyRenderer, openSection, toggleSection, ready, toggle } = vm;
  return (
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
  );
}
