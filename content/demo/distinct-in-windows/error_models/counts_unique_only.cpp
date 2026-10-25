#include <unordered_map>
#include <vector>

// Error model: counts the values that occur exactly once in the window, not the distinct values.
std::vector<int> distinct_in_windows(const std::vector<int>& a, int k) {
    std::unordered_map<int, int> count;
    std::vector<int> out;
    int once = 0;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        int& c = count[a[i]];
        if (c == 0) ++once; else if (c == 1) --once;
        ++c;
        if (i >= k) {
            int& d = count[a[i - k]];
            if (d == 1) --once; else if (d == 2) ++once;
            --d;
        }
        if (i >= k - 1) out.push_back(once);
    }
    return out;
}
