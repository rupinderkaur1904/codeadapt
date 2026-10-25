#include <vector>

// Alternative (unmodelled) error: only windows starting at index 0.
int longest_at_most(const std::vector<int>& a, int s) {
    long long sum = 0;
    int n = 0;
    for (int x : a) { sum += x; if (sum > s) break; ++n; }
    return n;
}
