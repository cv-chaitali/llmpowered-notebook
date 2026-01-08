#!/usr/bin/env bash
# Ubuntu Notes App - Installation Script

set -e

echo "======================================"
echo "  Ubuntu Notes App - Installer"
echo "======================================"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo ./install.sh"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$ACTUAL_USER)

echo "Installing for user: $ACTUAL_USER"
echo "Home directory: $USER_HOME"
echo ""

# Create installation directory
INSTALL_DIR="/opt/notes-app"
echo "[1/6] Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Copy application files
echo "[2/6] Copying application files..."
cp notes_app.py "$INSTALL_DIR/"
cp *.png "$INSTALL_DIR/" 2>/dev/null || echo "  Note: No PNG files found (optional)"
chmod +x "$INSTALL_DIR/notes_app.py"

# Create launcher script
echo "[3/6] Creating launcher script..."
cat > /usr/local/bin/notes-app << 'EOF'
#!/usr/bin/env bash
cd /opt/notes-app
python3 notes_app.py "$@"
EOF
chmod +x /usr/local/bin/notes-app

# Install desktop entry
echo "[4/6] Installing desktop entry..."
cat > /usr/share/applications/notes-app.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Notes
Comment=Note-taking app with AI assistance
Exec=/usr/local/bin/notes-app
Icon=/opt/notes-app/cat_pink.png
Terminal=false
Categories=Utility;TextEditor;Office;
Keywords=notes;editor;text;ai;
StartupNotify=true
EOF

# Update desktop database
echo "[5/6] Updating desktop database..."
update-desktop-database /usr/share/applications/ 2>/dev/null || true

# Set proper permissions
echo "[6/6] Setting permissions..."
chown -R root:root "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"
chmod 644 "$INSTALL_DIR"/*.py "$INSTALL_DIR"/*.png 2>/dev/null || true

echo ""
echo "✓ Installation complete!"
echo ""
echo "You can now:"
echo "  • Launch from Applications menu (search for 'Notes')"
echo "  • Run from terminal: notes-app"
echo ""
echo "Data will be stored in: $USER_HOME/.local/share/notes-app/"
echo ""
