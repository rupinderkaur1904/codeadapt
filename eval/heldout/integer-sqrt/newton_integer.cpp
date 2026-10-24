// Integer Newton iteration from above.
int int_sqrt(int x) {
    if (x < 2) return x;
    long long r = x;
    while (r * r > x) r = (r + x / r) / 2;
    return static_cast<int>(r);
}
