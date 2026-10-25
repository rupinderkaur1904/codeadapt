#include <unordered_map>
#include <vector>

std::vector<int> distinct_in_windows(const std::vector<int>& a, int k) {
    std::unordered_map<int, int> freq;
    std::vector<int> res;
    int singles = 0;
    auto change = [&](int v, int d) {
        if (freq[v] == 1) singles--;
        freq[v] += d;
        if (freq[v] == 1) singles++;
    };
    for (int r = 0; r < (int)a.size(); r++) {
        change(a[r], +1);
        if (r >= k) change(a[r - k], -1);
        if (r >= k - 1) res.push_back(singles);
    }
    return res;
}
