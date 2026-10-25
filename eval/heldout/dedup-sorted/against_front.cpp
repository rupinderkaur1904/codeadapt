#include <vector>

int remove_duplicates(std::vector<int>& a) {
    const int first = a.front();
    int w = 1;
    for (std::size_t r = 1; r < a.size(); ++r) {
        if (a[r] != first) a[w++] = a[r];
    }
    return w;
}
