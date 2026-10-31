#!/usr/bin/env python3
"""Backport AMD gpu_metrics v3.0 (Z2 Extreme) to our pinned MangoHud 0.8.1.

Schema: MangoHud v0.8.2 src/amdgpu.h; power arithmetic follows the
confirmed MangoHud Z2 Extreme fix (flightlessmango/MangoHud#1851).
This is intentionally independent of our Vulkan overlay/style patches.
"""
import pathlib
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "src")
header = root / "amdgpu.h"
source = root / "amdgpu.cpp"

def replace_once(data, old, new, context):
    if data.count(old) != 1:
        raise RuntimeError(f"{context}: expected one exact anchor, found {data.count(old)}")
    return data.replace(old, new, 1)

struct_v3 = "struct gpu_metrics_v3_0 {\n\tstruct metrics_table_header\tcommon_header;\n\n\t/* Temperature */\n\t/* gfx temperature on APUs */\n\tuint16_t\t\t\ttemperature_gfx;\n\t/* soc temperature on APUs */\n\tuint16_t\t\t\ttemperature_soc;\n\t/* CPU core temperature on APUs */\n\tuint16_t\t\t\ttemperature_core[16];\n\t/* skin temperature on APUs */\n\tuint16_t\t\t\ttemperature_skin;\n\n\t/* Utilization */\n\t/* time filtered GFX busy % [0-100] */\n\tuint16_t\t\t\taverage_gfx_activity;\n\t/* time filtered VCN busy % [0-100] */\n\tuint16_t\t\t\taverage_vcn_activity;\n\t/* time filtered IPU per-column busy % [0-100] */\n\tuint16_t\t\t\taverage_ipu_activity[8];\n\t/* time filtered per-core C0 residency % [0-100]*/\n\tuint16_t\t\t\taverage_core_c0_activity[16];\n\t/* time filtered DRAM read bandwidth [MB/sec] */\n\tuint16_t\t\t\taverage_dram_reads;\n\t/* time filtered DRAM write bandwidth [MB/sec] */\n\tuint16_t\t\t\taverage_dram_writes;\n\t/* time filtered IPU read bandwidth [MB/sec] */\n\tuint16_t\t\t\taverage_ipu_reads;\n\t/* time filtered IPU write bandwidth [MB/sec] */\n\tuint16_t\t\t\taverage_ipu_writes;\n\n\t/* Driver attached timestamp (in ns) */\n\tuint64_t\t\t\tsystem_clock_counter;\n\n\t/* Power/Energy */\n\t/* time filtered power used for PPT/STAPM [APU+dGPU] [mW] */\n\tuint32_t\t\t\taverage_socket_power;\n\t/* time filtered IPU power [mW] */\n\tuint16_t\t\t\taverage_ipu_power;\n\t/* time filtered APU power [mW] */\n\tuint32_t\t\t\taverage_apu_power;\n\t/* time filtered GFX power [mW] */\n\tuint32_t\t\t\taverage_gfx_power;\n\t/* time filtered dGPU power [mW] */\n\tuint32_t\t\t\taverage_dgpu_power;\n\t/* time filtered sum of core power across all cores in the socket [mW] */\n\tuint32_t\t\t\taverage_all_core_power;\n\t/* calculated core power [mW] */\n\tuint16_t\t\t\taverage_core_power[16];\n\t/* time filtered total system power [mW] */\n\tuint16_t\t\t\taverage_sys_power;\n\t/* maximum IRM defined STAPM power limit [mW] */\n\tuint16_t\t\t\tstapm_power_limit;\n\t/* time filtered STAPM power limit [mW] */\n\tuint16_t\t\t\tcurrent_stapm_power_limit;\n\n\t/* time filtered clocks [MHz] */\n\tuint16_t\t\t\taverage_gfxclk_frequency;\n\tuint16_t\t\t\taverage_socclk_frequency;\n\tuint16_t\t\t\taverage_vpeclk_frequency;\n\tuint16_t\t\t\taverage_ipuclk_frequency;\n\tuint16_t\t\t\taverage_fclk_frequency;\n\tuint16_t\t\t\taverage_vclk_frequency;\n\tuint16_t\t\t\taverage_uclk_frequency;\n\tuint16_t\t\t\taverage_mpipu_frequency;\n\n\t/* Current clocks */\n\t/* target core frequency [MHz] */\n\tuint16_t\t\t\tcurrent_coreclk[16];\n\t/* CCLK frequency limit enforced on classic cores [MHz] */\n\tuint16_t\t\t\tcurrent_core_maxfreq;\n\t/* GFXCLK frequency limit enforced on GFX [MHz] */\n\tuint16_t\t\t\tcurrent_gfx_maxfreq;\n\n\t/* Throttle Residency (ASIC dependent) */\n\tuint32_t\t\t\tthrottle_residency_prochot;\n\tuint32_t\t\t\tthrottle_residency_spl;\n\tuint32_t\t\t\tthrottle_residency_fppt;\n\tuint32_t\t\t\tthrottle_residency_sppt;\n\tuint32_t\t\t\tthrottle_residency_thm_core;\n\tuint32_t\t\t\tthrottle_residency_thm_gfx;\n\tuint32_t\t\t\tthrottle_residency_thm_soc;\n\n\t/* Metrics table alpha filter time constant [us] */\n\tuint32_t\t\t\ttime_filter_alphavalue;\n};\n\n"
h = header.read_text(encoding="utf-8")
if "struct gpu_metrics_v3_0" in h:
    raise RuntimeError("MangoHud already has v3.0 struct; refusing double patch")
