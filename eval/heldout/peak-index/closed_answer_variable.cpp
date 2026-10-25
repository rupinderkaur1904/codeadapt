#include <vector>

// Closed interval with a running answer: mid is a candidate when it is last or falls next.
int peak_index(const std::vector<int>& a) {
    int n = static_cast<int>(a.size());
    int lo = 0, hi = n - 1, answer = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (mid == n - 1 || a[mid] > a[mid + 1]) {
            answer = mid;
            hi = mid - 1;
        } else {
            lo = mid + 1;
        }
    }
    return answer;
}
