#include <vector>

// Only trades over consecutive days.
int max_profit(const std::vector<int>& prices) {
    int best = 0;
    for (std::size_t i = 1; i < prices.size(); ++i)
        if (prices[i] - prices[i - 1] > best) best = prices[i] - prices[i - 1];
    return best;
}
