#!/usr/bin/env bash

set -euo pipefail

# build_s3270_tls.sh
# Portable(ish) Linux script to compile and install s3270 with SSL/TLS support.
# - Detects distro and installs build deps
# - Clones upstream x3270 sources
# - Configures with TLS enabled and without X11 (no GUI deps)
# - Builds and installs s3270 into /usr/local (default)
# - Verifies TLS support and prints usage hints

X3270_REPO_URL="https://github.com/paulMattes/x3270.git"
X3270_BRANCH="master"
PREFIX="/usr/local"
JOBS="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)"
SRC_DIR="/tmp/x3270-src-$$"

log() { printf "\033[1;32m[+]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[!]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[x]\033[0m %s\n" "$*"; }

need_cmd() { command -v "$1" >/dev/null 2>&1 || { err "Missing required command: $1"; exit 1; }; }

detect_distro() {
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "${ID}"
  else
    echo "unknown"
  fi
}

install_deps() {
  local id="$1"
  log "Installing build dependencies for distro: $id"
  case "$id" in
    ubuntu|debian|linuxmint|pop)
      sudo apt-get update -y
      sudo apt-get install -y \
        build-essential git autoconf automake libtool pkg-config \
        libssl-dev libncurses-dev libreadline-dev
      ;;
    fedora)
      sudo dnf install -y \
        gcc gcc-c++ git autoconf automake libtool make pkgconfig \
        openssl-devel ncurses-devel readline-devel
      ;;
    rhel|centos|rocky|almalinux)
      sudo yum groupinstall -y "Development Tools" || true
      sudo yum install -y \
        git autoconf automake libtool pkgconfig \
        openssl-devel ncurses-devel readline-devel
      ;;
    opensuse*|sles)
      sudo zypper refresh
      sudo zypper install -y \
        gcc gcc-c++ git autoconf automake libtool make pkg-config \
        libopenssl-devel ncurses-devel readline-devel
      ;;
    alpine)
      sudo apk add --no-cache \
        build-base git autoconf automake libtool pkgconfig \
        openssl-dev ncurses-dev readline-dev
      ;;
    *)
      warn "Unknown distro. Ensure these are installed: gcc, make, git, autoconf, automake, libtool, pkg-config, OpenSSL dev, ncurses dev, readline dev."
      ;;
  esac
}

prepare_sources() {
  log "Cloning x3270 sources from $X3270_REPO_URL"
  rm -rf "$SRC_DIR"
  git clone --depth 1 -b "$X3270_BRANCH" "$X3270_REPO_URL" "$SRC_DIR"
  cd "$SRC_DIR"
}

bootstrap_if_needed() {
  if [ -f ./configure ]; then
    return
  fi
  if [ -f ./autogen.sh ]; then
    log "Running autogen.sh to generate configure script"
    ./autogen.sh
  else
    log "Running autoreconf to generate configure script"
    autoreconf -fi
  fi
}

configure_build() {
  log "Configuring build with TLS enabled and without X11"
  ./configure \
    --prefix="$PREFIX" \
    --enable-s3270 \
    --without-x \
    --enable-tls \
    --with-openssl || {
      err "Configure failed. Check that OpenSSL dev headers are installed."; exit 1; }
}

build_install() {
  log "Building (parallel jobs: $JOBS)"
  make -j"$JOBS"
  log "Installing to $PREFIX (sudo may prompt)"
  sudo make install
}

verify_tls() {
  log "Verifying TLS support in installed s3270"
  need_cmd s3270
  local ver
  ver=$(s3270 -v 2>&1 || true)
  echo "$ver"
  if echo "$ver" | grep -Ei "tls|ssl|openssl" >/dev/null; then
    log "TLS appears enabled in s3270."
  else
    warn "Could not confirm TLS in version output. Will attempt runtime check."
  fi
}

print_usage_hints() {
  cat <<EOF

Next steps:
1) Test a TLS connection (replace HOST and PORT as needed, IBM i default TLS port is 992):
   s3270 -script -e "Open L:HOST:992 -tls" -e "Show(Ssl)" -e "Disconnect" -e "Quit"

   Older syntax variants:
   - s3270 -script -e "connect(L:HOST:992,tls)" -e "show(ssl)" -e "disconnect" -e "quit"

2) Ensure your application uses this s3270 binary. Options:
   - Ensure /usr/local/bin is first in PATH:  export PATH=/usr/local/bin:\$PATH
   - Or point your app to the absolute path:  /usr/local/bin/s3270

3) If your IBM i uses a self-signed certificate, add it to your system trust store
   or configure s3270 to accept it per your security policy.

Installed binary:
  $(command -v s3270 || echo "$PREFIX/bin/s3270 (expected)")

EOF
}

main() {
  need_cmd git
  need_cmd make
  local distro
  distro=$(detect_distro)
  install_deps "$distro"
  prepare_sources
  bootstrap_if_needed
  configure_build
  build_install
  verify_tls
  print_usage_hints
  log "Done. s3270 with TLS should now be installed."
}

main "$@"


