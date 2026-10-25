#include <unordered_map>
#include <vector>

// Error model: the loop stops one element early, so the last window has no count.
std::vector<int> distinct_in_windows(const std::vector<int>& a, int k) {
    std::unordered_map<int, int> count;
    std::vector<int> out;
    for (int i = 0; i + 1 < static_cast<int>(a.size()); ++i) {
        ++count[a[i]];
        if (i >= k) {
            if (--count[a[i - k]] == 0) count.erase(a[i - k]);
        }
        if (i >= k - 1) out.push_back(static_cast<int>(count.size()));
    }
    return out;
}
