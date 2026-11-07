#pragma once
#include "claw_modular_imgui.h"

namespace claw_classic {
inline const char* key(int token) {
    static const char* keys[]={"","","fps.ms","","cpu.load","cpu.temp","cpu.clock","cpu.power","","gpu.load","gpu.temp","gpu.clock","gpu.power","gpu.junction","gpu.fan","gpu.voltage","","ram.value","","vram.value","vram.temp","vram.clock","","battery.value","","battery.power","","tdp.value","fps.extra","fps.extra","ram.game","ram.swap"};
    return token>=0&&token<32?keys[token]:"";
}
inline std::pair<std::string,std::string> parts(int token,const std::string& value) {
    if(token==13&&value.find(" Jnc")!=std::string::npos){
        const auto at=value.find("°");if(at!=std::string::npos)return {value.substr(0,at),value.substr(at)};
    }
    if((token==28||token==29)&&value.size()>4&&value.compare(value.size()-4,4," FPS")==0)
        return {value.substr(0,value.size()-4),"FPS"};
    return claw_modular::unit_parts(key(token),value);
}
// Equal-width digit cells stabilize changing values without reserving
// invisible extra digits between a reading and the next reading.
inline float digit_advance(ImFont* font,float size){
    float width=0;for(char ch='0';ch<='9';++ch)width=std::max(width,font->GetCharAdvance(ch));
    return width*size/font->FontSize;
}
inline float number_width(ImFont* font,float size,const std::string& value,bool tabular){
    if(!tabular)return font->CalcTextSizeA(size,1e10f,0,value.c_str()).x;
    const float digit=digit_advance(font,size);float width=0;
    for(size_t i=0;i<value.size();){
        if(value[i]>='0'&&value[i]<='9'){width+=digit;++i;}
        else{const auto end=value.find_first_of("0123456789",i);const auto part=value.substr(i,end==std::string::npos?end:end-i);width+=font->CalcTextSizeA(size,1e10f,0,part.c_str()).x;i=end==std::string::npos?value.size():end;}
    }return width;
}
inline void number_text(ImDrawList* draw,ImFont* font,float size,ImVec2 pos,ImU32 color,const std::string& value,bool tabular){
    if(!tabular){draw->AddText(font,size,pos,color,value.c_str());return;}
    const float digit=digit_advance(font,size);
    for(size_t i=0;i<value.size();){
        if(value[i]>='0'&&value[i]<='9'){
            const char text[]={value[i],0};const float advance=font->GetCharAdvance(value[i])*size/font->FontSize;
            draw->AddText(font,size,ImVec2(pos.x+(digit-advance)*.5f,pos.y),color,text);pos.x+=digit;++i;
        }else{const auto end=value.find_first_of("0123456789",i);const auto part=value.substr(i,end==std::string::npos?end:end-i);draw->AddText(font,size,pos,color,part.c_str());pos.x+=font->CalcTextSizeA(size,1e10f,0,part.c_str()).x;i=end==std::string::npos?value.size():end;}
    }
}
inline float& width_floor(){static float value=0;return value;}
inline float hold_width(float value){
    static ImVec2 viewport;const auto screen=ImGui::GetIO().DisplaySize;auto& width=width_floor();
    if(screen.x!=viewport.x||screen.y!=viewport.y){width=0;viewport=screen;}
    width=std::max(width,value);return width;
}
inline ImGuiTableFlags table_flags(bool compact){return ImGuiTableFlags_NoClip|(compact?ImGuiTableFlags_SizingFixedFit:0);}
inline bool draw_number(const std::string& value,ImU32 color,ImU32 outline=0,float thickness=0){
    if(value.empty()||value.find_first_not_of("0123456789.-+")!=std::string::npos)return false;
    auto* font=ImGui::GetFont();const float size=ImGui::GetFontSize();const auto origin=ImGui::GetCursorScreenPos();
    ImGui::Dummy(ImVec2(number_width(font,size,value,true),font->CalcTextSizeA(size,1e10f,0,value.c_str()).y));
    auto* draw=ImGui::GetWindowDrawList();
    if((outline&IM_COL32_A_MASK)&&thickness>0)for(auto shift:{ImVec2(-thickness,0),ImVec2(thickness,0),ImVec2(0,-thickness),ImVec2(0,thickness)})
        number_text(draw,font,size,ImVec2(origin.x+shift.x,origin.y+shift.y),outline,value,true);
    number_text(draw,font,size,origin,color,value,true);return true;
}
inline ImVec2 extent(int token,const std::string& value,ImFont* font,float size,bool raised,bool tabular=false) {
    const auto p=parts(token,value);
    const auto base=font->CalcTextSizeA(size,1e10f,0,p.first.c_str());
    if(p.second.empty())return base;
    const auto unit=font->CalcTextSizeA(size*(raised?.7f:1.f),1e10f,0,p.second.c_str());
    // Superscript changes the unit's baseline through its smaller font only.
    // Keep the number and the measured row height identical to ordinary text,
    // so adjacent category labels and following SameLine items never move.
    return ImVec2(number_width(font,size,p.first,tabular)+claw_modular::unit_gap(size)+unit.x,base.y);
}
struct DrawInk {
    float number_top=1e10f,number_bottom=-1e10f,unit_top=1e10f,unit_bottom=-1e10f;
    void capture(const ImDrawList* list,int first,bool unit){
        auto& top=unit?unit_top:number_top;auto& bottom=unit?unit_bottom:number_bottom;
        for(int i=first;i<list->VtxBuffer.Size;++i){top=std::min(top,list->VtxBuffer[i].pos.y);bottom=std::max(bottom,list->VtxBuffer[i].pos.y);}
    }
};
inline bool draw(int token,const std::string& value,ImU32 color,bool raised,bool stable,ImU32 outline=0,float thickness=0,ImU32 unit_color=0,DrawInk* ink=nullptr) {
    const auto p=parts(token,value);if(p.second.empty())return false;
    auto* font=ImGui::GetFont();const float size=ImGui::GetFontSize();
    const auto origin=ImGui::GetCursorScreenPos();auto box=extent(token,value,font,size,raised,stable);
    ImGui::Dummy(box);
    auto* list=ImGui::GetWindowDrawList();
    auto text=[&](float scale,ImVec2 pos,const std::string& value,ImU32 foreground,bool tabular){
        if((outline&IM_COL32_A_MASK)&&thickness>0)for(auto offset:{ImVec2(-thickness,0),ImVec2(thickness,0),ImVec2(0,-thickness),ImVec2(0,thickness)})
            number_text(list,font,scale,ImVec2(pos.x+offset.x,pos.y+offset.y),outline,value,tabular);
        number_text(list,font,scale,pos,foreground,value,tabular);
    };
    int first=list->VtxBuffer.Size;
    text(size,origin,p.first,color,stable);
    if(ink)ink->capture(list,first,false);
    const float width=number_width(font,size,p.first,stable);
    first=list->VtxBuffer.Size;
    text(size*(raised?.7f:1.f),ImVec2(origin.x+width+claw_modular::unit_gap(size),origin.y),p.second,unit_color?unit_color:color,false);
    if(ink)ink->capture(list,first,true);
    return true;
}
// Legacy non-inline rows submit a right-aligned number and a separate unit.
// Replace only that immediately preceding number's draw primitives, then
// submit a single measured reading. Never retain state across frames/windows.
struct PendingNumber {
    ImDrawList* list=nullptr;ImFont* font=nullptr;ImVec2 origin;
    std::string value;ImU32 color=IM_COL32_WHITE;int frame=-1,v0=0,i0=0,v1=0,i1=0;
};
inline PendingNumber& pending(){static PendingNumber value;return value;}
inline PendingNumber capture_number(const char* value,ImU32 color=IM_COL32_WHITE){
    PendingNumber out;const std::string text=value?value:"";
    if(text.empty()||text.find_first_not_of("0123456789.-+")!=std::string::npos)return out;
    out.list=ImGui::GetWindowDrawList();out.font=ImGui::GetFont();out.origin=ImGui::GetCursorScreenPos();
    out.value=text;out.color=color;out.frame=ImGui::GetFrameCount();out.v0=out.list->VtxBuffer.Size;out.i0=out.list->IdxBuffer.Size;return out;
}
inline void commit_number(PendingNumber out){
    if(out.list){out.v1=out.list->VtxBuffer.Size;out.i1=out.list->IdxBuffer.Size;}pending()=std::move(out);
}
inline bool finish_unit(const char* value,ImU32 color,ImU32 outline=0,float thickness=0){
    const std::string unit=value?value:"";
    const int token=unit=="%"?4:unit=="°C"||unit=="°F"?5:unit=="MHz"?6:unit=="W"?7:unit=="GiB"?17:unit=="ms"?2:unit=="mV"?15:unit=="RPM"?14:-1;
    if(token<0)return false;
    auto previous=pending();pending()={};auto* list=ImGui::GetWindowDrawList();
    if(!previous.list||previous.frame!=ImGui::GetFrameCount()||previous.list!=list||
       list->VtxBuffer.Size!=previous.v1||list->IdxBuffer.Size!=previous.i1||list->CmdBuffer.empty()||
       int(list->CmdBuffer.back().ElemCount)<previous.i1-previous.i0)return false;
    if(list->_VtxCurrentIdx<unsigned(previous.v1-previous.v0))return false;
    list->PrimUnreserve(previous.i1-previous.i0,previous.v1-previous.v0);
    list->_VtxCurrentIdx-=previous.v1-previous.v0;
    ImGui::PushFont(previous.font);ImGui::SetCursorScreenPos(previous.origin);
    const bool result=draw(token,previous.value+" "+unit,previous.color,true,false,outline,thickness,color);
    ImGui::PopFont();return result;
}
} // namespace claw_classic
