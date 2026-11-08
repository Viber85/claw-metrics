// Included at the end of hud_elements.cpp: reuses its actual fonts/colors/sensors.
bool ClawTryModular() {
    const char* filename=std::getenv("CLAW_MODULAR_LAYOUT_FILE");
    if(!filename||!*filename)filename=HUDElements.params->claw_modular_file.c_str();
    if(!filename||!*filename)return false;
    static claw_modular::FileLoader loader(filename);
    static std::shared_ptr<const claw_modular::Document> active;
    if(auto next=loader.take())active=std::move(next);
    if(!active)return false; // Until a valid import exists, keep the working HUD.
    auto& p=*HUDElements.params;auto& data=*HUDElements.sw_stats;
    if(p.no_display||steam_focused)return true;
    using claw_modular::Text;
    static const char* keys[]={"fps.label","fps.value","fps.ms","cpu.label","cpu.load","cpu.temp","cpu.clock","cpu.power","gpu.label","gpu.load","gpu.temp","gpu.clock","gpu.power","gpu.junction","gpu.fan","gpu.voltage","ram.label","ram.value","vram.label","vram.value","vram.temp","vram.clock","battery.label","battery.value","battery.time","battery.power","time.value","tdp.value","fps.average","fps.low1","ram.game","ram.swap"};
    std::map<std::string,Text> readings;
    auto fmt=[](const char* format,double value,bool valid=true){
        if(!valid||!std::isfinite(value))return std::string("--");
        char buffer[128];std::snprintf(buffer,sizeof(buffer),format,value);return std::string(buffer);
    };
    for(int token=0;token<32;++token){
        ImFont* font=ClawFontForToken(token);if(!font)font=ImGui::GetFont();
        ImVec4 color=HUDElements.colors.text;
        if(token==0)color=HUDElements.colors.engine;
        if(token==1&&p.enabled[OVERLAY_PARAM_ENABLED_fps_color_change]){
            LOAD_DATA levels={HUDElements.colors.fps_value_low,HUDElements.colors.fps_value_med,HUDElements.colors.fps_value_high,p.fps_value[0],p.fps_value[1]};
            color=change_on_load_temp(levels,int(data.fps));
        }
        if(token==3)color=HUDElements.colors.cpu;
        if(token==8)color=HUDElements.colors.gpu;
        if(token==16)color=HUDElements.colors.ram;
        if(token==18)color=HUDElements.colors.vram;
        if(token==22)color=HUDElements.colors.battery;
        readings[keys[token]]={"--",font,ImGui::ColorConvertFloat4ToU32(ClawColorForToken(token,color))};
    }
    auto set=[&](const char* key,std::string value){readings.at(key).value=std::move(value);};
    set("fps.label",p.fps_text.empty()?"FPS":p.fps_text);
    set("fps.value",fmt("%.0f",data.fps,data.fps>0));
    set("fps.ms",fmt("%.1f ms",data.fps>0?1000.0/data.fps:0,data.fps>0));
    set("fps.average",std::string("AVG ")+fmt("%.1f",data.claw_frames.average,data.claw_frames.count()>0));
    set("fps.low1",std::string("1% LOW ")+fmt("%.1f",data.claw_frames.low1,data.claw_frames.low1_ready));
    set("cpu.label",p.cpu_text.empty()?"CPU":p.cpu_text);
    const auto cpu=cpuStats.GetCPUDataTotal();
    set("cpu.load",fmt("%.0f%%",int(cpu.percent),p.enabled[OVERLAY_PARAM_ENABLED_cpu_stats]));
    auto temp=[&](double value,bool available){return fmt(p.enabled[OVERLAY_PARAM_ENABLED_temp_fahrenheit]?"%.0f°F":"%.0f°C",p.enabled[OVERLAY_PARAM_ENABLED_temp_fahrenheit]?HUDElements.convert_to_fahrenheit(value):value,available);};
    set("cpu.temp",temp(cpu.temp,p.enabled[OVERLAY_PARAM_ENABLED_cpu_temp]));
    set("cpu.clock",fmt("%.0f MHz",cpu.cpu_mhz,p.enabled[OVERLAY_PARAM_ENABLED_cpu_mhz]));
    set("cpu.power",fmt("%.1f W",cpu.power,p.enabled[OVERLAY_PARAM_ENABLED_cpu_power]));
    set("gpu.label","GPU");
    if(!gpus&&p.enabled[OVERLAY_PARAM_ENABLED_gpu_stats])gpus=std::make_unique<GPUS>(&p);
    if(gpus){
        auto selected=gpus->selected_gpus();
        if(!selected.empty()){
            auto gpu=selected.front();const auto m=gpu->metrics;
            set("gpu.label",gpu->gpu_text());
            set("gpu.load",fmt("%.0f%%",m.load,p.enabled[OVERLAY_PARAM_ENABLED_gpu_stats]));
            set("gpu.temp",temp(m.temp,p.enabled[OVERLAY_PARAM_ENABLED_gpu_temp]));
            set("gpu.clock",fmt("%.0f MHz",m.CoreClock,p.enabled[OVERLAY_PARAM_ENABLED_gpu_core_clock]));
            set("gpu.power",fmt("%.1f W",m.powerUsage,p.enabled[OVERLAY_PARAM_ENABLED_gpu_power]));
            set("gpu.junction",temp(m.junction_temp,m.junction_temp>=0&&p.enabled[OVERLAY_PARAM_ENABLED_gpu_junction_temp]));
            set("gpu.fan",fmt(m.fan_rpm?"%.0f RPM":"%.0f%% FAN",m.fan_speed,!gpu->is_apu()&&p.enabled[OVERLAY_PARAM_ENABLED_gpu_fan]));
            set("gpu.voltage",fmt("%.0f mV",m.voltage,p.enabled[OVERLAY_PARAM_ENABLED_gpu_voltage]));
            set("vram.value",fmt("%.1f GiB",m.memoryUsed+(gpu->is_apu()?m.gtt_used:0),p.enabled[OVERLAY_PARAM_ENABLED_vram]));
            set("vram.temp",temp(m.memory_temp,m.memory_temp>=0&&p.enabled[OVERLAY_PARAM_ENABLED_gpu_mem_temp]));
            set("vram.clock",fmt("%.0f MHz",m.MemClock,p.enabled[OVERLAY_PARAM_ENABLED_gpu_mem_clock]));
        }
    }
    set("ram.label",p.claw_ram_label.empty()?"RAM":p.claw_ram_label);
    set("ram.value",fmt("%.1f GiB",memused,p.enabled[OVERLAY_PARAM_ENABLED_ram]));
    set("ram.game",std::string("GAME ")+fmt("%.1f GiB",proc_mem_resident/1073741824.0,claw_proc_mem_valid&&p.claw_ram_game));
    set("ram.swap",std::string("SWAP ")+fmt("%.1f GiB",swapused,p.enabled[OVERLAY_PARAM_ENABLED_swap]));
    set("vram.label",p.claw_vram_label.empty()?"VRAM":p.claw_vram_label);
    set("battery.label",p.claw_battery_label.empty()?"BATT":p.claw_battery_label);
    set("battery.value",fmt("%.0f%%",Battery_Stats.current_percent,Battery_Stats.batt_count>0));
    const auto remaining=claw_modular::battery_time(Battery_Stats.batt_count,Battery_Stats.current_status,Battery_Stats.remaining_time,Battery_Stats.external_power.load());
    set("battery.time",remaining.text);readings["battery.time"].plugged=remaining.plugged;
    set("time.value",data.time.empty()?"--":data.time);
    set("tdp.value","TDP --");set("battery.power","DRAW --");
    for(const auto& item:HUDElements.exec_list){
        if(item.value.find("tdp.txt")!=std::string::npos)set("tdp.value",claw_modular::power_text(item.ret,"TDP"));
        if(item.value.find("draw.txt")!=std::string::npos)set("battery.power",claw_modular::power_text(item.ret,"DRAW"));
    }
    const char* slots[]={"","","888.8 ms","","100%","888°C","8888 MHz","88.8 W","","100%","888°C","8888 MHz","88.8 W","888°C","88888 RPM","8888 mV","","888.8 GiB","","888.8 GiB","888°C","8888 MHz","","100%","88:88","","88:88","","AVG 8888.8","1% LOW 8888.8","GAME 888.8 GiB","SWAP 888.8 GiB"};
    for(int token=0;token<32;++token)readings[keys[token]].slot=slots[token];
    for(int token:{25,27})readings[keys[token]].slot=ClawSlotReference(token,"%s",readings[keys[token]].value.c_str());
    // Keep existing TDP layout nodes and their explicit overrides intact while
    // applying separate category/value styles from Colors & Fonts.
    auto& tdp=readings["tdp.value"];
    const auto tdp_parts=claw_modular::power_parts(tdp.value,"TDP");
    tdp.prefix=tdp_parts.first;tdp.value=tdp_parts.second;tdp.slot="100 W";
    tdp.prefix_font=ClawFontForToken(32);if(!tdp.prefix_font)tdp.prefix_font=ImGui::GetFont();
    tdp.prefix_color=ImGui::ColorConvertFloat4ToU32(ClawColorForToken(32,HUDElements.colors.engine));
    data.stat_selector=OVERLAY_PLOTS_frame_timing;
    data.time_dividor=1000000.0f;
    std::vector<float> graph;
    const size_t count=std::min<uint64_t>(data.n_frames,ARRAY_SIZE(data.frames_stats));
    for(size_t k=0;k<count;++k){
        const auto& point=data.frames_stats[(data.n_frames-count+k)%ARRAY_SIZE(data.frames_stats)];
        const double ms=point.stats[OVERLAY_PLOTS_frame_timing]/1000000.0;
        if(std::isfinite(ms)&&ms>=0&&ms<=1000000)graph.push_back(float(ms));
    }
    std::vector<claw_modular::Style> styles(active->nodes.size());
    styles[0].rounding=p.round_corners;
    auto packed=[&](const std::string& hex,float opacity)->ImU32{
        if(hex.empty())return 0;
        const unsigned rgb=std::stoul(hex,nullptr,16);
        ImVec4 color(((rgb>>16)&255)/255.f,((rgb>>8)&255)/255.f,(rgb&255)/255.f,opacity/100);
        if(HUDElements.colors.convert)color=SRGBToLinear(color);
        return ImGui::ColorConvertFloat4ToU32(color);
    };
    for(size_t i=0;i<styles.size();++i){
        const auto& a=active->appearance[i];
        if(!a.background.empty())styles[i].fill=packed(a.background,a.opacity);
        styles[i].text=packed(a.color,100);
        if(i)styles[i].rounding=a.corner_radius>=0?a.corner_radius:(a.outline?6:0);
        if(a.outline){styles[i].outline=packed(a.outline_color,a.outline_opacity);styles[i].outline_width=a.outline_width;if(!i)styles[i].rounding=p.round_corners;}
    }
    try {
        const auto size=ImGui::GetIO().DisplaySize;
        const ImU32 root_fill=styles[0].fill;styles[0].fill=0;
        auto frame=claw_modular::prepare(active->nodes,styles,readings,graph,0,{size.x,size.y},active->anchor,active->x,active->y,p.font_size*p.font_scale,p.claw_unit_superscript,{nullptr,claw_metric_light,claw_metric_regular,claw_metric_semibold,claw_bold_fps_font});
        frame.graph_style=int(p.claw_graph_style);
        const auto& box=frame.geometry.boxes[0];
        if(!box.visible||box.w<=0||box.h<=0)return true;
        ClawModularBackground(ImVec4(box.x,box.y,box.w,box.h),p,!active->appearance[0].background.empty(),root_fill,active->appearance[0].outline);
        frame.graph_color=ImGui::ColorConvertFloat4ToU32(HUDElements.colors.frametime);
        const unsigned separator_rgb=p.horizontal_separator_color;
        frame.separator_color=IM_COL32((separator_rgb>>16)&255,(separator_rgb>>8)&255,separator_rgb&255,255);
        auto* draw=ImGui::GetForegroundDrawList();const int before=draw->VtxBuffer.Size;
        claw_modular::paint(frame,draw);
        if(std::getenv("CLAW_METRICS_VERIFY")){
            static std::string previous;
            const auto key=active->nodes[0].id;
            const auto signature=key+std::to_string(p.claw_graph_style)+std::to_string(p.claw_background_mode)+std::to_string(p.claw_unit_superscript)+std::to_string(int(active->anchor));
            if(data.n_frames>100&&(previous!=signature||data.n_frames%60==0)){previous=signature;std::fprintf(stderr,"CLAW_MODULAR nodes=%zu root=%s fps=%s vertices=%d outside=%d frame=%llu width=%.1f height=%.1f screen=%.0fx%.0f style=%u background=%u units=%u anchor=%d x=%.1f y=%.1f\n",active->nodes.size(),key.c_str(),readings["fps.value"].value.c_str(),draw->VtxBuffer.Size-before,frame.geometry.outside?1:0,static_cast<unsigned long long>(data.n_frames),frame.geometry.boxes[0].w,frame.geometry.boxes[0].h,size.x,size.y,unsigned(p.claw_graph_style),unsigned(p.claw_background_mode),unsigned(p.claw_unit_superscript),int(active->anchor),box.x,box.y);}
        }
        return true;
    }catch(const std::exception&){return false;} // Legacy HUD remains the fallback.
}
