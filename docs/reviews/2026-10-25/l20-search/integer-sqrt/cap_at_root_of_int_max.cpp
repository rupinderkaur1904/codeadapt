// cause: caps the search range at 46340 but starts the half-open search with hi = cap rather
//        than cap + 1 (search-space boundary, same skill as the model).
// cause-skill: search_space_boundaries (same skill as the model)
// compare-with: hi_cap_46340
int int_sqrt(int x) {
    long long lo = 0, hi = x < 46340 ? static_cast<long long>(x) + 1 : 46340;
    while (lo < hi) {
        const long long mid = lo + (hi - lo) / 2;
        if (mid * mid > x) hi = mid; else lo = mid + 1;
    }
    return static_cast<int>(lo - 1);
}
