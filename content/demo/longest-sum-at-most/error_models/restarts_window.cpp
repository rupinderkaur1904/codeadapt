#include <algorithm>
#include <vector>

// Error model: when the sum goes over s, starts a fresh window at the current element instead
// of shrinking from the left, so windows that keep part of the old one are missed.
int longest_at_most(const std::vector<int>& a, int s) {
    long long sum = 0;
    int left = 0, best = 0;
    for (int right = 0; right < static_cast<int>(a.size()); ++right) {
        sum += a[right];
        if (sum > s) {
            left = right;
            sum = a[right];
            if (sum > s) { left = right + 1; sum = 0; }
        }
        best = std::max(best, right - left + 1);
    }
    return best;
}
