// Included at the end of hud_elements.cpp: reuses its actual fonts/colors/sensors.
bool ClawTryModular() {
    const char* filename=std::getenv("CLAW_MODULAR_LAYOUT_FILE");
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
        if(token==0||token==28||token==29)color=HUDElements.colors.engine;
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
    set("cpu.load",fmt("%.0f%%",cpu.percent,p.enabled[OVERLAY_PARAM_ENABLED_cpu_stats]));
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
    if(Battery_Stats.batt_count>0&&Battery_Stats.remaining_time>0){
        float hours;const float minutes=std::modf(Battery_Stats.remaining_time,&hours)*60;
        char buffer[32];std::snprintf(buffer,sizeof(buffer),"%02d:%02d",int(hours),int(minutes));set("battery.time",buffer);
    }
    set("time.value",data.time.empty()?"--":data.time);
    for(const auto& item:HUDElements.exec_list){
        if(item.value.find("tdp.txt")!=std::string::npos)set("tdp.value",item.ret.empty()?"--":item.ret);
        if(item.value.find("draw.txt")!=std::string::npos)set("battery.power",item.ret.empty()?"--":item.ret);
    }
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
    ImVec4 background=HUDElements.colors.background;background.w=p.background_alpha;
    styles[0].fill=ImGui::ColorConvertFloat4ToU32(background);styles[0].rounding=p.round_corners;
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
        if(a.outline){styles[i].outline=packed("8FB8D9",100);styles[i].rounding=i?6:p.round_corners;}
    }
    try {
        const auto size=ImGui::GetIO().DisplaySize;
        auto frame=claw_modular::prepare(active->nodes,styles,readings,graph,0,{size.x,size.y},active->anchor,active->x,active->y,p.font_size*p.font_scale);
        frame.graph_color=ImGui::ColorConvertFloat4ToU32(HUDElements.colors.frametime);
        auto* draw=ImGui::GetForegroundDrawList();const int before=draw->VtxBuffer.Size;
        claw_modular::paint(frame,draw);
        if(std::getenv("CLAW_METRICS_VERIFY")){
            static std::string previous;
            const auto key=active->nodes[0].id;
            if(data.n_frames>100&&(previous!=key||data.n_frames%120==0)){previous=key;std::fprintf(stderr,"CLAW_MODULAR nodes=%zu root=%s fps=%s vertices=%d outside=%d frame=%llu\n",active->nodes.size(),key.c_str(),readings["fps.value"].value.c_str(),draw->VtxBuffer.Size-before,frame.geometry.outside?1:0,static_cast<unsigned long long>(data.n_frames));}
        }
        return true;
    }catch(const std::exception&){return false;} // Legacy HUD remains the fallback.
}
