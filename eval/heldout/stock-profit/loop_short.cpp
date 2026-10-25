#include <vector>

int max_profit(const std::vector<int>& prices) {
    const int n = static_cast<int>(prices.size());
    int best = 0, low = prices[0];
    for (int i = 0; i < n - 1; ++i) {
        if (prices[i] < low) low = prices[i];
        if (prices[i] - low > best) best = prices[i] - low;
    }
    return best;
}
