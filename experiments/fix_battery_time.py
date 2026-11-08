"""Use the checked battery formatter in both classic HUD battery paths."""
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'src')
path=root/'hud_elements.cpp';text=path.read_text()
condition='if (Battery_Stats.current_watt != 0) {'
# Restrict all changes to the battery function, with exact anchors/counts.
start=text.index('void HudElements::battery()')
end=text.index('\nvoid HudElements::',start+1)
battery=text[start:end]
assert battery.count(condition)==2
reading='claw_modular::battery_time(Battery_Stats.batt_count, Battery_Stats.current_status, Battery_Stats.remaining_time)'
battery=battery.replace(condition,'if (!'+reading+'.plugged) {')
a=battery.index('                float hours = 0.0f;');b=battery.index('\n            }',a)
battery=battery[:a]+'''                const auto remaining = '''+reading+''';
                ClawMetricGap();
                if (remaining.plugged)
                    HUDElements.TextColored(ClawColorForToken(24, HUDElements.colors.text), "%s", ICON_FK_PLUG);
                else
                    ClawText(24, HUDElements.colors.text, "%s", remaining.text.c_str());'''+battery[b:]
a=battery.index('                    float hours;');b=battery.index('\n                    if (!HUDElements.params',a)
battery=battery[:a]+'''                    const auto remaining = '''+reading+''';
                    const char* time_buffer = remaining.plugged ? ICON_FK_PLUG : remaining.text.c_str();
'''+battery[b:]
assert 'modf(Battery_Stats.remaining_time' not in battery
path.write_text(text[:start]+battery+text[end:])
