#include "claw_modular_transport.h"
#include <cassert>
#include <fstream>
#include <iterator>
#include <thread>
#include <iostream>
using namespace claw_modular;
int main(int argc,char**argv){
 if(argc!=2)return 2;
 std::ifstream file(argv[1]);std::string bytes((std::istreambuf_iterator<char>(file)),{});
 auto doc=decode(bytes);assert(doc.nodes.size()>1);
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
 std::cout<<"PASS: bounded decode, rejected/truncated imports, retained immutable snapshot, coalescing and concurrent publication\n";
}
