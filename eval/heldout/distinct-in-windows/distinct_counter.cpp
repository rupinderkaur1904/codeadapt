#include <unordered_map>
#include <vector>

std::vector<int> distinct_in_windows(const std::vector<int>& a, int k) {
    std::unordered_map<int, int> freq;
    int distinct = 0;
    std::vector<int> res;
    int n = a.size();
    for (int r = 0; r < n; r++) {
        if (freq[a[r]]++ == 0) distinct++;
        int l = r - k;
        if (l >= 0 && --freq[a[l]] == 0) distinct--;
        if (r + 1 >= k) res.push_back(distinct);
    }
    return res;
}
