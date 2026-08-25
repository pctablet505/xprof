#!/usr/bin/env bash
# Measures the suite's DETECTION POWER, not its pass rate.
#
# A suite that goes green proves nothing on its own -- the question is whether
# it goes RED when the app actually breaks. This script answers that by
# deliberately breaking a shared utility and checking that a previously-passing
# case flips to failing, then restoring.
#
# Two arms, because both outcomes are informative:
#   A. bytesToMiB -> NaN            EXPECT CAUGHT  (shape violation)
#   B. bytesToMiB silently doubled  EXPECT MISSED  (plausible wrong number)
#
# Arm B is not a bug in the suite. It documents a real, structural limit: these
# invariants check the SHAPE of rendered data, never its CORRECTNESS. There is
# no oracle for "is 47% the right duty cycle". Catching that class needs a
# golden-value fixture compared against known-good output, which this suite
# does not have.
#
# Usage:  bash tests/ui/mutation_proof.sh
set -euo pipefail
cd "$(dirname "$0")/../.."

export PATH="$HOME/.local/opt/node-v22.14.0-linux-x64/bin:$PWD/.venv-uitest/bin:$PATH"
export XPROF_REQUIRE_LOCAL_FRONTEND=1

U=frontend/app/common/utils/utils.ts
ORIG=$(mktemp)
cp "$U" "$ORIG"
# Restore the source even if a build or test run dies partway.
trap 'cp "$ORIG" "$U"; rm -f "$ORIG"' EXIT

# A case that passes on unmutated source, so a flip is attributable.
CASE='tests/ui/test_tool_sweep.py::test_tool_renders_without_invariant_violations[chromium-memory_viewer-tpu-training]'

run_case () {
  ( cd frontend && ../node_modules/.bin/ng build --configuration production >/dev/null 2>&1 )
  python -m tests.ui.sync_frontend >/dev/null 2>&1
  python -m pytest "$CASE" -q -p no:cacheprovider 2>&1 | tail -2
}

echo "########## BASELINE (unmutated) -- expect PASS ##########"
run_case

echo "########## MUTATION A: bytesToMiB -> NaN -- expect FAIL ##########"
sed -i 's|return numBytes / (1024 \* 1024);|return Number.NaN;|' "$U"
run_case
cp "$ORIG" "$U"

echo "########## MUTATION B: bytesToMiB doubled -- expect PASS (blind spot) ##########"
sed -i 's|return numBytes / (1024 \* 1024);|return (numBytes / (1024 * 1024)) * 2;|' "$U"
run_case
cp "$ORIG" "$U"

echo "########## restoring source and rebuilding ##########"
( cd frontend && ../node_modules/.bin/ng build --configuration production >/dev/null 2>&1 )
python -m tests.ui.sync_frontend >/dev/null 2>&1
echo "done"
