#include <algorithm>
#include <vector>

int max_profit(const std::vector<int>& prices) {
    int run = 0, best = 0;
    for (std::size_t i = 1; i < prices.size(); ++i) {
        run = std::max(0, run + prices[i] - prices[i - 1]);
        best = std::max(best, run);
    }
    return best;
}
