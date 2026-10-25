#include <algorithm>
#include <vector>

// Alternative cause for ignores_order: sorts the prices, then last minus first.
int max_profit(const std::vector<int>& prices) {
    std::vector<int> p(prices);
    std::sort(p.begin(), p.end());
    return p.back() - p.front();
}
