#include <vector>

int second_largest(const std::vector<int>& a) {
    int top = -1, runner = -1;
    std::size_t i = 1;
    while (i < a.size()) {
        const int x = a[i++];
        if (x > top) { runner = top; top = x; }
        else if (x != top && x > runner) runner = x;
    }
    return runner;
}
