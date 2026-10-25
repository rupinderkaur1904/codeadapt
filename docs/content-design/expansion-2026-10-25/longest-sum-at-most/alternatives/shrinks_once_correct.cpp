#include <algorithm>
#include <vector>

// Design finding: shrinking with `if` instead of `while` is CORRECT for the maximum length with
// positive values (the window never shrinks below the best length), so it is not an error model.
int longest_at_most(const std::vector<int>& a, int s) {
    long long sum = 0;
    int left = 0, best = 0;
    for (int right = 0; right < static_cast<int>(a.size()); ++right) {
        sum += a[right];
        if (sum > s) sum -= a[left++];
        best = std::max(best, right - left + 1);
    }
    return best;
}
