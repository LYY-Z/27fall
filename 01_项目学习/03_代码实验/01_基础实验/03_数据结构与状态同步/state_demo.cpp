// 教学生产者消费者：无网络、无电机，控制逻辑不在锁内执行。
#include <condition_variable>
#include <cstdint>
#include <iostream>
#include <mutex>
#include <queue>
#include <thread>

struct Feedback { std::uint64_t sequence; double value; };

int main() {
    std::queue<Feedback> queue;
    std::mutex mutex;
    std::condition_variable ready;
    bool done = false;
    std::size_t consumed = 0;
    std::thread consumer([&] {
        for (;;) {
            Feedback frame{};
            {
                std::unique_lock<std::mutex> lock(mutex);
                // The predicate handles spurious wakeups; wait releases and reacquires the lock.
                ready.wait(lock, [&] { return done || !queue.empty(); });
                // Drain queued frames before stopping, even after production finishes.
                if (done && queue.empty()) break;
                frame = queue.front();
                queue.pop();
            }
            ++consumed; // 仅消费者修改；main在join后读取
            std::cout << frame.sequence << ',' << frame.value << '\n';
        }
    });
    std::thread producer([&] {
        for (std::uint64_t i = 1; i <= 5; ++i) {
            {
                std::lock_guard<std::mutex> lock(mutex);
                queue.push(Feedback{i, 0.1 * static_cast<double>(i)});
            }
            ready.notify_one();
        }
        {
            std::lock_guard<std::mutex> lock(mutex);
            done = true;
        }
        ready.notify_all();
    });
    // Stack objects captured by reference remain alive until both joins finish.
    producer.join();
    consumer.join();
    std::cout << "consumed=" << consumed << '\n';
    return 0;
}
