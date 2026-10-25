#include <algorithm>
#include <vector>

int max_profit(const std::vector<int>& prices) {
    std::vector<int> p(prices);
    std::sort(p.begin(), p.end());
    return p.back() - p.front();
}
