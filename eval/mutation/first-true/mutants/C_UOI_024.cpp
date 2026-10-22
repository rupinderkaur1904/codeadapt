#include <vector>

// Recursive search over the half-open range [lo, hi) for the first index with flags[i] == 1.
static int search(const std::vector<int>& flags, int lo, int hi) {
    if (lo >= hi) {
        return lo;
    }
    const int mid = lo + (hi - lo) / 2;
    if (flags[(mid - 1)] == 0) {
        return search(flags, mid + 1, hi);
    }
    return search(flags, lo, mid);
}

int first_true(const std::vector<int>& flags) {
    return search(flags, 0, static_cast<int>(flags.size()));
}
