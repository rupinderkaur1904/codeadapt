#include <vector>

// Reports the position counting from 1.
int first_max_index(const std::vector<int>& a) {
    int pos = 0;
    for (int i = 1; i < static_cast<int>(a.size()); ++i) {
        if (a[i] > a[pos]) pos = i;
    }
    return pos + 1;
}
