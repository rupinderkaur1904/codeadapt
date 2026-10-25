#include <vector>

// Error model: returns the value that forms the longest run (the first such run) instead of its
// length.
int longest_run(const std::vector<int>& a) {
    int best = 1, run = 1, value = a[0];
    for (std::size_t i = 1; i < a.size(); ++i) {
        run = (a[i] == a[i - 1]) ? run + 1 : 1;
        if (run > best) { best = run; value = a[i]; }
    }
    return value;
}
