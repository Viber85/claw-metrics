"""Regression checks for the grouped Decky QAM interface.

Static checks complement TypeScript and Rollup compilation. They guard
against future redesigns accidentally hiding/removing working controls.
"""
import pathlib
import unittest

SOURCE = (pathlib.Path(__file__).resolve().parents[1] / "src" / "index.tsx").read_text()


class GroupedQamTests(unittest.TestCase):
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
            "Kopiraj launch komandu", "Kopiraj testnu komandu",
            "Kopiraj kratku testnu komandu", "Prikaži dugu rezervnu komandu",
            "Razmak unutar grupa", "Širina frametime grafa",
            "Vrati zadane boje", "OpaqueColorPicker",
            "SemiBold", "font_weight", "MangoHud",
            "Vrati zadane postavke Layouta", "Battery", "TDP limit (read-only)",
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
        self.assertIn('lastStyleCategory = id', SOURCE)
        self.assertIn('setStyleCategory(id)', SOURCE)

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
                     "active_style", "Vrijednosti", "DRAW", "Clock",
                     "Vrati zadane postavke Layouta", "groupIcons"):
            self.assertIn(name, SOURCE, name)
        self.assertIn("token_weights:{}", SOURCE)
        self.assertIn("token_colors:{}", SOURCE)

    def test_compact_three_column_grids_preserve_actions_and_focus(self):
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr))", SOURCE)
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

    def test_two_compact_preset_slots_fit_decky_width(self):
        self.assertIn('(["1","2"] as const).map(slot=>{', SOURCE)
        self.assertNotIn('(["1","2","3"] as const)', SOURCE)
        self.assertIn('className="claw-preset-list"', SOURCE)
        self.assertIn('className="claw-preset-actions"', SOURCE)
        self.assertIn('grid-template-columns: repeat(2, minmax(0, 1fr))', SOURCE)
        self.assertIn('min-width: 0 !important; margin: 0 !important', SOURCE)
        self.assertIn('max-width: 100% !important', SOURCE)
        self.assertIn('Trenutno učitan: Stil', SOURCE)
        self.assertNotIn('Preimenuj stil', SOURCE)
        self.assertNotIn('Obriši stil', SOURCE)

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
        self.assertIn('<FaPlay aria-hidden="true" /> Učitaj', SOURCE)
        self.assertIn('<FaDownload aria-hidden="true" /> Spremi', SOURCE)
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
        for item in ('label="FPS – veličina broja"',
                     'value={settings.fps_scale} min={100} max={200} step={10}',
                     'fontSize:Math.round(18*settings.fps_scale/100)',
                     'label="Centriraj horizontalno"',
                     'checked={settings.center_horizontal}',
                     'disabled={!ready || settings.center_horizontal}',
                     'value={settings.offset_x} min={-1920} max={1920} step={1}',
                     'center_horizontal:defaults.center_horizontal'):
            self.assertIn(item, SOURCE, item)

    def test_new_native_controls_are_patched_after_token_styling(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/layout-experiment.yml").read_text()
        native = (root / "experiments/enable_fps_size_center.py").read_text()
        self.assertIn("python3 ../experiments/enable_fps_size_center.py src", workflow)
        self.assertLess(workflow.index("apply_token_styles.py"),
                        workflow.index("enable_fps_size_center.py"))
        for marker in ("claw_fps_scale", "claw_center_horizontal",
                       "ClawFpsFontForToken", "AddFontFromFileTTF",
                       "ImGui::GetIO().DisplaySize"):
            self.assertIn(marker, native)

    def test_frametime_dropdown_has_four_styles(self):
        self.assertIn('label="Tip frametime grafa"',SOURCE)
        self.assertIn('rgOptions={graphStyleOptions} selectedOption={settings.graph_style}',SOURCE)
        self.assertIn('function GraphStyleIcon({kind}',SOURCE)
        self.assertIn('function graphOption(kind:GraphStyle, label:string)',SOURCE)
        for kind, label in (("area","A · Ispuna"),("line","B · Linijski graf"),
                            ("bars","C · Histogram"),("dual","F · Linija + blaga ispuna")):
            self.assertIn(f'graphOption("{kind}","{label}")',SOURCE)
        self.assertIn('kind === "bars"',SOURCE)
        self.assertIn('kind === "dual" ? 2.4 : 1.7',SOURCE)
        self.assertIn('fillOpacity={kind === "area" ? 0.8 : 0.2}',SOURCE)
        self.assertIn('maxWidth:"100%",minWidth:0',SOURCE)
        self.assertIn("graph_style:defaults.graph_style",SOURCE)

    def test_graph_styles_native_patch_present(self):
        root=pathlib.Path(__file__).resolve().parents[1]
        workflow=(root/".github/workflows/layout-experiment.yml").read_text()
        patcher=(root/"experiments/enable_frametime_graph_styles.py").read_text()
        self.assertIn("python3 ../experiments/enable_frametime_graph_styles.py src",workflow)
        for token in ("claw_graph_style","PlotHistogram","InvisibleButton",
                      "AddQuadFilled","AddLine","GetWindowDrawList"):
            self.assertIn(token,patcher)


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
        self.assertIn('label="Tip frametime grafa"', SOURCE)
        self.assertIn('value={settings.fps_scale} min={100} max={200}', SOURCE)

    def test_rename_modal_uses_steam_native_gamepad_textfield(self):
        # Raw HTML inputs do not reliably invoke the virtual keyboard in SteamOS Game Mode.
        self.assertIn("  TextField,", SOURCE)
        self.assertIn('<TextField label="Naziv stavke" focusOnMount', SOURCE)
        self.assertIn("event.currentTarget.value.slice(0,24)", SOURCE)
        self.assertIn("Vrati zadani naziv", SOURCE)
        self.assertIn('onOK={()=>onConfirm(cleanName(value))}', SOURCE)
        self.assertNotIn('<input autoFocus aria-label="Naziv stavke"', SOURCE)
        self.assertNotIn('e.key===\'Enter\'', SOURCE)

    def test_sections_keep_actions_and_do_not_fake_monitoring(self):
        self.assertIn("verifyRenderer", SOURCE)
        self.assertIn("copyLaunchCommand(true)", SOURCE)
        self.assertIn('copyLaunchCommand("short")', SOURCE)
        self.assertIn("short_launcher_ready", SOURCE)
        self.assertIn("onChange={(value: number) => update(", SOURCE)
        self.assertIn('Provjeri TDP očitanje', SOURCE)
        self.assertIn('get_tdp_status', SOURCE)


if __name__ == "__main__":
    unittest.main()
