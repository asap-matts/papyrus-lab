#!/usr/bin/env bash
# PapyrusLab — avvio sul Mac del socio per i compiti E02 S1 e S2 (docs/plans/2026-09-06-e02-compiti-socio.md).
# Deriva da scripts/e01_bootstrap_mac.sh (v2, con gli otto ostacoli di E01 integrati). Differenze: branch
# e02-socio, ambiente Python isolato in .venv da requirements-cpu.txt (le stesse versioni del portatile di
# Matteo), nessuna CLI Kaggle (S1 e S2 non usano Kaggle). Non legge ne' stampa credenziali. Rieseguibile.
#
#   brew install gh            # se manca
#   gh auth login              # GitHub.com, HTTPS, login nel browser (l'invito al repository e' gia' accettato da E01)
#   gh repo clone asap-matts/papyrus-lab ~/dev/papyrus-lab     # se il clone di E01 non c'e' piu'
#   bash ~/dev/papyrus-lab/scripts/e02_bootstrap_mac.sh
set -uo pipefail

REPO="asap-matts/papyrus-lab"
DIR="$HOME/dev/papyrus-lab"
BRANCH="${PAPYRUSLAB_BRANCH:-e02-socio}"
EXPECTED_SUBJECT="feat: E02 steps 1-3 (inventory, split, labels, metrics with tests)"
ok()   { printf '  \033[32mOK\033[0m  %s\n' "$1"; }
todo() { printf '  \033[33mDA FARE\033[0m  %s\n' "$1"; }
fail() { printf '  \033[31mSTOP\033[0m  %s\n' "$1"; exit 1; }

echo "== 1/4 GitHub CLI e repository (privato)"
command -v git >/dev/null 2>&1 || fail "git mancante: esegui 'xcode-select --install' e rilancia."
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
SUBJECT="$(git log -1 --format=%s)"
[ "$SUBJECT" = "$EXPECTED_SUBJECT" ] || fail "il branch $BRANCH e' su un commit inatteso: '$SUBJECT' (atteso: '$EXPECTED_SUBJECT'). Chiedi a Matteo."
ok "repository in $DIR, branch $(git branch --show-current), commit $(git log -1 --format='%h %s')"

echo "== 2/4 Python >= 3.11"
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

echo "== 3/4 Ambiente isolato .venv da requirements-cpu.txt"
# Un venv non e' soggetto alla protezione PEP 668 di Homebrew (ostacolo n. 4 di E01): nessun --break-system-packages.
if [ ! -x .venv/bin/python ]; then "$PY" -m venv .venv || fail "creazione di .venv fallita"; fi
PIP_LOG="$(mktemp)"
if ! .venv/bin/python -m pip install --quiet --upgrade pip >"$PIP_LOG" 2>&1 || ! .venv/bin/python -m pip install --quiet -r requirements-cpu.txt >"$PIP_LOG" 2>&1; then
  tail -8 "$PIP_LOG"; fail "installazione di requirements-cpu.txt fallita (vedi righe sopra). Non sostituire versioni: registra l'errore nel rapporto e chiedi a Matteo."
fi
rm -f "$PIP_LOG"
.venv/bin/python -c "import numpy, zarr, numcodecs, tifffile, scipy, fsspec, aiohttp; print('  numpy', numpy.__version__, '| zarr', zarr.__version__, '| scipy', scipy.__version__)" \
  || fail "le librerie non si importano dal venv"
ok "ambiente .venv pronto ($(.venv/bin/python --version 2>&1))"

echo "== 4/4 Riepilogo"
echo "  git $(git --version | awk '{print $3}') | $(.venv/bin/python --version 2>&1) | branch $(git branch --show-current)"
echo
echo "Tutto pronto. Apri Codex nella cartella $DIR e incolla il contenuto di:"
echo "  $DIR/docs/plans/e02-prompt-codex-socio.md"
echo "Nota per Codex: usa '$DIR/.venv/bin/python' come interprete per ogni comando Python."
