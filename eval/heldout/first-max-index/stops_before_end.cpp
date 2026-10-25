#include <vector>

int first_max_index(const std::vector<int>& a) {
    const int n = static_cast<int>(a.size());
    int pos = 0;
    for (int i = 0; i + 1 < n; ++i) {
        if (a[i] > a[pos]) pos = i;
    }
    return pos;
}
