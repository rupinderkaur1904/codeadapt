// VAL1-A behaviour ground truth (PLAN.md §5). Analysis only, run natively, never in the
// product's execution path. Usage: driver dump > ref.txt   |   driver check ref.txt
// `check` stops at the first input whose output differs from the reference and prints
// "DIFF <index> <expected> <got>", or "EQUIVALENT <count>".
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <random>
#include <signal.h>
#include <string>
#include <sys/time.h>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>

int lower_bound_index(const std::vector<int>& a, int target);

static std::vector<std::pair<std::vector<int>, int>> inputs() {
    std::mt19937 rng(20261021);
    std::vector<std::pair<std::vector<int>, int>> out;
    for (int i = 0; i < 3000; ++i) {
        int n = static_cast<int>(rng() % 21);
        std::vector<int> a(n);
        for (int& x : a) x = static_cast<int>(rng() % 10);
        std::sort(a.begin(), a.end());
        out.push_back({a, static_cast<int>(rng() % 12) - 1});
    }
    for (int n : {1000, 4096}) {
        for (int i = 0; i < 20; ++i) {
            std::vector<int> a(n);
            for (int& x : a) x = static_cast<int>(rng() % 60);
            std::sort(a.begin(), a.end());
            out.push_back({a, static_cast<int>(rng() % 62) - 1});
        }
    }
    return out;
}

static std::string run_one(const std::vector<int>& a, int target) {
    int p[2];
    if (pipe(p) != 0) return "PIPEFAIL";
    pid_t pid = fork();
    if (pid == 0) {
        close(p[0]);
        struct itimerval tv = {{0, 0}, {0, 50000}};
        setitimer(ITIMER_VIRTUAL, &tv, nullptr);
        int r = lower_bound_index(a, target);
        if (write(p[1], &r, sizeof r) != sizeof r) _exit(1);
        _exit(0);
    }
    close(p[1]);
    int r = 0;
    ssize_t got = read(p[0], &r, sizeof r);
    close(p[0]);
    int st = 0;
    waitpid(pid, &st, 0);
    if (got == sizeof r) return std::to_string(r);
    if (WIFSIGNALED(st) && WTERMSIG(st) == SIGVTALRM) return "TLE";
    return "CRASH";
}

int main(int argc, char** argv) {
    auto cases = inputs();
    if (argc >= 2 && std::strcmp(argv[1], "dump") == 0) {
        for (auto& c : cases) std::printf("%s\n", run_one(c.first, c.second).c_str());
        return 0;
    }
    if (argc < 3) return 2;
    FILE* f = std::fopen(argv[2], "r");
    if (!f) return 2;
    char buf[64];
    for (std::size_t i = 0; i < cases.size(); ++i) {
        if (!std::fgets(buf, sizeof buf, f)) return 2;
        buf[std::strcspn(buf, "\n")] = 0;
        std::string got = run_one(cases[i].first, cases[i].second);
        if (got != buf) {
            std::printf("DIFF %zu %s %s\n", i, buf, got.c_str());
            return 0;
        }
    }
    std::printf("EQUIVALENT %zu\n", cases.size());
    return 0;
}
