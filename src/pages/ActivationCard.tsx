import { useEffect, useState } from "react";
import { callable, FileSelectionType, openFilePicker } from "@decky/api";
import { ButtonItem, DropdownItem, Field, PanelSectionRow } from "@decky/ui";
import { FaCopy, FaPlayCircle } from "react-icons/fa";
import * as Core from "../controller";

const { AccordionCard } = Core;

type FrameGenStatus = {
  state: "ready" | "enabled" | "setup" | "update" | "unavailable";
  message: string;
  configured?: boolean;
};
type FrameGenGame = {appid: string; name: string; source: string};
type FrameGenLibrary = {games: FrameGenGame[]; home: string; message?: string};
const listFrameGenGames = callable<[], FrameGenLibrary>("list_framegen_games");
const getFrameGen = callable<[string, string | null], FrameGenStatus>("get_framegen_status");
const setFrameGen = callable<[boolean, string, string | null], FrameGenStatus>("set_framegen_enabled");

const lookupError = "Could not read Steam's game library.";
const unavailableStatus = (message: string): FrameGenStatus => ({state: "unavailable", message});

function FrameGenActivation({launcherReady}: {launcherReady: boolean}) {
  const [library, setLibrary] = useState<FrameGenLibrary>();
  const [loadError, setLoadError] = useState("");
  const [gameId, setGameId] = useState("");
  const [path, setPath] = useState<string | null>(null);
  const [status, setStatus] = useState<FrameGenStatus>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let mounted = true;
    void listFrameGenGames().then(
      result => { if (mounted) setLibrary(result); },
      () => { if (mounted) setLoadError(lookupError); },
    );
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (!gameId) return;
    let mounted = true;
    void getFrameGen(gameId, path).then(
      result => { if (mounted) setStatus(result); },
      () => { if (mounted) setStatus(unavailableStatus("Could not check this game's FSR files.")); },
    );
    return () => { mounted = false; };
  }, [gameId, path]);

  async function browse() {
    try {
      const result = await openFilePicker(FileSelectionType.FILE, path?.replace(/\/[^/]+$/, "") || library?.home || "/home",
                                           true, true, undefined, ["dll"], false, false);
      const selected = result?.path || result?.realpath;
      if (!selected?.endsWith("/amd_fidelityfx_framegeneration_dx12.dll")) {
        setError("Select amd_fidelityfx_framegeneration_dx12.dll in the game folder.");
        return;
      }
      if (selected !== path) setStatus(undefined);
      setPath(selected);
      setError("");
    } catch (reason) {
      if (!String(reason).includes("User canceled")) setError("Could not open the game file picker.");
    }
  }

  async function change(enable: boolean) {
    setError("");
    setBusy(true);
    try {
      const result = await setFrameGen(enable, gameId, path);
      if (result.state === "unavailable") setError(result.message);
      else setStatus(result);
    } catch {
      setError("Frame Gen setup failed. Try again after closing the game.");
    } finally {
      setBusy(false);
    }
  }

  const games = library?.games || [];
  const canRestore = status && (status.state === "enabled" || status.state === "setup" || status.configured);
  const canEnable = status && ["ready", "setup", "update"].includes(status.state);
  const description = !library ? loadError || "Looking for Steam and Non-Steam games…"
    : library.message || (!games.length ? "Add the game to Steam to set up its FSR metrics."
    : !gameId ? "Choose a game. Setup requires a compatible AMD DX12 Frame Gen DLL."
    : !status ? "Checking this game's FSR files…"
    : status.state === "unavailable" ? status.message
    : status.state === "enabled" ? "Adapter enabled. Start the game with the usual Better Overlay launch command."
    : status.state === "update" ? "The game DLL changed. Enable again to back up and use the current DLL."
    : "Close the game before setup. Better Overlay backs up the original AMD DLL.");

  return <>
    <PanelSectionRow><Field label="Internal FSR Frame Generation" description={description}/></PanelSectionRow>
    {games.length > 0 && <PanelSectionRow>
      <DropdownItem label="Game" disabled={busy} selectedOption={gameId}
        rgOptions={[{data:"", label:"Choose a game"}, ...games.map(game => ({
          data:game.appid, label:`${game.name} · ${game.source}`,
        }))]}
        onChange={option => {
          const next = String(option.data);
          if (next === gameId) return;
          setStatus(undefined);
          setPath(null);
          setError("");
          setGameId(next);
        }}/>
    </PanelSectionRow>}
    {gameId && status && !status.configured && status.state !== "enabled" && <PanelSectionRow>
      <ButtonItem layout="below" disabled={busy} onClick={() => void browse()}>
        Choose AMD Frame Gen DLL
      </ButtonItem>
    </PanelSectionRow>}
    {canEnable && <PanelSectionRow>
      <ButtonItem layout="below" disabled={busy || !launcherReady}
        onClick={() => void change(true)}>
        {busy ? "Updating adapter…" : "Enable FSR metrics"}
      </ButtonItem>
    </PanelSectionRow>}
    {canRestore && <PanelSectionRow>
      <ButtonItem layout="below" disabled={busy} onClick={() => void change(false)}>
        Restore original AMD DLL
      </ButtonItem>
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
