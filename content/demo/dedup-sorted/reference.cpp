#include <vector>

// A write pointer k marks the end of the kept prefix; a read pointer i copies each value that
// differs from the last kept one.
int remove_duplicates(std::vector<int>& a) {
    int k = 1;
    for (std::size_t i = 1; i < a.size(); ++i) {
        if (a[i] != a[k - 1]) a[k++] = a[i];
    }
    return k;
}
