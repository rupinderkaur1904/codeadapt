#include <cmath>

// cause: reads "square root" as rounded up (specification), using floating point.
// cause-skill: problem_specification (same skill as the model)
// compare-with: returns_ceiling
int int_sqrt(int x) {
    long long r = static_cast<long long>(std::sqrt(static_cast<double>(x)));
    while (r * r > x) --r;
    while ((r + 1) * (r + 1) <= x) ++r;
    return static_cast<int>(r * r == x ? r : r + 1);
}
