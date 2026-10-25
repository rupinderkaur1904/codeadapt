#include <vector>

// Only considers stretches that start at index 0.
int longest_at_most(const std::vector<int>& a, int s) {
    long long window = 0;
    int n = 0;
    for (int x : a) {
        window += x;
        if (window > s) break;
        ++n;
    }
    return n;
}
