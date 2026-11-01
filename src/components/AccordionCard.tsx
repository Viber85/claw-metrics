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
      background: active ? "#0d2945" : "#111e30",
      width: "100%", maxWidth: "100%", minWidth: 0, boxSizing: "border-box",
      border: active ? "1px solid #2c709d" : "1px solid #395579",
      borderLeft: active ? "4px solid #08d3fa" : "4px solid #8b65e7",
      borderRadius: 12,
      overflow: "hidden",
      marginBottom: 10,
      boxShadow: active ? "0 0 12px rgba(0,153,237,0.13)" : "none",
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
          background: active ? "#073858" : "#14243b",
          border: "none", borderRadius: 0, minHeight: 66, whiteSpace: "normal",
          outline: "none", boxShadow: "none",
        }}>
          <span style={{display: "flex", alignItems: "center", gap: 10, width: "100%", minWidth: 0}}>
            <span className="claw-accordion-icon"
              style={{display: "flex", alignItems: "center", justifyContent: "center",
              background: active ? "#075b83" : "#203551", borderRadius: 8, minWidth: 36, height: 36,
              fontSize: 20, color: active ? "#42e0ff" : "#acd7fe"}}>{icon}</span>
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
      </div>
      {open && <div style={{padding: "10px 8px 12px", borderTop: "1px solid #235b81"}}>
        {children}
      </div>}
    </div>
  );
}
