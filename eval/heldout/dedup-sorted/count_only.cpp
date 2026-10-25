#include <vector>

int remove_duplicates(std::vector<int>& a) {
    int distinct = 0;
    for (std::size_t r = 0; r < a.size(); ++r) {
        if (r == 0 || a[r] != a[r - 1]) ++distinct;
    }
    return distinct;
}
