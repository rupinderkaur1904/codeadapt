#include <unordered_map>
#include <vector>

// Keep a count per value in the window; a value leaves the map when its count reaches 0, so the
// map's size is the number of distinct values.
std::vector<int> distinct_in_windows(const std::vector<int>& a, int k) {
    std::unordered_map<int, int> count;
    std::vector<int> out;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        ++count[a[i]];
        if (i >= k) {
            if (--count[a[i - k]] == 0) count.erase(a[i - k]);
        }
        if (i >= k - 1) out.push_back(static_cast<int>(count.size()));
    }
    return out;
}
