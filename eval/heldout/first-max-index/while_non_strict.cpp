#include <vector>

int first_max_index(const std::vector<int>& a) {
    int pos = 0;
    std::size_t i = 0;
    while (++i < a.size()) {
        if (!(a[i] < a[pos])) pos = static_cast<int>(i);
    }
    return pos;
}
