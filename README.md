# Ubuntu Notes Application

A simple, elegant note-taking application for Ubuntu with Roboto Mono font, custom UI, and **offline AI-powered writing assistance using Ollama**.

## Features

- ✨ Clean Tkinter-based interface
- 📝 Create, edit, and delete notes
- 💾 Automatic save to JSON file
- 🔤 Roboto Mono font for better readability
- 📋 Sidebar with notes list
- 🗑️ Delete confirmation dialog
- ⌨️ Keyboard shortcuts (Ctrl+S to save, Ctrl+N for new note)
- 🎨 Custom cursor and pink background
- 🐱 Toggleable cat icons (pink/black)
- 🤖 **Offline AI Writing Assistant** - Powered by Ollama + Qwen 2.5 (no API key!)

## AI Writing Assistant

The app includes an **offline AI assistant** using Ollama with Qwen2.5-0.5B model:

- **🎭 Make it Poetic** - Transform plain text into beautiful, creative writing
- **📧 Professional Email** - Rephrase casual text as formal, professional emails
- **✍️ Improve Writing** - Enhance clarity, grammar, and style

### Why Ollama?

- ✅ **100% Offline** - No internet needed after setup
- ✅ **No API Key** - Works out of the box
- ✅ **Unlimited Usage** - No rate limits
- ✅ **Privacy** - All processing happens locally on your computer
- ✅ **Fast** - Optimized local inference

### Setup (One-Time)

1. **Install Ollama**:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

2. **Download Qwen model** (~400MB):

```bash
ollama pull qwen2.5:0.5b
```

3. **Done!** The AI assistant is now ready to use.

## Requirements

- Python 3 (with Tkinter - included by default)
- Roboto Mono font (optional)
- **Ollama** (for AI features)

## Installation

1. Install Roboto Mono font (optional):

```bash
sudo apt update
sudo apt install fonts-roboto
```

2. Install Ollama and model (for AI features):

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:0.5b
```

3. Run the application:

```bash
python3 notes_app.py
```

## Optional: Add to Application Menu

To add the app to your Ubuntu application menu:

```bash
# Copy the desktop file to applications directory
mkdir -p ~/.local/share/applications
cp notes-app.desktop ~/.local/share/applications/

# Update the Exec path in the desktop file to use absolute path
sed -i "s|/home/potatonim/des|$(pwd)|g" ~/.local/share/applications/notes-app.desktop

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

## Usage

- **New Note**: Click the "+" button in the sidebar or press Ctrl+N
- **Save Note**: Click the "Save" button or press Ctrl+S
- **Delete Note**: Click the "Delete" button (confirmation required)
- **Switch Notes**: Click on any note in the sidebar

## Data Storage

Notes are stored in JSON format at:

```
~/.local/share/notes-app/notes.json
```

Each note contains:

- Title
- Content
- Created timestamp
- Modified timestamp

## License

Free to use and modify.
