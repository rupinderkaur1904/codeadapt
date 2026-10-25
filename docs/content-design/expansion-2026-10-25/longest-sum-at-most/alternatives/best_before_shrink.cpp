#include <algorithm>
#include <vector>

// Alternative update error: records the length before shrinking.
int longest_at_most(const std::vector<int>& a, int s) {
    long long sum = 0;
    int left = 0, best = 0;
    for (int right = 0; right < static_cast<int>(a.size()); ++right) {
        sum += a[right];
        best = std::max(best, right - left + 1);
        while (sum > s) sum -= a[left++];
    }
    return best;
}
