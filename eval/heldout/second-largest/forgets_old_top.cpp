#include <vector>

int second_largest(const std::vector<int>& a) {
    int top = -1, runner = -1;
    for (std::size_t i = 0; i < a.size(); ++i) {
        if (a[i] > top) {
            top = a[i];
            continue;
        }
        if (a[i] != top && a[i] > runner) runner = a[i];
    }
    return runner;
}
