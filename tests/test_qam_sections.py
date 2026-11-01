"""Regression checks for the grouped Decky QAM interface.

Static checks complement TypeScript and Rollup compilation. They guard
against future redesigns accidentally hiding/removing working controls.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CARD_NAMES = ("OverlayCard", "LayoutCard", "MetricsCard", "ColorsAndFontCard",
              "ActivationCard", "AdvancedCard")
# Keep static regression coverage over ALL of the actual production modules,
# not just the thin index.tsx entry point. Preserve visual card order.
SOURCE = "\n".join(
    (SRC / path).read_text()
    for path in ("components/AccordionCard.tsx", "components/GamepadGrid.tsx",
                 "components/ControlGroup.tsx", "controller.tsx", "index.tsx",
                 *(f"pages/{name}.tsx" for name in CARD_NAMES))
)



class GroupedQamTests(unittest.TestCase):
    def test_vertical_orientation_control_and_safe_preview_limits(self):
        self.assertIn('export type HudOrientation = "horizontal" | "vertical"', SOURCE)
        self.assertIn('hud_orientation: HudOrientation', SOURCE)
        self.assertIn('hud_orientation:"horizontal"', SOURCE)
        self.assertIn('label="HUD orientation"', SOURCE)
        self.assertIn('id:"vertical",label:"Vertical"', SOURCE)
        self.assertIn('aria-pressed={settings.hud_orientation===choice.id}', SOURCE)
        self.assertIn('onClick={()=>update({hud_orientation:choice.id})}', SOURCE)
        self.assertIn('settings.hud_orientation==="vertical"', SOURCE)
        self.assertIn('hud_orientation:defaults.hud_orientation', SOURCE)
        self.assertIn('Vertical preview', SOURCE)
        self.assertIn('Uses MangoHud', SOURCE)
        self.assertIn('FPS-only scaling', SOURCE)

    def test_six_independent_card_modules_keep_one_shared_controller(self):
        entry = (SRC / "index.tsx").read_text()
        controller = (SRC / "controller.tsx").read_text()
        self.assertIn("const vm=useClawController();", entry)
        self.assertEqual(entry.count(" vm={vm}/>"), 6)
        self.assertNotIn("<AccordionCard id=", entry)
        self.assertIn("export type ClawController = ReturnType<typeof useClawController>", controller)
        for common in ("AccordionCard", "GamepadGrid", "ControlGroup"):
            body = (SRC / "components" / f"{common}.tsx").read_text()
            self.assertIn(f"export function {common}", body)
            self.assertIn(f'from "./components/{common}"', controller)
        self.assertIn("export function useClawController()", controller)
        self.assertIn("const [settings, setSettings] = useState<Settings>(defaults);", controller)
        self.assertIn("const saved=await withTimeout(load());", controller)
        self.assertIn("queue.current = queue.current.then", controller)
        for name, section in zip(CARD_NAMES,
                ("overlay","layout","metrics","colors","activation","advanced")):
            content = (SRC / "pages" / f"{name}.tsx").read_text()
            self.assertEqual(content.count("<AccordionCard id="), 1, name)
            self.assertIn(f'<AccordionCard id="{section}"', content)
            self.assertIn("vm:Core.ClawController", content)
            self.assertIn(f"<{name} vm={{vm}}/>", entry)


    def test_six_gamepad_focusable_accordion_sections(self):
        sections = ("overlay", "layout", "metrics", "colors", "activation", "advanced")
        for key in sections:
            self.assertIn(f'<AccordionCard id="{key}"', SOURCE)
        self.assertEqual(SOURCE.count("<AccordionCard id="), 6)
        self.assertIn('useState<SectionKey | null>(() => lastOpenSection)', SOURCE)
        self.assertIn('setOpenSection(next)', SOURCE)
        self.assertIn("<DialogButton onClick={onToggle}", SOURCE)

    def test_existing_controls_and_safe_color_picker_survive(self):
        for option in (
            "Copy launch command", "Copy extended Vulkan command",
            "Copy stock launch command", "Backup launch commands",
            "Within-group gap", "Frametime graph width",
            "Restore default colors", "OpaqueColorPicker",
            "SemiBold", "font_weight", "MangoHud",
            "Reset layout to defaults", "Battery", "TDP limit (read-only)",
        ):
            self.assertIn(option, SOURCE, option)
        self.assertNotIn("ColorPickerModal", SOURCE)
        self.assertNotIn("FPS Bold", SOURCE)
        self.assertNotIn("Uži red", SOURCE)

    def test_active_category_survives_react_remounts(self):
        self.assertIn('lastOpenSection: SectionKey | null = "metrics"', SOURCE)
        self.assertIn('useState<SectionKey | null>(() => lastOpenSection)', SOURCE)
        self.assertIn('lastOpenSection = next', SOURCE)
        self.assertIn('lastExpandedMetric = key', SOURCE)
        self.assertIn('lastStyleCategory = next', SOURCE)
        self.assertIn('setStyleCategory(next)', SOURCE)

    def test_every_nested_subcard_toggles_closed_on_second_press(self):
        controller=(SRC / "controller.tsx").read_text()
        layout=(SRC / "pages/LayoutCard.tsx").read_text()
        advanced=(SRC / "pages/AdvancedCard.tsx").read_text()
        common=(SRC / "components/ControlGroup.tsx").read_text()
        # Exactly the same behavior as Metrics and Appearance Editor:
        # one active subcard at a time, second press collapses to null.
        for id, prefix, options in (
            ("LayoutPanel", "Layout", ("position","size","spacing","frametime")),
            ("AdvancedPanel", "Advanced", ("updates","diagnostics","backup")),
        ):
            self.assertIn(f"last{id}: {id} | null", controller)
            self.assertIn(f"useState<{id} | null>(()=>last{id})", controller)
            self.assertIn(f"const next=last{id}===id?null:id;", controller)
            self.assertIn(f"last{id}=next;", controller)
            self.assertIn(f"set{id}(next);", controller)
            card=layout if prefix=="Layout" else advanced
            for option in options:
                self.assertIn(f'onToggle={{()=>toggle{prefix}Panel("{option}")}}',card)
                self.assertIn(f'open={{{prefix.lower()}Panel==="{option}"}}',card)
            self.assertNotIn(f'onToggle={{()=>set{id}(',card)
        self.assertIn('aria-expanded={open}',common)
        self.assertIn('{open && <div',common)
        # The already-working behavior on Metrics and Colors must remain.
        self.assertIn('expandMetric(open ? null : key)',SOURCE)
        self.assertIn('lastStyleCategory === id ? null : id',SOURCE)

    def test_appearance_category_is_collapsible_like_metrics(self):
        self.assertIn('lastStyleCategory: StyleCategory | null = "global"', SOURCE)
        self.assertIn('useState<StyleCategory | null>(() => lastStyleCategory)', SOURCE)
        self.assertIn('const next = lastStyleCategory === id ? null : id;', SOURCE)
        self.assertIn('setStyleCategory(next);', SOURCE)
        self.assertIn('styleCategory!==null && row.some(([key])=>key===styleCategory)', SOURCE)
        self.assertIn('onClick={()=>chooseStyleCategory(key)}', SOURCE)
        self.assertIn('aria-pressed={styleCategory===key}', SOURCE)

    def test_advanced_installed_version_comes_from_live_backend_not_literal(self):
        self.assertIn('getInstalledVersion = callable<[], {version:string}>("get_installed_version")', SOURCE)
        self.assertIn('withTimeout(getInstalledVersion())', SOURCE)
        self.assertIn('setInstalledVersion(result.version);', SOURCE)
        self.assertIn('installedVersionError', SOURCE)
        self.assertIn('"Claw Metrics "+installedVersion', SOURCE)
        self.assertNotIn('description="Claw Metrics 0.2.4-test.43"', SOURCE)
        self.assertIn('Reading installed package…', SOURCE)

    def test_metric_style_ui_is_real_not_placeholder(self):
        for action in (
            "cycleTokenWeight(token.key)", "openTokenColorPicker(token)",
            "resetTokenColor(token.key)", "savePreset(slot)", "loadPreset(slot)",
            "token_weights:", "token_colors:", "style_presets:", "weightOptions",
        ):
            self.assertIn(action, SOURCE, action)
        self.assertIn('font_weight: FontWeight;', SOURCE)
        self.assertIn('styleCategory==="global"', SOURCE)
        self.assertEqual(SOURCE.count('<AccordionCard id='), 6)

    def test_devlab_latest_controls_present(self):
        for name in ("custom_labels", "RenameMetricModal", "styleLayoutFrom",
                     "independentColors", "styleModified", "loaded-style-status",
                     "active_style", "Values", "DRAW", "Clock",
                     "Reset layout to defaults", "groupIcons"):
            self.assertIn(name, SOURCE, name)
        self.assertIn("token_weights: {}", SOURCE)
        self.assertIn("token_colors: {}", SOURCE)

    def test_compact_three_column_grids_preserve_actions_and_focus(self):
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr))", SOURCE)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", SOURCE)
        self.assertIn('<Focusable flow-children="column" className={className}>', SOURCE)
        self.assertIn('<Focusable key={rowIndex} flow-children="row"', SOURCE)
        self.assertIn('rows.push(items.slice(at,at+columns))', SOURCE)
        self.assertNotIn('<div className="claw-tiles claw-metric-tiles">', SOURCE)
        self.assertIn('data-metric={key} className="metric-card claw-control-button"', SOURCE)
        for kind in ('claw-metric-tiles', 'claw-hidden-metric-tiles',
                     'claw-style-tiles', 'claw-weight-tiles', 'claw-color-tiles'):
            self.assertIn('className="claw-tiles ' + kind + '"', SOURCE)
        self.assertIn('.claw-control-button.gpfocus', SOURCE)
        self.assertIn('.claw-control-button:focus-visible', SOURCE)
        self.assertIn('border: 2px solid #ffffff !important;', SOURCE)
        self.assertIn('box-shadow: 0 0 0 2px #31deff', SOURCE)
        for name in ("claw-style-tiles", "claw-color-tiles",
                     "claw-metric-tiles", "claw-hidden-metric-tiles",
                     "claw-weight-tiles"):
            self.assertIn(name, SOURCE, name)
        self.assertIn("min-width: 0 !important", SOURCE)
        self.assertIn("aria-pressed={styleCategory===key}", SOURCE)
        self.assertIn("aria-pressed={open}", SOURCE)
        self.assertIn("expandMetric(open ? null : key)", SOURCE)
        self.assertIn("onClick={()=>renameMetric(key)}", SOURCE)
        self.assertIn("onClick={()=>move(key,-1)}", SOURCE)
        self.assertIn("onClick={()=>move(key,1)}", SOURCE)
        self.assertIn("update({[key]:false})", SOURCE)
        self.assertIn("onChange={(checked:boolean)=>metric(id,checked)}", SOURCE)
        self.assertIn("onClick={()=>update({[key]:true})}", SOURCE)
        self.assertIn("openColorPicker(key,label)", SOURCE)
        self.assertIn("styleModified", SOURCE)

    def test_styles_save_and_restore_enabled_metric_groups_and_submetrics(self):
        helpers=(pathlib.Path(__file__).resolve().parents[1] /
                 "src/style-presets.ts").read_text()
        self.assertIn('version:3, ...styleLayoutFrom(d)', SOURCE)
        self.assertIn('...styleMetricSnapshotFrom(d)', SOURCE)
        self.assertIn('...styleMetricUpdatesFrom(preset,current.current)', SOURCE)
        self.assertIn('styleMetricSnapshotFrom, styleMetricUpdatesFrom', SOURCE)
        for name in ("styleMetricSnapshotFrom", "styleMetricUpdatesFrom",
                     "styleMetricSelectionsFrom"):
            self.assertIn("function "+name, helpers)
        self.assertIn("const selected=styleMetricSelectionsFrom(preset)", helpers)
        self.assertIn("if(current?.[key]!==value)return true;", helpers)
        self.assertIn("if(current?.metrics?.[key]!==value)return true;", helpers)
        self.assertIn("Presets save colors", SOURCE)
        self.assertIn("tests/style_presets.test.mjs", (
            pathlib.Path(__file__).resolve().parents[1] /
            ".github/workflows/layout-experiment.yml").read_text())
        self.assertNotIn("version:2, ...styleLayoutFrom(d)", SOURCE)

    def test_two_compact_preset_slots_fit_decky_width(self):
        self.assertIn('(["1","2"] as const).map(slot=>{', SOURCE)
        self.assertNotIn('(["1","2","3"] as const)', SOURCE)
        self.assertIn('className="claw-preset-list"', SOURCE)
        self.assertIn('className="claw-preset-actions"', SOURCE)
        self.assertIn('grid-template-columns: repeat(2, minmax(0, 1fr))', SOURCE)
        self.assertIn('min-width: 0 !important; margin: 0 !important', SOURCE)
        self.assertIn('max-width: 100% !important', SOURCE)
        self.assertIn('Active: ', SOURCE)
        self.assertIn('function RenameStyleModal', SOURCE)
        self.assertNotIn('Delete style', SOURCE)

    def test_expanded_card_uses_blue_surface_without_white_outline(self):
        self.assertIn("const active = open || focused;", SOURCE)
        self.assertIn('border: active ? "1px solid #2c709d"', SOURCE)
        self.assertIn('borderLeft: active ? "4px solid #08d3fa"', SOURCE)
        self.assertIn('background: active ? "#073858" : "#14243b"', SOURCE)
        self.assertIn('background: active ? "#075b83" : "#203551"', SOURCE)
        self.assertIn('open={openSection === "layout"}', SOURCE)
        self.assertIn('open={openSection === "colors"}', SOURCE)
        self.assertNotIn('claw-accordion-selection-ring', SOURCE)

    def test_closed_controller_focus_matches_expanded_card_background(self):
        self.assertIn('data-focused={focused ? "true" : "false"}', SOURCE)
        self.assertIn('onFocusCapture={()=>setFocused(true)} onBlurCapture={()=>setFocused(false)}', SOURCE)
        self.assertIn('.claw-accordion-header:focus-within > button', SOURCE)
        self.assertIn('.claw-accordion-header:has(.gpfocus) > button', SOURCE)
        self.assertIn('[data-section][data-focused="true"] .claw-accordion-header > button', SOURCE)
        self.assertIn('background: #073858 !important;', SOURCE)
        self.assertIn('background: #075b83 !important;', SOURCE)
        self.assertIn('outline: none !important;', SOURCE)
        component = SOURCE[SOURCE.index("function AccordionCard"):SOURCE.index("// Decky can remount")]
        self.assertNotIn('outline: 2px solid #ffffff', component)
        self.assertNotIn('border: open ? "2px solid #ffffff"', component)

    def test_preset_buttons_use_visual_load_and_save_icons(self):
        self.assertIn('FaPlay, FaDownload', SOURCE)
        self.assertIn('<FaPlay aria-hidden="true" /> Load', SOURCE)
        self.assertIn('<FaDownload aria-hidden="true" /> Save', SOURCE)
        self.assertIn('className="claw-preset-label"', SOURCE)
        self.assertIn('grid-template-columns: repeat(2, minmax(0, 1fr))', SOURCE)
        self.assertIn('flex: 0 0 auto;', SOURCE)

    def test_amd_gpu_metrics_v3_backport_is_in_native_build(self):
        workflow=(pathlib.Path(__file__).resolve().parents[1] /
                  ".github/workflows/layout-experiment.yml").read_text()
        script=(pathlib.Path(__file__).resolve().parents[1] /
                "experiments/enable_apu_v3_metrics.py").read_text()
        self.assertIn("python3 ../experiments/enable_apu_v3_metrics.py src", workflow)
        self.assertIn("python3 ../experiments/apply_token_styles.py src", workflow)
        self.assertLess(workflow.index("enable_apu_v3_metrics.py"),
                        workflow.index("apply_token_styles.py"))
        for required in ("gpu_metrics_v3_0", "structure_size",
                         "average_apu_power", "average_gfx_power",
                         "average_cpu_power_w", "sizeof(gpu_metrics_v3_0) == 264",
                         "nread < sizeof(gpu_metrics_v3_0)"):
            self.assertIn(required, script)

    def test_fps_size_preview_and_center_pill(self):
        for item in ('label="FPS value scale"',
                     'value={settings.fps_scale} min={100} max={200} step={10}',
                     'fontSize:Math.round(18*settings.fps_scale/100)',
                     'label="HUD position"',
                     'hudPositions.filter((anchor)=>anchor.id.startsWith(edge)).map((anchor)',
                     'settings.hud_position===anchor.id',
                     'anchor.id.endsWith("center")',
                     'value={settings.offset_x} min={-1920} max={1920} step={1}',
                     'center_horizontal:defaults.center_horizontal'):
            self.assertIn(item, SOURCE, item)

    def test_six_hud_position_buttons_are_edge_aligned(self):
        for pos in ("top-left", "top-center", "top-right",
                    "bottom-left", "bottom-center", "bottom-right"):
            self.assertIn(f'id:"{pos}"', SOURCE)
        self.assertIn('<Focusable flow-children="column" style={{display:"flex"', SOURCE)
        self.assertIn('(["top","bottom"] as const).map((edge)', SOURCE)
        self.assertIn('<Focusable key={edge} flow-children="row" style={{display:"grid"', SOURCE)
        self.assertIn('gridTemplateColumns:"repeat(3,minmax(0,1fr))"', SOURCE)
        self.assertNotIn('<Focusable flow-children="row" style={{display:"grid",', SOURCE)
        self.assertIn('label:"Top center"', SOURCE)
        self.assertIn('label:"Bottom center"', SOURCE)
        self.assertIn('settings.hud_position.endsWith("center")', SOURCE)
        self.assertNotIn('label:"Centar"', SOURCE)

    def test_gamepad_anchor_focus_is_distinct_from_selected_anchor(self):
        self.assertIn('className="claw-hud-anchor"', SOURCE)
        self.assertIn('data-anchor-position={anchor.id}', SOURCE)
        self.assertIn('aria-pressed={selected}', SOURCE)
        for selector in ('.claw-hud-anchor:focus',
                         '.claw-hud-anchor:focus-visible',
                         '.claw-hud-anchor.gpfocus',
                         '.claw-hud-anchor[class*="gpfocus"]',
                         '.claw-hud-anchor:focus-within'):
            self.assertIn(selector, SOURCE)
        self.assertIn('border: 2px solid #ffffff !important;', SOURCE)
        self.assertIn('outline: 2px solid #31deff !important;', SOURCE)
        self.assertIn('box-shadow: 0 0 0 2px #31deff', SOURCE)
        self.assertIn('offset_x: 8, offset_y: 0, padding_y: 0,', SOURCE)

    def test_fps_scale_ink_bounds_replace_font_linebox_padding(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        patch = (root / "experiments/trim_native_ink_padding.py").read_text()
        workflow = (root / ".github/workflows/layout-experiment.yml").read_text()
        self.assertIn('python3 ../experiments/trim_native_ink_padding.py src', workflow)
        self.assertLess(workflow.index('enable_fixed_numeric_slots.py'),
                        workflow.index('trim_native_ink_padding.py'))
        for marker in (
            'claw_ink_draw->VtxBuffer[vi].pos.y',
            'claw_ink_start = claw_ink_draw->VtxBuffer.Size',
            'ImGui::EndTable();',
            'std::isfinite(top)',
            'std::isfinite(bottom)',
            'claw_ink_trim_top + correction',
            'params.cellpadding_y * real_font_size.y',
            'window_size.y = ImClamp(claw_ink_bottom + claw_bottom_padding',
            'ImGuiStyleVar_WindowMinSize',
            'if (claw_ink_trim) ImGui::PopStyleVar();',
        ):
            self.assertIn(marker, patch, marker)
        self.assertNotIn('claw_ink_trim_top = claw_ink_trim_top + 10.0f', patch)

    def test_native_positioning_has_no_implicit_mangohud_edge_margin(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        patch = (root / "experiments/enable_exact_edge_anchors.py").read_text()
        workflow = (root / ".github/workflows/layout-experiment.yml").read_text()
        self.assertIn('python3 ../experiments/enable_exact_edge_anchors.py src', workflow)
        self.assertLess(workflow.index('enable_fps_size_center.py'),
                        workflow.index('enable_exact_edge_anchors.py'))
        self.assertIn('const float margin = 0.0f;', patch)
        self.assertIn('params.offset_y', patch)
        self.assertIn('params.claw_center_horizontal', patch)

    def test_new_native_controls_are_patched_after_token_styling(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/layout-experiment.yml").read_text()
        native = (root / "experiments/enable_fps_size_center.py").read_text()
        self.assertIn("python3 ../experiments/enable_fps_size_center.py src", workflow)
        self.assertLess(workflow.index("apply_token_styles.py"),
                        workflow.index("enable_fps_size_center.py"))
        for marker in ("claw_fps_scale", "claw_center_horizontal",
                       "claw_align_right", "ClawFpsFontForToken", "AddFontFromFileTTF",
                       "ImGui::GetIO().DisplaySize"):
            self.assertIn(marker, native)

    def test_frametime_styles_are_2x2_gamepad_buttons(self):
        self.assertIn('label="Frametime graph style"', SOURCE)
        self.assertNotIn('rgOptions={graphStyleOptions}', SOURCE)
        self.assertNotIn('DropdownItem', SOURCE)
        self.assertIn('function GraphStyleIcon({kind}', SOURCE)
        self.assertIn('const graphStyleChoices:', SOURCE)
        for kind, label in (("area", "Filled area"),
                            ("line", "Line"),
                            ("bars", "Histogram"),
                            ("dual", "Line + fill")):
            self.assertIn(f'id:"{kind}",label:"{label}"', SOURCE)
        self.assertNotIn('choice.letter', SOURCE)
        self.assertNotIn('letter:"A"', SOURCE)
        self.assertIn('aria-label={"Graph style: "+choice.label}', SOURCE)
        self.assertIn('<GraphStyleIcon kind={choice.id}/>', SOURCE)
        self.assertIn('width={46} height={35}', SOURCE)
        self.assertIn('minHeight:84', SOURCE)
        self.assertIn('items={graphStyleChoices} columns={2}', SOURCE)
        self.assertIn('aria-pressed={selected}', SOURCE)
        self.assertIn('onClick={()=>update({graph_style:choice.id})}', SOURCE)
        self.assertIn('disabled={!ready || !info?.layout_spacing_supported}', SOURCE)
        self.assertIn('kind === "bars"', SOURCE)
        self.assertIn('kind === "dual" ? 2.8 : 2.3', SOURCE)
        self.assertIn('fillOpacity={kind === "area" ? 0.88 : 0.19}', SOURCE)
        self.assertIn('graph_style:defaults.graph_style', SOURCE)
        
    def test_colors_subactions_support_controller_focus(self):
        self.assertIn('<Focusable flow-children="column" className="claw-preset-list">', SOURCE)
        self.assertIn('<Focusable flow-children="row" className="claw-preset-actions">', SOURCE)
        self.assertIn('className="claw-control-button" disabled={!ready||!stored}', SOURCE)
        self.assertIn('className="claw-token-controls"', SOURCE)
        self.assertIn('flow-children="row" className="claw-token-controls"', SOURCE)
        self.assertIn('className="claw-control-button claw-token-font"', SOURCE)
        self.assertIn('onClick={()=>cycleTokenWeight(token.key)}', SOURCE)
        self.assertIn('className="claw-control-button claw-token-color"', SOURCE)
        self.assertIn('onClick={()=>openTokenColorPicker(token)}', SOURCE)
        self.assertIn('className="claw-control-button claw-token-reset"', SOURCE)
        self.assertIn('disabled={!ready || !settings.token_colors?.[token.key]}', SOURCE)
        self.assertIn('onClick={()=>resetTokenColor(token.key)}', SOURCE)
        self.assertIn('aria-label={"Reset custom color: "+tokenTitle(token)}', SOURCE)

    def test_in_game_graph_taller_and_histogram_uses_separated_real_columns(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/layout-experiment.yml").read_text()
        patch = (root / "experiments/enhance_native_frametime_graph.py").read_text()
        self.assertIn("python3 ../experiments/enhance_native_frametime_graph.py src", workflow)
        self.assertLess(workflow.index("center_hud_vertically.py"),
                        workflow.index("enhance_native_frametime_graph.py"))
        # Text alignment and plot area must use identical height scaling.
        self.assertEqual(patch.count("font_size * 1.40f"), 2)
        self.assertEqual(patch.count("24.0f, 36.0f"), 2)
        self.assertIn("height = ImClamp(", patch)
        # Histogram uses actual frametimes, not fabricated or static data.
        self.assertIn("get_time_stat(HUDElements.sw_stats, idx)", patch)
        self.assertIn("const int n = ImMin(count, ImMax(2, int(w / 6.0f)))", patch)
        self.assertIn("const float bar_width = ImMax(2.0f, slot - 1.4f)", patch)
        self.assertIn("draw->AddRectFilled(", patch)
        self.assertIn("draw->PushClipRect(origin,", patch)
        self.assertIn("draw->PopClipRect();", patch)
        self.assertIn("std::isfinite(raw)", patch)
        self.assertIn("claw_style == 2", patch)
        # Geometry: 80-200px ranges, columns remain separate and within width.
        for width in (80, 100, 150, 200):
            n=max(2,int(width/6))
            slot=width/n
            bar_width=max(2.0,slot-1.4)
            self.assertLess(bar_width, slot)
            last_start=(n-1)*slot+0.7
            self.assertLessEqual(last_start+bar_width,width+0.0001)
        # No new global padding, native style ID or font-size control.
        self.assertNotIn("claw_padding_y=", patch)
        self.assertNotIn("claw_graph_height=", patch)

    def test_graph_styles_native_patch_present(self):
        root=pathlib.Path(__file__).resolve().parents[1]
        workflow=(root/".github/workflows/layout-experiment.yml").read_text()
        patcher=(root/"experiments/enable_frametime_graph_styles.py").read_text()
        self.assertIn("python3 ../experiments/enable_frametime_graph_styles.py src",workflow)
        for token in ("claw_graph_style","PlotHistogram","InvisibleButton",
                      "AddQuadFilled","AddLine","GetWindowDrawList"):
            self.assertIn(token,patcher)


    def test_zero_vertical_padding_native_patch_and_slider(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        patch = (root / "experiments/enable_zero_vertical_padding.py").read_text()
        native_build = (root / ".github/workflows/layout-experiment.yml").read_text()
        self.assertIn('label="Vertical padding (px)"', SOURCE)
        self.assertIn('padding_y: 0,', SOURCE)
        self.assertNotIn('"Dodatni padding gore/dolje (px)"', SOURCE)
        self.assertIn('python3 ../experiments/enable_zero_vertical_padding.py src', native_build)
        self.assertIn('ImVec2(params.claw_padding_x,5)', patch)
        self.assertIn('params.cellpadding_y * real_font_size.y', patch)
        self.assertIn('style.CellPadding.y = 0.0f;', patch)
        self.assertIn('GetCursorPosY() + claw_bottom_padding', patch)
        self.assertNotIn('claw_padding_y', patch)

    def test_frametime_graph_ignores_nonfinite_input(self):
        patch = (pathlib.Path(__file__).resolve().parents[1] /
                 "experiments/enable_frametime_graph_styles.py").read_text()
        self.assertIn('#include <cmath>', patch)
        self.assertIn('std::isfinite(min_time)', patch)
        self.assertIn('std::isfinite(max_time)', patch)
        self.assertIn('std::isfinite(raw_value)', patch)

    def test_fps_scale_font_atlas_supports_all_slider_steps(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        patch = (root / "experiments/enable_fps_size_center.py").read_text()
        align = (root / "experiments/center_hud_vertically.py").read_text()
        self.assertIn("font_size * 2.0f", patch)
        self.assertIn("claw_fps_digits", patch)
        self.assertIn("chosen->Scale = ImClamp(", patch)
        self.assertIn("claw_fps_scale) / 200.0f", patch)
        self.assertNotIn("font_size * params.claw_fps_scale / 100.0f", patch)
        self.assertIn("fps_font->FontSize * fps_font->Scale", align)
        for scale in range(100, 201, 10):
            with self.subTest(scale=scale):
                self.assertAlmostEqual(2.0 * (scale / 200.0), scale / 100.0)

    def test_main_card_focus_does_not_add_white_glow_or_ring(self):
        self.assertIn('const active = open || focused;', SOURCE)
        self.assertIn('onFocusCapture={()=>setFocused(true)} onBlurCapture={()=>setFocused(false)}', SOURCE)
        self.assertIn('.claw-accordion-header:focus-within .claw-accordion-icon', SOURCE)
        self.assertIn('.claw-accordion-header:has(.gpfocus) .claw-accordion-icon', SOURCE)
        self.assertNotIn('claw-accordion-selection-ring', SOURCE)
        self.assertNotIn('0 0 12px rgba(255,255,255,0.8)', SOURCE)

    def test_horizontal_center_uses_drawn_vertices_not_full_table_width(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        patch = (root / "experiments/enable_fps_size_center.py").read_text()
        workflow = (root / ".github/workflows/layout-experiment.yml").read_text()
        self.assertIn("python3 ../experiments/enable_fps_size_center.py src", workflow)
        for marker in ("claw_vertex_start = claw_draw->VtxBuffer.Size",
                       "claw_draw->VtxBuffer[vi].pos.x - window_left",
                       "ImGui::SetNextWindowSize(ImVec2(strip_width, window_size.y)",
                       "ImGui::GetIO().DisplaySize.x",
                       "content_width = ImClamp(strip_width"):
            self.assertIn(marker, patch)
        self.assertIn("params.claw_center_horizontal", patch)
        self.assertIn("LAYER_POSITION_BOTTOM_LEFT", patch)
        self.assertIn("ImGui::GetIO().DisplaySize.y - window_size.y", patch)
        self.assertIn("params.offset_y", patch)
        self.assertIn("Last drawn pixel + side padding", patch)


    def test_fixed_width_numeric_slots_keep_horizontal_hud_stable(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        patch = (root / "experiments/enable_fixed_numeric_slots.py").read_text()
        workflow = (root / ".github/workflows/layout-experiment.yml").read_text()
        self.assertIn("python3 ../experiments/enable_fixed_numeric_slots.py src", workflow)
        self.assertLess(workflow.index("center_hud_vertically.py"),
                        workflow.index("enable_fixed_numeric_slots.py"))
        for token in ('case 1:', 'case 2:', 'case 4:', 'case 9:',
                      'case 23:', 'case 24:', 'case 26:', 'case 27:',
                      'ClawSlotReference(', 'claw_pending_text_width = slot_width',
                      'stable_width = ImMax(textSize.x, claw_pending_text_width)',
                      'ImGui::ItemSize(ImVec2(stable_width, textSize.y), style.FramePadding.y)',
                      'claw_fixed_slot_right = ImMax(',
                      'claw_fixed_slot_right - window_left',
                      'ImGui::CalcTextSize(reference.c_str()).x'):
            self.assertIn(token, patch)
        self.assertIn('ClawStableText(1, ClawColorForToken(1, color)', patch)
        self.assertIn('ClawStableText(1, color, "%s", text)', patch)
        self.assertIn('ClawText(int token', patch)
        self.assertNotIn('claw_stabilize_all_metrics_by_extra_gap', patch)
        self.assertNotIn('ImGui::BeginGroup()', patch)
        self.assertNotIn('ImGui::EndGroup()', patch)
        self.assertNotIn('ImGui::Dummy(', patch)
        self.assertNotIn('ImGui::SameLine(0.0f, 0.0f)', patch)
        self.assertIn('if (!numeric && token != 1 && token != 25', patch)
        self.assertIn('HUDElements.TextColored(color, fmt, args...)', patch)

    def test_stable_numeric_layout_preserves_original_font_and_row_height(self):
        patch = (pathlib.Path(__file__).resolve().parents[1] /
                 'experiments/enable_fixed_numeric_slots.py').read_text()
        self.assertIn('ImGui::ItemSize(ImVec2(stable_width, textSize.y), style.FramePadding.y)',patch)
        self.assertIn('HUDElements.TextColored(color, "%s", rendered);', patch)
        self.assertIn('const float stable_width = ImMax(textSize.x, claw_pending_text_width);', patch)
        self.assertIn('claw_pending_text_width = 0.0f;', patch)
        self.assertIn('pos.x + stable_width', patch)
        self.assertNotIn('ImGui::ItemSize(ImVec2(stable_width, 1.0f)', patch)

    def test_fps_enlargement_centers_full_inline_hud_vertically(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/layout-experiment.yml").read_text()
        patcher = (root / "experiments/center_hud_vertically.py").read_text()
        self.assertIn("python3 ../experiments/center_hud_vertically.py src", workflow)
        self.assertLess(workflow.index("enable_frametime_graph_styles.py"),
                        workflow.index("center_hud_vertically.py"))
        # Font size is measured from real scaled FPS font rather than guessed.
        for marker in ("ClawFpsVerticalCenterOffset", "ImGui::SetCursorPosY",
                       "claw_fps_row_top", "claw_fps_scale <= 100",
                       "fps_font->FontSize", "FontGlobalScale", 'group == "fps"',
                       'group == "frame_timing"', "OVERLAY_PARAM_ENABLED_fps",
                       "ImGui::GetFontSize()"):
            self.assertIn(marker, patcher, marker)
        # No telemetry, TDP, DRAW or HUD layout settings changed.
        self.assertNotIn("main.py", patcher)
        self.assertIn('label="Frametime graph style"', SOURCE)
        self.assertIn('value={settings.fps_scale} min={100} max={200}', SOURCE)

    def test_rename_modal_uses_steam_native_gamepad_textfield(self):
        # Raw HTML inputs do not reliably invoke the virtual keyboard in SteamOS Game Mode.
        self.assertIn("  TextField,", SOURCE)
        self.assertIn('<TextField label="Metric label" focusOnMount', SOURCE)
        self.assertIn("event.currentTarget.value.slice(0,24)", SOURCE)
        self.assertIn("Use default label", SOURCE)
        self.assertIn('onOK={()=>onConfirm(cleanName(value))}', SOURCE)
        self.assertNotIn('<input autoFocus aria-label="Metric label"', SOURCE)
        self.assertNotIn('e.key===\'Enter\'', SOURCE)

    def test_advanced_github_updater_uses_decky_installer_and_confirmation(self):
        self.assertIn('const checkUpdates = callable<[], GithubUpdateInfo>("check_updates")', SOURCE)
        self.assertIn('Check for updates', SOURCE)
        self.assertIn('label="Update status"', SOURCE)
        self.assertIn('strOKButtonText="Install"', SOURCE)
        self.assertIn('release.notes', SOURCE)
        self.assertIn('installer.callable("utilities/install_plugin")', SOURCE)
        self.assertIn('release.asset_url, "Claw Metrics", release.version', SOURCE)
        self.assertIn('release.sha256, 2 /* UPDATE */', SOURCE)
        self.assertIn('Decky Settings → Developer → Install Plugin from URL', SOURCE)
        self.assertIn('If the new interface does not appear', SOURCE)
        self.assertIn('restart Decky Loader', SOURCE)
        self.assertIn('checkGithubRelease();', SOURCE)
        self.assertNotIn('fetch("https://api.github.com', SOURCE)
        # Manual consent only; no background updates or silent installations.
        self.assertIn('onOK={()=>{ dialog.Close(); requestGithubInstall(release); }}', SOURCE)
        self.assertIn('onClick={()=>{ void checkGithubRelease(); }}', SOURCE)

    def test_github_check_uses_decky_https_and_safe_python_validation(self):
        self.assertIn('GITHUB_RELEASES_API = "https://api.github.com/repos/ikorljan-droid/claw-metrics/releases?per_page=30"', SOURCE)
        self.assertIn('loader.callable("utilities/http_request")', SOURCE)
        self.assertIn('request("GET",GITHUB_RELEASES_API', SOURCE)
        self.assertIn('const validateGithubReleases = callable<[string],GithubUpdateInfo>("validate_github_releases")', SOURCE)
        self.assertIn('validateGithubReleases(http.body)', SOURCE)
        self.assertIn('if (!result.ok) throw new Error(result.error', SOURCE)
        self.assertIn('const fallback=await withTimeout(checkUpdates());', SOURCE)
        self.assertIn('if (!fallback.ok)', SOURCE)
        self.assertIn('Python HTTPS:', SOURCE)
        self.assertIn('No newer test release.', SOURCE)
        self.assertIn('GitHub API: HTTP ', SOURCE)
        # No unverified GitHub data is forwarded to the Decky installer.
        self.assertNotIn('JSON.parse(http.body)', SOURCE)
        self.assertNotIn('fetch(GITHUB_RELEASES_API)', SOURCE)

    def test_activation_keeps_primary_short_launcher_and_advanced_fallback(self):
        start=SOURCE.index('<AccordionCard id="activation"')
        advanced=SOURCE.index('<AccordionCard id="advanced"',start)
        activation=SOURCE[start:advanced]
        fallback=SOURCE[advanced:]
        self.assertIn('Copy launch command',activation)
        self.assertIn('copyLaunchCommand("short")',activation)
        self.assertNotIn('Copy stock launch command',activation)
        self.assertNotIn('FPS* potvrđuje',activation)
        self.assertIn('ControlGroup title="Backup launch commands"',fallback)
        self.assertIn('copyLaunchCommand(true)',fallback)
        self.assertIn('copyLaunchCommand();',fallback)

    def test_backend_issues_do_not_lock_entire_qam(self):
        # Settings are critical; renderer information is optional.
        self.assertIn("const saved=await withTimeout(load());", SOURCE)
        self.assertIn("setReady(true);", SOURCE)
        self.assertIn("const details=await withTimeout(getInfo());", SOURCE)
        self.assertLess(SOURCE.index("setReady(true);"),
                        SOURCE.index("const details=await withTimeout(getInfo());"))
        self.assertNotIn("Promise.all([load(), getInfo()])", SOURCE.replace(
            "// Previous Promise.all([load(),getInfo()])", ""))
        self.assertIn("setStatus(\"Settings connected; renderer information unavailable: \"", SOURCE)
        self.assertIn('title="Connection recovery"', SOURCE)
        self.assertIn("Retry backend connection", SOURCE)
        self.assertIn('disabled={connecting}', SOURCE)
        self.assertIn("if(await refresh() || cancelled)return;", SOURCE)
        self.assertIn("connectionAttempt.current", SOURCE)
        self.assertIn("Do not delete saved Claw Metrics settings.", SOURCE)

    def test_layout_nested_sliders_are_bounded_inside_cards(self):
        self.assertIn('className="claw-layout-slider"', SOURCE)
        self.assertEqual(SOURCE.count('className="claw-layout-slider"'), 10)
        self.assertIn('width: min(330px, calc(100% - 18px)) !important;', SOURCE)
        self.assertIn('max-width: calc(100% - 18px) !important;', SOURCE)
        self.assertIn('padding: 0 20px 0 0 !important;', SOURCE)
        self.assertIn('class*="SliderTrack"', SOURCE)
        self.assertIn('width: 100% !important;', SOURCE)
        self.assertIn('[data-section="layout"] .claw-layout-slider', SOURCE)
        self.assertIn('[class*="DialogSlider"]', SOURCE)
        self.assertIn('max-width: 100% !important;', SOURCE)
        # Still use SteamOS native SliderField for D-pad and numeric editing.
        self.assertIn('<SliderField label="Frametime graph width (px)"', SOURCE)
        self.assertIn('<SliderField label="Vertical padding (px)"', SOURCE)

    def test_appearance_editor_token_rows_are_compact_and_accessible(self):
        self.assertIn('className="claw-token-card"', SOURCE)
        self.assertIn('className="claw-token-title"', SOURCE)
        self.assertIn('className="claw-token-controls"', SOURCE)
        self.assertIn('minHeight:38', SOURCE)
        self.assertIn('fontSize:11.5', SOURCE)
        self.assertIn('[data-section="colors"] .claw-token-card', SOURCE)
        self.assertIn('[data-section="colors"] .claw-token-controls', SOURCE)
        self.assertIn('Font: {weightLabel[settings.token_weights?', SOURCE)
        self.assertIn('settings.token_colors?.[token.key]?"Custom":"Global"', SOURCE)
        # Every token still offers font, color and a conditional color reset.
        self.assertIn('onClick={()=>cycleTokenWeight(token.key)}', SOURCE)
        self.assertIn('onClick={()=>openTokenColorPicker(token)}', SOURCE)
        self.assertIn('onClick={()=>resetTokenColor(token.key)}', SOURCE)

    def test_metrics_show_active_sensor_fraction(self):
        self.assertIn('{count}/{total}</span>', SOURCE)
        self.assertIn('total>1', SOURCE)
        self.assertNotIn('{count} active</span>', SOURCE)

    def test_appearance_editor_expands_after_its_category_row(self):
        self.assertIn('className="claw-style-rows"', SOURCE)
        self.assertIn('styleTabs.slice(rowIndex*3,rowIndex*3+3)', SOURCE)
        self.assertIn('className="claw-style-row"', SOURCE)
        self.assertIn('items={row} columns={3} className="claw-tiles claw-style-tiles"', SOURCE)
        self.assertIn('row.some(([key])=>key===styleCategory)', SOURCE)
        self.assertIn('className="claw-style-detail"', SOURCE)
        self.assertLess(SOURCE.index('className="claw-style-detail"'),
                        SOURCE.index('styleCategory==="global" ? <>'))
        self.assertIn('onClick={()=>chooseStyleCategory(key)}', SOURCE)
        self.assertIn('lastStyleCategory = next', SOURCE)
        self.assertIn('className="claw-preset-list"', SOURCE)

    def test_ux_refresh_keeps_all_six_cards_controller_and_settings(self):
        for title in ('Position','Size & appearance','Spacing','Frametime graph'):
            self.assertIn('<ControlGroup title="'+title+'"', SOURCE)
        for title in ('Updates','Diagnostics','Backup launch commands'):
            self.assertIn('<ControlGroup title="'+title+'"', SOURCE)
        self.assertIn('row.includes(expanded)', SOURCE)
        self.assertIn('visible.slice(rowIndex*3,rowIndex*3+3)', SOURCE)
        self.assertIn('aria-label={"Rename "+styleTitle(slot)}', SOURCE)
        self.assertIn('onClick={()=>renameStyle(slot)}', SOURCE)
        self.assertIn('if(stored) confirmAction("Overwrite "+styleTitle(slot)+"?"', SOURCE)
        self.assertIn('style_names: Record<string,string>', SOURCE)
        self.assertIn('onClick={()=>update({font_weight:weight})}', SOURCE)
        self.assertNotIn('font_weight:weight,token_weights:{}', SOURCE)
        self.assertIn('HEX color (#RRGGBB)', SOURCE)
        self.assertIn('showTechnical?"Hide technical details":"Show technical details"', SOURCE)
        self.assertIn('Enable Frametime', SOURCE)
        # The previous confusing legacy testing guidance is gone.
        self.assertNotIn('FPS*', SOURCE)
        self.assertNotIn('testnu Vulkan', SOURCE)
        # User-facing content is English: Croatian accented letters should not remain.
        import re
        self.assertIsNone(re.search(r'[čćžšđČĆŽŠĐ]', SOURCE))

    def test_sections_keep_actions_and_do_not_fake_monitoring(self):
        self.assertIn("verifyRenderer", SOURCE)
        self.assertIn("copyLaunchCommand(true)", SOURCE)
        self.assertIn('copyLaunchCommand("short")', SOURCE)
        self.assertIn("short_launcher_ready", SOURCE)
        self.assertIn("onChange={(value: number) => update(", SOURCE)
        self.assertIn('Check TDP sensor', SOURCE)
        self.assertIn('get_tdp_status', SOURCE)


if __name__ == "__main__":
    unittest.main()
