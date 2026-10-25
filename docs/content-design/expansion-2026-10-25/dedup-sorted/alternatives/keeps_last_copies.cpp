#include <vector>

// Alternative (unmodelled) error: keeps a value when it differs from the next one, and forgets
// the final element.
int remove_duplicates(std::vector<int>& a) {
    int k = 0;
    for (std::size_t i = 0; i + 1 < a.size(); ++i) if (a[i] != a[i + 1]) a[k++] = a[i];
    return k;
}
