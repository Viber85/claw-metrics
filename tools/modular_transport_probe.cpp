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
 std::istringstream old_input(bytes);std::string line,legacy="CLAW_MODULAR_V1\n";std::getline(old_input,line);std::getline(old_input,line);legacy+=line+"\n";std::getline(old_input,line); // V3 root insets are absent from V1.
 std::string v2="CLAW_MODULAR_V2\n"+legacy.substr(legacy.find('\n')+1);
 while(std::getline(old_input,line)){if(line.empty())continue;std::istringstream record(line);std::vector<std::string> fields;std::string field;while(record>>field)fields.push_back(field);assert(fields.size()>=17);v2+=line+"\n";fields.erase(fields.begin()+6);for(size_t j=0;j<fields.size();++j){if(j)legacy+=' ';legacy+=fields[j];}legacy+='\n';}
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
  assert(loaded);write("invalid");std::this_thread::sleep_for(std::chrono::milliseconds(300));assert(!loader.take());
 }
 std::remove(live.c_str());
 ::mkfifo(live.c_str(),0600);
 {FileLoader loader(live);std::this_thread::sleep_for(std::chrono::milliseconds(20));assert(!loader.take());}
 std::remove(live.c_str()); // Non-regular paths cannot block loader shutdown.
 std::cout<<"PASS: bounded decode, rejected/truncated imports, retained immutable snapshot, coalescing and concurrent publication\n";
}
