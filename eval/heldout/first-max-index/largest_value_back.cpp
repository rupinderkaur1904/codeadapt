#include <vector>

int first_max_index(const std::vector<int>& a) {
    int top = a[0];
    for (int x : a) {
        if (x > top) top = x;
    }
    return top;
}
