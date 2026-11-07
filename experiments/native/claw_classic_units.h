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
inline std::string reference(int token,const std::string& value) {
    const auto p=parts(token,value);if(p.second.empty())return value;
    if(token==25||token==27){const auto at=p.first.find_last_of(' ');return (at==std::string::npos?std::string():p.first.substr(0,at+1))+"888.8 "+p.second;}
    return std::string(token==6||token==11||token==21?"8888":token==4||token==9||token==23?"100":"888.8")+" "+p.second;
}
inline ImVec2 extent(int token,const std::string& value,ImFont* font,float size,bool raised) {
    const auto p=parts(token,value);
    const auto base=font->CalcTextSizeA(size,1e10f,0,p.first.c_str());
    if(p.second.empty())return base;
    const auto unit=font->CalcTextSizeA(size*(raised?.7f:1.f),1e10f,0,p.second.c_str());
    return ImVec2(base.x+claw_modular::unit_gap(size)+unit.x,base.y+(raised?size*.18f:0));
}
inline bool draw(int token,const std::string& value,ImU32 color,bool raised,bool stable,ImU32 outline=0,float thickness=0) {
    const auto p=parts(token,value);if(p.second.empty())return false;
    auto* font=ImGui::GetFont();const float size=ImGui::GetFontSize();
    const auto origin=ImGui::GetCursorScreenPos();auto box=extent(token,value,font,size,raised);
    if(stable)box.x=std::max(box.x,extent(token,reference(token,value),font,size,raised).x)+1;
    ImGui::Dummy(box);
    auto* list=ImGui::GetWindowDrawList();
    auto text=[&](float scale,ImVec2 pos,const std::string& value){
        if((outline&IM_COL32_A_MASK)&&thickness>0)for(auto offset:{ImVec2(-thickness,0),ImVec2(thickness,0),ImVec2(0,-thickness),ImVec2(0,thickness)})
            list->AddText(font,scale,ImVec2(pos.x+offset.x,pos.y+offset.y),outline,value.c_str());
        list->AddText(font,scale,pos,color,value.c_str());
    };
    text(size,ImVec2(origin.x,origin.y+(raised?size*.18f:0)),p.first);
    const float width=font->CalcTextSizeA(size,1e10f,0,p.first.c_str()).x;
    text(size*(raised?.7f:1.f),ImVec2(origin.x+width+claw_modular::unit_gap(size),origin.y),p.second);
    return true;
}
// Legacy non-inline rows submit a right-aligned number and a separate unit.
// Replace only that immediately preceding number's draw primitives, then
// submit a single measured reading. Never retain state across frames/windows.
struct PendingNumber {
    ImDrawList* list=nullptr;ImFont* font=nullptr;ImVec2 origin;
    std::string value;int frame=-1,v0=0,i0=0,v1=0,i1=0;
};
inline PendingNumber& pending(){static PendingNumber value;return value;}
inline PendingNumber capture_number(const char* value){
    PendingNumber out;const std::string text=value?value:"";
    if(text.empty()||text.find_first_not_of("0123456789.-+")!=std::string::npos)return out;
    out.list=ImGui::GetWindowDrawList();out.font=ImGui::GetFont();out.origin=ImGui::GetCursorScreenPos();
    out.value=text;out.frame=ImGui::GetFrameCount();out.v0=out.list->VtxBuffer.Size;out.i0=out.list->IdxBuffer.Size;return out;
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
    const bool result=draw(token,previous.value+" "+unit,color,true,false,outline,thickness);
    ImGui::PopFont();return result;
}
} // namespace claw_classic
