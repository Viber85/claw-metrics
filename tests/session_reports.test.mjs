import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import ts from 'typescript';
const source=readFileSync('src/session-reports.ts','utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;
const module={exports:{}};runInNewContext(compiled,{module,exports:module.exports});
const latest=module.exports.latestReportSession;
const old={id:'old',state:'interrupted',started_at:10,samples:40};
const ended={id:'new',state:'overlay_unloaded',started_at:20,samples:232};
const active={id:'active',state:'recording',started_at:30,samples:5};
const sessions=[active,old,ended];
assert.equal(latest(sessions).id,'new');
assert.equal(sessions[0].id,'active'); // selection cannot reorder the live status list
assert.equal(latest([old,{...ended,state:'interrupted'}]).id,'new');
assert.equal(latest([active]),undefined);
assert.equal(latest([]),undefined);assert.equal(latest(undefined),undefined);
assert.equal(latest([{...ended,started_at:NaN}]),undefined);
assert.equal(latest([{...ended,state:'unknown'}]),undefined);
assert.equal(latest([{...ended,id:''}]),undefined);
for(const state of ['stopped','plugin_unloaded','size_limit','interrupted','overlay_unloaded'])
 assert.equal(latest([{...ended,state}]).id,'new');
console.log('Report selection: latest ended session, active exclusion, malformed data, empty history and immutable ordering passed.');
