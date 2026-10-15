# CodeAdapt sandbox toolchain image.
# Base pinned by digest for reproducibility (gcc:14.2.0, linux/amd64 + arm64 index).
# Rebuild with: docker build -t codeadapt-sandbox:gcc14.2-1 sandbox/
FROM gcc:14.2.0@sha256:b99b86a28812b1e6453a231a947dc43d76fe192788a12f344a9b568bf9f5d24c

# /work is the mount point of the per-job volume. Docker initialises a fresh named volume
# from the image's content at the mount point, including ownership, so the unprivileged
# sandbox user (nobody, 65534) can write sources and binaries during compilation only.
RUN mkdir -p /work/src /work/bin \
 && chown -R 65534:65534 /work \
 && chmod 0755 /work /work/src /work/bin

LABEL org.codeadapt.sandbox.toolchain="gcc-14.2.0" \
      org.codeadapt.sandbox.image-version="1"

USER 65534:65534
WORKDIR /work
