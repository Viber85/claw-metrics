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
                     'label="Položaj HUD-a"',
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
        self.assertIn('label:"Gore sredina"', SOURCE)
        self.assertIn('label:"Dolje sredina"', SOURCE)
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
        self.assertIn('label="Tip frametime grafa"', SOURCE)
        self.assertNotIn('rgOptions={graphStyleOptions}', SOURCE)
        self.assertNotIn('DropdownItem', SOURCE)
        self.assertIn('function GraphStyleIcon({kind}', SOURCE)
        self.assertIn('const graphStyleChoices:', SOURCE)
        for kind, letter, label in (("area", "A", "Ispuna"),
                                    ("line", "B", "Linijski graf"),
                                    ("bars", "C", "Histogram"),
                                    ("dual", "F", "Linija + ispuna")):
            self.assertIn(f'id:"{kind}",letter:"{letter}",label:"{label}"', SOURCE)
        self.assertIn('items={graphStyleChoices} columns={2}', SOURCE)
        self.assertIn('aria-pressed={selected}', SOURCE)
        self.assertIn('onClick={()=>update({graph_style:choice.id})}', SOURCE)
        self.assertIn('disabled={!ready || !info?.layout_spacing_supported}', SOURCE)
        self.assertIn('kind === "bars"', SOURCE)
        self.assertIn('kind === "dual" ? 2.4 : 1.7', SOURCE)
        self.assertIn('fillOpacity={kind === "area" ? 0.8 : 0.2}', SOURCE)
        self.assertIn('graph_style:defaults.graph_style', SOURCE)
        
    def test_colors_subactions_support_controller_focus(self):
        self.assertIn('<Focusable flow-children="column" className="claw-preset-list">', SOURCE)
        self.assertIn('<Focusable flow-children="row" className="claw-preset-actions">', SOURCE)
        self.assertIn('className="claw-control-button" disabled={!ready||!stored}', SOURCE)
        self.assertIn('<Focusable flow-children="row" style={{display:"flex",gap:5}}>', SOURCE)
        self.assertIn('className="claw-control-button" disabled={!ready} onClick={()=>openTokenColorPicker(token)}', SOURCE)
        self.assertIn('className="claw-control-button" disabled={!ready || !settings.token_colors?.[token.key]}', SOURCE)

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
        self.assertIn('["padding_y", "Padding gore/dolje (px)", 0, 24, 1]', SOURCE)
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
