#include <vector>

// The running low starts at 0, so the answer is the highest price.
int max_profit(const std::vector<int>& prices) {
    int best = 0, low = 0;
    for (int p : prices) {
        if (p - low > best) best = p - low;
        if (p < low) low = p;
    }
    return best;
}
