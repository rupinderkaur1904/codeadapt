#include <algorithm>
#include <vector>

// Grow the window to the right; while its sum is above s, shrink it from the left. Every
// window recorded has sum <= s, and all values are positive, so this finds the longest.
int longest_at_most(const std::vector<int>& a, int s) {
    long long sum = 0;
    int left = 0, best = 0;
    for (int right = 0; right < static_cast<int>(a.size()); ++right) {
        sum += a[right];
        while (sum > s) sum -= a[left++];
        best = std::max(best, right - left + 1);
    }
    return best;
}
