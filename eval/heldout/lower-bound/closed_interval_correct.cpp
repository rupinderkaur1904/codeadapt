#include <vector>

// Correct: closed interval [lo, hi] with an explicit answer variable.
int lower_bound_index(const std::vector<int>& a, int target) {
    int answer = static_cast<int>(a.size());
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] >= target) {
            answer = mid;
            hi = mid - 1;
        } else {
            lo = mid + 1;
        }
    }
    return answer;
}
