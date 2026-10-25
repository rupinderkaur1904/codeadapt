#include <map>
#include <vector>

std::vector<int> distinct_in_windows(const std::vector<int>& a, int k) {
    std::map<int, int> inWindow;
    for (int i = 0; i < k; i++) inWindow[a[i]]++;
    std::vector<int> ans;
    int n = a.size();
    for (int s = 0; s + k < n; s++) {
        ans.push_back(inWindow.size());
        auto it = inWindow.find(a[s]);
        if (--it->second == 0) inWindow.erase(it);
        inWindow[a[s + k]]++;
    }
    return ans;
}
