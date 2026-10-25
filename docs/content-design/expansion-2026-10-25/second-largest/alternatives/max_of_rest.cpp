#include <vector>

// Alternative cause for no_demotion? Two passes: maximum, then the largest value after the
// first maximum's position (a misreading of "second").
int second_largest(const std::vector<int>& a) {
    int m = 0;
    for (int i = 1; i < static_cast<int>(a.size()); ++i) if (a[i] > a[m]) m = i;
    int s = -1;
    for (int i = m + 1; i < static_cast<int>(a.size()); ++i) if (a[i] < a[m] && a[i] > s) s = a[i];
    return s;
}
