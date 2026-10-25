#include <vector>

int max_profit(const std::vector<int>& prices) {
    int best = 0, highest = 0;
    for (int i = static_cast<int>(prices.size()) - 1; i >= 0; --i) {
        if (highest - prices[i] > best) best = highest - prices[i];
        if (prices[i] > highest) highest = prices[i];
    }
    return best;
}
