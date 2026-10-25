#include <algorithm>
#include <vector>

// Alternative (unmodelled) error: only buys and sells on consecutive days.
int max_profit(const std::vector<int>& prices) {
    int best = 0;
    for (std::size_t i = 1; i < prices.size(); ++i) best = std::max(best, prices[i] - prices[i - 1]);
    return best;
}
