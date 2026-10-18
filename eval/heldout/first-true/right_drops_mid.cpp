#include <vector>

// For-loop form; on a 1 the right edge moves past mid as well.
int first_true(const std::vector<int>& flags) {
    int left = 0;
    int right = flags.size();
    for (; left < right;) {
        int m = (left + right) >> 1;
        if (flags[m]) right = m - 1;
        else left = m + 1;
    }
    return left;
}
