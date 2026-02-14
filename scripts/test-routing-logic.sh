#!/bin/bash
# Test script for routing logic functionality
# Tests the route_package and related routing functions

# Note: Don't use set -e because some functions return non-zero for test purposes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Source the routing functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/routing-functions.sh"

# Create temporary test directory
TEST_DIR=$(mktemp -d)
trap "rm -rf $TEST_DIR" EXIT

# Test helper functions
test_case() {
  local name="$1"
  echo -e "\n${YELLOW}Test: $name${NC}"
  TESTS_RUN=$((TESTS_RUN + 1))
}

assert_equals() {
  local expected="$1"
  local actual="$2"
  local message="$3"

  # Trim whitespace from actual value
  actual=$(echo "$actual" | xargs)

  if [ "$expected" = "$actual" ]; then
    echo -e "${GREEN}PASS${NC}: $message"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    echo -e "${RED}FAIL${NC}: $message"
    echo "  Expected: $expected"
    echo "  Actual:   $actual"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

assert_file_exists() {
  local filepath="$1"
  local message="$2"

  if [ -f "$filepath" ]; then
    echo -e "${GREEN}PASS${NC}: $message"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    echo -e "${RED}FAIL${NC}: $message"
    echo "  Expected file: $filepath"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

assert_file_not_exists() {
  local filepath="$1"
  local message="$2"

  if [ ! -f "$filepath" ]; then
    echo -e "${GREEN}PASS${NC}: $message"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
  else
    echo -e "${RED}FAIL${NC}: $message"
    echo "  Unexpected file: $filepath"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
  fi
}

count_files() {
  local pattern="$1"
  find "$TEST_DIR/apt-repo" -type f -path "$pattern" 2>/dev/null | wc -l
}

print_summary() {
  echo -e "\n========================================="
  echo "Test Summary"
  echo "========================================="
  echo "Tests run:    $TESTS_RUN"
  echo -e "${GREEN}Tests passed: $TESTS_PASSED${NC}"
  if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Tests failed: $TESTS_FAILED${NC}"
  else
    echo -e "${GREEN}Tests failed: $TESTS_FAILED${NC}"
  fi
  echo "========================================="

  if [ $TESTS_FAILED -gt 0 ]; then
    exit 1
  fi
}

# Helper function to create test package and metadata
create_test_package() {
  local package_name="$1"
  local distro="$2"
  local component="$3"
  local channel="$4"

  # Create a minimal dummy .deb file
  touch "$TEST_DIR/packages/${package_name}.deb"

  # Create metadata file
  cat > "$TEST_DIR/packages/${package_name}.deb.meta" <<EOF
package=$package_name
version=1.0.0-1
architecture=all
distro=$distro
component=$component
original_filename=${package_name}+${distro}+${component}.deb
EOF
}

# ============================================================================
# Test 1: Route distro=any, component=main (2 locations)
# ============================================================================
test_case "Route distro=any, component=main to 2 locations"

mkdir -p "$TEST_DIR/packages"
mkdir -p "$TEST_DIR/apt-repo"
cd "$TEST_DIR"

create_test_package "cockpit-apt_1.0.0-1_all" "any" "main"

# Call routing function
route_package "packages/cockpit-apt_1.0.0-1_all.deb" "stable" "$TEST_DIR"

# Verify package appears in 2 locations (bookworm-stable + trixie-stable)
assert_file_exists "$TEST_DIR/apt-repo/pool/bookworm-stable/main/cockpit-apt_1.0.0-1_all.deb" \
  "Package routed to bookworm-stable/main"
assert_file_exists "$TEST_DIR/apt-repo/pool/trixie-stable/main/cockpit-apt_1.0.0-1_all.deb" \
  "Package routed to trixie-stable/main"

# No legacy routing (no hatlabs component)
assert_file_not_exists "$TEST_DIR/apt-repo/pool/stable/main/cockpit-apt_1.0.0-1_all.deb" \
  "Package NOT routed to legacy stable/main"

count=$(count_files "**/cockpit-apt_1.0.0-1_all.deb")
assert_equals "2" "$count" "Package copied to exactly 2 locations"

# ============================================================================
# Test 2: Route distro=trixie, component=main (single location)
# ============================================================================
test_case "Route distro=trixie, component=main to 1 location"

rm -rf "$TEST_DIR/apt-repo"
mkdir -p "$TEST_DIR/apt-repo"

create_test_package "signalk_2.17.2-1_all" "trixie" "main"

route_package "packages/signalk_2.17.2-1_all.deb" "stable" "$TEST_DIR"

assert_file_exists "$TEST_DIR/apt-repo/pool/trixie-stable/main/signalk_2.17.2-1_all.deb" \
  "Package routed to trixie-stable/main"
assert_file_not_exists "$TEST_DIR/apt-repo/pool/bookworm-stable/main/signalk_2.17.2-1_all.deb" \
  "Package NOT routed to bookworm-stable/main"

count=$(count_files "**/signalk_2.17.2-1_all.deb")
assert_equals "1" "$count" "Package copied to exactly 1 location"

# ============================================================================
# Test 3: Route unstable channel (pre-release)
# ============================================================================
test_case "Route distro=trixie, component=main with unstable channel"

rm -rf "$TEST_DIR/apt-repo"
mkdir -p "$TEST_DIR/apt-repo"

create_test_package "cockpit-apt_0.2.0-1_all" "trixie" "main"

route_package "packages/cockpit-apt_0.2.0-1_all.deb" "unstable" "$TEST_DIR"

assert_file_exists "$TEST_DIR/apt-repo/pool/trixie-unstable/main/cockpit-apt_0.2.0-1_all.deb" \
  "Package routed to trixie-unstable/main"
assert_file_not_exists "$TEST_DIR/apt-repo/pool/trixie-stable/main/cockpit-apt_0.2.0-1_all.deb" \
  "Package NOT in stable channel"

# ============================================================================
# Test 4: Missing metadata file should fail
# ============================================================================
test_case "Missing metadata file causes failure"

rm -rf "$TEST_DIR/apt-repo"
mkdir -p "$TEST_DIR/apt-repo"

# Create package but NO metadata
touch "$TEST_DIR/packages/orphan_1.0-1_all.deb"

# Call routing function - should fail
route_package "packages/orphan_1.0-1_all.deb" "stable" "$TEST_DIR" 2>/dev/null
result=$?

if [ $result -ne 0 ]; then
  echo -e "${GREEN}PASS${NC}: Function correctly fails when metadata missing"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}FAIL${NC}: Function should fail when metadata is missing"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# ============================================================================
# Test 5: Invalid channel validation
# ============================================================================
test_case "Reject invalid channel names"

rm -rf "$TEST_DIR/apt-repo"
mkdir -p "$TEST_DIR/apt-repo"

create_test_package "test_1.0-1_all" "trixie" "main"

# Call routing with invalid channel
route_package "packages/test_1.0-1_all.deb" "stabel" "$TEST_DIR" 2>/dev/null
result=$?

if [ $result -ne 0 ]; then
  echo -e "${GREEN}PASS${NC}: Function rejects invalid channel 'stabel'"
  TESTS_PASSED=$((TESTS_PASSED + 1))
else
  echo -e "${RED}FAIL${NC}: Function should reject invalid channel"
  TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Verify no files were created
count=$(count_files "**/test_1.0-1_all.deb")
assert_equals "0" "$count" "No files created for invalid channel"

# ============================================================================
# Test 6: Multiple packages routed together
# ============================================================================
test_case "Route multiple packages correctly"

rm -rf "$TEST_DIR/apt-repo"
mkdir -p "$TEST_DIR/apt-repo"

create_test_package "pkg1_1.0-1_all" "any" "main"
create_test_package "pkg2_2.0-1_all" "trixie" "main"

route_package "packages/pkg1_1.0-1_all.deb" "stable" "$TEST_DIR"
route_package "packages/pkg2_2.0-1_all.deb" "stable" "$TEST_DIR"

# pkg1: 2 locations (bookworm-stable + trixie-stable, no legacy)
pkg1_count=$(count_files "**/pkg1_1.0-1_all.deb")
assert_equals "2" "$pkg1_count" "pkg1 (any/main) copied to 2 locations"

# pkg2: 1 location (trixie-specific)
pkg2_count=$(count_files "**/pkg2_2.0-1_all.deb")
assert_equals "1" "$pkg2_count" "pkg2 (trixie/main) copied to 1 location"

# Print summary
print_summary
