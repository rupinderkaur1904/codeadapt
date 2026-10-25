#include <vector>
int min_capacity(const std::vector<int>& w, int days) {
    int c = 0; for (int x : w) if (x > c) c = x;
    for (;; ++c) {
        int d = 1, cur = 0;
        for (int x : w) { if (cur + x > c) { ++d; cur = 0; } cur += x; }
        if (d <= days) return c;
    }
}
