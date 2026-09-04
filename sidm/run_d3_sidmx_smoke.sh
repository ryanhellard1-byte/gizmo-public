#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

gcc -std=c99 -Wall -Wextra -Werror -pedantic sidm/test_d3_sidmx_kernel.c -lm -o /tmp/test_d3_sidmx_kernel
/tmp/test_d3_sidmx_kernel
