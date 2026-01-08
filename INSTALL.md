# Ubuntu Notes Application - Installation Guide

## Quick Install

To install the Notes app system-wide on Ubuntu:

```bash
cd /home/potatonim/des
sudo ./install.sh
```

This will:

- Install the app to `/opt/notes-app/`
- Create a launcher command `notes-app`
- Add the app to your Applications menu
- Set up proper permissions

## Usage

After installation, you can launch the app:

**From Applications Menu:**

- Press Super key (Windows key)
- Search for "Notes"
- Click to launch

**From Terminal:**

```bash
notes-app
```

## Features

### ⌨️ Keyboard Shortcuts

- `Ctrl+S` - Save note
- `Ctrl+N` - New note
- `Ctrl+F` - Find and replace
- `Ctrl+B` - Bold selected text
- `Ctrl+I` - Italic selected text
- `Ctrl+K` - Insert code block
- `Ctrl+A` - Select all
- `Ctrl+C/V/X` - Copy/Paste/Cut
- `Ctrl+Z/Y` - Undo/Redo

### 📝 Code Formatting

- Click "📝 Code Block" or press `Ctrl+K` to insert code blocks
- Code blocks use ``` markdown syntax
- Monospace font for better code readability

### 🎨 Customization

- 5 theme presets (Pink, Dark, Light, Ocean, Forest)
- Font family selection (6 fonts)
- Font size (8-36)
- Text and background colors
- Sidebar width control
- Window scaling (0.8-2.5x)

### 🤖 AI Features

- Powered by Ollama + Qwen 2.5
- Make text poetic
- Rephrase as professional email
- Improve writing
- 100% offline, no API key needed

## Uninstall

To remove the app:

```bash
cd /home/potatonim/des
sudo ./uninstall.sh
```

Your notes data in `~/.local/share/notes-app/` will be preserved.

## Manual Installation

If you prefer to run without installing:

```bash
cd /home/potatonim/des
python3 notes_app.py
```

## Requirements

- Python 3 with Tkinter
- Ollama (for AI features)
- Optional: Roboto Mono font

## Data Location

Notes are stored in: `~/.local/share/notes-app/notes.json`
Settings are stored in: `~/.local/share/notes-app/config.json`
