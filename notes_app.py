#!/usr/bin/env python3
"""
Ubuntu Notes Application
A simple note-taking application with save/load functionality using Tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import json
import os
from datetime import datetime
import threading
import subprocess

class NotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Notes")
        self.root.geometry("900x600")
        
        # Set minimum window size for usability
        self.root.minsize(600, 400)
        
        # Set up the notes storage file
        self.notes_dir = os.path.expanduser("~/.local/share/notes-app")
        os.makedirs(self.notes_dir, exist_ok=True)
        self.notes_file = os.path.join(self.notes_dir, "notes.json")
        self.config_file = os.path.join(self.notes_dir, "config.json")
        
        # Initialize notes list
        self.notes = self.load_notes()
        self.current_note_index = None
        
        # Load configuration (API keys, etc.)
        self.config = self.load_config()
        
        # Set default settings if not in config
        defaults = {
            'font_size': 12,
            'font_family': 'TkDefaultFont',  # System default with Unicode support
            'text_color': '#000000',
            'bg_color': '#FFFFFF',
            'sidebar_bg': '#ffe8f0',
            'editor_bg': '#fff0f5',
            'sidebar_width': 200,
            'window_scale': 1.0,
            'theme': 'pink',  # pink, dark, light, custom
            'language': 'english',  # english, bengali, korean
            'ai_model': 'qwen2.5:0.5b',  # default Ollama model
            'code_preview_theme': 'light'  # light, dark
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        
        # Apply window scaling
        base_width = 900
        base_height = 600
        scaled_width = int(base_width * self.config['window_scale'])
        scaled_height = int(base_height * self.config['window_scale'])
        self.root.geometry(f"{scaled_width}x{scaled_height}")
        
        # Check if Ollama is available
        self.ollama_available = self.check_ollama()
        
        # Cat icon toggle state (True = pink, False = black)
        self.is_pink_cat = True
        
        # Get the directory where the script is located
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Get Unicode-compatible font
        unicode_font = self.get_unicode_font()
        
        # Update font_family if using fonts that don't work well with Tkinter
        # Use a font that supports Unicode (Korean, Bengali, etc.)
        if self.config.get('font_family') in ['Roboto Mono', 'DejaVu Sans']:
            self.config['font_family'] = unicode_font
        elif self.config.get('font_family') == 'TkDefaultFont':
            # Keep TkDefaultFont as it has good Unicode support
            pass
        
        # Load custom assets
        self.load_assets()
        
        # Configure style
        self.setup_style()
        
        # Create the UI
        self.create_ui()
        
        # Set custom cursor
        self.set_custom_cursor()
        
        # Bind window resize event
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Track last resize time for debouncing
        self.last_resize_time = 0
        self.resize_job = None
        
        # Load first note if available
        if self.notes:
                self.load_note(0)
    
    def get_unicode_font(self):
        """Get a font that supports Unicode characters (Bengali, Korean, etc.)"""
        import tkinter.font as tkfont
        
        # On Linux, Tkinter may not see all system fonts
        # We'll use TkDefaultFont and configure it, or try common fonts
        
        # First, try to use fonts that Tkinter can actually see
        available_families = list(tkfont.families())
        
        # Try these fonts in order - prioritizing those with good Unicode support
        preferred_fonts = [
            'DejaVu Sans',      # Excellent Unicode support
            'Noto Sans',        # Google's comprehensive Unicode font
            'Noto Sans CJK',    # Specifically for CJK (Chinese, Japanese, Korean)
            'Liberation Sans',  # Good Unicode coverage
            'FreeSans',         # Free font with Unicode
            'Ubuntu',           # Ubuntu system font
            'Cantarell',        # GNOME default
            'TkDefaultFont',    # System default, usually has Unicode support
        ]
        
        for font in preferred_fonts:
            if font in available_families:
                return font
        
        # If none found, return TkDefaultFont which should work
        return 'TkDefaultFont'
    
    def load_assets(self):
        """Load custom images for cursor, icons, and background"""
        try:
            # Load cursor image
            cursor_path = os.path.join(self.app_dir, "cursor.png")
            if os.path.exists(cursor_path):
                self.cursor_img = Image.open(cursor_path)
            else:
                self.cursor_img = None
            
            # Load cat icons
            cat_pink_path = os.path.join(self.app_dir, "cat_pink.png")
            cat_black_path = os.path.join(self.app_dir, "cat_black.png")
            
            if os.path.exists(cat_pink_path):
                self.cat_pink_img = ImageTk.PhotoImage(Image.open(cat_pink_path).resize((32, 32), Image.Resampling.LANCZOS))
            else:
                self.cat_pink_img = None
            
            if os.path.exists(cat_black_path):
                self.cat_black_img = ImageTk.PhotoImage(Image.open(cat_black_path).resize((32, 32), Image.Resampling.LANCZOS))
            else:
                self.cat_black_img = None
            
            # Load background image
            bg_path = os.path.join(self.app_dir, "pink_bg.png")
            if os.path.exists(bg_path):
                # Open and resize to fit window
                bg_image = Image.open(bg_path)
                # Resize to cover the window
                self.bg_img = ImageTk.PhotoImage(bg_image.resize((900, 600), Image.Resampling.LANCZOS))
            else:
                self.bg_img = None
                
        except Exception as e:
            print(f"Error loading assets: {e}")
            self.cursor_img = None
            self.cat_pink_img = None
            self.cat_black_img = None
            self.bg_img = None
    
    def set_custom_cursor(self):
        """Set custom cursor for the application"""
        try:
            if self.cursor_img:
                # Save cursor as temporary file for Tkinter
                cursor_path = os.path.join(self.app_dir, "cursor.png")
                if os.path.exists(cursor_path):
                    # Tkinter requires cursor in specific format
                    self.root.config(cursor=f"@{cursor_path}")
        except Exception as e:
            print(f"Error setting cursor: {e}")
    
    def setup_style(self):
        """Configure the application style"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        bg_color = "#f5f5f5"
        sidebar_color = "#e8e8e8"
        accent_color = "#4a90e2"
        
        self.root.configure(bg=bg_color)
        
        style.configure("Sidebar.TFrame", background=sidebar_color)
        style.configure("Main.TFrame", background=bg_color)
        style.configure("TButton", padding=6, relief="flat", background=accent_color)
        style.map("TButton", background=[('active', '#357abd')])
    
    def create_ui(self):
        # Main container
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Background image using Canvas (if available)
        if self.bg_img:
            self.bg_canvas = tk.Canvas(main_container, width=900, height=600, highlightthickness=0)
            self.bg_canvas.pack(fill=tk.BOTH, expand=True)
            
            # Bind resize event to update background
            def on_resize(event):
                # Resize background image to match canvas
                if self.bg_img:
                    try:
                        bg_image = Image.open(os.path.join(self.app_dir, "pink_bg.png"))
                        resized_bg = bg_image.resize((event.width, event.height), Image.Resampling.LANCZOS)
                        self.bg_img = ImageTk.PhotoImage(resized_bg)
                        self.bg_canvas.delete("bg")
                        self.bg_canvas.create_image(0, 0, image=self.bg_img, anchor=tk.NW, tags="bg")
                        self.bg_canvas.tag_lower("bg")
                    except Exception as e:
                        print(f"Error resizing background: {e}")
            
            self.bg_canvas.bind('<Configure>', on_resize)
            
            # Create frames on canvas
            sidebar_frame = tk.Frame(
                self.bg_canvas,
                bg=self.config['sidebar_bg']
            )
            self.sidebar_window = self.bg_canvas.create_window(0, 0, window=sidebar_frame, anchor=tk.NW, tags="sidebar")
            
            editor_frame = tk.Frame(self.bg_canvas, bg=self.config['editor_bg'])
            self.editor_window = self.bg_canvas.create_window(0, 0, window=editor_frame, anchor=tk.NW, tags="editor")
            
            # Update window positions on canvas resize
            def update_layout(event):
                canvas_width = event.width
                canvas_height = event.height
                sidebar_width = self.config['sidebar_width']
                
                # Update sidebar window
                self.bg_canvas.coords(self.sidebar_window, 0, 0)
                self.bg_canvas.itemconfig(self.sidebar_window, width=sidebar_width, height=canvas_height)
                
                # Update editor window
                self.bg_canvas.coords(self.editor_window, sidebar_width, 0)
                self.bg_canvas.itemconfig(self.editor_window, width=canvas_width - sidebar_width, height=canvas_height)
            
            self.bg_canvas.bind('<Configure>', lambda e: (on_resize(e), update_layout(e)), add='+')
            
        else:
            # Left sidebar for notes list
            sidebar_frame = tk.Frame(main_container, bg="#ffe8f0")
            sidebar_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
            
            # Right side - note editor
            editor_frame = tk.Frame(main_container, bg="#fff0f5")
            editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sidebar header
        header_frame = tk.Frame(sidebar_frame, bg="#ffe8f0")
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        sidebar_label = tk.Label(header_frame, text="My Notes", font=("Ubuntu", 14, "bold"),
                                 bg="#ffe8f0", fg="#333333")
        sidebar_label.pack(side=tk.LEFT)
        
        # Cat icon toggle button
        self.cat_button = tk.Button(header_frame, command=self.toggle_cat_icon,
                                    relief=tk.FLAT, bg="#ffe8f0", borderwidth=0)
        if self.is_pink_cat and self.cat_pink_img:
            self.cat_button.config(image=self.cat_pink_img)
        elif not self.is_pink_cat and self.cat_black_img:
            self.cat_button.config(image=self.cat_black_img)
        else:
            self.cat_button.config(text="🐱")
        self.cat_button.pack(side=tk.RIGHT, padx=2)
        
        new_button = ttk.Button(header_frame, text="+", width=3, command=self.on_new_note)
        new_button.pack(side=tk.RIGHT)
        
        # Notes listbox
        list_frame = tk.Frame(sidebar_frame, bg="#ffe8f0")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.notes_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                       font=("Ubuntu", 10), bg="white",
                                       selectmode=tk.SINGLE, relief=tk.FLAT,
                                       highlightthickness=0, borderwidth=0)
        self.notes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.notes_listbox.yview)
        
        self.notes_listbox.bind('<<ListboxSelect>>', self.on_note_selected)
        
        # Add mousewheel scrolling support
        self.bind_mousewheel(self.notes_listbox)
        
        self.refresh_notes_list()
        
        # Right side - note editor (semi-transparent pink)
        # Editor frame is already created above in both bg and non-bg modes
        
        # Editor header with title
        title_frame = tk.Frame(editor_frame, bg="#fff0f5")
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title label and entry
        title_row = tk.Frame(title_frame, bg="#fff0f5")
        title_row.pack(fill=tk.X, pady=(0, 5))
        
        title_label = tk.Label(title_row, text="Title:", font=("Ubuntu", 10),
                               bg="#fff0f5", fg="#333333")
        title_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.title_entry = ttk.Entry(title_row, font=("Ubuntu", 11))
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Buttons in a wrapping frame for responsiveness
        button_row = tk.Frame(title_frame, bg="#fff0f5")
        button_row.pack(fill=tk.X)
        
        # Main action buttons with plain text (no emoji for better compatibility)
        save_button = ttk.Button(button_row, text="Save", command=self.on_save_note)
        save_button.pack(side=tk.LEFT, padx=2, pady=2)
        
        delete_button = ttk.Button(button_row, text="Delete", command=self.on_delete_note)
        delete_button.pack(side=tk.LEFT, padx=2, pady=2)
        
        # AI Assistant button
        ai_button = ttk.Button(button_row, text="AI Assistant", command=self.open_ai_assistant)
        ai_button.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Settings button
        settings_button = ttk.Button(button_row, text="Settings", command=self.open_settings)
        settings_button.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Help button
        help_button = ttk.Button(button_row, text="Help", command=self.show_shortcuts_help)
        help_button.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Formatting toolbar
        format_frame = tk.Frame(editor_frame, bg="#fff0f5")
        format_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(format_frame, text="Code Block", command=self.insert_code_block).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="Preview", command=self.open_code_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="Find", command=self.open_find_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="B", command=self.toggle_bold, width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="I", command=self.toggle_italic, width=3).pack(side=tk.LEFT, padx=2)
        
        # Text editor with Roboto Mono font
        text_frame = tk.Frame(editor_frame, bg="#fff0f5")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_widget = scrolledtext.ScrolledText(
            text_frame,
            font=(self.config['font_family'], self.config['font_size']),
            wrap=tk.WORD,
            undo=True,
            fg=self.config['text_color'],
            bg=self.config['bg_color'],
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#ffb6c1",
            insertbackground=self.config['text_color'],
            padx=10,
            pady=10
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_label = tk.Label(editor_frame, text="Ready", font=("Ubuntu", 9),
                                     bg="#fff0f5", fg="#666666")
        self.status_label.pack(fill=tk.X, pady=(5, 0))
        
        # Keyboard shortcuts
        # File operations
        self.root.bind('<Control-s>', lambda e: self.on_save_note())
        self.root.bind('<Control-n>', lambda e: self.on_new_note())
        self.root.bind('<Control-w>', lambda e: self.on_new_note())  # Alternative for new
        self.root.bind('<Control-d>', lambda e: self.on_delete_note())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        
        # Search and navigation
        self.root.bind('<Control-f>', lambda e: self.open_find_dialog())
        self.root.bind('<Control-h>', lambda e: self.open_find_dialog())  # Alternative for find
        
        # Formatting
        self.root.bind('<Control-b>', lambda e: self.toggle_bold())
        self.root.bind('<Control-i>', lambda e: self.toggle_italic())
        self.root.bind('<Control-k>', lambda e: self.insert_code_block())
        
        # Tools
        self.root.bind('<Control-p>', lambda e: self.open_code_preview())
        self.root.bind('<Control-Shift-A>', lambda e: self.open_ai_assistant())
        self.root.bind('<Control-Shift-S>', lambda e: self.open_settings())
        
        # Help
        self.root.bind('<F1>', lambda e: self.show_shortcuts_help())
        self.root.bind('<Control-slash>', lambda e: self.show_shortcuts_help())
        
        # Utility
        self.root.bind('<Escape>', lambda e: self.text_widget.tag_remove(tk.SEL, "1.0", tk.END))
        
        # Text widget specific bindings (some may not work by default on Linux)
        self.text_widget.bind('<Control-a>', self.select_all)
        self.text_widget.bind('<Control-A>', self.select_all)  # Also bind uppercase
        
        # Text widget already supports these by default on most systems:
        # Ctrl+C (Copy), Ctrl+V (Paste), Ctrl+X (Cut), Ctrl+Z (Undo), Ctrl+Y (Redo)

    
    def refresh_notes_list(self):
        """Refresh the notes list display"""
        self.notes_listbox.delete(0, tk.END)
        for note in self.notes:
            title = note.get("title", "Untitled")
            self.notes_listbox.insert(tk.END, f"  {title}")
    
    def on_note_selected(self, event):
        """Handle note selection from list"""
        selection = self.notes_listbox.curselection()
        if selection:
            index = selection[0]
            self.load_note(index)
    
    def load_note(self, index):
        """Load a note into the editor"""
        if 0 <= index < len(self.notes):
            self.current_note_index = index
            note = self.notes[index]
            
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, note.get("title", ""))
            
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", note.get("content", ""))
            
            self.status_label.config(text=f"Loaded: {note.get('title', 'Untitled')}")
            
            # Select in listbox
            self.notes_listbox.selection_clear(0, tk.END)
            self.notes_listbox.selection_set(index)
            self.notes_listbox.see(index)
    
    def on_new_note(self):
        """Create a new note"""
        new_note = {
            "title": "New Note",
            "content": "",
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat()
        }
        self.notes.append(new_note)
        self.save_notes()
        self.refresh_notes_list()
        self.load_note(len(self.notes) - 1)
    
    def on_save_note(self):
        """Save the current note"""
        if self.current_note_index is not None:
            title = self.title_entry.get().strip()
            content = self.text_widget.get("1.0", tk.END).strip()
            
            self.notes[self.current_note_index]["title"] = title if title else "Untitled"
            self.notes[self.current_note_index]["content"] = content
            self.notes[self.current_note_index]["modified"] = datetime.now().isoformat()
            
            self.save_notes()
            self.refresh_notes_list()
            self.status_label.config(text=f"Saved: {title if title else 'Untitled'}")
            
            # Re-select current note
            self.notes_listbox.selection_clear(0, tk.END)
            self.notes_listbox.selection_set(self.current_note_index)
    
    def on_delete_note(self):
        """Delete the current note"""
        if self.current_note_index is not None and len(self.notes) > 0:
            result = messagebox.askyesno(
                "Delete Note",
                "Are you sure you want to delete this note?\nThis action cannot be undone.",
                icon='warning'
            )
            
            if result:
                deleted_title = self.notes[self.current_note_index].get("title", "Untitled")
                del self.notes[self.current_note_index]
                self.save_notes()
                self.refresh_notes_list()
                
                # Load another note or clear
                if self.notes:
                    new_index = min(self.current_note_index, len(self.notes) - 1)
                    self.load_note(new_index)
                else:
                    self.current_note_index = None
                    self.title_entry.delete(0, tk.END)
                    self.text_widget.delete("1.0", tk.END)
                
                self.status_label.config(text=f"Deleted: {deleted_title}")
    
    def load_notes(self):
        """Load notes from JSON file"""
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading notes: {e}")
                return []
        return []
    
    def save_notes(self):
        """Save notes to JSON file"""
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving notes: {e}")
            self.status_label.config(text=f"Error saving: {e}")
    
    def toggle_cat_icon(self):
        """Toggle between pink and black cat icons"""
        self.is_pink_cat = not self.is_pink_cat
        
        if self.is_pink_cat and self.cat_pink_img:
            self.cat_button.config(image=self.cat_pink_img)
            self.status_label.config(text="Switched to Pink Cat 🐱")
        elif not self.is_pink_cat and self.cat_black_img:
            self.cat_button.config(image=self.cat_black_img)
            self.status_label.config(text="Switched to Black Cat 🐱")
    
    def load_config(self):
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return {}
        return {}
    
    def save_config(self):
        """Save configuration to JSON file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def setup_gemini(self):
        """Initialize local AI model (Ollama)"""
        # This method is kept for compatibility
        pass
    
    def check_ollama(self):
        """Check if Ollama is installed and running"""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def get_available_models(self):
        """Get list of available Ollama models"""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse model names from output
                lines = result.stdout.strip().split('\n')
                models = []
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                return models if models else ['qwen2.5:0.5b']
            else:
                return ['qwen2.5:0.5b']
        except Exception as e:
            print(f"Error getting models: {e}")
            return ['qwen2.5:0.5b']
    
    def generate_text_ollama(self, prompt, max_tokens=300, model=None):
        """Generate text using Ollama"""
        if model is None:
            model = self.config.get('ai_model', 'qwen2.5:0.5b')
        
        try:
            # Use subprocess to call ollama
            result = subprocess.run(
                ['ollama', 'run', model, prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"Ollama error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Ollama timeout")
            return None
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return None
    
    def open_ai_assistant(self):
        """Open AI Assistant dialog"""
        if not self.ollama_available:
            messagebox.showerror(
                "AI Assistant Unavailable",
                "Ollama is not installed or not running.\n\n"
                "Install it with:\ncurl -fsSL https://ollama.com/install.sh | sh\n"
                "Then run: ollama pull qwen2.5:0.5b"
            )
            return
        
        # Show AI Assistant dialog
        AIAssistantDialog(self.root, self)
    
    def open_settings(self):
        """Open settings dialog"""
        SettingsDialog(self.root, self)
    
    def insert_code_block(self):
        """Insert a code block at cursor position"""
        try:
            # Get current selection or insert at cursor
            try:
                selected_text = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                selected_text = ""
            
            # Insert code block
            code_block = f"```\n{selected_text}\n```\n"
            self.text_widget.insert(tk.INSERT, code_block)
            self.status_label.config(text="📝 Code block inserted")
        except Exception as e:
            print(f"Error inserting code block: {e}")
    
    def toggle_bold(self):
        """Toggle bold formatting for selected text"""
        try:
            selected_text = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.text_widget.insert(tk.INSERT, f"**{selected_text}**")
            self.status_label.config(text="Bold applied")
        except tk.TclError:
            self.status_label.config(text="Select text first")
    
    def toggle_italic(self):
        """Toggle italic formatting for selected text"""
        try:
            selected_text = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.text_widget.insert(tk.INSERT, f"*{selected_text}*")
            self.status_label.config(text="Italic applied")
        except tk.TclError:
            self.status_label.config(text="Select text first")
    
    def select_all(self, event=None):
        """Select all text in the editor"""
        self.text_widget.tag_add(tk.SEL, "1.0", tk.END)
        self.text_widget.mark_set(tk.INSERT, "1.0")
        self.text_widget.see(tk.INSERT)
        return 'break'  # Prevent default behavior
    
    def open_find_dialog(self):
        """Open find and replace dialog"""
        FindDialog(self.root, self)
    
    def open_code_preview(self):
        """Open code block preview dialog"""
        CodeBlockPreviewDialog(self.root, self)
    
    def show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog"""
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("⌨️ Keyboard Shortcuts")
        help_dialog.geometry("600x500")
        help_dialog.transient(self.root)
        help_dialog.grab_set()
        
        # Center the dialog
        help_dialog.update_idletasks()
        x = (help_dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (help_dialog.winfo_screenheight() // 2) - (500 // 2)
        help_dialog.geometry(f"600x500+{x}+{y}")
        
        main_frame = tk.Frame(help_dialog, bg="#fff0f5", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="⌨️ Keyboard Shortcuts",
            font=("Ubuntu", 14, "bold"),
            bg="#fff0f5"
        )
        title_label.pack(pady=(0, 15))
        
        # Create scrollable frame
        canvas = tk.Canvas(main_frame, bg="#fff0f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#fff0f5")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Shortcuts data
        shortcuts = [
            ("📁 File Operations", [
                ("Ctrl+S", "Save current note"),
                ("Ctrl+N / Ctrl+W", "Create new note"),
                ("Ctrl+D", "Delete current note"),
                ("Ctrl+Q", "Quit application"),
            ]),
            ("🔍 Search & Navigation", [
                ("Ctrl+F / Ctrl+H", "Find and replace"),
                ("Escape", "Clear selection"),
            ]),
            ("✏️ Text Formatting", [
                ("Ctrl+B", "Bold text"),
                ("Ctrl+I", "Italic text"),
                ("Ctrl+K", "Insert code block"),
            ]),
            ("📝 Text Editing (Built-in)", [
                ("Ctrl+A", "Select all"),
                ("Ctrl+C", "Copy"),
                ("Ctrl+V", "Paste"),
                ("Ctrl+X", "Cut"),
                ("Ctrl+Z", "Undo"),
                ("Ctrl+Y", "Redo"),
            ]),
            ("🛠️ Tools", [
                ("Ctrl+P", "Preview code blocks"),
                ("Ctrl+Shift+A", "AI Assistant"),
                ("Ctrl+Shift+S", "Settings"),
            ]),
            ("❓ Help", [
                ("F1 / Ctrl+/", "Show this help"),
            ]),
        ]
        
        # Display shortcuts
        for category, items in shortcuts:
            # Category header
            category_label = tk.Label(
                scrollable_frame,
                text=category,
                font=("Ubuntu", 11, "bold"),
                bg="#fff0f5",
                fg="#333333"
            )
            category_label.pack(anchor=tk.W, pady=(10, 5))
            
            # Shortcuts in this category
            for shortcut, description in items:
                shortcut_frame = tk.Frame(scrollable_frame, bg="#fff0f5")
                shortcut_frame.pack(fill=tk.X, pady=2)
                
                shortcut_label = tk.Label(
                    shortcut_frame,
                    text=shortcut,
                    font=("Roboto Mono", 10, "bold"),
                    bg="#ffe8f0",
                    fg="#333333",
                    width=20,
                    anchor=tk.W,
                    padx=5,
                    pady=2
                )
                shortcut_label.pack(side=tk.LEFT, padx=(0, 10))
                
                desc_label = tk.Label(
                    shortcut_frame,
                    text=description,
                    font=("Ubuntu", 10),
                    bg="#fff0f5",
                    fg="#666666",
                    anchor=tk.W
                )
                desc_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Close button
        close_button = ttk.Button(
            main_frame,
            text="Close",
            command=help_dialog.destroy
        )
        close_button.pack(pady=(15, 0))
    
    def on_window_resize(self, event):
        """Handle window resize events with debouncing"""
        # Only process resize events for the root window
        if event.widget != self.root:
            return
        
        # Debounce resize events to avoid excessive processing
        import time
        current_time = time.time()
        
        # Cancel previous resize job if exists
        if self.resize_job:
            self.root.after_cancel(self.resize_job)
        
        # Schedule new resize job after 100ms delay
        self.resize_job = self.root.after(100, self.apply_responsive_layout)
        self.last_resize_time = current_time
    
    def apply_responsive_layout(self):
        """Apply responsive layout adjustments based on current window size"""
        try:
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            
            # Calculate responsive sidebar width (20-30% of window width)
            min_sidebar = 150
            max_sidebar = 400
            responsive_sidebar = int(window_width * 0.25)
            new_sidebar_width = max(min_sidebar, min(max_sidebar, responsive_sidebar))
            
            # Update sidebar width if using canvas layout
            if hasattr(self, 'bg_canvas') and hasattr(self, 'sidebar_window'):
                self.bg_canvas.itemconfig(self.sidebar_window, width=new_sidebar_width)
                editor_width = window_width - new_sidebar_width
                self.bg_canvas.itemconfig(self.editor_window, width=editor_width)
                self.bg_canvas.coords(self.editor_window, new_sidebar_width, 0)
        except Exception as e:
            print(f"Error in responsive layout: {e}")
    
    def calculate_responsive_sizes(self):
        """Calculate responsive sizes for UI elements based on window dimensions"""
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Calculate button sizes
        if window_width < 700:
            button_width = 8
            button_padding = 1
        elif window_width < 900:
            button_width = 10
            button_padding = 2
        else:
            button_width = 12
            button_padding = 2
        
        return {
            'button_width': button_width,
            'button_padding': button_padding,
            'sidebar_width': int(window_width * 0.25),
            'font_scale': 1.0 if window_width >= 800 else 0.9
        }
    
    def bind_mousewheel(self, widget):
        """Bind mousewheel scrolling to a widget"""
        def on_mousewheel(event):
            # Linux uses event.num to distinguish scroll direction
            if event.num == 4:  # Scroll up
                widget.yview_scroll(-1, "units")
            elif event.num == 5:  # Scroll down
                widget.yview_scroll(1, "units")
            # Windows and macOS use event.delta
            elif hasattr(event, 'delta'):
                widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Bind for Linux
        widget.bind("<Button-4>", on_mousewheel)
        widget.bind("<Button-5>", on_mousewheel)
        # Bind for Windows and macOS
        widget.bind("<MouseWheel>", on_mousewheel)


class AIAssistantDialog:
    def __init__(self, parent, notes_app):
        self.notes_app = notes_app
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("✨ AI Writing Assistant")
        
        # Calculate responsive dialog size (80% of parent window)
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = min(700, int(parent_width * 0.8))
        dialog_height = min(650, int(parent_height * 0.85))
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (dialog_width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (dialog_height // 2)
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        self.create_ui()
    
    def create_ui(self):
        main_frame = tk.Frame(self.dialog, bg="#fff0f5", padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="AI Writing Assistant",
            font=("Ubuntu", 14, "bold"),
            bg="#fff0f5"
        )
        title_label.pack(pady=(0, 10))
        
        # Settings Frame (Model and Language Selection)
        settings_frame = tk.LabelFrame(main_frame, text="AI Settings", bg="#fff0f5", font=("Ubuntu", 10, "bold"), padx=10, pady=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Model Selection
        model_label = tk.Label(settings_frame, text="Model:", bg="#fff0f5", font=("Ubuntu", 9))
        model_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        available_models = self.notes_app.get_available_models()
        self.model_var = tk.StringVar(value=self.notes_app.config.get('ai_model', 'qwen2.5:0.5b'))
        model_dropdown = ttk.Combobox(settings_frame, textvariable=self.model_var, values=available_models, state="readonly", width=25)
        model_dropdown.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Language Selection
        lang_label = tk.Label(settings_frame, text="Output Language:", bg="#fff0f5", font=("Ubuntu", 9))
        lang_label.grid(row=0, column=2, sticky=tk.W, padx=(15, 5))
        
        languages = [
            ("English", "english"),
            ("বাংলা (Bengali)", "bengali"),
            ("한국어 (Korean)", "korean")
        ]
        self.language_var = tk.StringVar(value=self.notes_app.config.get('language', 'english'))
        lang_dropdown = ttk.Combobox(settings_frame, textvariable=self.language_var, 
                                     values=[lang[0] for lang in languages], state="readonly", width=20)
        lang_dropdown.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # Map display names to internal values
        self.lang_map = {lang[0]: lang[1] for lang in languages}
        self.lang_reverse_map = {lang[1]: lang[0] for lang in languages}
        lang_dropdown.set(self.lang_reverse_map.get(self.language_var.get(), "English"))
        
        # Input text area
        input_label = tk.Label(
            main_frame,
            text="Your Text:",
            font=("Ubuntu", 10, "bold"),
            bg="#fff0f5"
        )
        input_label.pack(anchor=tk.W)
        
        # Get selected text or entire note content
        try:
            selected_text = self.notes_app.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            selected_text = self.notes_app.text_widget.get("1.0", tk.END).strip()
        
        self.input_text = scrolledtext.ScrolledText(
            main_frame,
            font=("Roboto Mono", 10),
            height=6,
            wrap=tk.WORD
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        self.input_text.insert("1.0", selected_text)
        
        # Transformation options
        options_label = tk.Label(
            main_frame,
            text="Choose Transformation:",
            font=("Ubuntu", 10, "bold"),
            bg="#fff0f5"
        )
        options_label.pack(anchor=tk.W, pady=(5, 5))
        
        # Button frames (2 rows)
        button_frame1 = tk.Frame(main_frame, bg="#fff0f5")
        button_frame1.pack(fill=tk.X, pady=(0, 5))
        
        button_frame2 = tk.Frame(main_frame, bg="#fff0f5")
        button_frame2.pack(fill=tk.X, pady=(0, 10))
        
        # Row 1 buttons
        ttk.Button(
            button_frame1,
            text="Ask Question",
            command=lambda: self.transform("question")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame1,
            text="🌐 Translate",
            command=lambda: self.transform("translate")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame1,
            text="📧 Mail Format",
            command=lambda: self.transform("email")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame1,
            text="✍️ Improve Writing",
            command=lambda: self.transform("improve")
        ).pack(side=tk.LEFT, padx=2)
        
        # Row 2 buttons
        ttk.Button(
            button_frame2,
            text="🎭 Make it Poetic",
            command=lambda: self.transform("poetic")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame2,
            text="Summarize",
            command=lambda: self.transform("summarize")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame2,
            text="Explain",
            command=lambda: self.transform("explain")
        ).pack(side=tk.LEFT, padx=2)
        
        # Output text area
        output_label = tk.Label(
            main_frame,
            text="AI Result:",
            font=("Ubuntu", 10, "bold"),
            bg="#fff0f5"
        )
        output_label.pack(anchor=tk.W, pady=(5, 5))
        
        self.output_text = scrolledtext.ScrolledText(
            main_frame,
            font=("Roboto Mono", 10),
            height=6,
            wrap=tk.WORD
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Ready",
            font=("Ubuntu", 9),
            bg="#fff0f5",
            fg="#666666"
        )
        self.status_label.pack(anchor=tk.W, pady=(5, 10))
        
        # Action buttons
        action_frame = tk.Frame(main_frame, bg="#fff0f5")
        action_frame.pack()
        
        ttk.Button(
            action_frame,
            text="Insert into Note",
            command=self.insert_into_note
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="Close",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def transform(self, mode):
        """Transform text using AI"""
        input_text = self.input_text.get("1.0", tk.END).strip()
        
        if not input_text:
            messagebox.showwarning("Empty Text", "Please enter some text to transform.")
            return
        
        # Get selected language
        lang_display = self.language_var.get()
        language = self.lang_map.get(lang_display, "english")
        
        # Language instruction for AI
        lang_instructions = {
            "english": "Respond in English.",
            "bengali": "Respond in Bengali (বাংলা). Use Bengali script.",
            "korean": "Respond in Korean (한국어). Use Korean script (Hangul)."
        }
        lang_instruction = lang_instructions.get(language, "Respond in English.")
        
        # Define prompts for different modes
        prompts = {
            "question": f"{lang_instruction} Answer the following question or provide information about the following text:\n\n{input_text}",
            "translate": f"Translate the following text to {language}. If it's already in {language}, translate it to English:\n\n{input_text}",
            "email": f"{lang_instruction} Rephrase the following text as a professional, polite email. Use proper email format with greeting, body, and closing:\n\n{input_text}",
            "improve": f"{lang_instruction} Improve the following text by making it clearer, more concise, and better written. Fix any grammar or style issues:\n\n{input_text}",
            "poetic": f"{lang_instruction} Transform the following text into a poetic and creative version. Make it beautiful and artistic while preserving the core meaning:\n\n{input_text}",
            "summarize": f"{lang_instruction} Provide a concise summary of the following text, capturing the main points:\n\n{input_text}",
            "explain": f"{lang_instruction} Explain the following text in simple, easy-to-understand terms:\n\n{input_text}"
        }
        
        prompt = prompts.get(mode, input_text)
        
        # Show loading status
        self.status_label.config(text="✨ AI is thinking...")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", "Generating...")
        self.dialog.update()
        
        # Get selected model
        model = self.model_var.get()
        
        # Run AI transformation in background thread
        def run_ai():
            try:
                # Generate response using Ollama
                result = self.notes_app.generate_text_ollama(prompt, max_tokens=500, model=model)
                
                if result:
                    # Update UI in main thread
                    self.dialog.after(0, lambda r=result: self.show_result(r))
                else:
                    self.dialog.after(0, lambda: self.show_error(f"Failed to generate text. Make sure Ollama is running and {model} model is installed."))
            except Exception as e:
                error_msg = str(e)
                self.dialog.after(0, lambda msg=error_msg: self.show_error(msg))
        
        thread = threading.Thread(target=run_ai, daemon=True)
        thread.start()
    
    def show_result(self, result):
        """Display AI result"""
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", result)
        self.status_label.config(text="✅ Transformation complete!")
    
    def show_error(self, error_msg):
        """Display error message"""
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", f"Error: {error_msg}")
        self.status_label.config(text="❌ Error occurred")
        messagebox.showerror("AI Error", f"An error occurred:\n\n{error_msg}")
    
    def insert_into_note(self):
        """Insert AI result into the current note"""
        result = self.output_text.get("1.0", tk.END).strip()
        
        if not result or result == "Generating...":
            messagebox.showwarning("No Result", "No AI result to insert.")
            return
        
        # Insert at cursor position or replace selection
        try:
            # Try to replace selected text
            self.notes_app.text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.notes_app.text_widget.insert(tk.INSERT, result)
        except tk.TclError:
            # No selection, insert at cursor
            self.notes_app.text_widget.insert(tk.INSERT, "\n\n" + result)
        
        self.notes_app.status_label.config(text="✨ AI text inserted")
        self.dialog.destroy()


class FindDialog:
    def __init__(self, parent, notes_app):
        self.notes_app = notes_app
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🔍 Find and Replace")
        
        # Calculate responsive dialog size
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = min(450, int(parent_width * 0.6))
        dialog_height = min(200, int(parent_height * 0.4))
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (dialog_width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (dialog_height // 2)
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        self.create_ui()
    
    def create_ui(self):
        main_frame = tk.Frame(self.dialog, bg="#fff0f5", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Find field
        find_label = tk.Label(main_frame, text="Find:", bg="#fff0f5", font=("Ubuntu", 10))
        find_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.find_entry = ttk.Entry(main_frame, font=("Ubuntu", 10))
        self.find_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.find_entry.focus()
        
        # Replace field
        replace_label = tk.Label(main_frame, text="Replace:", bg="#fff0f5", font=("Ubuntu", 10))
        replace_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.replace_entry = ttk.Entry(main_frame, font=("Ubuntu", 10))
        self.replace_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg="#fff0f5")
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="Find Next", command=self.find_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Replace", command=self.replace_current).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Replace All", command=self.replace_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(1, weight=1)
        
        # Bind Enter key to find next
        self.find_entry.bind('<Return>', lambda e: self.find_next())
    
    def find_next(self):
        """Find next occurrence of search text"""
        search_text = self.find_entry.get()
        if not search_text:
            return
        
        # Get current cursor position
        start_pos = self.notes_app.text_widget.index(tk.INSERT)
        
        # Search from current position
        pos = self.notes_app.text_widget.search(search_text, start_pos, tk.END, nocase=True)
        
        if pos:
            # Select found text
            end_pos = f"{pos}+{len(search_text)}c"
            self.notes_app.text_widget.tag_remove(tk.SEL, "1.0", tk.END)
            self.notes_app.text_widget.tag_add(tk.SEL, pos, end_pos)
            self.notes_app.text_widget.mark_set(tk.INSERT, end_pos)
            self.notes_app.text_widget.see(pos)
            self.notes_app.status_label.config(text=f"Found: {search_text}")
        else:
            # Try from beginning
            pos = self.notes_app.text_widget.search(search_text, "1.0", tk.END, nocase=True)
            if pos:
                end_pos = f"{pos}+{len(search_text)}c"
                self.notes_app.text_widget.tag_remove(tk.SEL, "1.0", tk.END)
                self.notes_app.text_widget.tag_add(tk.SEL, pos, end_pos)
                self.notes_app.text_widget.mark_set(tk.INSERT, end_pos)
                self.notes_app.text_widget.see(pos)
                self.notes_app.status_label.config(text=f"Found: {search_text} (from start)")
            else:
                self.notes_app.status_label.config(text="Not found")
    
    def replace_current(self):
        """Replace current selection"""
        try:
            selected = self.notes_app.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            search_text = self.find_entry.get()
            replace_text = self.replace_entry.get()
            
            if selected.lower() == search_text.lower():
                self.notes_app.text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                self.notes_app.text_widget.insert(tk.INSERT, replace_text)
                self.notes_app.status_label.config(text="Replaced")
                self.find_next()
        except tk.TclError:
            self.find_next()
    
    def replace_all(self):
        """Replace all occurrences"""
        search_text = self.find_entry.get()
        replace_text = self.replace_entry.get()
        
        if not search_text:
            return
        
        content = self.notes_app.text_widget.get("1.0", tk.END)
        count = content.lower().count(search_text.lower())
        
        if count > 0:
            # Case-insensitive replace
            import re
            new_content = re.sub(re.escape(search_text), replace_text, content, flags=re.IGNORECASE)
            self.notes_app.text_widget.delete("1.0", tk.END)
            self.notes_app.text_widget.insert("1.0", new_content)
            self.notes_app.status_label.config(text=f"Replaced {count} occurrence(s)")
        else:
            self.notes_app.status_label.config(text="Not found")

class CodeBlockPreviewDialog:
    def __init__(self, parent, notes_app):
        self.notes_app = notes_app
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("👁️ Code Block Preview")
        
        # Calculate responsive dialog size (90% of parent window)
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = min(800, int(parent_width * 0.9))
        dialog_height = min(600, int(parent_height * 0.9))
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (dialog_width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (dialog_height // 2)
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Extract code blocks from current note
        self.code_blocks = self.extract_code_blocks()
        self.current_block_index = 0
        
        self.create_ui()
        
        if self.code_blocks:
            self.display_block(0)
        else:
            messagebox.showinfo("No Code Blocks", "No code blocks found in the current note.\\n\\nUse ```language\\ncode\\n``` format to create code blocks.")
            self.dialog.destroy()
    
    def extract_code_blocks(self):
        """Extract all code blocks from the current note"""
        content = self.notes_app.text_widget.get("1.0", tk.END)
        blocks = []
        
        import re
        # Match code blocks with optional language
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for lang, code in matches:
            blocks.append({
                'language': lang if lang else 'text',
                'code': code.strip()
            })
        
        return blocks
    
    def create_ui(self):
        main_frame = tk.Frame(self.dialog, bg="#fff0f5", padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and navigation
        header_frame = tk.Frame(main_frame, bg="#fff0f5")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(
            header_frame,
            text="Code Block Preview",
            font=("Ubuntu", 14, "bold"),
            bg="#fff0f5"
        )
        title_label.pack(side=tk.LEFT)
        
        # Navigation buttons
        nav_frame = tk.Frame(header_frame, bg="#fff0f5")
        nav_frame.pack(side=tk.RIGHT)
        
        self.prev_button = ttk.Button(nav_frame, text="Previous", command=self.prev_block)
        self.prev_button.pack(side=tk.LEFT, padx=2)
        
        self.block_label = tk.Label(nav_frame, text="", bg="#fff0f5", font=("Ubuntu", 10))
        self.block_label.pack(side=tk.LEFT, padx=10)
        
        self.next_button = ttk.Button(nav_frame, text="Next", command=self.next_block)
        self.next_button.pack(side=tk.LEFT, padx=2)
        
        # Language label
        self.lang_label = tk.Label(
            main_frame,
            text="Language: ",
            font=("Ubuntu", 10, "bold"),
            bg="#fff0f5"
        )
        self.lang_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Code display with syntax highlighting
        code_frame = tk.Frame(main_frame, bg="#fff0f5")
        code_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Get theme
        theme = self.notes_app.config.get('code_preview_theme', 'light')
        if theme == 'dark':
            bg_color = '#1E1E1E'
            fg_color = '#D4D4D4'
        else:
            bg_color = '#F5F5F5'
            fg_color = '#000000'
        
        self.code_text = scrolledtext.ScrolledText(
            code_frame,
            font=("Roboto Mono", 11),
            wrap=tk.NONE,
            bg=bg_color,
            fg=fg_color,
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#cccccc",
            padx=10,
            pady=10
        )
        self.code_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure syntax highlighting tags
        self.setup_syntax_tags()
        
        # Action buttons
        button_frame = tk.Frame(main_frame, bg="#fff0f5")
        button_frame.pack()
        
        ttk.Button(
            button_frame,
            text="Copy to Clipboard",
            command=self.copy_to_clipboard
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def setup_syntax_tags(self):
        """Setup tags for syntax highlighting"""
        theme = self.notes_app.config.get('code_preview_theme', 'light')
        
        if theme == 'dark':
            # Dark theme colors
            self.code_text.tag_config('keyword', foreground='#569CD6')
            self.code_text.tag_config('string', foreground='#CE9178')
            self.code_text.tag_config('comment', foreground='#6A9955')
            self.code_text.tag_config('function', foreground='#DCDCAA')
            self.code_text.tag_config('number', foreground='#B5CEA8')
        else:
            # Light theme colors
            self.code_text.tag_config('keyword', foreground='#0000FF')
            self.code_text.tag_config('string', foreground='#A31515')
            self.code_text.tag_config('comment', foreground='#008000')
            self.code_text.tag_config('function', foreground='#795E26')
            self.code_text.tag_config('number', foreground='#098658')
    
    def apply_syntax_highlighting(self, code, language):
        """Apply basic syntax highlighting"""
        import re
        
        # Common keywords for different languages
        keywords = {
            'python': ['def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'return', 'try', 'except', 'with', 'as', 'in', 'is', 'and', 'or', 'not', 'None', 'True', 'False'],
            'javascript': ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return', 'class', 'import', 'export', 'from', 'async', 'await', 'true', 'false', 'null'],
            'java': ['public', 'private', 'class', 'static', 'void', 'int', 'String', 'if', 'else', 'for', 'while', 'return', 'new', 'true', 'false', 'null'],
            'c': ['int', 'char', 'float', 'double', 'if', 'else', 'for', 'while', 'return', 'void', 'struct', 'typedef', 'include'],
            'cpp': ['int', 'char', 'float', 'double', 'if', 'else', 'for', 'while', 'return', 'void', 'class', 'public', 'private', 'namespace', 'using'],
        }
        
        lang_keywords = keywords.get(language.lower(), keywords.get('python', []))
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            line_start = f"{i+1}.0"
            
            # Highlight comments
            if language.lower() in ['python', 'bash', 'shell']:
                comment_match = re.search(r'#.*$', line)
                if comment_match:
                    start = f"{i+1}.{comment_match.start()}"
                    end = f"{i+1}.{comment_match.end()}"
                    self.code_text.tag_add('comment', start, end)
            elif language.lower() in ['javascript', 'java', 'c', 'cpp']:
                comment_match = re.search(r'//.*$', line)
                if comment_match:
                    start = f"{i+1}.{comment_match.start()}"
                    end = f"{i+1}.{comment_match.end()}"
                    self.code_text.tag_add('comment', start, end)
            
            # Highlight strings
            for string_match in re.finditer(r'["\'].*?["\']', line):
                start = f"{i+1}.{string_match.start()}"
                end = f"{i+1}.{string_match.end()}"
                self.code_text.tag_add('string', start, end)
            
            # Highlight numbers
            for num_match in re.finditer(r'\b\d+\.?\d*\b', line):
                start = f"{i+1}.{num_match.start()}"
                end = f"{i+1}.{num_match.end()}"
                self.code_text.tag_add('number', start, end)
            
            # Highlight keywords
            for keyword in lang_keywords:
                for match in re.finditer(r'\b' + re.escape(keyword) + r'\b', line):
                    start = f"{i+1}.{match.start()}"
                    end = f"{i+1}.{match.end()}"
                    self.code_text.tag_add('keyword', start, end)
    
    def display_block(self, index):
        """Display a specific code block"""
        if 0 <= index < len(self.code_blocks):
            self.current_block_index = index
            block = self.code_blocks[index]
            
            # Update language label
            self.lang_label.config(text=f"Language: {block['language']}")
            
            # Update navigation label
            self.block_label.config(text=f"Block {index + 1} of {len(self.code_blocks)}")
            
            # Update navigation buttons
            self.prev_button.config(state=tk.NORMAL if index > 0 else tk.DISABLED)
            self.next_button.config(state=tk.NORMAL if index < len(self.code_blocks) - 1 else tk.DISABLED)
            
            # Display code
            self.code_text.delete("1.0", tk.END)
            self.code_text.insert("1.0", block['code'])
            
            # Apply syntax highlighting
            self.apply_syntax_highlighting(block['code'], block['language'])
    
    def prev_block(self):
        """Show previous code block"""
        if self.current_block_index > 0:
            self.display_block(self.current_block_index - 1)
    
    def next_block(self):
        """Show next code block"""
        if self.current_block_index < len(self.code_blocks) - 1:
            self.display_block(self.current_block_index + 1)
    
    def copy_to_clipboard(self):
        """Copy current code block to clipboard"""
        if self.code_blocks:
            code = self.code_blocks[self.current_block_index]['code']
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(code)
            messagebox.showinfo("Copied", "Code copied to clipboard!")

class SettingsDialog:
    def __init__(self, parent, notes_app):
        self.notes_app = notes_app
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("⚙️ Settings")
        
        # Calculate responsive dialog size (70% of parent window)
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = min(600, int(parent_width * 0.7))
        dialog_height = min(550, int(parent_height * 0.8))
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (dialog_width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (dialog_height // 2)
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        self.create_ui()
    
    def create_ui(self):
        # Main container for the entire dialog
        container = tk.Frame(self.dialog, bg="#fff0f5")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for title and scrollable content
        main_frame = tk.Frame(container, bg="#fff0f5", padx=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Customization Settings",
            font=("Ubuntu", 14, "bold"),
            bg="#fff0f5"
        )
        title_label.pack(pady=(0, 15))
        
        # Create scrollable frame for settings
        canvas = tk.Canvas(main_frame, bg="#fff0f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#fff0f5")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Theme Presets
        theme_frame = tk.LabelFrame(scrollable_frame, text="🎨 Theme Presets", bg="#fff0f5", font=("Ubuntu", 11, "bold"), padx=10, pady=10)
        theme_frame.pack(fill=tk.X, pady=10)
        
        themes = [
            ("Pink (Default)", "pink"),
            ("Dark Mode", "dark"),
            ("Light Mode", "light"),
            ("Ocean Blue", "ocean"),
            ("Forest Green", "forest")
        ]
        
        for theme_name, theme_id in themes:
            btn = ttk.Button(
                theme_frame,
                text=theme_name,
                command=lambda t=theme_id: self.apply_theme(t)
            )
            btn.pack(side=tk.LEFT, padx=5)
        
        # Font Settings
        font_frame = tk.LabelFrame(scrollable_frame, text="🔤 Font Settings", bg="#fff0f5", font=("Ubuntu", 11, "bold"), padx=10, pady=10)
        font_frame.pack(fill=tk.X, pady=10)
        
        # Font Family
        family_label = tk.Label(font_frame, text="Font Family:", font=("Ubuntu", 10), bg="#fff0f5")
        family_label.pack(anchor=tk.W)
        
        self.font_family_var = tk.StringVar(value=self.notes_app.config['font_family'])
        font_families = ["Roboto Mono", "Ubuntu Mono", "Courier New", "Monospace", "Arial", "Times New Roman"]
        font_dropdown = ttk.Combobox(font_frame, textvariable=self.font_family_var, values=font_families, state="readonly")
        font_dropdown.pack(fill=tk.X, pady=5)
        
        # Font Size
        size_label = tk.Label(
            font_frame,
            text=f"Font Size: {self.notes_app.config['font_size']}",
            font=("Ubuntu", 10),
            bg="#fff0f5"
        )
        size_label.pack(anchor=tk.W, pady=(10, 0))
        
        self.font_size_var = tk.IntVar(value=self.notes_app.config['font_size'])
        font_slider = tk.Scale(
            font_frame,
            from_=8,
            to=36,
            orient=tk.HORIZONTAL,
            variable=self.font_size_var,
            bg="#fff0f5",
            command=lambda v: size_label.config(text=f"Font Size: {v}")
        )
        font_slider.pack(fill=tk.X, pady=5)
        
        # Color Settings
        color_frame = tk.LabelFrame(scrollable_frame, text="🎨 Color Settings", bg="#fff0f5", font=("Ubuntu", 11, "bold"), padx=10, pady=10)
        color_frame.pack(fill=tk.X, pady=10)
        
        # Text Color
        text_color_label = tk.Label(color_frame, text="Text Color:", font=("Ubuntu", 10), bg="#fff0f5")
        text_color_label.pack(anchor=tk.W)
        
        self.text_color_var = tk.StringVar(value=self.notes_app.config['text_color'])
        text_colors = [("Black", "#000000"), ("Blue", "#0000FF"), ("Green", "#008000"), ("Red", "#FF0000"), ("Purple", "#800080"), ("White", "#FFFFFF")]
        
        text_color_buttons = tk.Frame(color_frame, bg="#fff0f5")
        text_color_buttons.pack(fill=tk.X, pady=5)
        
        for color_name, color_code in text_colors:
            btn = tk.Button(
                text_color_buttons,
                text=color_name,
                bg=color_code,
                fg="white" if color_code not in ["#FFFFFF", "#FFFF00"] else "black",
                command=lambda c=color_code: self.text_color_var.set(c),
                width=8
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # Background Color
        bg_color_label = tk.Label(color_frame, text="Editor Background:", font=("Ubuntu", 10), bg="#fff0f5")
        bg_color_label.pack(anchor=tk.W, pady=(10, 0))
        
        self.bg_color_var = tk.StringVar(value=self.notes_app.config['bg_color'])
        bg_colors = [("White", "#FFFFFF"), ("Light Gray", "#F0F0F0"), ("Cream", "#FFFDD0"), ("Light Blue", "#E6F2FF"), ("Light Green", "#E8F5E9"), ("Black", "#000000")]
        
        bg_color_buttons = tk.Frame(color_frame, bg="#fff0f5")
        bg_color_buttons.pack(fill=tk.X, pady=5)
        
        for color_name, color_code in bg_colors:
            btn = tk.Button(
                bg_color_buttons,
                text=color_name,
                bg=color_code,
                fg="black" if color_code != "#000000" else "white",
                command=lambda c=color_code: self.bg_color_var.set(c),
                width=10
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # AI Settings
        ai_frame = tk.LabelFrame(scrollable_frame, text="🤖 AI Settings", bg="#fff0f5", font=("Ubuntu", 11, "bold"), padx=10, pady=10)
        ai_frame.pack(fill=tk.X, pady=10)
        
        # Language Preference
        lang_label = tk.Label(ai_frame, text="Preferred Language:", font=("Ubuntu", 10), bg="#fff0f5")
        lang_label.pack(anchor=tk.W)
        
        languages = [
            ("English", "english"),
            ("বাংলা (Bengali)", "bengali"),
            ("한국어 (Korean)", "korean")
        ]
        self.language_var = tk.StringVar(value=self.notes_app.config.get('language', 'english'))
        lang_display_names = [lang[0] for lang in languages]
        lang_map = {lang[1]: lang[0] for lang in languages}
        
        lang_dropdown = ttk.Combobox(ai_frame, textvariable=self.language_var, values=lang_display_names, state="readonly")
        lang_dropdown.set(lang_map.get(self.notes_app.config.get('language', 'english'), "English"))
        lang_dropdown.pack(fill=tk.X, pady=5)
        
        # Store mapping for later use
        self.lang_reverse_map = {lang[0]: lang[1] for lang in languages}
        
        # Default AI Model
        model_label = tk.Label(ai_frame, text="Default AI Model:", font=("Ubuntu", 10), bg="#fff0f5")
        model_label.pack(anchor=tk.W, pady=(10, 0))
        
        available_models = self.notes_app.get_available_models()
        self.ai_model_var = tk.StringVar(value=self.notes_app.config.get('ai_model', 'qwen2.5:0.5b'))
        model_dropdown = ttk.Combobox(ai_frame, textvariable=self.ai_model_var, values=available_models, state="readonly")
        model_dropdown.pack(fill=tk.X, pady=5)
        
        # Code Preview Theme
        preview_label = tk.Label(ai_frame, text="Code Preview Theme:", font=("Ubuntu", 10), bg="#fff0f5")
        preview_label.pack(anchor=tk.W, pady=(10, 0))
        
        self.code_theme_var = tk.StringVar(value=self.notes_app.config.get('code_preview_theme', 'light'))
        theme_dropdown = ttk.Combobox(ai_frame, textvariable=self.code_theme_var, values=["light", "dark"], state="readonly")
        theme_dropdown.pack(fill=tk.X, pady=5)
        
        # Window Settings
        window_frame = tk.LabelFrame(scrollable_frame, text="📐 Window Settings", bg="#fff0f5", font=("Ubuntu", 11, "bold"), padx=10, pady=10)
        window_frame.pack(fill=tk.X, pady=10)
        
        # Sidebar Width
        sidebar_label = tk.Label(
            window_frame,
            text=f"Sidebar Width: {self.notes_app.config['sidebar_width']}px",
            font=("Ubuntu", 10),
            bg="#fff0f5"
        )
        sidebar_label.pack(anchor=tk.W)
        
        self.sidebar_width_var = tk.IntVar(value=self.notes_app.config['sidebar_width'])
        sidebar_slider = tk.Scale(
            window_frame,
            from_=150,
            to=400,
            orient=tk.HORIZONTAL,
            variable=self.sidebar_width_var,
            bg="#fff0f5",
            command=lambda v: sidebar_label.config(text=f"Sidebar Width: {v}px")
        )
        sidebar_slider.pack(fill=tk.X, pady=5)
        
        # Window Scale
        scale_label = tk.Label(
            window_frame,
            text=f"Window Scale: {self.notes_app.config['window_scale']:.1f}x",
            font=("Ubuntu", 10),
            bg="#fff0f5"
        )
        scale_label.pack(anchor=tk.W, pady=(10, 0))
        
        self.scale_var = tk.DoubleVar(value=self.notes_app.config['window_scale'])
        scale_slider = tk.Scale(
            window_frame,
            from_=0.8,
            to=2.5,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.scale_var,
            bg="#fff0f5",
            command=lambda v: scale_label.config(text=f"Window Scale: {float(v):.1f}x")
        )
        scale_slider.pack(fill=tk.X, pady=5)
        
        # Info label
        info_label = tk.Label(
            scrollable_frame,
            text="💡 Tip: Some settings require app restart to take full effect",
            font=("Ubuntu", 9),
            bg="#fff0f5",
            fg="#666666"
        )
        info_label.pack(pady=10)
        
        # Bottom frame for action buttons (outside scrollable area)
        bottom_frame = tk.Frame(container, bg="#fff0f5", padx=20, pady=10)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Separator line
        separator = ttk.Separator(bottom_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 10))
        
        # Action buttons
        button_frame = tk.Frame(bottom_frame, bg="#fff0f5")
        button_frame.pack()
        
        apply_button = ttk.Button(
            button_frame,
            text="Apply Settings",
            command=self.apply_settings
        )
        apply_button.pack(side=tk.LEFT, padx=5)
        
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
    
    def apply_theme(self, theme_id):
        """Apply a preset theme"""
        themes = {
            "pink": {
                'text_color': '#000000',
                'bg_color': '#FFFFFF',
                'sidebar_bg': '#ffe8f0',
                'editor_bg': '#fff0f5'
            },
            "dark": {
                'text_color': '#FFFFFF',
                'bg_color': '#1E1E1E',
                'sidebar_bg': '#252525',
                'editor_bg': '#2D2D2D'
            },
            "light": {
                'text_color': '#000000',
                'bg_color': '#FFFFFF',
                'sidebar_bg': '#F5F5F5',
                'editor_bg': '#FAFAFA'
            },
            "ocean": {
                'text_color': '#003366',
                'bg_color': '#E6F2FF',
                'sidebar_bg': '#CCE5FF',
                'editor_bg': '#E6F2FF'
            },
            "forest": {
                'text_color': '#1B5E20',
                'bg_color': '#F1F8E9',
                'sidebar_bg': '#DCEDC8',
                'editor_bg': '#F1F8E9'
            }
        }
        
        if theme_id in themes:
            theme = themes[theme_id]
            self.text_color_var.set(theme['text_color'])
            self.bg_color_var.set(theme['bg_color'])
            messagebox.showinfo("Theme Applied", f"'{theme_id.title()}' theme colors set! Click 'Apply Settings' to save.")
    
    def apply_settings(self):
        """Apply settings and update the app"""
        # Update config
        self.notes_app.config['font_size'] = self.font_size_var.get()
        self.notes_app.config['font_family'] = self.font_family_var.get()
        self.notes_app.config['text_color'] = self.text_color_var.get()
        self.notes_app.config['bg_color'] = self.bg_color_var.get()
        self.notes_app.config['sidebar_width'] = self.sidebar_width_var.get()
        self.notes_app.config['window_scale'] = self.scale_var.get()
        
        # Update AI settings
        lang_display = self.language_var.get()
        self.notes_app.config['language'] = self.lang_reverse_map.get(lang_display, 'english')
        self.notes_app.config['ai_model'] = self.ai_model_var.get()
        self.notes_app.config['code_preview_theme'] = self.code_theme_var.get()
        
        # Save config
        self.notes_app.save_config()
        
        # Apply font and color changes immediately
        self.notes_app.text_widget.config(
            font=(self.notes_app.config['font_family'], self.notes_app.config['font_size']),
            fg=self.notes_app.config['text_color'],
            bg=self.notes_app.config['bg_color'],
            insertbackground=self.notes_app.config['text_color']
        )
        
        # Show success message
        messagebox.showinfo(
            "Settings Applied",
            "✓ Settings saved successfully!\n\n" +
            "Font, colors, and AI settings applied immediately.\n" +
            "Window size/sidebar changes require restart."
        )
        
        self.dialog.destroy()

def main():
    root = tk.Tk()
    app = NotesApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
