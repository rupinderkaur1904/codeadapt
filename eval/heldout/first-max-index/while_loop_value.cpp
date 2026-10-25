#include <vector>

int first_max_index(const std::vector<int>& a) {
    std::size_t i = 1, pos = 0;
    int value = a[0];
    while (i < a.size()) {
        if (a[i] > value) {
            value = a[i];
            pos = i;
        }
        ++i;
    }
    return static_cast<int>(pos);
}
