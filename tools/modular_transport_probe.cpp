#include "claw_modular_transport.h"
#include "claw_modular_loader.h"
#include "claw_modular_power.h"
#include <cassert>
#include <fstream>
#include <iterator>
#include <thread>
#include <iostream>
using namespace claw_modular;
int main(int argc,char**argv){
 if(argc!=2)return 2;
 assert(power_parts("Power Limit 20 W","TDP")==std::make_pair(std::string("Power Limit"),std::string("20W")));
 assert(power_parts("Limit --","TDP")==std::make_pair(std::string("Limit"),std::string("--")));
 assert(power_parts("nanW","TDP")==std::make_pair(std::string("TDP"),std::string("--")));
 assert(power_text("TDP 28W","TDP")=="TDP 28W");
 assert(power_text("Total draw 12.3 W","DRAW")=="Total draw 12.3 W");
 assert(power_text("Discharge --","DRAW")=="Discharge --");
 assert(power_text("cat: /tmp/profile/tdp.txt: No such file or directory","TDP")=="TDP --");
 assert(power_text("DRAW nanW","DRAW")=="DRAW --");
 assert(power_text("DRAW 123456789W","DRAW")=="DRAW --");
 assert(power_text("DRAW 12W\ninjected","DRAW")=="DRAW --");
 std::ifstream file(argv[1]);std::string bytes((std::istreambuf_iterator<char>(file)),{});
 auto doc=decode(bytes);assert(doc.nodes.size()>1);
 assert(doc.nodes[1].self_align==SelfAlign::End);
 for(const char* token:{"tdp.value","tdp.label","tdp.reading"}){
  assert(std::any_of(doc.nodes.begin(),doc.nodes.end(),[&](const Node& node){return !node.group&&node.token==token;}));
 }
 std::istringstream old_input(bytes);std::string line,legacy="CLAW_MODULAR_V1\n";std::getline(old_input,line);std::getline(old_input,line);legacy+=line+"\n";
 std::string v2="CLAW_MODULAR_V2\n"+line+"\n";std::getline(old_input,line);
 std::string v6="CLAW_MODULAR_V6\n"+legacy.substr(legacy.find('\n')+1)+line+"\n";
 std::string v5="CLAW_MODULAR_V5\n"+legacy.substr(legacy.find('\n')+1)+line+"\n";
 std::string v4="CLAW_MODULAR_V4\n"+legacy.substr(legacy.find('\n')+1)+line+"\n";
 std::string v3="CLAW_MODULAR_V3\n"+legacy.substr(legacy.find('\n')+1)+line+"\n";
 while(std::getline(old_input,line)){
  if(line.empty())continue;
  std::istringstream record(line);std::vector<std::string> fields;std::string field;while(record>>field)fields.push_back(field);
  assert(fields.size()>=30);
  auto join=[](const std::vector<std::string>& values){std::string out;for(size_t j=0;j<values.size();++j){if(j)out+=' ';out+=values[j];}return out+"\n";};
  fields.erase(fields.begin()+25,fields.begin()+30);v6+=join(fields);
  fields.erase(fields.begin()+24);v5+=join(fields);
  fields.erase(fields.begin()+22,fields.begin()+24);v4+=join(fields);
  fields.erase(fields.begin()+17,fields.begin()+22);
  v2+=join(fields);v3+=join(fields);fields.erase(fields.begin()+6);legacy+=join(fields);
 }
 const auto v6_doc=decode(v6);
 assert(inset_left(v6_doc.nodes[0])==27&&inset_bottom(v6_doc.nodes[0])==13);
 assert(inset_left(doc.nodes[0])==0&&inset_right(doc.nodes[0])==27);
 assert(inset_top(doc.nodes[0])==13&&inset_bottom(doc.nodes[0])==21);
 const auto& reading=doc.nodes[doc.nodes.size()-2];
 assert(reading.token=="tdp.reading"&&reading.min_width==72);
 assert(inset_left(reading)==6&&inset_right(reading)==3);
 assert(v6_doc.nodes[v6_doc.nodes.size()-2].min_width==0);
 auto v5_doc=decode(v5);
 assert(v5_doc.nodes.back().axis==Axis::Row&&v5_doc.appearance.back().separator_opacity==100);
 assert(doc.nodes.back().axis==Axis::Column&&doc.appearance.back().separator_opacity==37);
 auto v4_doc=decode(v4);assert(v4_doc.appearance[1].corner_radius==-1&&v4_doc.nodes[1].font_weight==0);
 assert(doc.appearance[1].corner_radius==1000&&doc.nodes[1].font_weight==3);
 auto prior=decode(v3);assert(prior.nodes[0].overlay_padding_x==27&&prior.nodes[0].overlay_padding_y==13);
 assert(prior.nodes[1].overlay_padding_x==0&&prior.appearance[1].outline_width==1);
 assert(doc.nodes[1].overlay_padding_x==9&&doc.nodes[1].overlay_padding_y==5);
 assert(doc.appearance[1].outline_color=="FFAA22"&&doc.appearance[1].outline_width==4&&doc.appearance[1].outline_opacity==35);
 auto previous=decode(v2);assert(previous.nodes[0].overlay_padding_x==0&&previous.nodes[1].self_align==SelfAlign::End);
 assert(doc.nodes[0].overlay_padding_x==27&&doc.nodes[0].overlay_padding_y==13);
 auto migrated=decode(legacy);assert(migrated.nodes.size()==doc.nodes.size()&&migrated.nodes[1].self_align==SelfAlign::Auto);
 assert(doc.appearance[0].background=="112233"&&doc.appearance[0].opacity==44&&doc.appearance[0].outline);
 assert(doc.appearance.back().color=="ABCDEF");
 Exchange exchange;assert(!exchange.take());exchange.publish(bytes);auto first=exchange.take();assert(first&&!exchange.take());
 std::string unknown=bytes;const auto token_pos=unknown.find("fps.value");assert(token_pos!=std::string::npos);unknown.replace(token_pos,9,"unknown.token");
 for(const auto& invalid:{std::string(""),bytes.substr(0,bytes.size()/2),bytes+"extra",unknown,std::string(1024*1024+1,'x')}){
  bool rejected=false;try{exchange.publish(invalid);}catch(const std::invalid_argument&){rejected=true;}assert(rejected&&!exchange.take());
 }
 exchange.publish(bytes);
 bool rejected=false;try{exchange.publish("broken");}catch(const std::invalid_argument&){rejected=true;}
 assert(rejected&&exchange.take()); // A previously queued valid snapshot survives rejection.
 std::atomic<bool> done{false};
 std::thread loader([&]{for(int i=0;i<1000;++i)exchange.publish(bytes);done.store(true);});
 while(!done.load()){auto next=exchange.take();if(next)assert(next->nodes.size()==first->nodes.size());}
 loader.join();assert(first->nodes[0].id==doc.nodes[0].id);
 exchange.publish(bytes);exchange.publish(bytes);assert(exchange.take()&&!exchange.take());
 const std::string live=std::string(argv[1])+".live";
 auto write=[&](const std::string& value){std::ofstream output(live);output<<value;};
 write(bytes);
 {
  FileLoader loader(live);std::shared_ptr<const Document> loaded;
  for(int i=0;i<100&&!loaded;++i){std::this_thread::sleep_for(std::chrono::milliseconds(10));loaded=loader.take();}
  assert(loaded);assert(loader.enabled()); // No companion flag: legacy opt-in still works.
  const std::string state=live+".enabled";
  auto write_state=[&](const char* flag){std::ofstream out(state);out<<flag<<std::endl;};
  auto wait_enabled=[&](bool expected){
   for(int i=0;i<100&&loader.enabled()!=expected;++i)std::this_thread::sleep_for(std::chrono::milliseconds(20));
   assert(loader.enabled()==expected);
  };
  write_state("0");wait_enabled(false);
  // The worker still watches layouts while Classic mode is selected.
  write("invalid");std::this_thread::sleep_for(std::chrono::milliseconds(300));assert(!loader.take());
  write_state("1");wait_enabled(true);
  write_state("0");wait_enabled(false);
  std::remove(state.c_str());
 }
 std::remove(live.c_str());
 ::mkfifo(live.c_str(),0600);
 {FileLoader loader(live);std::this_thread::sleep_for(std::chrono::milliseconds(20));assert(!loader.take());}
 std::remove(live.c_str()); // Non-regular paths cannot block loader shutdown.
 std::cout<<"PASS: bounded decode, rejected/truncated imports, retained immutable snapshot, coalescing and concurrent publication\n";
}
