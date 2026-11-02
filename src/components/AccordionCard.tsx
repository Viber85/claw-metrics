import {useState,type ReactNode} from "react";
import {DialogButton} from "@decky/ui";
import {FaChevronDown,FaChevronRight} from "react-icons/fa";

export type SectionKey = "overlay" | "layout" | "metrics" | "colors" | "activation" | "advanced";
export type AccordionCardProps = {
  id: SectionKey;
  title: string;
  subtitle: string;
  icon: ReactNode;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
};

export function AccordionCard({id, title, subtitle, icon, open, onToggle, children}: AccordionCardProps) {
  const [focused, setFocused] = useState(false);
  const active = open || focused;
  return (
    <div data-section={id} data-selected={open ? "true" : "false"}
      data-focused={focused ? "true" : "false"} style={{
      background: active ? "#151d27" : "#10161e",
      width: "100%", maxWidth: "100%", minWidth: 0, boxSizing: "border-box",
      border: active ? "1px solid #3b5678" : "1px solid #29333f",
      borderLeft: active ? "1px solid #3b5678" : "1px solid #29333f",
      borderRadius: 12,
      overflow: "hidden",
      marginBottom: 10,
      boxShadow: "none",
    }}>
      {/* Steam and Decky retain normal button navigation; highlight is in the background. */}
      <div className="claw-accordion-header"
        onFocusCapture={()=>setFocused(true)} onBlurCapture={()=>setFocused(false)}
        style={{position:"relative",width:"100%",minWidth:0,
        maxWidth:"100%",boxSizing:"border-box"}}>
        <DialogButton onClick={onToggle} aria-pressed={open} style={{
          width: "100%", minWidth: 0, boxSizing: "border-box",
          display: "flex", alignItems: "center",
          textAlign: "left", margin: 0, padding: "12px 10px",
          background: active ? "#1b2c43" : "#121a23",
          border: "none", borderRadius: 0, minHeight: 66, whiteSpace: "normal",
          outline: "none", boxShadow: "none",
        }}>
          <span style={{display: "flex", alignItems: "center", gap: 10, width: "100%", minWidth: 0}}>
            <span className="claw-accordion-icon"
              style={{display: "flex", alignItems: "center", justifyContent: "center",
              background: active ? "#243449" : "#1c2632", borderRadius: 8, minWidth: 36, height: 36,
              fontSize: 20, color: active ? "#e1e6ed" : "#d5dce6"}}>{icon}</span>
            <span style={{display: "flex", flex: 1, minWidth: 0, flexDirection: "column", gap: 3}}>
              <span style={{fontWeight: 700, fontSize: 16, color: "#f1f7ff"}}>{title}</span>
              <span style={{fontWeight: 400, fontSize: 11, lineHeight: 1.35,
                color: "#aab4c1", overflowWrap: "anywhere"}}>{subtitle}</span>
            </span>
            <span style={{display: "flex", color: "#c6d0dd", fontSize: 16, flexShrink: 0}}>
              {open ? <FaChevronDown /> : <FaChevronRight />}
            </span>
          </span>
        </DialogButton>
      </div>
      {open && <div style={{padding: "10px 8px 12px", borderTop: "1px solid #2b3643"}}>
        {children}
      </div>}
    </div>
  );
}
