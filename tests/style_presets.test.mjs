// Functional regression tests for the actual TypeScript style helpers.
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {runInNewContext} from "node:vm";
import ts from "typescript";

const source = readFileSync("src/style-presets.ts", "utf8");
const compiled = ts.transpileModule(source,{
  compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}
}).outputText;
const module = {exports:{}};
runInNewContext(compiled,{module,exports:module.exports});
const {styleMetricSnapshotFrom,styleMetricSelectionsFrom,
       styleMetricUpdatesFrom,styleModified} = module.exports;
const plain = value => JSON.parse(JSON.stringify(value));

const current = {
  fps:true,frametime:true,cpu:true,gpu:false,ram:true,vram:false,
  battery:true,tdp:false,draw:false,time:true,
  metrics:{fps_ms:true,graph:false,cpu_temp:false,cpu_mhz:true,
    cpu_power:false,gpu_temp:true,gpu_junction_temp:false,
    gpu_core_clock:false,gpu_mem_clock:false,gpu_mem_temp:false,
    gpu_power:true,gpu_fan:false,gpu_voltage:false,
    battery_icon:true,battery_time:false},
  font_weight:"regular",colors:{text:"F0F2F5"},token_weights:{},token_colors:{},
};
const snapshot=plain(styleMetricSnapshotFrom(current));
assert.equal(Object.keys(snapshot.groups).length,10);
assert.equal(Object.keys(snapshot.metrics).length,15);
assert.equal(snapshot.groups.gpu,false);
assert.equal(snapshot.groups.cpu,true);
assert.equal(snapshot.metrics.graph,false);
assert.equal(snapshot.metrics.cpu_temp,false);
assert.equal(snapshot.metrics.battery_icon,true);

// Both slots must be able to store conflicting sensor selections and restore
// them without mutating the source objects or losing other live metric keys.
const second = {...current, cpu:false, gpu:true,
  metrics:{...current.metrics,graph:true,gpu_power:false}};
const slot1={...snapshot,colors:current.colors,font_weight:"regular",
  token_weights:{},token_colors:{}};
const slot2={...plain(styleMetricSnapshotFrom(second)),
  colors:current.colors,font_weight:"regular",token_weights:{},token_colors:{}};
const live={...current,cpu:true,gpu:true,
  metrics:{...current.metrics,graph:true,cpu_temp:true,unrelated:true}};
const first=plain(styleMetricUpdatesFrom(slot1,live));
assert.equal(first.gpu,false);
assert.equal(first.cpu,true);
assert.equal(first.metrics.graph,false);
assert.equal(first.metrics.cpu_temp,false);
assert.equal(first.metrics.unrelated,true);
assert.equal(live.metrics.graph,true);
const secondLoaded=plain(styleMetricUpdatesFrom(slot2,live));
assert.equal(secondLoaded.gpu,true);
assert.equal(secondLoaded.cpu,false);
assert.equal(secondLoaded.metrics.graph,true);
assert.equal(secondLoaded.metrics.gpu_power,false);

// Dirty indicator must include both a disabled main group and submetric.
assert.equal(styleModified(slot1,current),false);
assert.equal(styleModified(slot1,{...current,gpu:true}),true);
assert.equal(styleModified(slot1,{...current,metrics:{...current.metrics,graph:true}}),true);

// A legacy style has NO metric snapshot and must not reset current sensors.
const legacy={colors:current.colors,font_weight:"regular",
 token_weights:{},token_colors:{}};
assert.deepEqual(plain(styleMetricUpdatesFrom(legacy,live)),{});
assert.equal(styleModified(legacy,live),false);
assert.deepEqual(plain(styleMetricSelectionsFrom({
  groups:{fps:0,cpu:"false",gpu:false,unknown:true},
  metrics:{graph:false,cpu_temp:1,alien:true}
})),{groups:{gpu:false},metrics:{graph:false}});
const {styleLayoutFrom} = module.exports;
assert.equal(styleLayoutFrom({hud_orientation:"vertical"}).hud_orientation,"vertical");
assert.equal(styleLayoutFrom({hud_orientation:"horizontal"}).hud_orientation,"horizontal");
assert.equal(styleLayoutFrom({hud_orientation:"sideways"}).hud_orientation,undefined);
assert.equal(styleLayoutFrom({}).hud_orientation,undefined);
assert.equal(styleModified({...legacy,hud_orientation:"vertical"},{...live,hud_orientation:"horizontal"}),true);
assert.equal(styleModified({...legacy,hud_orientation:"vertical"},{...live,hud_orientation:"vertical"}),false);
assert.equal(styleModified(legacy,{...live,hud_orientation:"vertical"}),false);
console.log("Style metric snapshots: save, restore, old styles, dirty state and invalid toggles passed");
