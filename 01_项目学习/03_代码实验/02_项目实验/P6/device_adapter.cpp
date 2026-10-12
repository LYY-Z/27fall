// C++17 teaching adapter and owned asynchronous work. No network or hardware.
#include <cstdint>
#include <string>
#include <memory>
#include <set>
#include <cmath>
#include <fstream>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <mutex>
#include <future>
#include <utility>

struct Command { std::string action_id; double value; };
struct Feedback { std::uint64_t sequence; double value; bool online; };
struct Execution { bool accepted; Feedback feedback; };

class DeviceAdapter {
public:
    virtual ~DeviceAdapter() = default; // Safe destruction through a base pointer.
    virtual Feedback readFeedback() = 0;
    virtual bool execute(const Command&) = 0;
    virtual void stop() = 0;
};

// This class itself is not thread safe. SharedDevice serializes all its accesses.
class MockAdapter final : public DeviceAdapter {
    Feedback state_{0,0.0,true};
    std::set<std::string> executed_;
public:
    Feedback readFeedback() override { return state_; }
    bool execute(const Command& c) override {
        if (!state_.online || c.action_id.empty() || !std::isfinite(c.value)
            || std::abs(c.value)>1 || executed_.count(c.action_id)) return false;
        state_.value=c.value;
        ++state_.sequence;
        executed_.insert(c.action_id);
        return true;
    }
    void stop() override { state_.value=0; ++state_.sequence; }
};

class SharedDevice {
    std::unique_ptr<DeviceAdapter> adapter_;
    std::mutex mutex_;
public:
    explicit SharedDevice(std::unique_ptr<DeviceAdapter> adapter)
        : adapter_(std::move(adapter)) {
        if (!adapter_) throw std::invalid_argument("null adapter");
    }
    Execution executeAndRead(const Command& c) {
        std::lock_guard<std::mutex> lock(mutex_);
        const bool accepted=adapter_->execute(c);
        return Execution{accepted,adapter_->readFeedback()};
    }
    Feedback stopAndRead() {
        std::lock_guard<std::mutex> lock(mutex_);
        adapter_->stop();
        return adapter_->readFeedback();
    }
};

std::future<Execution> dispatchOwned(std::shared_ptr<SharedDevice> device,
                                     Command command) {
    if (!device) throw std::invalid_argument("null shared device");
    // Both captures own their data: no references to a caller's stack object.
    return std::async(std::launch::async,
        [device=std::move(device),command=std::move(command)] {
            return device->executeAndRead(command);
        });
}

int main(int argc,char** argv) {
    try {
        if (argc!=3 || std::string(argv[1])!="--out-dir")
            throw std::runtime_error("usage: device_adapter --out-dir PATH");
        const std::filesystem::path out(argv[2]);
        std::filesystem::create_directories(out);
        std::ofstream f(out/"adapter.csv");
        if (!f) throw std::runtime_error("cannot open output");
        f<<"operation,accepted,sequence,value_normalized,online\n";
        auto device=std::make_shared<SharedDevice>(std::make_unique<MockAdapter>());
        auto log=[&f](const std::string& operation,const Execution& result) {
            const auto& state=result.feedback;
            f<<operation<<","<<result.accepted<<","<<state.sequence
             <<","<<state.value<<","<<state.online<<"\n";
        };
        for (const Command c : {Command{"a1",.5},Command{"a1",.5},Command{"a2",2.0}})
            log(c.action_id,device->executeAndRead(c));
        auto future=dispatchOwned(device,Command{"a3",.25});
        // get waits for completion and propagates errors. It is NOT a deadline.
        log("async_a3",future.get());
        // All our work is finished before stop; this demo has no cancellation.
        log("stop",Execution{true,device->stopAndRead()});
        if (!f) throw std::runtime_error("output write failed");
        std::cout<<(out/"adapter.csv").string()<<"\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr<<e.what()<<"\n";
        return 1;
    }
}
