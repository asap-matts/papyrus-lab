#!/usr/bin/env bash
# PapyrusLab — avvio sul Mac del socio per la procedura E03 S1 -> S2 -> S3
# (docs/plans/2026-09-07-e03-compiti-socio.md). Deriva da scripts/e02_bootstrap_mac.sh, con tre differenze:
# branch e03-socio; il messaggio del commit di partenza non e' scritto qui ma letto dall'intestazione del piano
# (unica fonte di verita', compilata al passo 10 del piano madre); verifica anche gh, curl e i file che servono
# ai tre compiti. Non legge ne' stampa credenziali. Rieseguibile.
#
#   brew install gh            # se manca
#   gh auth login              # GitHub.com, HTTPS, login nel browser (l'invito al repository e' gia' accettato)
#   gh repo clone asap-matts/papyrus-lab ~/dev/papyrus-lab     # se il clone di E02 non c'e' piu'
#   bash ~/dev/papyrus-lab/scripts/e03_bootstrap_mac.sh
set -uo pipefail

REPO="asap-matts/papyrus-lab"
DIR="$HOME/dev/papyrus-lab"
BRANCH="${PAPYRUSLAB_BRANCH:-e03-socio}"
PLAN="docs/plans/2026-09-07-e03-compiti-socio.md"
ok()   { printf '  \033[32mOK\033[0m  %s\n' "$1"; }
todo() { printf '  \033[33mDA FARE\033[0m  %s\n' "$1"; }
fail() { printf '  \033[31mSTOP\033[0m  %s\n' "$1"; exit 1; }

echo "== 1/5 GitHub CLI e repository (privato)"
command -v git >/dev/null 2>&1 || fail "git mancante: esegui 'xcode-select --install' e rilancia."
command -v curl >/dev/null 2>&1 || fail "curl mancante (serve a S1)."
if ! command -v gh >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then brew install gh >/dev/null 2>&1 || fail "installazione di gh fallita: 'brew install gh' a mano."
  else fail "manca 'gh' e manca Homebrew. Installa Homebrew (https://brew.sh) oppure gh da https://cli.github.com, poi rilancia."; fi
fi
if gh auth status >/dev/null 2>&1; then ok "gh autenticato come $(gh api user --jq .login 2>/dev/null || echo '?')"
else todo "esegui:  gh auth login   (GitHub.com, HTTPS, login nel browser) — poi rilancia questo script"; exit 2; fi
gh auth setup-git >/dev/null 2>&1 || true
mkdir -p "$HOME/dev"
if [ -d "$DIR/.git" ]; then git -C "$DIR" fetch -q origin || fail "fetch fallito"
else gh repo clone "$REPO" "$DIR" -- -q || fail "clone fallito: hai ancora accesso al repository? (https://github.com/$REPO)"; fi
cd "$DIR"
[ -z "$(git status --porcelain)" ] || fail "l'albero di lavoro ha modifiche locali: mettile da parte (git stash) o chiedi a Matteo"
if git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
  git switch -q "$BRANCH" 2>/dev/null || git switch -q -c "$BRANCH" "origin/$BRANCH" || fail "impossibile passare al branch $BRANCH"
  git pull -q --ff-only origin "$BRANCH" || fail "pull non fast-forward: il branch locale e' divergente, chiedi a Matteo"
else
  fail "branch $BRANCH assente sul remoto: chiedi a Matteo quale branch usare (PAPYRUSLAB_BRANCH=<nome> bash $0)"
fi
ok "repository in $DIR, branch $(git branch --show-current), commit $(git log -1 --format='%h %s')"