h = replace_once(h, "struct amdgpu_files\n", struct_v3 + "struct amdgpu_files\n", "v3 header")
h = replace_once(h, "struct gpu_metrics_v3_0 {", "struct gpu_metrics_v3_0 {", "v3 exists")
# Ensure exact Linux kernel structure layout; device reports size 0x0108=264.
h = replace_once(h, struct_v3 + "struct amdgpu_files\n",
    struct_v3 + 'static_assert(sizeof(gpu_metrics_v3_0) == 264, "Unexpected AMD gpu_metrics 3.0 layout");\n\n'
    + "struct amdgpu_files\n", "v3 struct assertion")

s = source.read_text(encoding="utf-8")
s = replace_once(s,
    "\t\t\tthis->is_apu = true;\n\t\t\treturn true;\n\t\tdefault:\n",
    "\t\t\tthis->is_apu = true;\n\t\t\treturn true;\n"
    "\t\tcase 3: // gfx metrics 3.0 on Z2 Extreme and newer AMD APUs\n"
    "\t\t\tif (header.content_revision != 0 || header.structure_size < sizeof(gpu_metrics_v3_0))\n"
    "\t\t\t\tbreak;\n"
    "\t\t\tthis->is_apu = true;\n"
    "\t\t\treturn true;\n"
    "\t\tdefault:\n", "recognize v3.0 and its structure size")
s = replace_once(s,
    "\tvoid *buf[MAX(sizeof(struct gpu_metrics_v1_3), sizeof(struct gpu_metrics_v2_4))/sizeof(void*)+1];\n"
    "\tstruct metrics_table_header* header = (metrics_table_header*)buf;",
    "\talignas(gpu_metrics_v3_0) unsigned char buf[sizeof(gpu_metrics_v3_0) + 1] = {};\n"
    "\tstruct metrics_table_header* header = (metrics_table_header*)buf;",
    "read complete 264-byte v3.0 blob with correct alignment")
s = replace_once(s,
    "\t// Read the whole file\n"
    "\tif (fread(buf, sizeof(buf), 1, f) != 0) {\n"
    "\t\tSPDLOG_DEBUG(\"amdgpu metrics file '{}' is larger than the buffer\", gpu_metrics_path.c_str());\n"
    "\t\tfclose(f);\n"
    "\t\treturn;\n"
    "\t}\n"
    "\tfclose(f);",
    "\t// Read a variable-length sysfs blob; v3.0 is 264 bytes. Avoid stale/short data.\n"
    "\tsize_t nread = fread(buf, 1, sizeof(buf), f);\n"
    "\tfclose(f);\n"
    "\tif (nread < sizeof(*header) || nread == sizeof(buf)) return;\n"
    "\tif (header->format_revision == 3 && (header->content_revision != 0 ||\n"
    "\t\t\theader->structure_size < sizeof(gpu_metrics_v3_0) || nread < sizeof(gpu_metrics_v3_0)))\n"
    "\t\treturn;",
    "read correct length; reject partial v3 telemetry")
s = replace_once(s,
    "\t\tindep_throttle_status = amdgpu_metrics->indep_throttle_status;\n\t}\n\n\t/* Throttling: See",
    "\t\tindep_throttle_status = amdgpu_metrics->indep_throttle_status;\n"
    "\t} else if (header->format_revision == 3) {\n"
    "\t\t// Z2 Extreme: average_apu_power includes GFX; remove GFX portion.\n"
    "\t\tauto *v3 = reinterpret_cast<gpu_metrics_v3_0*>(buf);\n"
    "\t\tmetrics->gpu_load_percent = v3->average_gfx_activity;\n"
    "\t\tmetrics->gpu_temp_c = v3->temperature_gfx / 100;\n"
    "\t\tmetrics->soc_temp_c = v3->temperature_soc / 100;\n"
    "\t\tint hottest = 0;\n"
    "\t\tfor (auto core : v3->temperature_core) {\n"
    "\t\t\tif (core == 0xffff) break;\n"
    "\t\t\tif (core > hottest) hottest = core;\n"
    "\t\t}\n"
    "\t\tmetrics->apu_cpu_temp_c = hottest / 100;\n"
    "\t\tconst int64_t apu_mw = v3->average_apu_power;\n"
    "\t\tconst int64_t gfx_mw = v3->average_gfx_power;\n"
    "\t\tmetrics->average_cpu_power_w = static_cast<float>(MAX(0LL, apu_mw - gfx_mw)) / 1000.0f;\n"
    "\t\tmetrics->average_gfx_power_w = static_cast<float>(gfx_mw) / 1000.0f;\n"
    "\t\tmetrics->current_gfxclk_mhz = v3->average_gfxclk_frequency;\n"
    "\t\tmetrics->current_uclk_mhz = v3->average_uclk_frequency;\n"
    "\t\t// v3 uses residency counters instead of v1/v2 throttle bits.\n"
    "\t\t// Do not invent an instantaneous throttle status from those counters.\n"
    "\t}\n\n\t/* Throttling: See", "decode v3 APU/GFX watts")
header.write_text(h, encoding="utf-8")
source.write_text(s, encoding="utf-8")
print("Backported AMD gpu_metrics 3.0 on the native MangoHud 0.8.1 source")
