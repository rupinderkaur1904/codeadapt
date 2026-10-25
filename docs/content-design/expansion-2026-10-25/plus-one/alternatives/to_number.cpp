#include <vector>

// Alternative (unmodelled) error: converts to a long long, so long numbers overflow... kept
// short-safe here: converts only when n <= 18, else returns the input unchanged.
std::vector<int> plus_one(const std::vector<int>& digits) {
    if (digits.size() > 18) return digits;
    long long v = 0;
    for (int x : digits) v = v * 10 + x;
    ++v;
    std::vector<int> r;
    while (v) { r.insert(r.begin(), static_cast<int>(v % 10)); v /= 10; }
    return r;
}