echo "== 2/5 Commit di partenza dichiarato nel piano"
[ -f "$PLAN" ] || fail "$PLAN assente su questo branch: il piano non e' ancora stato consegnato."
# Riga attesa nell'intestazione:  **Commit di partenza:** `sha` — messaggio esatto
LINE="$(grep -m1 '^\*\*Commit di partenza:\*\*' "$PLAN" || true)"
[ -n "$LINE" ] || fail "riga 'Commit di partenza' assente nell'intestazione di $PLAN."
EXPECTED_SUBJECT="$(printf '%s' "$LINE" | sed -n 's/.*—[[:space:]]*//p' | sed 's/[[:space:]]*$//')"
case "$LINE" in *"DA COMPILARE"*) fail "il piano non e' ancora pronto per il socio: il commit di partenza non e' compilato. Chiedi a Matteo.";; esac
[ -n "$EXPECTED_SUBJECT" ] || fail "non riesco a leggere il messaggio del commit atteso da $PLAN (formato: **Commit di partenza:** \`sha\` — messaggio)."
SUBJECT="$(git log -1 --format=%s)"
[ "$SUBJECT" = "$EXPECTED_SUBJECT" ] || fail "il branch $BRANCH e' su un commit inatteso.
    atteso:  $EXPECTED_SUBJECT
    trovato: $SUBJECT
  Chiedi a Matteo prima di procedere."
ok "commit di partenza corretto: $SUBJECT"

echo "== 3/5 Python >= 3.11"
PY=""
for cand in /opt/homebrew/opt/python@3.12/libexec/bin/python3 /opt/homebrew/opt/python@3.11/libexec/bin/python3 \
            /usr/local/opt/python@3.12/libexec/bin/python3 python3.12 python3.11 python3; do
  p="$(command -v "$cand" 2>/dev/null || true)"; [ -n "$p" ] || continue
  if "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then PY="$p"; break; fi
done
if [ -z "$PY" ]; then
  todo "nessun Python >= 3.11 trovato (di sistema: $(python3 --version 2>&1)). Esegui:  brew install python@3.12   — poi rilancia questo script"
  exit 4
fi
ok "$("$PY" --version 2>&1) in $PY"

echo "== 4/5 Ambiente isolato .venv da requirements-cpu.txt"
if [ ! -x .venv/bin/python ]; then "$PY" -m venv .venv || fail "creazione di .venv fallita"; fi
PIP_LOG="$(mktemp)"
if ! .venv/bin/python -m pip install --quiet --upgrade pip >"$PIP_LOG" 2>&1 || ! .venv/bin/python -m pip install --quiet -r requirements-cpu.txt >"$PIP_LOG" 2>&1; then
  tail -8 "$PIP_LOG"; fail "installazione di requirements-cpu.txt fallita (vedi righe sopra). Non sostituire versioni: registra l'errore nel rapporto e chiedi a Matteo."
fi
rm -f "$PIP_LOG"
.venv/bin/python -c "import numpy, zarr, numcodecs, tifffile, scipy, fsspec, aiohttp; print('  numpy', numpy.__version__, '| zarr', zarr.__version__, '| scipy', scipy.__version__)" \
  || fail "le librerie non si importano dal venv"
ok "ambiente .venv pronto ($(.venv/bin/python --version 2>&1))"

echo "== 5/5 File richiesti dai tre compiti"
MISSING=""
for f in scripts/e03_pool_shifted.py scripts/tree_sha256.py docs/06-ricerca-community.md \
         docs/plans/2026-09-07-e03-tolleranza-offset-z.md docs/plans/e03-prompt-codex-socio.md; do
  [ -f "$f" ] || MISSING="$MISSING $f"
done
[ -z "$MISSING" ] || fail "file attesi assenti su questo branch:$MISSING — chiedi a Matteo."
N_METRICS="$(ls docs/reports/e03-r01/metrics/*.json 2>/dev/null | grep -v '/curve\.json$' | wc -l | tr -d ' ')"
[ "$N_METRICS" -ge 1 ] || fail "docs/reports/e03-r01/metrics/ non contiene JSON di metriche: S3 non e' eseguibile. Chiedi a Matteo."
ok "script e $N_METRICS JSON di metriche presenti (curve.json escluso dal conteggio: non va letto)"
if .venv/bin/python -m pytest tests/ -q >/dev/null 2>&1; then ok "test del repository superati"
else todo "i test del repository non passano su questo Mac: NON correggere nulla, registralo come ostacolo nel rapporto"; fi

echo
echo "Tutto pronto. Apri Codex nella cartella $DIR e incolla il blocco di testo contenuto in:"
echo "  $DIR/docs/plans/e03-prompt-codex-socio.md"
echo "Note per Codex: usa '$DIR/.venv/bin/python' per ogni comando Python; non aprire"
echo "  docs/reports/e03-r01/metrics/curve.json, la scheda di E03 o scripts/e03_curve.py prima della consegna."
