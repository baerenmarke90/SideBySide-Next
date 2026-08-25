#!/usr/bin/env bash
#
# Erzeugt die Client-API-Schichten aus dem versionierten OpenAPI-Vertrag.
#
#   tools/openapi/generate.sh          erzeugt neu
#   tools/openapi/generate.sh --check  prueft nur auf Drift (CI)
#
# Der Vertrag `backend/openapi.json` ist die einzige Quelle. Er wird hier
# nicht erzeugt, sondern gelesen: wer ihn aendert, aendert ihn im Backend,
# und der bestehende Contract-Check haelt ihn an der echten ASGI-App fest.
#
# Der Generator laeuft in seinem offiziellen Container, festgenagelt auf
# Version und Digest. Damit braucht niemand lokal ein JDK, und ein Lauf auf
# einem anderen Rechner erzeugt dieselben Dateien.
set -euo pipefail

wurzel="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$wurzel"

# shellcheck source=/dev/null
source tools/openapi/generator.env
image="openapitools/openapi-generator-cli:${OPENAPI_GENERATOR_VERSION}@${OPENAPI_GENERATOR_DIGEST}"

vertrag="backend/openapi.json"
ts_ziel="web/src/api/generated"
kt_ziel="android/api/generated"

pruefmodus="${1:-}"

if [ ! -f "$vertrag" ]; then
  echo "Vertrag fehlt: $vertrag" >&2
  exit 1
fi

# Der Container laeuft als der aufrufende Benutzer, sonst gehoeren die
# erzeugten Dateien root und der naechste Lauf scheitert am Schreibrecht.
lauf() {
  docker run --rm \
    --user "$(id -u):$(id -g)" \
    --volume "$wurzel:/local" \
    --workdir /local \
    "$image" "$@"
}

erzeugen() {
  local ausgabe_ts="$1"
  local ausgabe_kt="$2"

  rm -rf "$ausgabe_ts" "$ausgabe_kt"

  lauf generate \
    --input-spec "$vertrag" \
    --generator-name typescript-fetch \
    --config tools/openapi/typescript-fetch.yaml \
    --output "$ausgabe_ts" \
    --skip-validate-spec \
    >/dev/null

  lauf generate \
    --input-spec "$vertrag" \
    --generator-name kotlin \
    --config tools/openapi/kotlin-models.yaml \
    --output "$ausgabe_kt" \
    --global-property models,modelDocs=false,modelTests=false \
    --skip-validate-spec \
    >/dev/null

  # Der Generator legt in jedem Ausgabeverzeichnis eine Datei mit seiner
  # Versionsnummer ab. Sie wuerde bei jedem Versionswechsel als Diff
  # auftauchen, ohne etwas ueber den erzeugten Code auszusagen - die
  # Version steht bereits nachvollziehbar in generator.env.
  find "$ausgabe_ts" "$ausgabe_kt" -name '.openapi-generator' -type d -exec rm -rf {} + 2>/dev/null || true
  find "$ausgabe_ts" "$ausgabe_kt" -name '.openapi-generator-ignore' -delete 2>/dev/null || true
}

if [ "$pruefmodus" = "--check" ]; then
  # Der Vergleichslauf muss innerhalb des Repos liegen: der Container sieht
  # nur dieses Verzeichnis. Er darf den Arbeitsbaum nicht veraendern, sonst
  # repariert er in CI genau den Zustand, den er melden soll.
  temp="$wurzel/.openapi-check"
  trap 'rm -rf "$temp"' EXIT
  erzeugen ".openapi-check/ts" ".openapi-check/kt"
  abweichung=0
  diff -r -q "$temp/ts" "$ts_ziel" >/dev/null 2>&1 || abweichung=1
  diff -r -q "$temp/kt" "$kt_ziel" >/dev/null 2>&1 || abweichung=1
  if [ "$abweichung" -ne 0 ]; then
    echo "Der eingecheckte Client-Code weicht vom Vertrag ab."
    echo "Erzeugen mit: tools/openapi/generate.sh"
    diff -r "$ts_ziel" "$temp/ts" || true
    diff -r "$kt_ziel" "$temp/kt" || true
    exit 1
  fi
  echo "Client-Code stimmt mit dem OpenAPI-Vertrag ueberein."
  exit 0
fi

erzeugen "$ts_ziel" "$kt_ziel"
echo "Erzeugt: $ts_ziel und $kt_ziel"
