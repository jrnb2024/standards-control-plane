#!/usr/bin/env bash
# Re-render every architecture diagram from its mermaid source.
#
# Output: docs/diagrams/diagram-NN.png  (high-DPI PNG, used by
# scripts/generate_demo_deck.py).
#
# Requires: npx (Node), or a globally-installed @mermaid-js/mermaid-cli.

set -euo pipefail

cd "$(dirname "$0")"

for src in diagram-*.mmd; do
  out="${src%.mmd}.png"
  echo "[diagrams] rendering $src -> $out"
  npx -y -p @mermaid-js/mermaid-cli mmdc \
    -i "$src" \
    -o "$out" \
    -w 3200 \
    -H 1800 \
    --backgroundColor white \
    > /dev/null 2>&1
done

echo "[diagrams] done — $(ls -1 diagram-*.png | wc -l | tr -d ' ') diagrams rendered"
