#!/usr/bin/env bash
# PapyrusLab — avvio di E01 sul Mac del socio. Il repository e' privato (curl sull'URL raw da' 404), quindi:
#
#   gh auth login
#   gh repo clone asap-matts/papyrus-lab ~/dev/papyrus-lab
#   bash ~/dev/papyrus-lab/scripts/e01_bootstrap_mac.sh
#
# Cosa fa: controlla git e Python, installa gh (se manca, con Homebrew) e la CLI Kaggle, clona il repository in
# ~/dev/papyrus-lab (fuori da iCloud), passa al branch e01-socio, verifica l'autenticazione Kaggle e dice cosa manca.
# Non legge ne' stampa credenziali. Rieseguibile: ogni passo controlla se e' gia' fatto.
set -uo pipefail

REPO="asap-matts/papyrus-lab"
DIR="$HOME/dev/papyrus-lab"
BRANCH="e01-socio"
ok()   { printf '  \033[32mOK\033[0m  %s\n' "$1"; }
todo() { printf '  \033[33mDA FARE\033[0m  %s\n' "$1"; }
fail() { printf '  \033[31mSTOP\033[0m  %s\n' "$1"; exit 1; }

echo "== 1/5 Strumenti"
command -v git >/dev/null 2>&1 || fail "git mancante: esegui 'xcode-select --install' e rilancia."
ok "git $(git --version | awk '{print $3}')"
PY="$(command -v python3 || true)"
[ -n "$PY" ] || fail "python3 mancante: 'brew install python@3.12' oppure python.org, poi rilancia."
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || fail "serve Python 3.11 o superiore (trovato $("$PY" --version 2>&1))."
ok "$("$PY" --version 2>&1)"

echo "== 2/5 GitHub CLI (il repository e' privato)"
if ! command -v gh >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then brew install gh >/dev/null 2>&1 || fail "installazione di gh fallita: 'brew install gh' a mano."
  else fail "manca 'gh' e manca Homebrew. Installa Homebrew (https://brew.sh) oppure gh da https://cli.github.com, poi rilancia."; fi
fi
if gh auth status >/dev/null 2>&1; then ok "gh autenticato"
else todo "esegui:  gh auth login   (scegli GitHub.com, HTTPS, login nel browser) — poi rilancia questo script"; exit 2; fi
gh auth setup-git >/dev/null 2>&1 || true

echo "== 3/5 Repository"
mkdir -p "$HOME/dev"
if [ -d "$DIR/.git" ]; then git -C "$DIR" fetch -q origin || fail "fetch fallito"
else gh repo clone "$REPO" "$DIR" -- -q || fail "clone fallito: hai accettato l'invito al repository? (mail da GitHub o https://github.com/$REPO/invitations)"; fi
cd "$DIR"
git switch -q "$BRANCH" 2>/dev/null || git switch -q -c "$BRANCH" "origin/$BRANCH" || fail "branch $BRANCH non trovato sul remoto"
git pull -q --ff-only origin "$BRANCH" || fail "pull non fast-forward: il branch locale e' divergente, chiedi a Matteo"
ok "clone in $DIR, branch $(git branch --show-current), commit $(git log -1 --format='%h %s')"
[ -f docs/plans/2026-09-06-e01-ripetizione-socio.md ] || fail "piano E01 assente: repository non aggiornato"
[ -d kaggle/e01-r01-seed42 ] || fail "notebook E01 assenti: repository non aggiornato"

echo "== 4/5 CLI Kaggle"
"$PY" -m pip install --user --quiet --upgrade kaggle >/dev/null 2>&1 || fail "installazione della CLI Kaggle fallita"
ok "kaggle $("$PY" -m kaggle --version 2>/dev/null | awk '{print $NF}')"

echo "== 5/5 Autenticazione Kaggle"
if "$PY" -m kaggle kernels list --mine --page-size 1 >/dev/null 2>&1; then ok "autenticazione Kaggle attiva"
else
  todo "esegui:  python3 -m kaggle auth login   (si apre il browser; oppure salva un token da kaggle.com/settings/api in ~/.kaggle/access_token) — poi rilancia questo script"
  exit 3
fi

echo
echo "Tutto pronto. Ora apri Codex nella cartella $DIR e incolla il contenuto di:"
echo "  $DIR/docs/plans/e01-prompt-codex.md"
echo "Codex fara' il resto e si fermera' a chiederti il via prima di ogni run GPU."
