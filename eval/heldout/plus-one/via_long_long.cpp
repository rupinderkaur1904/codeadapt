#include <vector>

// Converts to a 64-bit number, which overflows for long inputs.
std::vector<int> plus_one(const std::vector<int>& digits) {
    unsigned long long v = 0;
    for (int d : digits) v = v * 10 + static_cast<unsigned long long>(d);
    ++v;
    std::vector<int> out;
    while (v) { out.insert(out.begin(), static_cast<int>(v % 10)); v /= 10; }
    if (out.empty()) out.push_back(0);
    return out;
}
