#include <vector>

// cause: intended as a closed interval that records the wrong candidate. MEASURED: it agrees
//        with the reference on every test and every domain input, so it is a correct
//        program and not an alternative cause (kept as a record of the attempt).
// cause-skill: search_space_boundaries (same skill as the model)
// compare-with: hi_skips_candidate
int peak_index(const std::vector<int>& a) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1, ans = 0;
    while (lo <= hi) {
        const int mid = lo + (hi - lo) / 2;
        if (mid + 1 < static_cast<int>(a.size()) && a[mid] < a[mid + 1]) { lo = mid + 1; ans = lo; }
        else { hi = mid - 1; }
    }
    return ans;
}
