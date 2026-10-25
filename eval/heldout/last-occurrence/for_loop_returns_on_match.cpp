#include <vector>

// For-loop form of a closed search that returns the first match it meets.
int last_occurrence(const std::vector<int>& a, int target) {
    for (int lo = 0, hi = static_cast<int>(a.size()) - 1; lo <= hi;) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] < target) lo = mid + 1;
        else if (a[mid] > target) hi = mid - 1;
        else return mid;
    }
    return -1;
}
