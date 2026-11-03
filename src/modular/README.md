# Decky layout builder

Based on release v0.2.4-test.73 (ff3f671), reusing model.ts and Hud.tsx from
Viber85/claw-devlab main (Modular Lab 01). Builder.tsx adapts the DevLab tree,
preview and selected-node inspector to native Decky controls and a modal.

The QAM entry retains preset selection and JSON import/export. The modal edits a
validated draft, with 40 undo steps; Apply publishes the complete tree using the
existing test.73 settings path. Cancel discards the draft. Legacy Layout controls
are hidden while modular mode is active. Existing renderer/backend are unchanged.

The preview is an HTML simulation using sample sensor values, not a native game
screenshot. Native DropdownItem, DialogButton, ToggleField, TextField and SliderField
are used for Steam input; real controller focus, keyboard handling and modal sizing
still require on-device validation. Colors use the existing Decky color dialog.

Validation: npm run typecheck; npm run build; node tests/modular_editor.test.mjs;
node tests/modular_builder.test.mjs; python -m unittest discover -s tests.
The browser screenshot check could not run because Chromium was unavailable and
its download failed. Do not describe this as visually or hardware validated.
