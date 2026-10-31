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

    def test_selected_main_group_has_white_persistent_outline(self):
        self.assertIn('border: open ? "2px solid #ffffff"', SOURCE)
        self.assertIn('boxShadow: open ? "inset 0 0 0 1px #ffffff', SOURCE)
        self.assertIn('width: "100%", maxWidth: "100%", minWidth: 0, boxSizing: "border-box"', SOURCE)
        self.assertIn('open={openSection === "layout"}', SOURCE)
        self.assertIn('open={openSection === "colors"}', SOURCE)

    def test_selected_group_border_is_drawn_above_decky_button(self):
        # The wrapper's old border was insufficient with Steam's focus styling.
        self.assertIn('data-selected={open ? "true" : "false"}', SOURCE)
        self.assertIn('className="claw-accordion-header"', SOURCE)
        self.assertIn('className="claw-accordion-selection-ring"', SOURCE)
        self.assertIn('position:"absolute",inset:3,zIndex:2,pointerEvents:"none"', SOURCE)
        self.assertIn('border:open?"2px solid #ffffff":"2px solid transparent"', SOURCE)
        self.assertIn('[data-section][data-selected="true"] .claw-accordion-header > button', SOURCE)
        self.assertIn('outline: 2px solid #ffffff !important', SOURCE)

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
