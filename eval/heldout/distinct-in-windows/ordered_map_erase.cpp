#include <map>
#include <vector>

std::vector<int> distinct_in_windows(const std::vector<int>& a, int k) {
    std::map<int, int> inWindow;
    for (int i = 0; i < k; i++) inWindow[a[i]]++;
    std::vector<int> ans{(int)inWindow.size()};
    for (size_t i = k; i < a.size(); i++) {
        auto it = inWindow.find(a[i - k]);
        if (--it->second == 0) inWindow.erase(it);
        inWindow[a[i]]++;
        ans.push_back(inWindow.size());
    }
    return ans;
}
