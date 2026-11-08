# Decky layout builder

The editor uses a Decky route and works on a validated draft. Apply publishes
after the editor unmounts; Cancel discards changes. Save style shares the main
menu slots. Undo/Redo retain both layout and appearance changes.

Groups have no padding, including the root overlay. Existing layouts and saved
styles are normalized to zero group padding without changing their metrics,
colors, font settings, alignment or other geometry. The old padding field remains
readable for layout v1/native V2 compatibility; native geometry also ignores
legacy group padding. Metric padding remains unchanged.

Group spacing exposes every containing row/column gap while a nested group is
selected. Labels include the group name and axis; each slider affects every gap
between that container's items. Horizontal and vertical gaps are independent,
0–240 px in 1 px steps. The selected group's internal reading gap is separate.
No ineffective axis control is shown when the tree contains no such container.

The HTML preview uses simulated readings. Native ImGui fixtures and geometry
tests check tight/expanded nested layouts; CI exercises Vulkan/OpenGL and ZIP
packaging. None of these establish Steam controller focus or handheld stability.

Superscript mode reserves the same main-text line box for every text token,
including group labels, clocks and unavailable readings. Only units use the
smaller raised font. Charged/full/charge-limit states replace battery time with
a vector plug while retaining the time reservation. Discharge estimates must
be finite and between one minute and 100 hours; unavailable data shows --.
Classic battery time uses the same checked formatter.
