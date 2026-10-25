#include <unordered_map>
#include <vector>

// Error model: decrements the leaving value's count but never erases it at 0, so the map's size
// counts values that have left the window.
std::vector<int> distinct_in_windows(const std::vector<int>& a, int k) {
    std::unordered_map<int, int> count;
    std::vector<int> out;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        ++count[a[i]];
        if (i >= k) --count[a[i - k]];
        if (i >= k - 1) out.push_back(static_cast<int>(count.size()));
    }
    return out;
}
