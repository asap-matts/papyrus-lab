#!/usr/bin/env bash
# PapyrusLab — avvio sul Mac di un operatore (usato per E01). Il repository e' privato (curl sull'URL raw da' 404), quindi:
#
#   brew install gh            # se manca
#   gh auth login              # GitHub.com, HTTPS, login nel browser; poi accettare l'invito al repository
#   gh repo clone asap-matts/papyrus-lab ~/dev/papyrus-lab
#   bash ~/dev/papyrus-lab/scripts/e01_bootstrap_mac.sh
#
# Cosa fa, nell'ordine: repository e branch (subito, cosi' anche se un controllo successivo si ferma il clone e'
# gia' sul branch giusto), strumenti, Python >= 3.11 (preferendo quello di Homebrew se il python3 di sistema e'
# vecchio), CLI Kaggle (gestendo la protezione PEP 668 di Homebrew), autenticazione Kaggle. Non legge ne'
# stampa credenziali. Rieseguibile: ogni passo controlla se e' gia' fatto.
#
# Versione 2 (dopo E01-R01, 6 settembre 2026): integra gli otto ostacoli registrati dal socio nella scheda
# docs/reports/2026-09-06-e01-r01.md.
set -uo pipefail

REPO="asap-matts/papyrus-lab"
DIR="$HOME/dev/papyrus-lab"
BRANCH="${PAPYRUSLAB_BRANCH:-e01-socio}"
ok()   { printf '  \033[32mOK\033[0m  %s\n' "$1"; }
todo() { printf '  \033[33mDA FARE\033[0m  %s\n' "$1"; }
fail() { printf '  \033[31mSTOP\033[0m  %s\n' "$1"; exit 1; }

echo "== 1/5 GitHub CLI e repository (privato)"
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
else gh repo clone "$REPO" "$DIR" -- -q || fail "clone fallito: hai accettato l'invito al repository? (mail da GitHub o https://github.com/$REPO/invitations)"; fi
cd "$DIR"
if git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
  git switch -q "$BRANCH" 2>/dev/null || git switch -q -c "$BRANCH" "origin/$BRANCH" || fail "impossibile passare al branch $BRANCH"
  git pull -q --ff-only origin "$BRANCH" || fail "pull non fast-forward: il branch locale e' divergente, chiedi a Matteo"
else
  fail "branch $BRANCH assente sul remoto: chiedi a Matteo quale branch usare (PAPYRUSLAB_BRANCH=<nome> bash $0)"
fi
ok "repository in $DIR, branch $(git branch --show-current), commit $(git log -1 --format='%h %s')"

echo "== 2/5 Python >= 3.11"
# macOS espone spesso un python3 di sistema vecchio (3.9); Homebrew mette i binari non versionati in libexec/bin.
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

echo "== 3/5 CLI Kaggle"
PIP_LOG="$(mktemp)"
if ! "$PY" -m pip install --user --quiet --upgrade kaggle >"$PIP_LOG" 2>&1; then
  if grep -q "externally-managed-environment" "$PIP_LOG"; then
    # Homebrew Python (PEP 668) rifiuta pip --user: si consente l'eccezione per il solo pacchetto kaggle
    "$PY" -m pip install --user --quiet --upgrade --break-system-packages kaggle >"$PIP_LOG" 2>&1 \
      || { tail -5 "$PIP_LOG"; fail "installazione della CLI Kaggle fallita anche con --break-system-packages (vedi righe sopra)"; }
    ok "CLI Kaggle installata con --break-system-packages (Python di Homebrew, PEP 668)"
  else
    tail -5 "$PIP_LOG"; fail "installazione della CLI Kaggle fallita (vedi righe sopra)"
  fi
fi
rm -f "$PIP_LOG"
ok "kaggle $("$PY" -m kaggle --version 2>/dev/null | awk '{print $NF}')"

echo "== 4/5 Autenticazione Kaggle"
# `kernels list --mine` stampa 'Not found' con codice 0 quando l'account non ha ancora notebook: e' autenticato.
# Se NON e' autenticato stampa 'Authentication required' (codice 0 o 1 a seconda della versione).
AUTH_OUT="$("$PY" -m kaggle kernels list --mine --page-size 1 2>&1 || true)"
if printf '%s' "$AUTH_OUT" | grep -qi "authentication required\|unauthorized\|401"; then
  todo "esegui:  $PY -m kaggle auth login   (si apre il browser; se poi il browser mostra ERR_CONNECTION_REFUSED su localhost, e' normale: guarda il Terminale, deve dire 'You are now logged in'). In alternativa salva un token da kaggle.com/settings/api in ~/.kaggle/access_token. Poi rilancia questo script"
  exit 3
fi
ok "autenticazione Kaggle attiva$( printf '%s' "$AUTH_OUT" | grep -qi 'not found' && echo ' (nessun notebook ancora: normale)')"

echo "== 5/5 Riepilogo"
echo "  git $(git --version | awk '{print $3}') | $("$PY" --version 2>&1) | kaggle $("$PY" -m kaggle --version 2>/dev/null | awk '{print $NF}')"
echo
echo "Tutto pronto. Apri Codex nella cartella $DIR e incolla il contenuto di:"
echo "  $DIR/docs/plans/e01-prompt-codex.md"
echo "Nota per Codex: usa '$PY' come interprete (il python3 di sistema puo' essere troppo vecchio)."
echo "Codex fara' il resto e si fermera' a chiederti il via prima di ogni run GPU."
