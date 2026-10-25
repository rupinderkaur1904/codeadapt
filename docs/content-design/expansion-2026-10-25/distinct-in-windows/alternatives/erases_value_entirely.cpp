#include <unordered_map>
#include <vector>

// Alternative (unmodelled) error: erases the leaving value even if it still occurs in the window.
std::vector<int> distinct_in_windows(const std::vector<int>& a, int k) {
    std::unordered_map<int, int> count;
    std::vector<int> out;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        ++count[a[i]];
        if (i >= k) count.erase(a[i - k]);
        if (i >= k - 1) out.push_back(static_cast<int>(count.size()));
    }
    return out;
}
