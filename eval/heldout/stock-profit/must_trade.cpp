#include <climits>
#include <vector>

int max_profit(const std::vector<int>& prices) {
    int best = INT_MIN, low = prices[0];
    for (std::size_t i = 1; i < prices.size(); ++i) {
        const int gain = prices[i] - low;
        if (gain > best) best = gain;
        if (prices[i] < low) low = prices[i];
    }
    return best;
}
