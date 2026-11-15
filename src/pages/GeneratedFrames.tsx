import { useEffect, useState } from "react";
import { callable } from "@decky/api";
import { ButtonItem, Field, PanelSectionRow, Router } from "@decky/ui";

type CurrentGame = { appid: string; name: string };
type FrameGenResult = {
  state?: "ready" | "enabled" | "setup" | "update" | "unavailable" | "waiting";
  appid?: string;
  name?: string;
  provider?: string;
  pending?: "enable" | "disable" | null;
  message?: string;
};

const getResult = callable<[], FrameGenResult>("get_current_framegen_result");
const checkGame = callable<[string | null, string], FrameGenResult>("check_current_framegen");
const applyChange = callable<[boolean, string], FrameGenResult>("change_current_framegen");
const cancelChange = callable<[], FrameGenResult>("cancel_current_framegen");

export function currentGame(): CurrentGame | undefined {
  try {
    const app = Router?.MainRunningApp;
    const id = Number(app?.appid ?? Router?.MainRunningAppID);
    if (!Number.isInteger(id) || id < -0x80000000 || id > 0xffffffff || !id) return;
    return {appid: String(id >>> 0), name: app?.display_name || ""};
  } catch {
    return undefined;
  }
}

export function addOverlayCommand(options: string, command: string): string | undefined {
  const placeholder = "%command%";
  if (!command.endsWith(" " + placeholder)) return;
  const wrapper = command.slice(0, -placeholder.length).trimEnd();
  if (options.includes(wrapper + " ") || /(?:^|\s)~\/claw-metrics\s/.test(options)) return options;
  if (!options.trim()) return command;
  const index = options.indexOf(placeholder);
  if (index < 0 || options.indexOf(placeholder, index + placeholder.length) >= 0) return;
  const prefix = options.slice(0, index);
  const suffix = options.slice(index + placeholder.length);
  // Restrict insertion to one unquoted command placeholder. Keep complex
  // scripts intact and let the user use their existing Activation command.
  if ((prefix && !/\s$/.test(prefix)) || (suffix && !/^\s/.test(suffix))
      || /['"\\`$|;&<>#()\n\r]/.test(prefix)) return;
  return prefix + command + suffix;
}

async function ensureOverlayCommand(appid: string, command: string): Promise<boolean> {
  const id = Number(appid);
  const apps = window.SteamClient?.Apps;
  if (!apps || typeof apps.RegisterForAppDetails !== "function") return false;
  const shortcut = id >= 0x80000000;
  const read = async (expected?: string) => {
    let registration: ReturnType<typeof apps.RegisterForAppDetails> | undefined;
    let timeout: ReturnType<typeof setTimeout> | undefined;
    try {
      return await new Promise<string | undefined>(resolve => {
        timeout = setTimeout(() => resolve(undefined), 2500);
        registration = apps.RegisterForAppDetails(id, details => {
          const options = shortcut ? details?.strShortcutLaunchOptions : details?.strLaunchOptions;
          if (typeof options === "string" && (expected === undefined || options === expected)) resolve(options);
        });
      });
    } catch {
      return undefined;
    } finally {
      clearTimeout(timeout);
      registration?.unregister();
    }
  };
  const options = await read();
  if (options === undefined) return false;
  const updated = addOverlayCommand(options, command);
  if (updated === undefined) return false;
  if (updated === options) return true;
  try {
    if (shortcut) apps.SetShortcutLaunchOptions(id, updated);
    else apps.SetAppLaunchOptions(id, updated);
    return (await read(updated)) === updated;
  } catch {
    return false;
  }
}

function statusText(result: FrameGenResult) {
  switch (result.state) {
    case "waiting":
      return result.pending === "disable"
        ? "Close the game to restore the original DLL automatically."
        : "Close the game. Claw Metrics will then apply the changes automatically.";
    case "enabled":
      return "Enabled. Launch the game and turn on FSR Frame Generation. Classic shows Game FPS and Generated FPS. In Layout Builder, add those metrics to your layout.";
    case "setup":
    case "ready":
    case "update":
      return "Compatible FSR DX12 files found. Enable to show Game FPS and Generated FPS separately.";
    case "unavailable":
      return result.message || "Compatibility check unavailable.";
    default:
      return "Start the game you want to check.";
  }
}

export function GeneratedFrames({ready, launchOption}: {ready: boolean; launchOption?: string}) {
  const [result, setResult] = useState<FrameGenResult>();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (!ready) return;
    let mounted = true;
    const refresh = async () => {
      try {
        const next = await getResult();
        if (mounted) setResult(next);
      } catch {
        if (mounted) setResult({state:"unavailable", message:"Could not read Frame Gen status."});
      }
    };
    void refresh();
    return () => { mounted = false; };
  }, [ready]);

  useEffect(() => {
    if (result?.state !== "waiting" || busy) return;
    let mounted = true;
    const timer = setTimeout(() => {
      void getResult().then(
        next => { if (mounted) setResult(next); },
        () => { if (mounted) setResult({state:"unavailable", message:"Could not read Frame Gen status. Reopen this card to refresh."}); },
      );
    }, 1200);
    return () => { mounted = false; clearTimeout(timer); };
  }, [result, busy]);

  async function run(action: () => Promise<FrameGenResult>) {
    setBusy(true);
    setNotice("");
    try {
      setResult(await action());
    } catch {
      setNotice("Claw Metrics could not complete this action. Try again.");
    } finally {
      setBusy(false);
    }
  }

  function change(enabled: boolean) {
    const id = result?.appid;
    if (!id) return;
    const running = currentGame();
    if (running && running.appid !== id) {
      setNotice("The current game changed. Check its compatibility first.");
      return;
    }
    void run(async () => {
      const next = await applyChange(enabled, id);
      if (enabled && launchOption && (next.state === "waiting" || next.state === "enabled")
          && !await ensureOverlayCommand(id, launchOption)) {
        setNotice("Check the game's Steam Launch Options for the Claw Metrics command shown in Activation.");
      }
      return next;
    });
  }

  const state = result?.state;
  const canEnable = state === "ready" || state === "setup" || state === "update";
  const canRestore = state === "enabled" || state === "setup" || state === "update";

  return <>
    <PanelSectionRow>
      <ButtonItem layout="below" disabled={!ready || busy || !result || state === "waiting"}
        onClick={() => {
          const game = currentGame();
          void run(() => checkGame(game?.appid ?? null, game?.name ?? ""));
        }}>
        Check current game compatibility
      </ButtonItem>
    </PanelSectionRow>
    <PanelSectionRow><Field label={result?.name || "Current game"} description={busy ? "Checking…" : statusText(result || {})}/></PanelSectionRow>
    {canEnable && <PanelSectionRow><ButtonItem layout="below" disabled={busy || !launchOption}
      onClick={() => change(true)}>Enable generated frame metrics</ButtonItem></PanelSectionRow>}
    {canRestore && <PanelSectionRow><ButtonItem layout="below" disabled={busy}
      onClick={() => change(false)}>Restore original AMD DLL</ButtonItem></PanelSectionRow>}
    {state === "waiting" && <PanelSectionRow><ButtonItem layout="below" disabled={busy}
      onClick={() => void run(cancelChange)}>Cancel pending change</ButtonItem></PanelSectionRow>}
    {notice && <PanelSectionRow><Field label="Generated Frames" description={notice}/></PanelSectionRow>}
  </>;
}
