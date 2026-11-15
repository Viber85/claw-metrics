import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {runInNewContext} from 'node:vm';
import {JSDOM} from 'jsdom';
import React, {act} from 'react';
import ts from 'typescript';

const dom = new JSDOM('<div id="app"></div>');
global.window = dom.window;
global.document = dom.window.document;
global.IS_REACT_ACT_ENVIRONMENT = true;
const {createRoot} = await import('react-dom/client');
const require = createRequire(import.meta.url);
const router = {};
const calls = [];
let result = {};
let launches = '';
let unregisters = 0;
window.SteamClient = {Apps: {
  RegisterForAppDetails(id, update) {
    calls.push(['read', id]);
    update({strShortcutLaunchOptions: launches});
    return {unregister() { unregisters++; }};
  },
  SetShortcutLaunchOptions(id, options) {
    calls.push(['shortcut', id, options]);
    launches = options;
  },
}};

const api = {
  callable: name => async (...args) => {
    calls.push([name, ...args]);
    switch (name) {
      case 'get_current_framegen_result':
        return {...result};
      case 'check_current_framegen':
        result = args[0] && args[1] === 'FSR game'
          ? {state:'ready', appid:args[0],name:args[1],provider:'FSR'}
          : {state:'unavailable',message:args[0] ? 'No FSR module found.' : 'Start a game in Steam and try again.'};
        return {...result};
      case 'change_current_framegen':
        result = {...result,state:'waiting',pending:args[0] ? 'enable' : 'disable'};
        return {...result};
      case 'cancel_current_framegen':
        result = {};
        return {};
      default:
        throw Error(name);
    }
  },
};
const ui = {
  Router: router,
  PanelSectionRow: ({children}) => React.createElement('div', null, children),
  Field: ({label,description}) => React.createElement('p', null, label, ': ', description),
  ButtonItem: ({children,onClick,disabled}) => React.createElement('button', {onClick,disabled}, children),
};
const module = {exports:{}};
const source = readFileSync('src/pages/GeneratedFrames.tsx','utf8');
runInNewContext(ts.transpileModule(source, {
  compilerOptions: {module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020},
}).outputText, {
  module, exports:module.exports, window, setTimeout, clearTimeout,
  require: id => id === '@decky/api' ? api : id === '@decky/ui' ? ui : require(id),
});

const {GeneratedFrames, addOverlayCommand} = module.exports;
const launcher = '~/claw-metrics %command%';
assert.equal(addOverlayCommand('', launcher), launcher);
assert.equal(addOverlayCommand('FOO=1 gamemoderun %command% -dx12', launcher),
  'FOO=1 gamemoderun ~/claw-metrics %command% -dx12');
assert.equal(addOverlayCommand('FOO=1 ~/claw-metrics %command%', launcher),
  'FOO=1 ~/claw-metrics %command%');
for (const special of ['-dx12','bash -c "%command%"','A=1 %command% %command%','FOO=1;%command%']) {
  assert.equal(addOverlayCommand(special, launcher), undefined);
}

const container = document.getElementById('app');
const root = createRoot(container);
const button = label => [...container.querySelectorAll('button')].find(el=>el.textContent===label);
const check = 'Check current game compatibility';
const enable = 'Enable generated frame metrics';

await act(async()=>root.render(React.createElement(GeneratedFrames, {ready:true,launchOption:launcher})));
assert.ok(!button(enable));
await act(async()=>button(check).click());
assert.match(container.textContent, /Start a game/);
router.MainRunningApp = {appid:123,display_name:'Other game'};
await act(async()=>button(check).click());
assert.match(container.textContent, /No FSR module/);
assert.ok(!button(enable));

router.MainRunningApp = {appid:-268435444,display_name:'FSR game'};
await act(async()=>button(check).click());
assert.match(container.textContent, /FSR game/);
assert.ok(button(enable));
router.MainRunningApp = {appid:123,display_name:'Other game'};
await act(async()=>button(enable).click());
assert.match(container.textContent, /current game changed/);
assert.equal(calls.filter(([method])=>method==='change_current_framegen').length, 0);
router.MainRunningApp = {appid:-268435444,display_name:'FSR game'};
await act(async()=>button(enable).click());
assert.match(container.textContent, /Close the game/);
assert.ok(button('Cancel pending change'));
assert.deepEqual(calls.filter(([method])=>method==='change_current_framegen'), [
  ['change_current_framegen', true, '4026531852'],
]);
assert.deepEqual(calls.filter(([method])=>method==='shortcut'), [
  ['shortcut', 4026531852, launcher],
]);
assert.equal(unregisters, 2);

delete router.MainRunningApp;
result = {...result,state:'enabled',pending:null};
await act(async()=>await new Promise(resolve=>setTimeout(resolve,1300)));
assert.ok(button('Restore original AMD DLL'));
assert.match(container.textContent, /Classic shows Game FPS and Generated FPS/);
assert.ok(!button(enable));
await act(async()=>root.unmount());
console.log('PASS current-game check, shortcut identity, activation after exit and Steam launch options with mocked Decky controls.');
