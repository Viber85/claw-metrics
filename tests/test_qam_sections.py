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
        self.assertIn('useState<SectionKey | null>("metrics")', SOURCE)
        self.assertIn('setOpenSection(old => old === id ? null : id)', SOURCE)
        self.assertIn("<DialogButton onClick={onToggle}", SOURCE)

    def test_existing_controls_and_safe_color_picker_survive(self):
        for option in (
            "Kopiraj launch komandu", "Kopiraj testnu komandu",
            "Razmak unutar grupa", "Širina frametime grafa",
            "Vrati zadane boje", "OpaqueColorPicker",
            "SemiBold", "fps_bold", "font_weight", "MangoHud",
            "Vrati položaj", "Battery", "TDP · Panel de Control",
        ):
            self.assertIn(option, SOURCE, option)
        self.assertNotIn("ColorPickerModal", SOURCE)

    def test_sections_keep_actions_and_do_not_fake_monitoring(self):
        self.assertIn("verifyRenderer", SOURCE)
        self.assertIn("copyLaunchCommand(true)", SOURCE)
        self.assertIn("onChange={(value: number) => update(", SOURCE)
        self.assertIn('Očitanje primijenjenog limita još nije dostupno.', SOURCE)


if __name__ == "__main__":
    unittest.main()
