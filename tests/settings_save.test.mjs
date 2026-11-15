import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';

const settings = {};
const calls = [];
let nextWrite;
const runtime = { setTimeout, clearTimeout };
function load(source, imports = {}) {
  const module = {exports:{}};
  const compiled = ts.transpileModule(source, {
    compilerOptions: {module:ts.ModuleKind.CommonJS, jsx:ts.JsxEmit.ReactJSX, target:ts.ScriptTarget.ES2020},
  }).outputText;
  runInNewContext(compiled, {
    ...runtime, module, exports:module.exports, require:name => imports[name] ?? {},
  });
  return module.exports;
}

const {useClawController, defaults} = load(readFileSync('src/controller.tsx', 'utf8'), {
  './settings-save': load(readFileSync('src/settings-save.ts', 'utf8')),
  './modular/editor-page': {traceEditor: (...args) => calls.push(['trace', ...args])},
  'react/jsx-runtime': {jsx: () => null},
  react: {useState: initial => [typeof initial === 'function' ? initial() : initial, () => {}],
          useRef: current => ({current}), useEffect: () => {}},
  '@decky/api': {callable: name => async (...args) => {
    calls.push([name, ...args]);
    if (name === 'get_settings') return settings.current;
    if (name === 'get_info') return {config_readable:true};
    if (name === 'save_settings') {
      const wait = nextWrite;
      nextWrite = undefined;
      if (wait) await wait();
      settings.current = args[0];
      return {ok:true};
    }
    if (name === 'save_style_settings') return {ok:true};
    throw new Error(name);
  }},
});
settings.current = defaults;
const writes = () => calls.filter(([method]) => method === 'save_settings');
const traces = () => calls.filter(([method]) => method === 'trace');

const vm = useClawController();
const burst = Array.from({length:20}, (_, i) => vm.updateSlider({offset_x:i + 1}));
assert.equal(vm.current.current.offset_x, 20, 'QAM updates without waiting for the RPC');
assert.equal(writes().length, 0);
assert.ok((await Promise.all(burst)).every(Boolean));
assert.equal(writes().length, 1);
assert.equal(traces().length, 3);
assert.equal(settings.current.offset_x, 20);

calls.length = 0;
let unblock;
nextWrite = () => new Promise(resolve => { unblock = resolve; });
const liveChange = vm.update({enabled:false});
await new Promise(setImmediate);
assert.equal(writes().length, 1);
const early = vm.updateSlider({padding_x:8});
await new Promise(resolve => setTimeout(resolve, 150));
const final = vm.updateSlider({padding_x:21});
const style = vm.update({style_names:{'1':'Draft'}}, true);
unblock();
assert.ok((await Promise.all([liveChange, early, final, style])).every(Boolean));
assert.deepEqual(calls.filter(([name]) => name !== 'trace').map(([name, change]) =>
  [name, change.padding_x]), [['save_settings', defaults.padding_x], ['save_settings', 21], ['save_style_settings', 21]]);

calls.length = 0;
const pending = vm.updateSlider({offset_y:33});
const reopened = useClawController();
assert.equal(await reopened.refresh(), true, 'the reopened menu waits for the last save');
assert.equal(await pending, true);
assert.equal(reopened.current.current.offset_y, 33);
assert.deepEqual(calls.filter(([name]) => name !== 'trace').map(([name]) => name),
  ['save_settings', 'get_settings', 'get_info']);

nextWrite = async () => { throw new Error('Disk unavailable'); };
assert.equal(await vm.updateSlider({offset_x:34}), false);
assert.equal(await vm.updateSlider({offset_x:35}), true);
assert.equal(settings.current.offset_x, 35);
console.log('PASS settings saves: 20 rapid slider changes → 1 settings RPC and 3 diagnostic RPCs; order, errors and reopen tested.');
