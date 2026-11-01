import type {ReactNode} from "react";
import {Focusable} from "@decky/ui";

/** Match the real SteamOS navigation tree to the visible grid.
 * The parent handles up/down, each row handles left/right. */
export function GamepadGrid<T>({items, columns, className, renderItem}:{
  items:readonly T[]; columns:2|3; className:string;
  renderItem:(item:T,index:number)=>ReactNode;
}) {
  const rows:T[][]=[];
  for(let at=0;at<items.length;at+=columns) rows.push(items.slice(at,at+columns));
  return <Focusable flow-children="column" className={className}>
    {rows.map((row,rowIndex)=>
      <Focusable key={rowIndex} flow-children="row"
        className={"claw-grid-row claw-grid-cols-"+columns}>
        {row.map((item,colIndex)=>renderItem(item,rowIndex*columns+colIndex))}
      </Focusable>)}
  </Focusable>;
}
