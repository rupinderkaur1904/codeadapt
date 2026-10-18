#include <vector>

// Loops while more than one candidate remains (hi - lo > 1) and returns lo without
// checking it, so it is wrong when the answer is lo + 1.
int first_true(const std::vector<int>& flags) {
    int lo = 0;
    int hi = static_cast<int>(flags.size());
    while (hi - lo > 1) {
        const int mid = lo + (hi - lo) / 2;
        if (flags[mid] == 0) {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    return lo;
}
