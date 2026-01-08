#!/usr/bin/env bash
# Ubuntu Notes App - Uninstallation Script

set -e

echo "======================================"
echo "  Ubuntu Notes App - Uninstaller"
echo "======================================"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo ./uninstall.sh"
    exit 1
fi

echo "This will remove the Notes app from your system."
echo "Your notes data in ~/.local/share/notes-app/ will NOT be deleted."
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""
echo "[1/4] Removing application files..."
rm -rf /opt/notes-app

echo "[2/4] Removing launcher script..."
rm -f /usr/local/bin/notes-app

echo "[3/4] Removing desktop entry..."
rm -f /usr/share/applications/notes-app.desktop

echo "[4/4] Updating desktop database..."
update-desktop-database /usr/share/applications/ 2>/dev/null || true

echo ""
echo "✓ Uninstallation complete!"
echo ""
echo "Your notes data is still in ~/.local/share/notes-app/"
echo "Delete manually if you want to remove it completely."
echo ""
