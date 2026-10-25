#include <vector>

// Alternative (unmodelled) error: compares with a[i - 1] after earlier writes may have changed it
// (correct for sorted input, so expected to pass).
int remove_duplicates(std::vector<int>& a) {
    int k = 1;
    for (std::size_t i = 1; i < a.size(); ++i) if (a[i] != a[i - 1]) a[k++] = a[i];
    return k;
}
