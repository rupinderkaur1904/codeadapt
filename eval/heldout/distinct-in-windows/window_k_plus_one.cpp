#include <unordered_map>
#include <vector>

std::vector<int> distinct_in_windows(const std::vector<int>& a, int k) {
    std::unordered_map<int, int> freq;
    int distinct = 0;
    std::vector<int> res;
    for (int r = 0; r < (int)a.size(); r++) {
        if (freq[a[r]]++ == 0) distinct++;
        if (r > k && --freq[a[r - k - 1]] == 0) distinct--;
        if (r >= k - 1) res.push_back(distinct);
    }
    return res;
}
