#include <vector>

int first_max_index(const std::vector<int>& a) {
    long long top = 0;
    int pos = 0, i = 0;
    for (int x : a) {
        if (x > top) {
            top = x;
            pos = i;
        }
        ++i;
    }
    return pos;
}
