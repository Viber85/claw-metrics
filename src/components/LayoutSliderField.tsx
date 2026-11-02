import type {ComponentProps} from "react";
import {SliderField} from "@decky/ui";

/**
 * A native SteamOS slider with a dedicated full-width label/value heading.
 * Native showValue compresses numbers to "1..." when a long label wraps
 * inside Decky's narrow Quick Access Menu.
 * Keep the real SliderField for controller focus, stepping and onChange.
 */
export function LayoutSliderField(props:ComponentProps<typeof SliderField>) {
  return <div className="claw-slider-control">
    <div className="claw-slider-heading">
      <span className="claw-slider-label">{props.label}</span>
      <output className="claw-slider-number">{String(props.value)}</output>
    </div>
    <div className="claw-slider-native">
      <SliderField {...props} label="" showValue={false}/>
    </div>
  </div>;
}
