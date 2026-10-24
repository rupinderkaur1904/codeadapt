#include <vector>

// Half-open lower bound returned as the answer, without checking that it holds the target.
int search_index(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size());
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if (a[mid] < target) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}
