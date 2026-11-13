#pragma once
#include "claw_modular_transport.h"
#include <condition_variable>
#include <chrono>
#include <atomic>
#include <fcntl.h>
#include <unistd.h>
#include <thread>
#include <sys/stat.h>

namespace claw_modular {
// Explicit experimental path only. No thread or I/O exists when not constructed.
class FileLoader {
    Exchange exchange;
    std::string path,last_attempt;
    std::atomic<bool> live_enabled{true}; // Backward-compatible when the companion state file is absent.
    std::mutex mutex;
    std::condition_variable wake;
    bool stopped=false;
    std::thread worker;
    void run(){
        std::unique_lock<std::mutex> lock(mutex);
        while(!stopped){
            lock.unlock();
            try {
                struct Descriptor { int fd; ~Descriptor(){if(fd>=0)::close(fd);} };
                // This state file is written atomically by the Decky backend.
                // Always read it on the worker, never synchronously on a render frame.
                Descriptor state{::open((path+".enabled").c_str(),O_RDONLY|O_CLOEXEC|O_NONBLOCK)};
                if(state.fd>=0){
                    struct stat status{};
                    if(!::fstat(state.fd,&status)&&S_ISREG(status.st_mode)&&status.st_size>0&&status.st_size<=4){
                        char flag[4]={};
                        const auto n=::read(state.fd,flag,sizeof(flag));
                        if(n>0&&(flag[0]=='0'||flag[0]=='1'))live_enabled.store(flag[0]=='1',std::memory_order_release);
                    }
                }
                Descriptor file{::open(path.c_str(),O_RDONLY|O_CLOEXEC|O_NONBLOCK)};
                struct stat info{};
                if(file.fd>=0&&!::fstat(file.fd,&info)&&S_ISREG(info.st_mode)&&info.st_size>=0&&info.st_size<=1024*1024){
                    std::string bytes;bytes.reserve(static_cast<size_t>(info.st_size));
                    char buffer[4096];bool valid=true;
                    while(bytes.size()<=1024*1024){
                        const auto count=::read(file.fd,buffer,sizeof(buffer));
                        if(count==0)break;
                        if(count<0){valid=false;break;}
                        bytes.append(buffer,static_cast<size_t>(count));
                    }
                    if(valid&&bytes.size()<=1024*1024&&bytes!=last_attempt){
                        last_attempt=bytes;
                        exchange.publish(bytes);
                    }
                }
            }catch(const std::exception&){ /* Keep last valid pending/active document. */ }
            lock.lock();
            wake.wait_for(lock,std::chrono::milliseconds(250),[&]{return stopped;});
        }
    }
public:
    explicit FileLoader(std::string filename):path(std::move(filename)),worker([this]{run();}){}
    FileLoader(const FileLoader&)=delete;
    FileLoader& operator=(const FileLoader&)=delete;
    ~FileLoader(){
        {std::lock_guard<std::mutex> lock(mutex);stopped=true;}
        wake.notify_all();if(worker.joinable())worker.join();
    }
    std::shared_ptr<const Document> take(){return exchange.take();}
    bool enabled() const{return live_enabled.load(std::memory_order_acquire);}
};
} // namespace claw_modular
