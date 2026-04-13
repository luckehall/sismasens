#!/bin/bash
# SISMASENS — Script di deploy su VPS
#
# Utilizzo:
#   bash deploy.sh          → installa Docker, crea .env template, si ferma
#   bash deploy.sh --start  → esegue il deploy completo (richiede .env compilato)
#
# Prerequisiti VPS:
#   - Apache2 installato e in esecuzione
#   - Certbot installato (apt install certbot python3-certbot-apache)
#   - DNS di sismasens.iotzator.com puntato a questo server

set -euo pipefail

DOMAIN="sismasens.iotzator.com"
CERTBOT_EMAIL="admin@iotzator.com"
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Colori ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC}  $*"; }
die()  { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

# ── Step 1: Docker ────────────────────────────────────────────────────────────
install_docker() {
    if command -v docker &>/dev/null; then
        ok "Docker già installato: $(docker --version)"
        return
    fi
    warn "Docker non trovato — installazione in corso..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker
    ok "Docker installato"
}

# ── Step 2: .env ──────────────────────────────────────────────────────────────
setup_env() {
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        warn "Creato $BACKEND_DIR/.env da .env.example"
        warn "Edita il file con le password reali e poi rilancia:"
        warn "  bash $0 --start"
        exit 0
    fi
    ok ".env trovato"
}

# ── Step 3: Certificato TLS ───────────────────────────────────────────────────
setup_tls() {
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        ok "Certificato TLS già presente per $DOMAIN"
        return
    fi
    warn "Certificato non trovato — richiesta a Let's Encrypt..."
    # Usa webroot: Apache deve già rispondere su :80 per $DOMAIN
    # Il vhost HTTP (porta 80) deve essere abilitato prima di questo step
    if ! apache2ctl -S 2>/dev/null | grep -q "$DOMAIN"; then
        # Abilita prima il vhost HTTP-only per la challenge
        cp "$BACKEND_DIR/apache/$DOMAIN.conf" "/etc/apache2/sites-available/$DOMAIN.conf"
        a2ensite "$DOMAIN"
        apache2ctl configtest && systemctl reload apache2
    fi
    certbot certonly \
        --webroot \
        -w /var/www/html \
        -d "$DOMAIN" \
        --non-interactive \
        --agree-tos \
        -m "$CERTBOT_EMAIL"
    ok "Certificato TLS ottenuto per $DOMAIN"
}

# ── Step 4: Apache vhost ──────────────────────────────────────────────────────
setup_apache() {
    local conf_src="$BACKEND_DIR/apache/$DOMAIN.conf"
    local conf_dst="/etc/apache2/sites-available/$DOMAIN.conf"

    # Abilita moduli necessari
    for mod in proxy proxy_http proxy_wstunnel ssl rewrite headers; do
        a2enmod -q "$mod"
    done

    cp "$conf_src" "$conf_dst"
    a2ensite "$DOMAIN"
    apache2ctl configtest || die "Errore nella configurazione Apache — controlla $conf_dst"
    systemctl reload apache2
    ok "Apache vhost abilitato per $DOMAIN"
}

# ── Step 5: Container Docker ──────────────────────────────────────────────────
start_containers() {
    cd "$BACKEND_DIR"
    docker compose pull --quiet 2>/dev/null || true
    docker compose up -d --build
    ok "Container avviati"

    echo ""
    echo "Stato container:"
    docker compose ps
}

# ── Main ──────────────────────────────────────────────────────────────────────
[ "$(id -u)" -eq 0 ] || die "Esegui come root: sudo bash $0 $*"

install_docker
setup_env     # esce qui se .env non era presente

[ "${1:-}" = "--start" ] || {
    warn "Aggiungi --start per procedere con il deploy completo"
    exit 0
}

setup_tls
setup_apache
start_containers

echo ""
ok "SISMASENS backend operativo su https://$DOMAIN"
echo ""
echo "Verifica:"
echo "  curl -s https://$DOMAIN/api/health"
echo "  docker compose -f $BACKEND_DIR/docker-compose.yml logs -f"
echo ""
echo "Admin EMQX (da locale via SSH tunnel):"
echo "  ssh -L 18083:localhost:18083 root@$DOMAIN"
echo "  → apri http://localhost:18083"
