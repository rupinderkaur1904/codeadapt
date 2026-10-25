#include <algorithm>
#include <vector>

// Error model: treats "at most s" as "less than s", so windows summing exactly to s are rejected.
int longest_at_most(const std::vector<int>& a, int s) {
    long long sum = 0;
    int left = 0, best = 0;
    for (int right = 0; right < static_cast<int>(a.size()); ++right) {
        sum += a[right];
        while (sum >= s) sum -= a[left++];
        best = std::max(best, right - left + 1);
    }
    return best;
}
