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
