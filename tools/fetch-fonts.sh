#!/usr/bin/env bash
# Pull the latin woff2 subsets once from Google Fonts' CSS API (a modern UA gets woff2), so the
# live site makes no third-party request. Both faces are SIL Open Font License 1.1.
set -euo pipefail
cd "$(dirname "$0")/.."
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
get() { # family weight outfile
  css=$(curl -fsSL -A "$UA" "https://fonts.googleapis.com/css2?family=$1:wght@$2&display=swap")
  url=$(printf '%s' "$css" | sed -n '/\/\* latin \*\//,$p' | grep -o 'url([^)]*)' | head -1 | sed 's/^url(//; s/)$//')
  [ -n "$url" ] || { echo "no latin url for $1 $2" >&2; exit 1; }
  curl -fsSL -A "$UA" "$url" -o "fonts/$3"; echo "fonts/$3 <- $url"
}
get Unbounded 800 unbounded-800.woff2
get Archivo 400 archivo-400.woff2
get Archivo 500 archivo-500.woff2
get Archivo 700 archivo-700.woff2
printf 'Unbounded (c) The Unbounded Project Authors, Archivo (c) Omnibus-Type. Both under the SIL Open Font License 1.1: https://openfontlicense.org\n' > fonts/LICENSE.txt
file fonts/*.woff2
