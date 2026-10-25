#include <vector>

int remove_duplicates(std::vector<int>& a) {
    int last = 0;
    for (std::size_t r = 1; r < a.size(); ++r) {
        if (a[r] > a[last]) {
            ++last;
            a[last] = a[r];
        }
    }
    return last;
}
