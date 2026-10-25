#include <vector>

int longest_at_most(const std::vector<int>& a, int s) {
    long long window = 0;
    int count = 0, best = 0;
    for (int x : a) {
        if (window + x > s) {
            window = 0;
            count = 0;
        }
        if (x <= s) {
            window += x;
            ++count;
        }
        if (count > best) best = count;
    }
    return best;
}
