# Multi-stage build for Latinium compiler + EWVM runtime
# Uses Chainguard images for minimal attack surface

# -----------------------------------------------------------------------------
# Stage 1: Build the EWVM from source
# -----------------------------------------------------------------------------
FROM cgr.dev/chainguard/wolfi-base:latest AS builder

# Install build toolchain and dependencies
RUN apk add --no-cache \
    build-base \
    gcc \
    make \
    flex \
    bison \
    glib-dev \
    readline-dev \
    pkgconf

WORKDIR /build

# Extract and build the VM
COPY vms-source.zip .
RUN unzip -q vms-source.zip && \
    cd vms && \
    make

# -----------------------------------------------------------------------------
# Stage 2: Runtime image with Python + EWVM
# -----------------------------------------------------------------------------
FROM cgr.dev/chainguard/python:latest

# Install runtime libraries needed by the VM binary
RUN apk add --no-cache \
    glib \
    readline \
    ncurses \
    pcre2 \
    libstdc++

# Copy the built VM binary from builder stage
COPY --from=builder /build/vms/vms /usr/local/bin/vms
RUN chmod +x /usr/local/bin/vms

# Set up application directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Install Latinium compiler in editable mode
RUN pip install --no-cache-dir -e .

# Default entrypoint
ENTRYPOINT ["lat"]
CMD ["--help"]
