// VAL1-A2 behaviour ground truth (PLAN.md §5). Analysis only, compiled natively, never in the
// product's execution path. Build with exactly one of -DP_LOWER_BOUND, -DP_COUNT, -DP_LAST,
// -DP_FIRST_TRUE.
//   driver dump                  one output per input: a number, TLE or CRASH
//   driver match F1 [F2 ...]     for each dump file, MATCH or "DIFF <first index>"; stops
//                                running inputs once every file has differed
// Inputs are fixed by the seed; each runs in a forked child with a 50 ms CPU limit.
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

#if defined(P_LOWER_BOUND)
int lower_bound_index(const std::vector<int>& a, int target);
static int call(const std::vector<int>& a, int t) { return lower_bound_index(a, t); }
#elif defined(P_COUNT)
int count_occurrences(const std::vector<int>& a, int target);
static int call(const std::vector<int>& a, int t) { return count_occurrences(a, t); }
#elif defined(P_LAST)
int last_less_than(const std::vector<int>& a, int target);
static int call(const std::vector<int>& a, int t) { return last_less_than(a, t); }
#elif defined(P_FIRST_TRUE)
int first_true(const std::vector<int>& flags);
static int call(const std::vector<int>& a, int) { return first_true(a); }
#else
#error "define a problem"
#endif

static std::vector<std::pair<std::vector<int>, int>> inputs() {
    std::mt19937 rng(20261021);
    std::vector<std::pair<std::vector<int>, int>> out;
    for (int i = 0; i < 3000; ++i) {
        int n = static_cast<int>(rng() % 21);
        std::vector<int> a(n);
#if defined(P_FIRST_TRUE)
        int ones = n == 0 ? 0 : static_cast<int>(rng() % (n + 1));
        for (int j = 0; j < n; ++j) a[j] = j >= n - ones ? 1 : 0;
        out.push_back({a, 0});
#else
        for (int& x : a) x = static_cast<int>(rng() % 10);
        std::sort(a.begin(), a.end());
        out.push_back({a, static_cast<int>(rng() % 12) - 1});
#endif
    }
    for (int n : {1000, 4096}) {
        for (int i = 0; i < 20; ++i) {
            std::vector<int> a(n);
#if defined(P_FIRST_TRUE)
            int ones = static_cast<int>(rng() % (n + 1));
            for (int j = 0; j < n; ++j) a[j] = j >= n - ones ? 1 : 0;
            out.push_back({a, 0});
#else
            for (int& x : a) x = static_cast<int>(rng() % 60);
            std::sort(a.begin(), a.end());
            out.push_back({a, static_cast<int>(rng() % 62) - 1});
#endif
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
        int r = call(a, target);
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
    if (argc < 3 || std::strcmp(argv[1], "match") != 0) return 2;
    std::vector<std::vector<std::string>> expected;
    for (int f = 2; f < argc; ++f) {
        FILE* fp = std::fopen(argv[f], "r");
        if (!fp) return 2;
        std::vector<std::string> lines;
        char buf[64];
        while (std::fgets(buf, sizeof buf, fp)) {
            buf[std::strcspn(buf, "\n")] = 0;
            lines.push_back(buf);
        }
        std::fclose(fp);
        if (lines.size() != cases.size()) return 2;
        expected.push_back(lines);
    }
    std::vector<long> first_diff(expected.size(), -1);
    std::size_t alive = expected.size();
    for (std::size_t i = 0; i < cases.size() && alive > 0; ++i) {
        std::string got = run_one(cases[i].first, cases[i].second);
        for (std::size_t f = 0; f < expected.size(); ++f) {
            if (first_diff[f] < 0 && expected[f][i] != got) {
                first_diff[f] = static_cast<long>(i);
                --alive;
            }
        }
    }
    for (std::size_t f = 0; f < expected.size(); ++f) {
        if (first_diff[f] < 0) std::printf("MATCH\n");
        else std::printf("DIFF %ld\n", first_diff[f]);
    }
    return 0;
}
