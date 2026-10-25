#include <vector>

// Error model: compares each element with a[0] instead of the last kept value, so every value
// different from the first is kept, duplicates included.
int remove_duplicates(std::vector<int>& a) {
    int k = 1;
    for (std::size_t i = 1; i < a.size(); ++i) {
        if (a[i] != a[0]) a[k++] = a[i];
    }
    return k;
}
