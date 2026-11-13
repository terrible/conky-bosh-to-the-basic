#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$DIR/bosh-to-the-basic"
TARGET="${CONKY_TARGET:-$HOME/.config/conky/bosh-to-the-basic}"
AUTOSTART="${CONKY_AUTOSTART:-$HOME/.config/autostart}"
DESKTOP_FILE="$AUTOSTART/conky-bosh-to-the-basic.desktop"

CONKY_BIN="$(command -v conky || true)"

if [[ -z "$CONKY_BIN" ]]; then
    echo "Conky no está instalado."

    . /etc/os-release

    if [[ " ${ID:-} ${ID_LIKE:-} " == *" fedora "* ]] || [[ " ${ID:-} ${ID_LIKE:-} " == *" rhel "* ]]; then
        echo "Instálalo con: sudo dnf install conky"
    elif [[ " ${ID:-} ${ID_LIKE:-} " == *" arch "* ]]; then
        echo "Instálalo con: sudo pacman -S conky"
    elif [[ " ${ID:-} ${ID_LIKE:-} " == *" debian "* ]]; then
        echo "Instálalo con: sudo apt install conky-all"
    else
        echo "Instala Conky desde los repositorios de tu distribución."
    fi

    exit 1
fi

if [[ ! -f "$SOURCE/bosh-to-the-basic.conf" ]]; then
    echo "ERROR: No se encuentra bosh-to-the-basic.conf"
    exit 1
fi

mkdir -p "$(dirname "$TARGET")" "$AUTOSTART"

STAGING="${TARGET}.staging-$$"
BACKUP=""

cleanup() {
    rm -rf "$STAGING"
}
trap cleanup EXIT

rm -rf "$STAGING"
mkdir -p "$STAGING"
cp -a "$SOURCE/." "$STAGING/"

if [[ ! -f "$STAGING/bosh-to-the-basic.conf" ]]; then
    echo "ERROR: La copia temporal está incompleta."
    exit 1
fi

sed -i "s|@CONKY_DIR@|$TARGET|g" "$STAGING/bosh-to-the-basic.conf"

find "$STAGING/scripts" -type f -name "*.sh" -exec chmod +x {} +

if [[ -d "$TARGET" ]]; then
    BACKUP="$TARGET.backup-$(date +%Y%m%d-%H%M%S)"
    mv "$TARGET" "$BACKUP"
    echo "Copia anterior guardada en: $BACKUP"
fi

if ! mv "$STAGING" "$TARGET"; then
    echo "ERROR: No se pudo instalar el tema."
    if [[ -n "$BACKUP" && -d "$BACKUP" ]]; then
        mv "$BACKUP" "$TARGET"
        echo "Se restauró la instalación anterior."
    fi
    exit 1
fi

trap - EXIT

cat > "$DESKTOP_FILE" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Conky Bosh To The Basic
Comment=Monitor del sistema
Exec=/bin/sh -c "sleep 8; $CONKY_BIN -c $TARGET/bosh-to-the-basic.conf -d"
Terminal=false
X-KDE-autostart-enabled=true
DESKTOP

chmod 644 "$DESKTOP_FILE"

echo
echo "Instalación completada."
echo "Ubicación: $TARGET"
echo "Inicio automático configurado."
echo
echo "Para iniciar Conky ahora:"
echo "$CONKY_BIN -c $TARGET/bosh-to-the-basic.conf -d"
