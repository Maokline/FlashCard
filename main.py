#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hauptanwendung für das Flashcard-Projekt.
Startet die FlashcardApp und integriert alle Module.
"""

import matplotlib
matplotlib.use('TkAgg') 
matplotlib.interactive(False)
import os
import sys
import json
import csv
import shutil
import random
import datetime
import winreg
import logging
from logging.handlers import RotatingFileHandler
import enum
import platformdirs
import numpy as np
import customtkinter as ctk
import tkinter as tk
from tkcalendar import Calendar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from typing import Callable, List, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from tkinter import ttk, messagebox, colorchooser, filedialog
from tkinter import font as tkfont
from collections import defaultdict
from scipy.stats import pearsonr
from leitner_system import LeitnerSystem, LeitnerCard # type: ignore
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageTk


import seaborn as sns
import gc
import mplcursors
from data_manager import DataManager, ThemeManager, StatisticsManager, Flashcard, get_persistent_path


from custom_widgets import ModernButton, ModernCombobox
from export_import import export_flashcards_to_csv, import_flashcards_from_csv
from calendar_ui import WeeklyCalendarView
from calendar_ui_modern import PlannerSelectionView, ModernWeeklyCalendarView

sns.set_style("whitegrid")
sns.set_palette("husl")

APP_NAME = "FlashCards"
APP_DISPLAY_NAME = "FlashCards"

# ------------------------------------------------------------------------------
# LOGGING-KONFIGURATION
# ------------------------------------------------------------------------------
# Bereits in setup_logging definiert

# ------------------------------------------------------------------------------
# SETUP AND INITIALIZATION FUNCTIONS
# ------------------------------------------------------------------------------


def setup_logging():
    """Konfiguriert das Logging-System."""
    # Verwende get_persistent_path, um den Pfad im Benutzerverzeichnis zu erhalten
    log_file = get_persistent_path("flashcard_app.log")
    
    # Stelle sicher, dass das Log-Verzeichnis existiert
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Konfiguriere den RotatingFileHandler
    handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
    
    # Konfiguriere das Logging
    logging.basicConfig(
        level=logging.DEBUG, # <-- HIER ÄNDERN!
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler('app.log', maxBytes=1024*1024*5, backupCount=3, encoding='utf-8'),
            logging.StreamHandler() # Optional: Auch in Konsole ausgeben
        ]
    )
    logging.info("Logging gestartet.")
def get_app_data_dir() -> str:
    """
    Zentrale Funktion zur Bestimmung des Anwendungsdatenverzeichnisses.
    Verhindert doppelte Verzeichnisstrukturen.
    """
    # Holen nur das Basisverzeichnis von platformdirs
    base_dir = Path(platformdirs.user_data_dir()).parent
    # Fügen APP_NAME nur einmal hinzu
    return str(base_dir / APP_NAME)

def resource_path(relative_path: str) -> str:
    """
    Nur noch für Icons/Bilder/Fonts nötig.
    Holt den absoluten Pfad zur Ressource, egal ob als .py oder in EXE.
    """
    try:
        base_path = Path(sys._MEIPASS)  # PyInstaller: _MEIPASS existiert
    except AttributeError:
        base_path = Path(__file__).parent.resolve()  # Normaler Dev-Modus
    return str(base_path / relative_path)

def ensure_initial_files(data_manager: DataManager):
    """
    Stellt sicher, dass die notwendigen JSON-Dateien existieren.
    Falls nicht, werden sie initialisiert oder aus dem Bundle (_MEIPASS) kopiert.
    """
 # Importiere hier, falls es noch nicht importiert ist

    # Liste der benötigten Dateien mit Standardinhalten oder aus dem Bundle
    required_files = {
        'flashcards.json': [],
        'categories.json': {},
        'stats.json': [],
        'themes.json': {
            "light": {
                "default_bg": "#ffffff",
                "text_bg_color": "#ffffff",
                "text_fg_color": "#000000",
                "button_bg_color": "#4a90e2",
                "button_fg_color": "#ffffff",
                "font_family": "Segoe UI",
                "font_size": 12
            },
            "dark": {
                "default_bg": "#2c3e50",
                "text_bg_color": "#34495e",
                "text_fg_color": "#ecf0f1",
                "button_bg_color": "#2980b9",
                "button_fg_color": "#ecf0f1",
                "font_family": "Segoe UI",
                "font_size": 12
            },
            "system": {
                "default_bg": "#ffffff",
                "text_bg_color": "#ffffff",
                "text_fg_color": "#000000",
                "button_bg_color": "#4a90e2",
                "button_fg_color": "#ffffff",
                "font_family": "Segoe UI",
                "font_size": 12
            }
        }
    }

    files_created = False
    for filename, default_content in required_files.items():
        # Sonderfall für 'themes.json'
        if filename == "themes.json":
            # Verwende 'theme_file' statt 'themes_file'
            file_path = Path(data_manager.theme_file)
        else:
            # Standardfall: <dateiname ohne .json>_file
            file_path = Path(getattr(data_manager, f"{filename.split('.')[0]}_file"))
        
        logging.info(f"Überprüfe Datei: {file_path}")
        
        if not file_path.exists():
            try:
                if getattr(sys, 'frozen', False):
                    # Wenn die App gebündelt ist, kopiere die Datei aus dem Bundle
                    bundle_path = Path(sys._MEIPASS) / filename
                    if bundle_path.exists():
                        shutil.copy(str(bundle_path), file_path)
                        logging.info(f"Kopiert {filename} aus dem Bundle nach {file_path}")
                    else:
                        # Falls die Datei nicht im Bundle ist, initialisiere mit Standardinhalt
                        with file_path.open('w', encoding='utf-8') as f:
                            json.dump(default_content, f, indent=4, ensure_ascii=False)
                        logging.info(f"Initialisiere leere Datei: {file_path}")
                else:
                    # Im Entwicklungsmodus initialisiere mit Standardinhalt
                    with file_path.open('w', encoding='utf-8') as f:
                        json.dump(default_content, f, indent=4, ensure_ascii=False)
                    logging.info(f"Initialisiere leere Datei: {file_path}")
                files_created = True
            except Exception as e:
                logging.error(f"Fehler beim Erstellen der Datei {file_path}: {e}")
        else:
            # Überprüfen, ob die Datei leer ist (leeres dict oder leere liste)
            try:
                with file_path.open('r', encoding='utf-8') as f:
                    content = json.load(f)
                if not content:
                    # Inhalt ist leer
                    if getattr(sys, 'frozen', False):
                        # Wenn gebündelt, versuche aus dem Bundle zu kopieren
                        bundle_path = Path(sys._MEIPASS) / filename
                        if bundle_path.exists():
                            shutil.copy(str(bundle_path), file_path)
                            logging.info(f"Kopiert {filename} aus dem Bundle nach {file_path}")
                        else:
                            # Falls nicht im Bundle, initialisiere mit Standardinhalt
                            with file_path.open('w', encoding='utf-8') as f:
                                json.dump(default_content, f, indent=4, ensure_ascii=False)
                            logging.info(f"Initialisiere leere Datei: {file_path}")
                    else:
                        # Im Entwicklungsmodus initialisiere mit Standardinhalt
                        with file_path.open('w', encoding='utf-8') as f:
                            json.dump(default_content, f, indent=4, ensure_ascii=False)
                        logging.info(f"Initialisiere leere Datei: {file_path}")
                    files_created = True
            except json.JSONDecodeError:
                # Ungültiges JSON, überschreibe mit initial_content
                try:
                    if getattr(sys, 'frozen', False):
                        # Wenn gebündelt, kopiere aus dem Bundle
                        bundle_path = Path(sys._MEIPASS) / filename
                        if bundle_path.exists():
                            shutil.copy(str(bundle_path), file_path)
                            logging.info(f"Kopiert {filename} aus dem Bundle nach {file_path}")
                        else:
                            # Initialisiere mit Standardinhalt
                            with file_path.open('w', encoding='utf-8') as f:
                                json.dump(default_content, f, indent=4, ensure_ascii=False)
                            logging.info(f"Initialisiere leere Datei: {file_path}")
                    else:
                        # Im Entwicklungsmodus initialisiere mit Standardinhalt
                        with file_path.open('w', encoding='utf-8') as f:
                            json.dump(default_content, f, indent=4, ensure_ascii=False)
                        logging.info(f"Initialisiere leere Datei: {file_path}")
                    files_created = True
                except Exception as e:
                    logging.error(f"Fehler beim Initialisieren der Datei {file_path}: {e}")


    # Initialisiere Flashcards mit Beispielkarten, falls leer
    try:
        flashcards_file = Path(data_manager.flashcards_file)
        with flashcards_file.open('r', encoding='utf-8') as f:
            flashcards_content = json.load(f)
        if not flashcards_content:
            logging.info("Flashcards-Datei ist leer. Füge Standard-Flashcards hinzu.")
            default_flashcards = [
                Flashcard(
                    question="Was ist die Hauptstadt von Frankreich?",
                    answer="Paris",
                    category="Geographie",
                    subcategory="Hauptstädte",
                    tags=["Europa", "Politik"],
                    interval=1,
                    ease_factor=2.5,
                    repetitions=0,
                    last_reviewed=datetime.date.today().isoformat(),
                    next_review=(datetime.date.today() + datetime.timedelta(days=1)).isoformat(),
                    consecutive_correct=0,
                    success_count=0
                ),
                Flashcard(
                    question="Was ist die chemische Formel von Wasser?",
                    answer="H₂O",
                    category="Chemie",
                    subcategory="Grundlagen",
                    tags=["Wissenschaft", "Chemie"],
                    interval=1,
                    ease_factor=2.5,
                    repetitions=0,
                    last_reviewed=datetime.date.today().isoformat(),
                    next_review=(datetime.date.today() + datetime.timedelta(days=1)).isoformat(),
                    consecutive_correct=0,
                    success_count=0
                )
            ]
            try:
                with flashcards_file.open('w', encoding='utf-8') as f:
                    json.dump([fc.to_dict() for fc in default_flashcards], f, indent=4, ensure_ascii=False)
                data_manager.flashcards = default_flashcards
                logging.info(f"Standard-Flashcards hinzugefügt in {flashcards_file}.")
                files_created = True
            except Exception as e:
                logging.error(f"Fehler beim Hinzufügen der Standard-Flashcards: {e}")
    except json.JSONDecodeError:
        # Überschreibe ungültiges JSON
        logging.error(f"Ungültiges JSON in {flashcards_file}. Überschreibe mit Standard-Flashcards.")
        default_flashcards = [
            Flashcard(
                question="Was ist die Hauptstadt von Frankreich?",
                answer="Paris",
                category="Geographie",
                subcategory="Hauptstädte",
                tags=["Europa", "Politik"],
                interval=1,
                ease_factor=2.5,
                repetitions=0,
                last_reviewed=datetime.date.today().isoformat(),
                next_review=(datetime.date.today() + datetime.timedelta(days=1)).isoformat(),
                consecutive_correct=0,
                success_count=0
            ),
            Flashcard(
                question="Was ist die chemische Formel von Wasser?",
                answer="HÃ¢â€šâ€šO",
                category="Chemie",
                subcategory="Grundlagen",
                tags=["Wissenschaft", "Chemie"],
                interval=1,
                ease_factor=2.5,
                repetitions=0,
                last_reviewed=datetime.date.today().isoformat(),
                next_review=(datetime.date.today() + datetime.timedelta(days=1)).isoformat(),
                consecutive_correct=0,
                success_count=0
            )
        ]
        try:
            with flashcards_file.open('w', encoding='utf-8') as f:
                json.dump([fc.to_dict() for fc in default_flashcards], f, indent=4, ensure_ascii=False)
            data_manager.flashcards = default_flashcards
            logging.info(f"Standard-Flashcards hinzugefügt in {flashcards_file}.")
            files_created = True
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen der Standard-Flashcards: {e}")

    # Initialisiere Kategorien mit Standarddaten, falls leer
    try:
        categories_file = Path(data_manager.categories_file)
        with categories_file.open('r', encoding='utf-8') as f:
            categories_content = json.load(f)
        if not categories_content:
            logging.info("Kategorien-Datei ist leer. Füge Standard-Kategorien hinzu.")
            default_categories = {
                "geographie": {
                    "hauptstädte": [],
                    "länder": []
                },
                "chemie": {
                    "grundlagen": [],
                    "organische chemie": []
                }
            }
            try:
                with categories_file.open('w', encoding='utf-8') as f:
                    json.dump(default_categories, f, indent=4, ensure_ascii=False)
                data_manager.categories = defaultdict(dict, default_categories)
                logging.info(f"Standard-Kategorien hinzugefügt in {categories_file}.")
                files_created = True
            except Exception as e:
                logging.error(f"Fehler beim Hinzufügen der Standard-Kategorien: {e}")
    except json.JSONDecodeError:
        # Überschreibe ungültiges JSON
        logging.error(f"Ungültiges JSON in {categories_file}. Überschreibe mit Standard-Kategorien.")
        default_categories = {
            "geographie": {
                "hauptstädte": [],
                "länder": []
            },
            "chemie": {
                "grundlagen": [],
                "organische chemie": []
            }
        }
        try:
            with categories_file.open('w', encoding='utf-8') as f:
                json.dump(default_categories, f, indent=4, ensure_ascii=False)
            data_manager.categories = defaultdict(dict, default_categories)
            logging.info(f"Standard-Kategorien hinzugefügt in {categories_file}.")
            files_created = True
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen der Standard-Kategorien: {e}")

    # Wenn neue Dateien erstellt wurden, erstelle ein initiales Backup
    if files_created:
        backup_dir = Path(data_manager.backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        logging.info("Backup-Verzeichnis überprüft/erstellt")
        
        timestamp = datetime.datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
        backup_path = backup_dir / f'initial_backup_{timestamp}'
        backup_path.mkdir(parents=True, exist_ok=True)
        
        for filename in required_files.keys():
            # Korrigierte Attributnamen-Behandlung
            if filename == "themes.json":
                src = Path(data_manager.theme_file)
            else:
                src = Path(getattr(data_manager, f"{filename.split('.')[0]}_file"))
            
            dst = backup_path / filename
            if src.exists():
                try:
                    shutil.copy2(src, dst)
                    logging.info(f"Datei {filename} erfolgreich migriert nach {dst}")
                except Exception as e:
                    logging.error(f"Fehler bei der Migration von {filename}: {e}")
        
        logging.info("Initiales Backup erstellt")


def migrate_existing_data():
    """Migriert bestehende Daten aus dem alten in das neue Verzeichnis."""
    base_dir = Path(platformdirs.user_data_dir()).parent
    old_dirs = [
        base_dir / APP_NAME / APP_NAME,
        base_dir / APP_NAME / APP_NAME / APP_NAME
    ]
    new_dir = Path(get_app_data_dir())
    
    for old_dir in old_dirs:
        logging.info(f"Überprüfe altes Verzeichnis: {old_dir}")
        
        if old_dir.exists() and old_dir != new_dir:
            logging.info(f"Starte Migration von {old_dir} nach {new_dir}")
            
            files_to_migrate = [
                'flashcards.json', 
                'categories.json', 
                'stats.json', 
                'themes.json'
            ]
            
            new_dir.mkdir(parents=True, exist_ok=True)
            
            for file in files_to_migrate:
                old_path = old_dir / file
                new_path = new_dir / file
                
                if old_path.exists() and not new_path.exists():
                    try:
                        shutil.copy2(old_path, new_path)
                        logging.info(f"Datei {file} erfolgreich migriert")
                    except Exception as e:
                        logging.error(f"Fehler bei der Migration von {file}: {e}")
            
            # Migriere Backup-Verzeichnis
            old_backup = old_dir / 'backup'
            new_backup = new_dir / 'backup'
            if old_backup.exists() and not new_backup.exists():
                try:
                    shutil.copytree(old_backup, new_backup)
                    logging.info("Backup-Verzeichnis erfolgreich migriert")
                except Exception as e:
                    logging.error(f"Fehler bei der Migration des Backup-Verzeichnisses: {e}")
            
            # Lösche altes Verzeichnis
            try:
                shutil.rmtree(old_dir)
                logging.info(f"Altes Verzeichnis {old_dir} erfolgreich gelöscht")
            except Exception as e:
                logging.error(f"Fehler beim Löschen des alten Verzeichnisses {old_dir}: {e}")
        else:
            logging.info(f"Keine Migration erforderlich für: {old_dir}")

# ------------------------------------------------------------------------------
# KONFIGURATION (Konstanten und Einstellungen)
# ------------------------------------------------------------------------------
DEFAULT_BG_COLOR = "#ffffff"  # Standard-Hintergrundfarbe (global)
SRS_SETTINGS = {
    "initial_interval": 1,
    "ease_factor": 2.5
}
SESSION_LIMIT = 5
COLORS = {
    "hover": "#B8D4E8",  # Hellere Hover-Farbe passend zum neuen Design
    "active": "#4A90E2",  # Moderne blaue Aktiv-Farbe
    "active_secondary": "#5CA0F2",  # Hellere aktive Farbe für Secondary Buttons
    "active_danger": "#E57373"  # Hellere aktive Farbe für Danger Buttons
}
BUTTON_STYLES = {
    'primary': {
        'bg': '#4A90E2',  # Modernes Blau
        'fg': '#ffffff',
        'font': ("Segoe UI", 10, "bold"),
        'padx': 10,
        'pady': 5,
        'borderwidth': 0
    },
    'secondary': {
        'bg': '#6EB0FF',  # Helleres Blau für Secondary Buttons
        'fg': '#ffffff',
        'font': ("Segoe UI", 10),
        'padx': 10,
        'pady': 5,
        'borderwidth': 0
    },
    'danger': {
        'bg': '#EF5350',  # Helleres Rot
        'fg': '#ffffff',
        'font': ("Segoe UI", 10, "bold"),
        'padx': 10,
        'pady': 5,
        'borderwidth': 0  # Borderwidth explizit definieren
    }
}

@dataclass
class AppearanceSettings:
    text_bg_color: str = "#ffffff"
    text_fg_color: str = "#000000"
    button_bg_color: str = "#4a90e2"
    button_fg_color: str = "#ffffff"
    text_opacity: float = 1.0
    font_family: str = "Segoe UI"
    font_size: int = 12
    track_learning_time: bool = True

class ButtonStyle(enum.Enum):
    PRIMARY = 'Primary.TButton'
    SECONDARY = 'Secondary.TButton'
    DANGER = 'Danger.TButton'
    ACTIVE_PRIMARY = 'Active.Primary.TButton'
    ACTIVE_SECONDARY = 'Active.Secondary.TButton'
    ACTIVE_DANGER = 'Active.Danger.TButton'

SRS_SETTINGS = {
    "initial_interval": 1,
    "ease_factor": 2.5
}
SESSION_LIMIT = 5
DEFAULT_BG_COLOR = "#ffffff"
COLORS = {
    "hover": "#B8D4E8",  # Hellere Hover-Farbe passend zum neuen Design
    "active": "#4A90E2",  # Moderne blaue Aktiv-Farbe
    "active_secondary": "#5CA0F2",  # Hellere aktive Farbe für Secondary Buttons
    "active_danger": "#E57373"  # Hellere aktive Farbe für Danger Buttons
}
BUTTON_STYLES = {
    'primary': {'bg': '#4A90E2', 'fg': '#ffffff', 'font': ("Segoe UI", 10, "bold"), 'padx': 10, 'pady': 5, 'borderwidth': 0},
    'secondary': {'bg': '#6EB0FF', 'fg': '#ffffff', 'font': ("Segoe UI", 10), 'padx': 10, 'pady': 5, 'borderwidth': 0},
    'danger': {'bg': '#EF5350', 'fg': '#ffffff', 'font': ("Segoe UI", 10, "bold"), 'padx': 10, 'pady': 5, 'borderwidth': 0}
}

# ------------------------------------------------------------------------------
# HAUPT-ANWENDUNG (FlashcardApp)
# ------------------------------------------------------------------------------
class FlashcardApp:
    """
    Hauptklasse der Flashcard-Anwendung.
    Implementiert die grafische Benutzeroberfläche und Kernfunktionalitäten.
    """

    def __init__(self, master: tk.Tk, data_manager):
        self.master = master
        self.data_manager = data_manager    
        self.master.title("Flashcard App")
        self.master.geometry("1200x700")
        self.fullscreen = False
        self.sidebar_expanded = True
        self.use_custom_tkinter = True
        self.multi_select_active = tk.BooleanVar(value=False)
        self.sidebar_width = 200
        self.sidebar_collapsed_width = 50

        # Moderne Sidebar mit hellerem Design
        self.sidebar_frame = tk.Frame(self.master, bg="#E8F4F8", width=self.sidebar_width)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False)
        self.sidebar_frame.pack_propagate(False)

        # Erstelle einen Canvas für den Gradient-Effekt
        self.sidebar_canvas = tk.Canvas(
            self.sidebar_frame,
            bg="#E8F4F8",
            highlightthickness=0,
            width=self.sidebar_width
        )
        self.sidebar_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Zeichne einen subtilen Gradient
        def draw_sidebar_gradient():
            height = self.sidebar_canvas.winfo_height()
            if height <= 1:
                height = 700
            colors = [
                "#E8F4F8",  # Hell-Cyanblau
                "#D5E8F0",  # Mittleres Cyanblau
                "#C2DCE8",  # Dunkleres Cyanblau
            ]
            steps = len(colors) - 1
            for i in range(steps):
                start_color = colors[i]
                end_color = colors[i + 1]
                segment_height = height // steps
                for j in range(segment_height):
                    ratio = j / segment_height
                    # Interpoliere zwischen den Farben
                    r1, g1, b1 = int(start_color[1:3], 16), int(start_color[3:5], 16), int(start_color[5:7], 16)
                    r2, g2, b2 = int(end_color[1:3], 16), int(end_color[3:5], 16), int(end_color[5:7], 16)
                    r = int(r1 + (r2 - r1) * ratio)
                    g = int(g1 + (g2 - g1) * ratio)
                    b = int(b1 + (b2 - b1) * ratio)
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    y = i * segment_height + j
                    self.sidebar_canvas.create_line(0, y, self.sidebar_width, y, fill=color)

        self.master.after(100, draw_sidebar_gradient)

        # Logo-Bereich am oberen Rand
        logo_frame = tk.Frame(self.sidebar_frame, bg="#E8F4F8")
        logo_frame.pack(pady=(15, 5), padx=10, fill='x')

        logo_label = tk.Label(
            logo_frame,
            text="📚 FlashCards",
            font=("Segoe UI", 16, "bold"),
            bg="#E8F4F8",
            fg="#2C3E50"
        )
        logo_label.pack()

        # Trennlinie
        separator = tk.Frame(self.sidebar_frame, bg="#4A90E2", height=2)
        separator.pack(fill='x', padx=10, pady=10)

        self.toggle_button = ModernButton(
            self.sidebar_frame,
            text="☰",
            command=self.toggle_sidebar,
            width=2,
            style='Secondary.TButton'
        )
        self.toggle_button.pack(pady=(5,10), padx=5, anchor='e')
        
        self.theme_file_path = get_persistent_path('themes.json')
        self.theme_backup_dir = os.path.join(self.data_manager.backup_dir, 'theme_backups')
        os.makedirs(self.theme_backup_dir, exist_ok=True)

        self.flashcards_backup_dir = os.path.join(self.data_manager.backup_dir, 'flashcards_backups')
        os.makedirs(self.flashcards_backup_dir, exist_ok=True)

        self.ensure_default_themes()
        self.stats_manager = StatisticsManager(self.data_manager)
        self.appearance_settings = AppearanceSettings()
        self.default_bg = DEFAULT_BG_COLOR
        self.bg_image = None
        self.current_bg_image_path = None
        self.bg_canvas = None
        self.current_category = None
        self.current_subcategory = None

        self.master.configure(bg=self.default_bg)

        self.style = ttk.Style()
        self.configure_styles()
        self.theme_menu_items = []

        self.content_frame = tk.Frame(self.master, bg=self.default_bg)
        self.content_frame.pack(side=tk.LEFT, fill="both", expand=True)

        self.sidebar_buttons = {}
        
        # Aufruf der zentralen Methode zur Erstellung der Sidebar-Buttons
        self._create_sidebar_buttons()
        
        # Initialisierung der App-Logik
        self.leitner_system = LeitnerSystem(self.data_manager)
        self.selected_subcategories = set()

        available_themes = self.data_manager.theme_manager.get_theme_names()
        if "light" in available_themes:
            self.load_theme("light")
        elif available_themes:
            self.load_theme(available_themes[0])
        else:
            messagebox.showwarning("Warnung", "Keine Themes verfügbar. Bitte ein Theme hinzufügen.")

        self.srs_settings = SRS_SETTINGS
        self.session_limit = SESSION_LIMIT
        self.cards_this_session = []
        self.session_results = []

        self.init_navigation()
        self.create_main_menu()
        self.setup_keyboard_shortcuts()
        self.set_app_icon()
        self.setup_auto_save()
    
    def _create_sidebar_buttons(self):
        """Erstellt alle Buttons für die Seitenleiste an einer zentralen Stelle."""
        button_configs = [
            {"name": "Home", "style": "Primary.TButton"},
            {"name": "Lernsession", "style": "Secondary.TButton"},
            {"name": "📅 Wochenplaner", "style": "Secondary.TButton"},
            {"name": "Kategorien", "style": "Secondary.TButton"},
            {"name": "Karten verwalten", "style": "Secondary.TButton"},
            {"name": "Tag-Suche", "style": "Secondary.TButton"},
            {"name": "Statistiken", "style": "Secondary.TButton"},
            {"name": "Einstellungen", "style": "Secondary.TButton"},
            {"name": "Theme-Verwaltung", "style": "Secondary.TButton"},
            {"name": "Backup-Verwaltung", "style": "Secondary.TButton"},
            {"name": "Hilfe", "style": "Secondary.TButton"},
            {"name": "Statistik zurücksetzen", "style": "Danger.TButton"},
        ]

        for config in button_configs:
            btn = ModernButton(
                self.sidebar_frame,
                text=config["name"],
                style=config["style"],
                command=lambda n=config["name"]: self._on_sidebar_button_click(n)
            )
            btn.pack(pady=(0,10), padx=10, fill='x')
            self.sidebar_buttons[config["name"]] = btn
            btn.original_style = config["style"]
    # In FlashCard Develop/main.py, innerhalb der FlashcardApp-Klasse

    def _on_sidebar_button_click(self, name):
        """Behandelt Klicks auf die Sidebar-Buttons."""
        logging.info(f"Sidebar-Button '{name}' geklickt.")
        action = {
            "Home": self.create_main_menu,
            "Lernsession": self.show_learning_options,
            "📅 Wochenplaner": self.show_weekly_calendar,
            "Kategorien": self.manage_categories,
            "Karten verwalten": self.show_card_management,
            "Tag-Suche": self.show_tag_search_interface,
            "Statistiken": self.show_statistics,
            "Statistik zurücksetzen": self.show_reset_statistics,
            "Einstellungen": self.configure_appearance,
            "Theme-Verwaltung": self.show_theme_manager,
            "Backup-Verwaltung": self.show_backup_manager,
            "Hilfe": self.show_help
        }.get(name)
        
        if action:
            action()
            self.highlight_active_button(name)
    def setup_auto_save(self):
        """Richtet periodisches Auto-Save ein (alle 5 Minuten)."""
        def auto_save():
            try:
                logging.info("Starte Auto-Save...")
                self.data_manager.save_flashcards()
                self.data_manager.save_categories()
                self.data_manager.save_stats()
                if hasattr(self, 'leitner_system'):
                    self.leitner_system.save_cards()
                logging.info("Auto-Save erfolgreich durchgeführt.")
            except Exception as e:
                logging.error(f"Fehler beim Auto-Save: {e}")
            finally:
                # Nächsten Auto-Save in 5 Minuten planen
                self.master.after(300000, auto_save)  # 300000 ms = 5 Minuten
        
        # Starte den ersten Auto-Save Timer
        self.master.after(300000, auto_save)
 
    def confirm_and_reschedule(self):
        """ Zeigt eine Bestätigungsbox an und führt die Neuplanung aus. """
        answer = messagebox.askyesno(
            "Fälligkeiten neu planen?",
            "WARNUNG:\n\n"
            "Dies setzt die 'Nächste Wiederholung'-Daten ALLER Karten basierend auf ihrem aktuellen Leitner-Level neu.\n"
            "Punkte und Level bleiben unverändert.\n\n"
            "Diese Aktion ist dafür gedacht, die Karten einmalig besser über die Zeit zu verteilen, um Lernspitzen zu vermeiden.\n\n"
            "Sind Sie sicher, dass Sie fortfahren möchten?"
        )
        if answer:
            logging.info("Benutzer hat Neuplanung der Fälligkeiten bestätigt.")
            # Zugriff auf LeitnerSystem (stellen sicher, dass es in __init__ initialisiert wurde)
            # Gehen Sie davon aus, dass Sie 'self.leitner_system = LeitnerSystem(self.data_manager)' in __init__ haben
            if hasattr(self, 'leitner_system') and self.leitner_system:
                try:
                    self.master.config(cursor="watch") # Zeige Ladecursor
                    self.master.update_idletasks() # Aktualisiere UI sofort
                    success = self.leitner_system.reschedule_due_dates_evenly()
                    self.master.config(cursor="") # Setze Cursor zurück
                    if success:
                        messagebox.showinfo("Erfolg", "Die Fälligkeitstermine wurden erfolgreich neu geplant.")
                        # Optional: UI aktualisieren, falls nötig (z.B. Statistik oder Editor neu laden)
                    else:
                        messagebox.showerror("Fehler", "Die Neuplanung konnte nicht vollständig abgeschlossen werden. Bitte überprüfen Sie die Logdatei für Details.")
                except Exception as e:
                    self.master.config(cursor="") # Setze Cursor zurück
                    logging.exception("Ein unerwarteter Fehler ist während der Neuplanung aufgetreten.")
                    messagebox.showerror("Schwerer Fehler", f"Ein unerwarteter Fehler ist aufgetreten:\n{e}\n\nÜberprüfen Sie die Logdatei.")

            else:
                 messagebox.showerror("Fehler", "LeitnerSystem nicht verfügbar oder nicht initialisiert.")
                 logging.error("Versuch, Neuplanung aufzurufen, aber self.leitner_system ist nicht verfügbar.")
        else:
            logging.info("Benutzer hat Neuplanung abgebrochen.")
    def set_app_icon(self):
        """
        Setzt das Anwendungsicon für das Hauptfenster.
        """
        try:
            icon_path = os.path.join(get_app_data_dir(), 'flashcard_icon.ico')
            if os.path.exists(icon_path):
                self.master.iconbitmap(icon_path)
            else:
                logging.warning(f"Icon-Datei nicht gefunden: {icon_path}")
        except Exception as e:
            logging.error(f"Fehler beim Setzen des App-Icons: {e}")
            messagebox.showerror("Fehler", f"App-Icon konnte nicht gesetzt werden: {e}")
    def ensure_default_themes(self):
        """
        Prüft und erzeugt ggf. Standard-Themes, falls sie nicht existieren.
        """
        predefined = {
            "light": {
                "default_bg": "#ffffff",
                "text_bg_color": "#ffffff",
                "text_fg_color": "#000000",
                "button_bg_color": "#4a90e2",
                "button_fg_color": "#ffffff"
            },
            "dark": {
                "default_bg": "#2b2b2b",
                "text_bg_color": "#3a3a3a",
                "text_fg_color": "#ffffff",
                "button_bg_color": "#444444",
                "button_fg_color": "#ffffff"
            },
            "system": {
                "default_bg": "",
                "text_bg_color": "",
                "text_fg_color": "",
                "button_bg_color": "",
                "button_fg_color": ""
            }
        }
        for theme_name, theme_data in predefined.items():
            if not self.data_manager.theme_manager.get_theme(theme_name):
                self.data_manager.theme_manager.add_or_update_theme(theme_name, theme_data)

    def show_learning_time_overview(self):
        self._clear_content_frame()
        header = tk.Label(
            self.content_frame,
            text="Lernzeit-Übersicht",
            font=("Segoe UI", 18, "bold"),
            bg="#ffffff"
        )
        header.pack(pady=20)

        main_frame = tk.Frame(self.content_frame, bg="#ffffff")
        main_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)

        # Gesamtlernzeit anzeigen
        total_learning_time = sum(stat['total_time'] for stat in self.data_manager.stats if isinstance(stat, dict) and 'total_time' in stat)
        tk.Label(
            main_frame,
            text=f"Gesamte Lernzeit: {total_learning_time} Minuten",
            font=("Segoe UI", 14),
            bg="#ffffff"
        ).pack(pady=10)

        # Durchschnittliche Lernzeit pro Sitzung
        total_sessions = len(self.data_manager.stats)
        average_learning_time = (total_learning_time / total_sessions) if total_sessions else 0
        tk.Label(
            main_frame,
            text=f"Durchschnittliche Lernzeit pro Sitzung: {average_learning_time:.2f} Minuten",
            font=("Segoe UI", 14),
            bg="#ffffff"
        ).pack(pady=10)

        # Erweiterte Analysen: Verteilung der Lernzeiten über Tageszeiten
        self._create_time_of_day_distribution(main_frame)

        # Korrelation zwischen Lernzeit und Erfolgsquote
        self._create_time_success_correlation(main_frame)

        # Zurück-Button
        back_btn = ModernButton(
            self.content_frame,
            text="Zurück zum Hauptmenü",
            command=self.create_main_menu,
            width=20,
            style=ButtonStyle.SECONDARY.value
        )
        back_btn.pack(pady=20)
        self.sidebar_buttons["back_to_main_from_learning_time"] = back_btn

        # Setze den aktiven Button auf 'learning_time_overview'
        self.highlight_active_button('learning_time_overview')

    def _create_time_of_day_distribution(self, parent_frame):
        """Erstellt eine Visualisierung der Lernzeitverteilung über verschiedene Tageszeiten."""
        # Kategorien für Tageszeiten
        time_of_day = {
            "Morgen (5-12)": 0,
            "Nachmittag (12-17)": 0,
            "Abend (17-21)": 0,
            "Nacht (21-5)": 0
        }

        for stat in self.data_manager.stats:
            if isinstance(stat, dict) and 'date' in stat and 'total_time' in stat:
                try:
                    date_obj = datetime.datetime.strptime(stat['date'], "%d.%m.%Y").date()
                    # Annahme: Wir haben eine Zeitkomponente, z.B., 'review_time'
                    review_time_str = stat.get('review_time', "12:00")  # Fallback zu Mittag
                    review_time = datetime.datetime.strptime(review_time_str, "%H:%M").time()
                    hour = review_time.hour

                    if 5 <= hour < 12:
                        time_of_day["Morgen (5-12)"] += stat['total_time']
                    elif 12 <= hour < 17:
                        time_of_day["Nachmittag (12-17)"] += stat['total_time']
                    elif 17 <= hour < 21:
                        time_of_day["Abend (17-21)"] += stat['total_time']
                    else:
                        time_of_day["Nacht (21-5)"] += stat['total_time']
                except ValueError:
                    continue

        labels = list(time_of_day.keys())
        values = list(time_of_day.values())

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(x=labels, y=values, palette="viridis", ax=ax)
        ax.set_title("Verteilung der Lernzeiten über Tageszeiten", fontsize=16)
        ax.set_ylabel("Lernzeit (Minuten)", fontsize=14)
        ax.set_xlabel("Tageszeit", fontsize=14)
        ax.tick_params(labelsize=12)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=20)

        # Interaktive Tooltips mit mplcursors
        cursor = mplcursors.cursor(ax.patches, hover=True)


    def _create_time_success_correlation(self, parent_frame):
        """Erstellt eine Visualisierung der Korrelation zwischen Lernzeit und Erfolgsquote."""
        learning_times = []
        success_rates = []

        for stat in self.data_manager.stats:
            if isinstance(stat, dict) and 'total_time' in stat and 'cards_correct' in stat and 'cards_total' in stat:
                total_time = stat['total_time']
                success = (stat['cards_correct'] / stat['cards_total']) * 100 if stat['cards_total'] > 0 else 0
                learning_times.append(total_time)
                success_rates.append(success)

        if learning_times and success_rates:
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.scatterplot(x=learning_times, y=success_rates, alpha=0.6, ax=ax)
            ax.set_title("Korrelation zwischen Lernzeit und Erfolgsquote", fontsize=16)
            ax.set_xlabel("Lernzeit (Minuten)", fontsize=14)
            ax.set_ylabel("Erfolgsquote (%)", fontsize=14)

            # Berechnung der Korrelation
            correlation = self._calculate_correlation(learning_times, success_rates)
            ax.text(0.05, 0.95, f"Korrelation: {correlation:.2f}", transform=ax.transAxes, fontsize=12,
                    verticalalignment='top')

            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=parent_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(pady=20)

            # Interaktive Tooltips mit mplcursors
            cursor = mplcursors.cursor(ax.collections, hover=True)
            @cursor.connect("add")
            def on_add(sel):
                i = sel.index
                x = learning_times[i]
                y = success_rates[i]
                sel.annotation.set(text=f"Lernzeit: {x} Min\nErfolgsquote: {y:.1f}%")
        else:
            tk.Label(
                parent_frame,
                text="Nicht genügend Daten für die Korrelation zwischen Lernzeit und Erfolgsquote.",
                font=("Segoe UI", 12),
                bg="#ffffff"
            ).pack(pady=10)
    
    def highlight_active_button(self, button_name):
        """
        Hebt den aktiven Sidebar-Button hervor und setzt die vorherige Hervorhebung zurück.

        Args:
            button_name (str): Der Name des Buttons, der hervorgehoben werden soll.
        """
        try:
            # Setze die Hervorhebung des vorherigen aktiven Buttons zurück
            if hasattr(self, 'active_sidebar_button') and self.active_sidebar_button:
                previous_btn = self.sidebar_buttons.get(self.active_sidebar_button)
                if previous_btn:
                    # Verwende die ButtonStyle Enumeration
                    if previous_btn.style.startswith('Primary'):
                        previous_btn.configure(style=ButtonStyle.PRIMARY.value)
                    elif previous_btn.style.startswith('Secondary'):
                        previous_btn.configure(style=ButtonStyle.SECONDARY.value)

            # Hebe den neuen aktiven Button hervor
            current_btn = self.sidebar_buttons.get(button_name)
            if current_btn:
                # Bestimme den aktiven Stil basierend auf dem ursprünglichen Stil
                if current_btn.style.startswith('Primary'):
                    active_style = ButtonStyle.ACTIVE_PRIMARY.value
                else:
                    # Für Secondary Buttons den Primary Active Style verwenden
                    active_style = ButtonStyle.ACTIVE_PRIMARY.value
                
                # Konfiguriere den Button mit dem aktiven Stil
                current_btn.configure(style=active_style)
                self.active_sidebar_button = button_name
                
            logging.info(f"Button '{button_name}' hervorgehoben")
        except Exception as e:
            logging.error(f"Fehler beim Hervorheben des Buttons '{button_name}': {e}")
        
    def _calculate_correlation(self, x, y):
        """Berechnet die Pearson-Korrelation zwischen zwei Listen."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        try:
            # Einfache Korrelationsberechnung statt pearsonr
            mean_x = sum(x) / len(x)
            mean_y = sum(y) / len(y)
            
            numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
            denominator = (
                (sum((x[i] - mean_x) ** 2 for i in range(len(x)))) ** 0.5 *
                (sum((y[i] - mean_y) ** 2 for i in range(len(y)))) ** 0.5
            )
            
            return numerator / denominator if denominator != 0 else 0.0
        except Exception as e:
            logging.error(f"Fehler bei der Berechnung der Korrelation: {e}")
            return 0.0



    def _create_progress_stats(self, parent_frame):
        """
        Erstellt den Statistik-Tab mit einem zweizeiligen Filter-Menü oben
        und einem scrollbaren Bereich für den gesamten Inhalt (inkl. Chart).
        """

        # 1) Scrollbarer Haupt-Container (damit man alles scrollen kann, wenn es zu hoch wird)
        scrollable_frame = ctk.CTkScrollableFrame(parent_frame)
        scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Wir packen nun ALLE Widgets (Filter + Chart) in dieses scrollable_frame
        scrollable_frame.grid_rowconfigure(2, weight=1)  # Zeile 2 (Chart) soll sich dehnen
        scrollable_frame.grid_columnconfigure(0, weight=1)

        # ---------------- DATUMS-Variablen DEFINIEREN ----------------
        self.date_var = tk.StringVar()
        self.start_date_var = tk.StringVar()
        self.end_date_var = tk.StringVar()

        # ---------------- ZWEIZEILIGES FILTER-MENÜ ----------------

        # ========== Zeile 0: Diagrammtyp, Zeitraumfilter, Datums-Frame ==========
        filter_row_0 = ctk.CTkFrame(scrollable_frame)
        filter_row_0.grid(row=0, column=0, sticky="ew", pady=(0,5))
        # Feste Spaltenaufteilung
        for c in range(6):
            filter_row_0.grid_columnconfigure(c, weight=0)

        # Diagrammtyp
        ctk.CTkLabel(
            filter_row_0, text="Diagrammtyp:", font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, padx=(0,5), pady=2, sticky="w")

        self.chart_type_var = tk.StringVar(value="Gesamt")
        chart_types = [
            "Gesamt", "Richtig/Falsch", "Nach Kategorie",
            "Kategorien (Kartenzahl)", "Kategorien (Richtig/Falsch)",
            "Lernzeit", "Heatmap"
        ]
        ctk.CTkOptionMenu(
            filter_row_0,
            variable=self.chart_type_var,
            values=chart_types,
            width=120
        ).grid(row=0, column=1, padx=(0,10), pady=2, sticky="w")

        # Zeitraumfilter
        ctk.CTkLabel(
            filter_row_0, text="Zeitraumfilter:", font=ctk.CTkFont(size=12)
        ).grid(row=0, column=2, padx=(0,5), pady=2, sticky="w")

        self.time_period_var = tk.StringVar(value="Gesamt")
        time_periods = ["Gesamt", "Tag", "Woche", "Monat", "Benutzerdefiniert"]
        ctk.CTkOptionMenu(
            filter_row_0,
            variable=self.time_period_var,
            values=time_periods,
            width=120,
            command=self._update_date_selection  # Falls Sie es schon haben
        ).grid(row=0, column=3, padx=(0,10), pady=2, sticky="w")

        # Datums-Frame
        self.date_selection_frame = ctk.CTkFrame(filter_row_0)
        self.date_selection_frame.grid(row=0, column=4, padx=5, pady=2, sticky="w")

        # ========== Zeile 1: Kategorie, Unterkategorie, Vergleich & Button ==========
        filter_row_1 = ctk.CTkFrame(scrollable_frame)
        filter_row_1.grid(row=1, column=0, sticky="ew", pady=(0,5))
        for c in range(7):
            filter_row_1.grid_columnconfigure(c, weight=0)

        # Kategorie
        ctk.CTkLabel(
            filter_row_1, text="Kategorie:", font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, padx=(0,5), pady=2, sticky="w")

        self.selected_category_var = tk.StringVar(value="Alle")
        cat_list = ["Alle"] + sorted(self.data_manager.categories.keys())
        ctk.CTkOptionMenu(
            filter_row_1,
            variable=self.selected_category_var,
            values=cat_list,
            width=120
        ).grid(row=0, column=1, padx=(0,10), pady=2, sticky="w")

        # Unterkategorie
        ctk.CTkLabel(
            filter_row_1, text="Unterkategorie:", font=ctk.CTkFont(size=12)
        ).grid(row=0, column=2, padx=(0,5), pady=2, sticky="w")

        self.subcategory_var = tk.StringVar(value="Alle")
        self.subcategory_menu = ctk.CTkOptionMenu(
            filter_row_1,
            variable=self.subcategory_var,
            values=["Alle"],
            width=120
        )
        self.subcategory_menu.grid(row=0, column=3, padx=(0,10), pady=2, sticky="w")

        # Vergleichskategorie
        ctk.CTkLabel(
            filter_row_1, text="Vergleichskat.:", font=ctk.CTkFont(size=12)
        ).grid(row=0, column=4, padx=(0,5), pady=2, sticky="w")

        self.second_category_var = tk.StringVar(value="Keine")
        cat_list_2 = ["Keine"] + sorted(self.data_manager.categories.keys())
        ctk.CTkOptionMenu(
            filter_row_1,
            variable=self.second_category_var,
            values=cat_list_2,
            width=120
        ).grid(row=0, column=5, padx=(0,10), pady=2, sticky="w")

        # Vergleichs-Unterkategorie
        self.second_subcategory_var = tk.StringVar(value="Alle")
        self.second_subcategory_menu = ctk.CTkOptionMenu(
            filter_row_1,
            variable=self.second_subcategory_var,
            values=["Alle"],
            width=120
        )
        self.second_subcategory_menu.grid(row=0, column=6, padx=(0,10), pady=2, sticky="w")

        # "Filter anwenden"-Button am Ende
        apply_filter_btn = ModernButton(
            filter_row_1,
            text="Filter anwenden",
            command=self.update_progress_stats,
            width=15,
            style=ButtonStyle.PRIMARY.value
        )
        apply_filter_btn.grid(row=0, column=7, padx=(10,0), pady=2, sticky="e")

        # Subkategorie aktualisieren, wenn Hauptkategorie wechselt
        def update_subcategories(*_):
            selected = self.selected_category_var.get()
            if selected == "Alle":
                subcats = ["Alle"]
            else:
                subcats = ["Alle"] + sorted(self.data_manager.categories.get(selected, {}).keys())
            self.subcategory_menu.configure(values=subcats)
            self.subcategory_var.set("Alle")

        self.selected_category_var.trace_add('write', update_subcategories)

        # ---------------- CHART-BEREICH (Zeile 2) ----------------
        self.progress_chart_frame = ctk.CTkFrame(scrollable_frame)
        self.progress_chart_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0,5))

        # Zum Schluss gleich updaten
        self.update_progress_stats()

            # Event Handler für Updates
        def update_second_subcategories(*_):
            selected_second_cat = self.second_category_var.get()
            if selected_second_cat in ["Keine", "Alle"]:
                subcats = ["Alle"]
            else:
                subcats = ["Alle"] + sorted(self.data_manager.categories.get(selected_second_cat, {}).keys())
            self.second_subcategory_menu.configure(values=subcats)
            self.second_subcategory_var.set("Alle")

        # Und an diese Variable binden wir den Handler
        self.second_category_var.trace_add('write', update_second_subcategories)

    def show_card_management(self):
        """Zeigt das Karten-Management-Menü an."""
        self._clear_content_frame()

        # Moderner Gradient-Header ähnlich wie bei Kategorien
        header_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='#3b82f6',
            corner_radius=0,
            height=120
        )
        header_container.pack(fill='x', pady=(0, 30))
        header_container.pack_propagate(False)

        header_content = ctk.CTkFrame(header_container, fg_color='transparent')
        header_content.place(relx=0.5, rely=0.5, anchor='center')

        # Icon und Titel
        icon_title_frame = ctk.CTkFrame(header_content, fg_color='transparent')
        icon_title_frame.pack()

        ctk.CTkLabel(
            icon_title_frame,
            text="🎴",
            font=ctk.CTkFont(size=40),
            text_color='#ffffff'
        ).pack(side='left', padx=(0, 15))

        title_frame = ctk.CTkFrame(icon_title_frame, fg_color='transparent')
        title_frame.pack(side='left')

        ctk.CTkLabel(
            title_frame,
            text="Karten verwalten",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color='#ffffff'
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_frame,
            text="Organisiere und pflege deine Lernkartensammlung",
            font=ctk.CTkFont(size=14),
            text_color='#dbeafe'
        ).pack(anchor='w')

        # Hauptcontainer
        main_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='transparent'
        )
        main_container.pack(fill='both', expand=True, padx=50, pady=0)

        # Container für die Optionen
        options_container = ctk.CTkFrame(main_container, fg_color='transparent')
        options_container.pack(fill='both', expand=True)

        # 1. Neue Karte hinzufügen - Ultramodernes Design mit Schatten-Effekt
        add_card_outer = ctk.CTkFrame(
            options_container,
            fg_color='#e0e7ff',
            corner_radius=22
        )
        add_card_outer.pack(fill='x', pady=(0, 25), padx=2)

        add_card = ctk.CTkFrame(
            add_card_outer,
            fg_color='#ffffff',
            corner_radius=20,
            border_width=2,
            border_color='#10b981'
        )
        add_card.pack(fill='x', padx=3, pady=3)

        # Linker Bereich mit Icon und Gradient-Effekt
        left_section = ctk.CTkFrame(
            add_card,
            fg_color='#10b981',
            corner_radius=18,
            width=130
        )
        left_section.pack(side='left', fill='y', padx=4, pady=4)
        left_section.pack_propagate(False)

        icon_frame = ctk.CTkFrame(left_section, fg_color='transparent')
        icon_frame.place(relx=0.5, rely=0.5, anchor='center')

        ctk.CTkLabel(
            icon_frame,
            text="✨",
            font=ctk.CTkFont(size=52),
            text_color="#ffffff"
        ).pack()

        ctk.CTkLabel(
            icon_frame,
            text="NEU",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(5, 0))

        # Rechter Bereich mit Inhalt
        right_section = ctk.CTkFrame(add_card, fg_color='transparent')
        right_section.pack(side='left', fill='both', expand=True, padx=30, pady=28)

        # Header mit Badge
        header_frame = ctk.CTkFrame(right_section, fg_color='transparent')
        header_frame.pack(anchor='w', pady=(0, 10))

        ctk.CTkLabel(
            header_frame,
            text="Neue Karte hinzufügen",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#111827"
        ).pack(side='left')

        badge = ctk.CTkFrame(header_frame, fg_color='#d1fae5', corner_radius=14, height=28)
        badge.pack(side='left', padx=12)
        ctk.CTkLabel(
            badge,
            text="⭐ Empfohlen",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#059669"
        ).pack(padx=12, pady=4)

        ctk.CTkLabel(
            right_section,
            text="Erstelle eine neue Lernkarte mit individuellen Fragen und Antworten. Füge optional Bilder und Kategorien hinzu.",
            font=ctk.CTkFont(size=14),
            text_color="#6b7280",
            wraplength=550,
            justify='left'
        ).pack(anchor='w', pady=(0, 20))

        # Button mit modernem Design
        button_frame = ctk.CTkFrame(right_section, fg_color='transparent')
        button_frame.pack(anchor='w')

        ctk.CTkButton(
            button_frame,
            text="→  Jetzt erstellen",
            command=self.add_card,
            height=48,
            width=190,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            corner_radius=14,
            border_width=0
        ).pack()

        # 2. Karten entfernen - Ultramodernes Design mit Schatten-Effekt
        remove_card_outer = ctk.CTkFrame(
            options_container,
            fg_color='#fee2e2',
            corner_radius=22
        )
        remove_card_outer.pack(fill='x', pady=(0, 25), padx=2)

        remove_card = ctk.CTkFrame(
            remove_card_outer,
            fg_color='#ffffff',
            corner_radius=20,
            border_width=2,
            border_color='#ef4444'
        )
        remove_card.pack(fill='x', padx=3, pady=3)

        # Linker Bereich mit Icon und Gradient-Effekt
        left_section = ctk.CTkFrame(
            remove_card,
            fg_color='#ef4444',
            corner_radius=18,
            width=130
        )
        left_section.pack(side='left', fill='y', padx=4, pady=4)
        left_section.pack_propagate(False)

        icon_frame = ctk.CTkFrame(left_section, fg_color='transparent')
        icon_frame.place(relx=0.5, rely=0.5, anchor='center')

        ctk.CTkLabel(
            icon_frame,
            text="🗑️",
            font=ctk.CTkFont(size=52),
            text_color="#ffffff"
        ).pack()

        ctk.CTkLabel(
            icon_frame,
            text="CLEAN",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(5, 0))

        # Rechter Bereich mit Inhalt
        right_section = ctk.CTkFrame(remove_card, fg_color='transparent')
        right_section.pack(side='left', fill='both', expand=True, padx=30, pady=28)

        # Header mit Warnung-Badge
        header_frame = ctk.CTkFrame(right_section, fg_color='transparent')
        header_frame.pack(anchor='w', pady=(0, 10))

        ctk.CTkLabel(
            header_frame,
            text="Karten entfernen",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#111827"
        ).pack(side='left')

        badge = ctk.CTkFrame(header_frame, fg_color='#fee2e2', corner_radius=14, height=28)
        badge.pack(side='left', padx=12)
        ctk.CTkLabel(
            badge,
            text="⚠️ Vorsicht",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#dc2626"
        ).pack(padx=12, pady=4)

        ctk.CTkLabel(
            right_section,
            text="Entferne nicht mehr benötigte Lernkarten aus deiner Sammlung. Gelöschte Karten können nicht wiederhergestellt werden.",
            font=ctk.CTkFont(size=14),
            text_color="#6b7280",
            wraplength=550,
            justify='left'
        ).pack(anchor='w', pady=(0, 20))

        # Button mit modernem Design
        button_frame = ctk.CTkFrame(right_section, fg_color='transparent')
        button_frame.pack(anchor='w')

        ctk.CTkButton(
            button_frame,
            text="→  Karten verwalten",
            command=self.show_remove_cards,
            height=48,
            width=190,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#ef4444",
            hover_color="#dc2626",
            corner_radius=14,
            border_width=0
        ).pack()

        # 3. Karten Management - Ultramodernes Design mit Schatten-Effekt
        manage_card_outer = ctk.CTkFrame(
            options_container,
            fg_color='#dbeafe',
            corner_radius=22
        )
        manage_card_outer.pack(fill='x', pady=(0, 25), padx=2)

        manage_card = ctk.CTkFrame(
            manage_card_outer,
            fg_color='#ffffff',
            corner_radius=20,
            border_width=2,
            border_color='#3b82f6'
        )
        manage_card.pack(fill='x', padx=3, pady=3)

        # Linker Bereich mit Icon und Gradient-Effekt
        left_section = ctk.CTkFrame(
            manage_card,
            fg_color='#3b82f6',
            corner_radius=18,
            width=130
        )
        left_section.pack(side='left', fill='y', padx=4, pady=4)
        left_section.pack_propagate(False)

        icon_frame = ctk.CTkFrame(left_section, fg_color='transparent')
        icon_frame.place(relx=0.5, rely=0.5, anchor='center')

        ctk.CTkLabel(
            icon_frame,
            text="📚",
            font=ctk.CTkFont(size=52),
            text_color="#ffffff"
        ).pack()

        ctk.CTkLabel(
            icon_frame,
            text="EDIT",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(5, 0))

        # Rechter Bereich mit Inhalt
        right_section = ctk.CTkFrame(manage_card, fg_color='transparent')
        right_section.pack(side='left', fill='both', expand=True, padx=30, pady=28)

        # Header mit Badge
        header_frame = ctk.CTkFrame(right_section, fg_color='transparent')
        header_frame.pack(anchor='w', pady=(0, 10))

        ctk.CTkLabel(
            header_frame,
            text="Karten Management",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#111827"
        ).pack(side='left')

        badge = ctk.CTkFrame(header_frame, fg_color='#dbeafe', corner_radius=14, height=28)
        badge.pack(side='left', padx=12)
        ctk.CTkLabel(
            badge,
            text="✓ Vollzugriff",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#1e40af"
        ).pack(padx=12, pady=4)

        ctk.CTkLabel(
            right_section,
            text="Bearbeite und verwalte alle deine bestehenden Lernkarten. Ändere Inhalte, passe Kategorien an oder organisiere deine Sammlung.",
            font=ctk.CTkFont(size=14),
            text_color="#6b7280",
            wraplength=550,
            justify='left'
        ).pack(anchor='w', pady=(0, 20))

        # Button mit modernem Design
        button_frame = ctk.CTkFrame(right_section, fg_color='transparent')
        button_frame.pack(anchor='w')

        ctk.CTkButton(
            button_frame,
            text="→  Karten bearbeiten",
            command=self.show_card_details_manager,
            height=48,
            width=190,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#3b82f6",
            hover_color="#2563eb",
            corner_radius=14,
            border_width=0
        ).pack()

        # Moderner Zurück-Button
        back_button_frame = ctk.CTkFrame(main_container, fg_color='transparent')
        back_button_frame.pack(pady=(30, 0))

        back_btn = ctk.CTkButton(
            back_button_frame,
            text="←  Zurück zum Hauptmenü",
            command=self.create_main_menu,
            height=45,
            width=220,
            font=ctk.CTkFont(size=14),
            fg_color="#f3f4f6",
            hover_color="#e5e7eb",
            text_color="#374151",
            corner_radius=12,
            border_width=2,
            border_color="#d1d5db"
        )
        back_btn.pack()

    def show_card_details_manager(self):
        """Zeigt detaillierte Kartenübersicht mit Bearbeitungsmöglichkeiten UND SUCHE."""
        self._clear_content_frame()

        # Moderner Header mit Gradient-Hintergrund
        header_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='#3b82f6',
            corner_radius=0,
            height=110
        )
        header_container.pack(fill='x', pady=(0, 20))
        header_container.pack_propagate(False)

        header_content = ctk.CTkFrame(header_container, fg_color='transparent')
        header_content.place(relx=0.5, rely=0.5, anchor='center')

        # Icon und Titel
        icon_title_frame = ctk.CTkFrame(header_content, fg_color='transparent')
        icon_title_frame.pack()

        ctk.CTkLabel(
            icon_title_frame,
            text="📚",
            font=ctk.CTkFont(size=36),
            text_color='#ffffff'
        ).pack(side='left', padx=(0, 15))

        title_frame = ctk.CTkFrame(icon_title_frame, fg_color='transparent')
        title_frame.pack(side='left')

        ctk.CTkLabel(
            title_frame,
            text="Karten Management",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color='#ffffff'
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_frame,
            text="Verwalte, bearbeite und organisiere alle deine Lernkarten",
            font=ctk.CTkFont(size=13),
            text_color='#dbeafe'
        ).pack(anchor='w')

        # Container für den gesamten Inhalt dieser Ansicht
        # Verwende grid für bessere Kontrolle über die Zeilenaufteilung
        manager_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        manager_container.pack(fill='both', expand=True)
        manager_container.grid_columnconfigure(0, weight=1)
        manager_container.grid_rowconfigure(0, weight=0) # Filter-Zeile
        manager_container.grid_rowconfigure(1, weight=1) # Karten-Zeile (expandiert)
        manager_container.grid_rowconfigure(2, weight=0) # Paginierungs-Zeile

        # === Moderner Filter-Bereich ===
        filter_container = ctk.CTkFrame(
            manager_container,
            fg_color='#ffffff',
            corner_radius=15,
            border_width=2,
            border_color='#3b82f6'
        )
        filter_container.grid(row=0, column=0, sticky='ew', padx=20, pady=(0, 15))

        top_filter_frame = ctk.CTkFrame(filter_container, fg_color='transparent')
        top_filter_frame.pack(fill='x', padx=20, pady=15)

        # Icon für Filter
        ctk.CTkLabel(
            top_filter_frame,
            text="🔍",
            font=ctk.CTkFont(size=20)
        ).pack(side='left', padx=(0, 15))

        # --- Kategorie & Subkategorie (links) ---
        cat_subcat_frame = ctk.CTkFrame(top_filter_frame, fg_color='transparent')
        cat_subcat_frame.pack(side='left', padx=(0, 20))

        # Kategorie Filter
        cat_row = ctk.CTkFrame(cat_subcat_frame, fg_color='transparent')
        cat_row.pack(fill='x', pady=4)

        ctk.CTkLabel(
            cat_row,
            text="Kategorie:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color='#374151',
            width=100
        ).pack(side='left', padx=(0, 8))

        self.category_var = tk.StringVar(value=getattr(self, 'last_category', "Alle"))
        categories = ["Alle"] + sorted(self.data_manager.categories.keys())
        self.category_menu = ctk.CTkOptionMenu(
            cat_row,
            variable=self.category_var,
            values=categories,
            width=180,
            height=36,
            corner_radius=10,
            fg_color='#3b82f6',
            button_color='#2563eb',
            button_hover_color='#1d4ed8',
            font=ctk.CTkFont(size=12),
            command=lambda *args: (update_subcategories(), self.apply_card_management_filters())
        )
        self.category_menu.pack(side='left')

        # Subkategorie Filter
        subcat_row = ctk.CTkFrame(cat_subcat_frame, fg_color='transparent')
        subcat_row.pack(fill='x', pady=4)

        ctk.CTkLabel(
            subcat_row,
            text="Unterkategorie:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color='#374151',
            width=100
        ).pack(side='left', padx=(0, 8))

        self.subcategory_var = tk.StringVar(value=getattr(self, 'last_subcategory', "Alle"))
        self.subcategory_menu = ctk.CTkOptionMenu(
            subcat_row,
            variable=self.subcategory_var,
            values=["Alle"],
            width=180,
            height=36,
            corner_radius=10,
            fg_color='#3b82f6',
            button_color='#2563eb',
            button_hover_color='#1d4ed8',
            font=ctk.CTkFont(size=12),
            state="disabled",
            command=lambda *args: self.apply_card_management_filters()
        )
        self.subcategory_menu.pack(side='left')

        # --- Suchfeld (rechts) ---
        search_frame = ctk.CTkFrame(top_filter_frame, fg_color='transparent')
        search_frame.pack(side='left', padx=(20, 0), fill='x', expand=True)

        ctk.CTkLabel(
            search_frame,
            text="Suche:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color='#374151'
        ).pack(side='left', padx=(0, 8))

        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            width=250,
            height=36,
            corner_radius=10,
            border_width=2,
            border_color='#d1d5db',
            placeholder_text="Begriff in Frage oder Antwort...",
            font=ctk.CTkFont(size=12)
        )
        search_entry.pack(side='left', padx=(0, 10), fill='x', expand=True)

        # Such-Button
        search_button = ctk.CTkButton(
            search_frame,
            text="🔍 Suchen",
            command=self.apply_card_management_filters,
            width=100,
            height=36,
            corner_radius=10,
            fg_color='#3b82f6',
            hover_color='#2563eb',
            font=ctk.CTkFont(size=12, weight="bold")
        )
        search_button.pack(side='left')

        # Enter-Taste im Suchfeld löst auch die Filterung aus
        search_entry.bind("<Return>", lambda event: self.apply_card_management_filters())

        # === Container für die Kartenanzeige (Scrollbar etc.) ===
        # Wird im grid platziert, damit es sich korrekt ausdehnt
        # Wichtig: Diesen Frame *unterhalb* des top_filter_frame platzieren (row=1)
        self.cards_display_container = ctk.CTkFrame(manager_container, fg_color="transparent")
        self.cards_display_container.grid(row=1, column=0, sticky='nsew', padx=20, pady=0)
        self.cards_display_container.grid_rowconfigure(0, weight=1)    # Scroll area soll sich ausdehnen
        self.cards_display_container.grid_columnconfigure(0, weight=1)

        # === Container für Paginierung / "Mehr laden" Button ===
        # Wird im grid platziert (row=2)
        self.bottom_frame_manage_container = ctk.CTkFrame(manager_container, fg_color="transparent")
        self.bottom_frame_manage_container.grid(row=2, column=0, sticky='ew', padx=20, pady=(5, 10))
        self.bottom_frame_manage_container.grid_columnconfigure(0, weight=1) # Button zentrieren

        # --- Hilfsfunktion zum Aktualisieren der Subkategorien ---
        def update_subcategories(*args):
            """Aktualisiert Subkategorie-Dropdown basierend auf Kategorie."""
            selected_category = self.category_var.get()
            if selected_category == "Alle":
                self.subcategory_menu.configure(state="disabled", values=["Alle"])
                self.subcategory_var.set("Alle")
            else:
                subcategories = sorted(self.data_manager.categories.get(selected_category, {}).keys())
                if subcategories:
                    self.subcategory_menu.configure(state="normal", values=["Alle"] + subcategories)
                    # Wenn die letzte Subkategorie nicht mehr gültig ist, setze auf "Alle"
                    if self.subcategory_var.get() not in (["Alle"] + subcategories):
                         self.subcategory_var.set("Alle")
                    # Wenn die letzte Subkategorie "Keine" war, setze auf "Alle"
                    elif self.subcategory_var.get() == "Keine":
                         self.subcategory_var.set("Alle")

                else:
                    self.subcategory_menu.configure(state="disabled", values=["Keine"])
                    self.subcategory_var.set("Keine")
            # WICHTIG: Filterung wird jetzt durch command/trace der Menüs ausgelöst

        # Initialen Zustand setzen und erste Filterung
        update_subcategories() # Füllt Subkategorien initial korrekt
        self.apply_card_management_filters() # Zeigt initial alle Karten oder basierend auf last_category

        def show_card_preview(self, card, image_path):
            """Zeigt eine Vorschau des Kartenbildes."""
            preview_window = ctk.CTkToplevel(self.master)
            preview_window.title("Bildvorschau")
            preview_window.geometry("800x600")
            
            try:
                image = Image.open(image_path)
                # Bild auf maximale Größe skalieren
                display_size = (780, 580)
                image.thumbnail(display_size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                label = tk.Label(preview_window, image=photo)
                label.image = photo  # Referenz behalten
                label.pack(expand=True, fill='both', padx=10, pady=10)
                
                # SchlieÃƒÅ¸en-Button hinzufügen
                close_btn = ctk.CTkButton(
                    preview_window,
                    text="Schließen",
                    command=preview_window.destroy,
                    width=100
                )
                close_btn.pack(pady=10)
                
                # Tastenkürzel zum Schließen
                preview_window.bind('<Escape>', lambda e: preview_window.destroy())
                
            except Exception as e:
                ctk.CTkLabel(
                    preview_window,
                    text=f"Fehler beim Laden des Bildes:\n{e}",
                    font=ctk.CTkFont(size=12)
                ).pack(pady=20)

        def show_card_stats(self, card):
            """Zeigt Statistiken für eine einzelne Karte."""
            stats_window = ctk.CTkToplevel(self.master)
            stats_window.title("Kartenstatistik")
            stats_window.geometry("400x500")
            
            # Header
            header = ctk.CTkLabel(
                stats_window,
                text=f"Statistik für Karte",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            header.pack(pady=10)
            
            # Frage der Karte
            question_frame = ctk.CTkFrame(stats_window)
            question_frame.pack(fill='x', padx=20, pady=5)
            
            ctk.CTkLabel(
                question_frame,
                text="Frage:",
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(anchor='w')
            
            ctk.CTkLabel(
                question_frame,
                text=card.question,
                font=ctk.CTkFont(size=12),
                wraplength=350
            ).pack(anchor='w')
            
            # Stats Frame
            stats_frame = ctk.CTkFrame(stats_window)
            stats_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Statistik-Informationen
            stats = [
                ("Wiederholungen", card.repetitions),
                ("Richtige Antworten", card.success_count),
                ("Erfolgsquote", f"{(card.success_count/card.repetitions*100 if card.repetitions > 0 else 0):.1f}%"),
                ("Aktuelle Serie", card.consecutive_correct),
                ("Schwierigkeitsgrad", f"{card.difficulty_rating:.1f}/5.0"),
                ("Nächste Wiederholung", card.next_review),
                ("Letzte Wiederholung", card.last_reviewed),
                ("Kategorie", f"{card.category} > {card.subcategory}"),
                ("Tags", ", ".join(card.tags) if card.tags else "Keine")
            ]
            
            for label, value in stats:
                row = ctk.CTkFrame(stats_frame)
                row.pack(fill='x', pady=5)
                ctk.CTkLabel(
                    row, 
                    text=f"{label}:", 
                    font=ctk.CTkFont(size=12, weight="bold")
                ).pack(side='left', padx=5)
                ctk.CTkLabel(
                    row, 
                    text=str(value), 
                    font=ctk.CTkFont(size=12)
                ).pack(side='right', padx=5)
            
            # SchlieÃƒÅ¸en-Button
            close_btn = ctk.CTkButton(
                stats_window,
                text="SchlieÃƒÅ¸en",
                command=stats_window.destroy,
                width=100
            )
            close_btn.pack(pady=10)
            
            # TastenkÃƒÂ¼rzel zum SchlieÃƒÅ¸en
            stats_window.bind('<Escape>', lambda e: stats_window.destroy())
    def apply_card_management_filters(self):
        """Liest alle Filter (Kategorie, Subkategorie, Suche) aus und aktualisiert die Kartenanzeige."""
        try:
            category = self.category_var.get()
            subcategory = self.subcategory_var.get()
            search_term = self.search_var.get().strip()

            # Filtere Kategorie und Subkategorie für die Anzeige
            category_filter = category if category not in [None, "Bitte wählen..."] else None
            subcategory_filter = subcategory if subcategory not in [None, "Bitte wählen...", "Bitte zuerst Kategorie wählen", "Keine Unterkategorien verfügbar"] else None

            # Rufe die (modifizierte) Anzeigemethode auf
            self.display_filtered_cards(
                category=category_filter,
                subcategory=subcategory_filter,
                page=1, # Starte immer auf Seite 1 bei neuer Filterung/Suche
                search_term=search_term if search_term else None # Nur Suchbegriff übergeben, wenn vorhanden
            )
        except AttributeError as e:
            logging.error(f"Fehler beim Zugriff auf Filtervariablen: {e}. Wurden sie initialisiert?")
            messagebox.showerror("Fehler", "Filter konnten nicht angewendet werden. Variablen fehlen.")
        except Exception as e:
            logging.error(f"Unerwarteter Fehler beim Anwenden der Filter: {e}")
            messagebox.showerror("Fehler", "Ein Fehler ist beim Filtern aufgetreten.")
        

    def edit_card(self, card):
        """Bearbeitet eine Karte mit mehrzeiligen Textfeldern und Bild-Support für beide Seiten."""
        self._clear_content_frame()

        # Moderner Header mit Gradient-Hintergrund
        header_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='#8b5cf6',
            corner_radius=0,
            height=110
        )
        header_container.pack(fill='x', pady=(0, 20))
        header_container.pack_propagate(False)

        header_content = ctk.CTkFrame(header_container, fg_color='transparent')
        header_content.place(relx=0.5, rely=0.5, anchor='center')

        # Icon und Titel
        icon_title_frame = ctk.CTkFrame(header_content, fg_color='transparent')
        icon_title_frame.pack()

        ctk.CTkLabel(
            icon_title_frame,
            text="✏️",
            font=ctk.CTkFont(size=36),
            text_color='#ffffff'
        ).pack(side='left', padx=(0, 15))

        title_frame = ctk.CTkFrame(icon_title_frame, fg_color='transparent')
        title_frame.pack(side='left')

        ctk.CTkLabel(
            title_frame,
            text="Karte bearbeiten",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color='#ffffff'
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_frame,
            text="Bearbeite Frage, Antwort und weitere Details deiner Lernkarte",
            font=ctk.CTkFont(size=13),
            text_color='#e9d5ff'
        ).pack(anchor='w')

        # Scrollbarer Container
        edit_container = ctk.CTkScrollableFrame(self.content_frame)
        edit_container.pack(fill='both', expand=True, padx=20, pady=10)

        # === FRAGE SEKTION ===
        question_section = ctk.CTkFrame(
            edit_container,
            fg_color='#f0fdf4',
            corner_radius=15,
            border_width=2,
            border_color='#10b981'
        )
        question_section.pack(fill='x', pady=(0, 20))

        # Header der Frage-Sektion mit Icon
        question_header = ctk.CTkFrame(question_section, fg_color='transparent')
        question_header.pack(fill='x', pady=(15, 10), padx=15)

        ctk.CTkLabel(
            question_header,
            text="❓",
            font=ctk.CTkFont(size=24)
        ).pack(side='left', padx=(0, 10))

        ctk.CTkLabel(
            question_header,
            text="FRAGE",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color='#047857'
        ).pack(side='left')
        
        # Frage-Text (mehrzeilig)
        ctk.CTkLabel(
            question_section,
            text="Fragentext:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#065f46'
        ).pack(anchor='w', padx=15, pady=(5, 5))

        question_textbox = ctk.CTkTextbox(
            question_section,
            width=600,
            height=120,
            wrap='word',
            font=ctk.CTkFont(size=14),
            corner_radius=10,
            border_width=2,
            border_color='#10b981'
        )
        question_textbox.insert("1.0", card.question)
        question_textbox.pack(padx=15, pady=(0, 15), fill='x')

        # Frage-Bild
        ctk.CTkLabel(
            question_section,
            text="🖼️ Bild zur Frage (optional):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#065f46'
        ).pack(anchor='w', padx=15, pady=(10, 5))
        question_image_var = tk.StringVar(value=getattr(card, 'question_image_path', '') or '')
        
        question_img_frame = ctk.CTkFrame(question_section, fg_color="transparent")
        question_img_frame.pack(fill='x', padx=15, pady=(0, 15))

        question_img_entry = ctk.CTkEntry(
            question_img_frame,
            textvariable=question_image_var,
            state='readonly',
            width=350,
            height=36,
            corner_radius=10,
            border_width=2,
            border_color='#10b981'
        )
        question_img_entry.pack(side='left', padx=(0, 10))

        def choose_question_image():
            file_path = filedialog.askopenfilename(
                title="Bild für Frage auswählen",
                filetypes=[("Bilder", "*.jpg *.jpeg *.png *.gif *.bmp"), ("Alle", "*.*")]
            )
            if file_path:
                question_image_var.set(file_path)

        ctk.CTkButton(
            question_img_frame,
            text="📁 Bild wählen",
            command=choose_question_image,
            width=140,
            height=36,
            corner_radius=10,
            fg_color='#10b981',
            hover_color='#059669',
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            question_img_frame,
            text="🗑️ Entfernen",
            command=lambda: question_image_var.set(""),
            width=120,
            height=36,
            corner_radius=10,
            fg_color="#6b7280",
            hover_color="#4b5563",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side='left')

        # === ANTWORT SEKTION ===
        answer_section = ctk.CTkFrame(
            edit_container,
            fg_color='#eff6ff',
            corner_radius=15,
            border_width=2,
            border_color='#3b82f6'
        )
        answer_section.pack(fill='x', pady=(0, 20))

        # Header der Antwort-Sektion mit Icon
        answer_header = ctk.CTkFrame(answer_section, fg_color='transparent')
        answer_header.pack(fill='x', pady=(15, 10), padx=15)

        ctk.CTkLabel(
            answer_header,
            text="✅",
            font=ctk.CTkFont(size=24)
        ).pack(side='left', padx=(0, 10))

        ctk.CTkLabel(
            answer_header,
            text="ANTWORT",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color='#1e40af'
        ).pack(side='left')

        # Antwort-Text (mehrzeilig)
        ctk.CTkLabel(
            answer_section,
            text="Antworttext:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#1e3a8a'
        ).pack(anchor='w', padx=15, pady=(5, 5))

        answer_textbox = ctk.CTkTextbox(
            answer_section,
            width=600,
            height=120,
            wrap='word',
            font=ctk.CTkFont(size=14),
            corner_radius=10,
            border_width=2,
            border_color='#3b82f6'
        )
        answer_textbox.insert("1.0", card.answer)
        answer_textbox.pack(padx=15, pady=(0, 15), fill='x')

        # Antwort-Bild
        ctk.CTkLabel(
            answer_section,
            text="🖼️ Bild zur Antwort (optional):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#1e3a8a'
        ).pack(anchor='w', padx=15, pady=(10, 5))
        answer_image_var = tk.StringVar(value=card.image_path or '')
        
        answer_img_frame = ctk.CTkFrame(answer_section, fg_color="transparent")
        answer_img_frame.pack(fill='x', padx=15, pady=(0, 15))

        answer_img_entry = ctk.CTkEntry(
            answer_img_frame,
            textvariable=answer_image_var,
            state='readonly',
            width=350,
            height=36,
            corner_radius=10,
            border_width=2,
            border_color='#3b82f6'
        )
        answer_img_entry.pack(side='left', padx=(0, 10))

        def choose_answer_image():
            file_path = filedialog.askopenfilename(
                title="Bild für Antwort auswählen",
                filetypes=[("Bilder", "*.jpg *.jpeg *.png *.gif *.bmp"), ("Alle", "*.*")]
            )
            if file_path:
                answer_image_var.set(file_path)

        ctk.CTkButton(
            answer_img_frame,
            text="📁 Bild wählen",
            command=choose_answer_image,
            width=140,
            height=36,
            corner_radius=10,
            fg_color='#3b82f6',
            hover_color='#2563eb',
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            answer_img_frame,
            text="🗑️ Entfernen",
            command=lambda: answer_image_var.set(""),
            width=120,
            height=36,
            corner_radius=10,
            fg_color="#6b7280",
            hover_color="#4b5563",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side='left')

        # === KATEGORIEN ===
        meta_section = ctk.CTkFrame(
            edit_container,
            fg_color='#fef3c7',
            corner_radius=15,
            border_width=2,
            border_color='#f59e0b'
        )
        meta_section.pack(fill='x', pady=(0, 20))

        # Header der Kategorisierungs-Sektion mit Icon
        meta_header = ctk.CTkFrame(meta_section, fg_color='transparent')
        meta_header.pack(fill='x', pady=(15, 10), padx=15)

        ctk.CTkLabel(
            meta_header,
            text="🏷️",
            font=ctk.CTkFont(size=24)
        ).pack(side='left', padx=(0, 10))

        ctk.CTkLabel(
            meta_header,
            text="KATEGORISIERUNG",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color='#92400e'
        ).pack(side='left')
        
        # Kategorie
        cat_frame = ctk.CTkFrame(meta_section, fg_color="transparent")
        cat_frame.pack(fill='x', padx=15, pady=(5, 10))

        ctk.CTkLabel(
            cat_frame,
            text="Kategorie:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#92400e',
            width=140
        ).pack(side='left')

        edit_category_var = tk.StringVar(value=card.category)
        all_categories = sorted(self.data_manager.categories.keys())
        category_menu = ctk.CTkOptionMenu(
            cat_frame,
            variable=edit_category_var,
            values=all_categories if all_categories else ["Keine Kategorien"],
            width=220,
            height=36,
            corner_radius=10,
            fg_color='#f59e0b',
            button_color='#d97706',
            button_hover_color='#b45309',
            font=ctk.CTkFont(size=12)
        )
        category_menu.pack(side='left', padx=10)

        # Unterkategorie
        subcat_frame = ctk.CTkFrame(meta_section, fg_color="transparent")
        subcat_frame.pack(fill='x', padx=15, pady=(0, 10))

        ctk.CTkLabel(
            subcat_frame,
            text="Unterkategorie:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#92400e',
            width=140
        ).pack(side='left')

        edit_subcategory_var = tk.StringVar(value=card.subcategory)
        subcategory_menu = ctk.CTkOptionMenu(
            subcat_frame,
            variable=edit_subcategory_var,
            values=["Bitte Kategorie wählen"],
            width=220,
            height=36,
            corner_radius=10,
            fg_color='#f59e0b',
            button_color='#d97706',
            button_hover_color='#b45309',
            font=ctk.CTkFont(size=12)
        )
        subcategory_menu.pack(side='left', padx=10)
        
        def update_subcategories(*args):
            selected_cat = edit_category_var.get()
            if selected_cat and selected_cat != "Keine Kategorien":
                subcats = sorted(self.data_manager.categories.get(selected_cat, {}).keys())
                subcategory_menu.configure(values=subcats if subcats else ["Keine Unterkategorien"])
            else:
                subcategory_menu.configure(values=["Bitte Kategorie wählen"])
        
        edit_category_var.trace_add('write', update_subcategories)
        update_subcategories()
        
        # Tags
        tags_frame = ctk.CTkFrame(meta_section, fg_color="transparent")
        tags_frame.pack(fill='x', padx=15, pady=(0, 15))

        ctk.CTkLabel(
            tags_frame,
            text="Tags:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#92400e',
            width=140
        ).pack(side='left')

        tags_entry = ctk.CTkEntry(
            tags_frame,
            width=350,
            height=36,
            corner_radius=10,
            border_width=2,
            border_color='#f59e0b',
            font=ctk.CTkFont(size=12)
        )
        tags_entry.insert(0, ', '.join(card.tags))
        tags_entry.pack(side='left', padx=10)

        # === BUTTONS ===
        button_frame = ctk.CTkFrame(edit_container, fg_color="transparent")
        button_frame.pack(pady=20)

        def save_changes():
            new_question = question_textbox.get("1.0", "end-1c").strip()
            new_answer = answer_textbox.get("1.0", "end-1c").strip()
            new_category = edit_category_var.get()
            new_subcategory = edit_subcategory_var.get()
            new_tags = [t.strip() for t in tags_entry.get().split(',') if t.strip()]
            new_question_img = question_image_var.get()
            new_answer_img = answer_image_var.get()

            if not new_question:
                messagebox.showwarning("Warnung", "Frage darf nicht leer sein.")
                return
            
            if not new_answer and not new_answer_img:
                messagebox.showwarning("Warnung", "Antwort (Text oder Bild) erforderlich.")
                return

            try:
                # Bilder verarbeiten
                if new_question_img and new_question_img != getattr(card, 'question_image_path', ''):
                    card.question_image_path = self.data_manager.handle_image(new_question_img)
                elif not new_question_img:
                    card.question_image_path = None
                    
                if new_answer_img and new_answer_img != card.image_path:
                    card.image_path = self.data_manager.handle_image(new_answer_img)
                elif not new_answer_img:
                    card.image_path = None

                # Karte aktualisieren
                card.question = new_question
                card.answer = new_answer
                card.category = new_category
                card.subcategory = new_subcategory
                card.tags = new_tags

                self.data_manager.save_flashcards()
                messagebox.showinfo("Erfolg", "Karte wurde aktualisiert!")
                self.show_card_details_manager()
                
            except Exception as e:
                logging.error(f"Fehler beim Speichern: {e}")
                messagebox.showerror("Fehler", f"Beim Speichern ist ein Fehler aufgetreten: {e}")

        ctk.CTkButton(
            button_frame,
            text="💾 Änderungen speichern",
            command=save_changes,
            width=220,
            height=45,
            corner_radius=12,
            fg_color='#10b981',
            hover_color='#059669',
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side='left', padx=10)

        ctk.CTkButton(
            button_frame,
            text="❌ Abbrechen",
            command=self.show_card_details_manager,
            width=180,
            height=45,
            corner_radius=12,
            fg_color="#6b7280",
            hover_color="#4b5563",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side='left', padx=10)

    # Hilfsmethode zum Wiederherstellen der Filter nach Bearbeitung/Abbruch
    def restore_card_management_filters(self, category, subcategory, search_term, page):
        """Setzt die Filter-Widgets und lädt die Karten für die gegebene Seite."""
        try:
            if hasattr(self, 'category_var'):
                 self.category_var.set(category if category else "Alle")
                 # Manuelles Triggern des Updates für Subkategorien, falls Kategorie nicht "Alle"
                 if category and category != "Alle":
                     self.update_subcategories_srs() # Oder eine generische Update-Funktion
                 # Kurze Verzögerung, damit das Subkategorie-Menü aktualisiert ist
                 self.master.after(100, lambda: self.subcategory_var.set(subcategory if subcategory else "Alle") if hasattr(self, 'subcategory_var') else None)

            if hasattr(self, 'search_var'):
                 self.search_var.set(search_term if search_term else "")

            # Lade die spezifische Seite neu mit den wiederhergestellten Filtern
            self.master.after(200, lambda: self.display_filtered_cards(
                category=category if category else "Alle",
                subcategory=subcategory if subcategory else "Alle",
                page=page,
                search_term=search_term if search_term else None
            ))
            logging.info(f"Filter wiederhergestellt: Kat={category}, SubKat={subcategory}, Suche={search_term}, Seite={page}")
        except Exception as e:
            logging.error(f"Fehler beim Wiederherstellen der Filter: {e}")

    def _update_flashcard_from_leitner(self, flashcard_obj: Flashcard, leitner_card: LeitnerCard):
        """
        Aktualisiert die Leitner-Attribute eines Flashcard-Objekts
        basierend auf dem Zustand eines LeitnerCard-Objekts.
        Konvertiert datetime-Objekte in ISO-Strings für die Speicherung.
        """
        if not flashcard_obj or not leitner_card:
            logging.warning("Versuch, Flashcard von ungültigem LeitnerCard/Flashcard zu aktualisieren.")
            return

        try:
            # Datums-Objekte sicher in Strings umwandeln
            lr_obj = leitner_card.last_reviewed
            nr_obj = leitner_card.next_review_date
            lr_val_after = lr_obj.isoformat() if isinstance(lr_obj, (datetime.datetime, datetime.date)) else None
            nr_val_after = nr_obj.isoformat() if isinstance(nr_obj, (datetime.datetime, datetime.date)) else None

            # Attribute des Flashcard-Objekts aktualisieren
            flashcard_obj.leitner_points = leitner_card.points
            flashcard_obj.leitner_level = leitner_card.level
            flashcard_obj.leitner_positive_streak = leitner_card.positive_streak
            flashcard_obj.leitner_negative_streak = leitner_card.negative_streak
            flashcard_obj.leitner_last_reviewed = lr_val_after
            flashcard_obj.leitner_next_review_date = nr_val_after
            flashcard_obj.leitner_in_recovery_mode = leitner_card.in_recovery_mode
            flashcard_obj.leitner_recovery_interval = leitner_card.recovery_interval
            
            # KORREKTUR: Erfolgshistorie ebenfalls synchronisieren
            flashcard_obj.leitner_success_history = list(leitner_card.success_history)

        except AttributeError as e:
            logging.error(f"Attributfehler beim Aktualisieren der Flashcard {flashcard_obj.id} von Leitner: {e}")
        except Exception as e:
            logging.exception(f"Unerwarteter Fehler beim Aktualisieren der Flashcard {flashcard_obj.id} von Leitner.")

    def display_filtered_cards(self, category, subcategory, page=1, cards_per_page=30, search_term=None):
        """Zeigt die gefilterten Karten im Grid-Layout an, berücksichtigt Suche und Paginierung."""
        try:
            # Speichere aktuelle Filter-Einstellungen
            self.last_category = category if category else "Alle"
            self.last_subcategory = subcategory if subcategory else "Alle"
            self.current_page = page # Aktuelle Seite merken

            # === Kartenfilterung (wie zuvor) ===
            subcat_filter = subcategory if subcategory and subcategory != "Alle" else None
            cat_filter = category if category and category != "Alle" else None
            base_filtered_cards = self.data_manager.filter_flashcards_by_category_and_subcategory(cat_filter, subcat_filter)

            if search_term:
                search_term_lower = search_term.lower()
                filtered_cards = [
                    card for card in base_filtered_cards
                    if search_term_lower in card.question.lower() or \
                       search_term_lower in card.answer.lower() or \
                       any(search_term_lower in tag.lower() for tag in getattr(card, 'tags', []))
                ]
            else:
                filtered_cards = base_filtered_cards

            # Speichere die VOLLSTÄNDIGE gefilterte Liste
            self.currently_displayed_filtered_cards = filtered_cards

            # === Paginierung ===
            start_idx = (page - 1) * cards_per_page
            end_idx = start_idx + cards_per_page
            current_cards_to_display = filtered_cards[start_idx:end_idx]

            # === Kartenanzeige ===

            # 1. Scroll-Frame sicher holen oder neu erstellen
            # Prüfe, ob der Frame existiert UND zum cards_display_container gehört
            # Stelle sicher, dass cards_display_container existiert (wird in show_card_details_manager erstellt)
            if not hasattr(self, 'cards_display_container') or not self.cards_display_container.winfo_exists():
                 logging.error("cards_display_container existiert nicht in display_filtered_cards. Breche ab.")
                 # Optional: Nachricht an Benutzer
                 # messagebox.showerror("UI Fehler", "Anzeigebereich für Karten nicht gefunden.")
                 return

            create_new_scroll_frame = True
            if hasattr(self, 'scroll_frame_manage') and \
               self.scroll_frame_manage.winfo_exists() and \
               self.scroll_frame_manage.master == self.cards_display_container:
                if page == 1: # Nur auf Seite 1 alles löschen
                     logging.debug("Seite 1: Leere bestehenden Scroll-Frame.")
                     for widget in self.scroll_frame_manage.winfo_children():
                        widget.destroy()
                     # Scroll-Position zurücksetzen
                     self.scroll_frame_manage._parent_canvas.yview_moveto(0.0)
                else: # Auf Folgeseiten nur weiternutzen
                    logging.debug(f"Seite {page}: Verwende bestehenden Scroll-Frame weiter.")
                    create_new_scroll_frame = False
            else: # Wenn Frame fehlt oder falsch platziert ist
                 if hasattr(self, 'scroll_frame_manage') and self.scroll_frame_manage.winfo_exists():
                     logging.warning("Altes scroll_frame_manage gefunden, wird zerstört.")
                     self.scroll_frame_manage.destroy() # Altes Frame sicher entfernen
                 create_new_scroll_frame = True


            if create_new_scroll_frame:
                logging.debug("Erstelle neuen Scroll-Frame.")
                self.scroll_frame_manage = ctk.CTkScrollableFrame(self.cards_display_container)
                # Wichtig: .grid statt .pack verwenden, damit es in cards_display_container passt
                self.scroll_frame_manage.grid(row=0, column=0, sticky="nsew")
                # Konfiguriere Grid im ScrollFrame selbst
                max_cols = 2 # Spalten im Grid des ScrollFrames
                for i in range(max_cols):
                    self.scroll_frame_manage.grid_columnconfigure(i, weight=1) # Spalten gleichmÃƒÂ¤ÃƒÅ¸ig verteilen


            # 2. PrÃƒÂ¼fen, ob Karten vorhanden sind
            if not filtered_cards and page == 1:
                logging.debug("Keine Karten gefunden für Filter.")
                # Lösche alten ScrollFrame, falls er leer ist
                if hasattr(self, 'scroll_frame_manage') and self.scroll_frame_manage.winfo_exists():
                   self.scroll_frame_manage.destroy()
                   del self.scroll_frame_manage

                # Nachricht direkt im Container anzeigen
                ctk.CTkLabel(
                    self.cards_display_container,
                    text="Keine Karten für die gewÃƒÂ¤hlten Filter gefunden.",
                    font=ctk.CTkFont(size=14)
                ).grid(row=0, column=0, pady=20) # Platziere im Grid des Containers

                # Paginierungs-Frame leeren
                # Stelle sicher, dass der Container existiert
                if hasattr(self, 'bottom_frame_manage_container') and self.bottom_frame_manage_container.winfo_exists():
                     for widget in self.bottom_frame_manage_container.winfo_children():
                        widget.destroy()
                return

            # 3. Karten im Grid des ScrollFrames anzeigen
            # Startreihe wird nicht mehr benötigt, da grid() im ScrollFrame verwendet wird
            max_cols = 2
            logging.debug(f"Zeige Karten {start_idx+1} bis {min(end_idx, len(filtered_cards))} an.")
            for i, card in enumerate(current_cards_to_display):
                 # Aktuelle Reihe und Spalte im Grid des *ScrollFrames*
                 current_row = i // max_cols
                 current_col = i % max_cols

                 if not hasattr(self, 'scroll_frame_manage') or not self.scroll_frame_manage.winfo_exists():
                     logging.error("Scroll-Frame existiert nicht mehr beim Anzeigen der Karten.")
                     break

                 card_frame = ctk.CTkFrame(self.scroll_frame_manage, border_width=1, border_color=("gray70", "gray30"))
                 # Verwende grid für die Karten-Frames *innerhalb* des Scroll-Frames
                 card_frame.grid(row=current_row, column=current_col, padx=10, pady=10, sticky="nsew")

                 # --- Inhalt der Karte (wie zuvor) ---
                 main_info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
                 main_info_frame.pack(fill='x', padx=10, pady=5)
                 # ... (Code für Info-Label, Frage, Antwort, Kategorie, Tags - bleibt gleich) ...
                 leitner_card_obj = self.leitner_system.cards.get(card.id) if hasattr(self, 'leitner_system') else None
                 info_text_parts = []
                 if leitner_card_obj:
                     leitner_status = self.leitner_system.get_card_status(leitner_card_obj)
                     level_name = self.leitner_system.get_level(leitner_status['points'])
                     info_text_parts.append(f"L-Level: {leitner_status['level']}. {level_name}")
                     info_text_parts.append(f"L-Punkte: {leitner_status['points']}")
                     if leitner_status['days_overdue'] > 0:
                          info_text_parts.append(f"Überfällig: {leitner_status['days_overdue']} T.")
                 else:
                     info_text_parts.append(f"Wdh.: {getattr(card, 'repetitions', 0)}")
                     srs_success_rate = (getattr(card, 'success_count', 0) / max(1, getattr(card, 'repetitions', 1)) * 100)
                     info_text_parts.append(f"Erfolg: {srs_success_rate:.0f}%")
                     info_text_parts.append(f"Schwierigk.: {getattr(card, 'difficulty_rating', 3.0):.1f}")

                 info_text = " | ".join(info_text_parts)
                 ctk.CTkLabel(main_info_frame, text=info_text, font=ctk.CTkFont(size=10)).pack(anchor='w')
                 ctk.CTkLabel(main_info_frame, text=f"F: {getattr(card, 'question', '')}", font=ctk.CTkFont(size=12, weight="bold"), wraplength=350, anchor="w", justify="left").pack(anchor='w', fill='x')
                 answer_text = getattr(card, 'answer', '')
                 if len(answer_text) > 60: answer_text = answer_text[:60] + "..."
                 ctk.CTkLabel(main_info_frame, text=f"A: {answer_text}", font=ctk.CTkFont(size=12), wraplength=350, anchor="w", justify="left").pack(anchor='w', fill='x')
                 ctk.CTkLabel(main_info_frame, text=f"Kat: {getattr(card, 'category', '')} > {getattr(card, 'subcategory', '')}", font=ctk.CTkFont(size=10), wraplength=350, anchor="w", justify="left").pack(anchor='w', fill='x')
                 if hasattr(card, 'tags') and card.tags:
                    ctk.CTkLabel(main_info_frame, text=f"Tags: {', '.join(card.tags)}", font=ctk.CTkFont(size=10), wraplength=350, anchor="w", justify="left").pack(anchor='w', fill='x')

                 # --- Ende Inhalt der Karte ---

                 content_display_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
                 content_display_frame.pack(fill='x', padx=10, pady=5)

                 btn_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
                 btn_frame.pack(fill='x', padx=10, pady=5)

                 # --- Buttons (modernisiert) ---
                 stats_btn = ctk.CTkButton(
                     btn_frame,
                     text="📊",
                     command=lambda frm=content_display_frame, c=card: self.show_stats_inline(frm, c),
                     width=40,
                     height=32,
                     corner_radius=8,
                     fg_color='#3b82f6',
                     hover_color='#2563eb',
                     font=ctk.CTkFont(size=16)
                 )
                 stats_btn.pack(side='left', padx=3)

                 image_path = getattr(card, 'image_path', None)
                 # Baue den vollständigen, absoluten Pfad zum Bild
                 absolute_image_path = None
                 if image_path and self.data_manager.images_dir:
                     absolute_image_path = os.path.join(self.data_manager.images_dir, image_path)

                 if absolute_image_path and os.path.exists(absolute_image_path):
                      img_btn = ctk.CTkButton(
                          btn_frame,
                          text="🖼️",
                          command=lambda frm=content_display_frame, p=absolute_image_path: self.show_image_inline(frm, p),
                          width=40,
                          height=32,
                          corner_radius=8,
                          fg_color='#8b5cf6',
                          hover_color='#7c3aed',
                          font=ctk.CTkFont(size=16)
                      )
                      img_btn.pack(side='left', padx=3)
                 elif image_path: # Pfad existiert in Daten, aber Datei nicht
                      logging.warning(f"Bildpfad in Karte {card.id} angegeben, aber Datei nicht gefunden: {absolute_image_path}")

                 edit_btn = ctk.CTkButton(
                     btn_frame,
                     text="✏️",
                     command=lambda c=card: self.edit_card(c),
                     width=40,
                     height=32,
                     corner_radius=8,
                     fg_color='#10b981',
                     hover_color='#059669',
                     font=ctk.CTkFont(size=16)
                 )
                 edit_btn.pack(side='left', padx=3)

                 delete_btn = ctk.CTkButton(
                     btn_frame,
                     text="🗑️",
                     command=lambda c=card: self.confirm_delete_card(c),
                     width=40,
                     height=32,
                     corner_radius=8,
                     fg_color="#ef4444",
                     hover_color="#dc2626",
                     font=ctk.CTkFont(size=16)
                 )
                 delete_btn.pack(side='left', padx=3)
                 # --- Ende Buttons ---


            # --- "Mehr laden"-Button im Paginierungs-Container ---
            # Alten Button lÃƒÂ¶schen
            # Stelle sicher, dass der Container existiert
            if hasattr(self, 'bottom_frame_manage_container') and self.bottom_frame_manage_container.winfo_exists():
                for widget in self.bottom_frame_manage_container.winfo_children():
                    widget.destroy()
            else:
                 # Erstelle den Container neu, falls er fehlt
                 logging.warning("bottom_frame_manage_container fehlte, wird neu erstellt.")
                 self.bottom_frame_manage_container = ctk.CTkFrame(self.manager_container, fg_color="transparent") # Korrekter Parent
                 self.bottom_frame_manage_container.grid(row=2, column=0, sticky='ew', padx=20, pady=(5, 10))
                 self.bottom_frame_manage_container.grid_columnconfigure(0, weight=1) # Button zentrieren


            # Nur neuen Button erstellen, wenn noch mehr Karten geladen werden können
            if end_idx < len(filtered_cards):
                load_more_btn = ctk.CTkButton(
                    self.bottom_frame_manage_container,
                    text=f"⬇️ Mehr laden ({len(filtered_cards) - end_idx} übrig)",
                    command=lambda cat=category, subcat=subcategory, p=page + 1, st=search_term: self.display_filtered_cards(cat, subcat, p, cards_per_page, st),
                    height=40,
                    corner_radius=10,
                    fg_color='#3b82f6',
                    hover_color='#2563eb',
                    font=ctk.CTkFont(size=13, weight="bold")
                )
                # Zentriere den Button im Container
                load_more_btn.grid(row=0, column=0, pady=5)

        except Exception as e:
            logging.error(f"Fehler in display_filtered_cards: {e}")
            import traceback
            logging.error(traceback.format_exc())
            messagebox.showerror("Fehler", f"Fehler beim Anzeigen der Karten: {e}")

            # --- Ende Kartenanzeige-Code ---

            # --- "Mehr laden"-Button ---
            # Alten Frame lÃƒÂ¶schen, falls vorhanden (wichtig für korrekte Platzierung)
            if hasattr(self, 'bottom_frame_manage') and self.bottom_frame_manage.winfo_exists():
                self.bottom_frame_manage.destroy()
                if hasattr(self, 'bottom_frame_manage'): # PrÃƒÂ¼fe nochmal nach destroy
                    del self.bottom_frame_manage

            # Nur neuen Frame erstellen, wenn noch mehr Karten geladen werden können
            if end_idx < len(filtered_cards):
                self.bottom_frame_manage = ctk.CTkFrame(content_container) # Im Haupt-Container erstellen
                self.bottom_frame_manage.pack(side='bottom', fill='x', pady=(5,0)) # Direkt unter dem Scroll-Frame

                load_more_btn = ctk.CTkButton(
                    self.bottom_frame_manage,
                    text=f"⬇️ Mehr laden ({len(filtered_cards) - end_idx} übrig)",
                    command=lambda cat=category, subcat=subcategory, p=page + 1, st=search_term: self.display_filtered_cards(cat, subcat, p, cards_per_page, st),
                    height=40,
                    corner_radius=10,
                    fg_color='#3b82f6',
                    hover_color='#2563eb',
                    font=ctk.CTkFont(size=13, weight="bold")
                )
                load_more_btn.pack(pady=5, padx=20) # Zentriert

        except Exception as e:
            logging.error(f"Fehler in display_filtered_cards: {e}")
            import traceback
            logging.error(traceback.format_exc())
            messagebox.showerror("Fehler", f"Fehler beim Anzeigen der Karten: {e}")

    # FÃƒÂ¼ge diese Methode zur FlashcardApp-Klasse hinzu (gleiche Ebene wie __init__)
    def show_stats_inline(self, frame, card):
        """Zeigt Statistiken für eine einzelne Karte inline im angegebenen Frame an."""
        logging.debug(f"Zeige Inline-Stats für: {card.question}")

        # Lösche vorherige Inhalte im Frame
        for widget in frame.winfo_children():
            widget.destroy()

        # Hole Leitner-Status (falls es eine LeitnerCard ist)
        is_leitner_card = isinstance(card, LeitnerCard)
        leitner_status = None
        if is_leitner_card and hasattr(self, 'leitner_system'):
            leitner_status = self.leitner_system.get_card_status(card)

        # Basis-Flashcard-Status (immer vorhanden)
        srs_status = {
            'repetitions': getattr(card, 'repetitions', 0),
            'success_count': getattr(card, 'success_count', 0),
            'consecutive_correct': getattr(card, 'consecutive_correct', 0),
            'difficulty_rating': getattr(card, 'difficulty_rating', 3.0),
            'next_review': getattr(card, 'next_review', 'N/A'),
            'last_reviewed': getattr(card, 'last_reviewed', 'N/A')
        }
        success_rate = (srs_status['success_count'] / srs_status['repetitions'] * 100) if srs_status['repetitions'] > 0 else 0

        # --- Detaillierte Statistik-Liste ---
        stats_data = [
            ("Wiederholungen (SRS)", srs_status['repetitions']),
            ("Richtige Antworten (SRS)", srs_status['success_count']),
            ("Erfolgsquote (SRS)", f"{success_rate:.1f}%"),
            ("Aktuelle Serie (SRS)", srs_status['consecutive_correct']),
            ("Schwierigkeit (SRS)", f"{srs_status['difficulty_rating']:.1f}/5.0"),
            ("Nächste Wiederholung (SRS)", srs_status['next_review']),
            ("Letzte Wiederholung (SRS)", srs_status['last_reviewed']),
        ]

        # FÃƒÂ¼ge Leitner-Stats hinzu, falls vorhanden und Karte eine LeitnerCard ist
        if is_leitner_card and leitner_status:
            level_name = self.leitner_system.get_level(leitner_status['points'])
            leitner_stats_specific = [
                ("--- Leitner System ---", ""), # Trennlinie
                ("Leitner Level", f"{leitner_status['level']}. {level_name}"),
                ("Leitner Punkte", leitner_status['points']),
                ("Leitner Positiv-Serie", getattr(card, 'positive_streak', 'N/A')),
                ("Leitner Negativ-Serie", getattr(card, 'negative_streak', 'N/A')),
                ("Leitner Wiederaufbau", 'Ja' if getattr(card, 'in_recovery_mode', False) else 'Nein'),
                ("Nächste Wiederholung (Leitner)", leitner_status['next_review_date'].strftime('%d.%m.%Y') if isinstance(leitner_status.get('next_review_date'), (datetime.date, datetime.datetime)) else 'N/A'),
                ("Letzte Wiederholung (Leitner)", leitner_status['last_reviewed'].strftime('%d.%m.%Y %H:%M') if isinstance(leitner_status.get('last_reviewed'), datetime.datetime) else 'N/A'),
                ("Tage Überfällig (Leitner)", leitner_status['days_overdue'])
            ]
            stats_data.extend(leitner_stats_specific)
        # --- Ende der Statistik-Liste ---

        # Erstelle ein Grid innerhalb des Frames für die Statistik-Anzeige
        stats_grid_frame = ctk.CTkFrame(frame, fg_color="transparent")
        stats_grid_frame.pack(fill='x')

        for idx, (label, value) in enumerate(stats_data):
             # Wenn es nur ein Trenner ist, mache ihn breiter
            if value == "":
                 ctk.CTkLabel(
                     stats_grid_frame,
                     text=label,
                     font=ctk.CTkFont(size=10, weight="bold"),
                     anchor="w"
                 ).grid(row=idx, column=0, columnspan=2, sticky="ew", padx=5, pady=1)
            else:
                # Normale Zeile
                lbl = ctk.CTkLabel(
                    stats_grid_frame,
                    text=f"{label}:",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    anchor="w"
                )
                lbl.grid(row=idx, column=0, sticky="w", padx=5, pady=1)

                val_lbl = ctk.CTkLabel(
                    stats_grid_frame,
                    text=str(value),
                    font=ctk.CTkFont(size=10),
                    anchor="e" # RechtsbÃƒÂ¼ndig
                )
                val_lbl.grid(row=idx, column=1, sticky="e", padx=5, pady=1)

        # Stelle sicher, dass die Spalten sich anpassen
        stats_grid_frame.grid_columnconfigure(0, weight=1)
        stats_grid_frame.grid_columnconfigure(1, weight=1)
    def show_image_inline(self, frame, image_path):
        """Zeigt eine Bildvorschau inline an mit modernem Design."""
        # Lösche vorherige Inhalte
        for widget in frame.winfo_children():
            widget.destroy()

        if not image_path or not os.path.exists(image_path):
             logging.warning(f"Bildpfad ungültig oder nicht gefunden: {image_path}")
             ctk.CTkLabel(
                 frame,
                 text="📷 Kein Bild vorhanden",
                 font=ctk.CTkFont(size=13),
                 text_color="gray"
             ).pack(pady=20)
             return

        try:
            image = Image.open(image_path)
            # Maximale Größe für das Vorschaubild
            max_size = (400, 300)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Moderner Container mit Rahmen
            image_container = ctk.CTkFrame(
                frame,
                fg_color=("white", "gray20"),
                corner_radius=15,
                border_width=2,
                border_color=("#8b5cf6", "#a78bfa")
            )
            image_container.pack(expand=True, fill='both', padx=10, pady=10)

            # Verwende CTkImage für bessere Theme-Integration
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)

            image_label = ctk.CTkLabel(
                image_container,
                text="",
                image=ctk_image,
                corner_radius=13
            )
            image_label.image = ctk_image # Referenz behalten!
            image_label.pack(expand=True, fill='both', padx=5, pady=5)

            # Moderner Button zum Vergrößern
            enlarge_btn = ctk.CTkButton(
                image_container,
                text="🔍 Bild vergrößern",
                command=lambda p=image_path: self._show_fullscreen_image(p),
                height=32,
                corner_radius=10,
                fg_color=("#8b5cf6", "#7c3aed"),
                hover_color=("#7c3aed", "#6d28d9"),
                font=ctk.CTkFont(size=13, weight="bold")
            )
            enlarge_btn.pack(pady=(5, 10), padx=10)

        except Exception as e:
            logging.error(f"Fehler beim Laden des Inline-Bildes: {e}")
            ctk.CTkLabel(
                frame,
                text=f"❌ Fehler beim Laden des Bildes:\n{e}",
                font=ctk.CTkFont(size=12),
                text_color="red"
            ).pack(pady=20)
    
    def confirm_delete_card(self, card):
        """Zeigt BestÃƒÂ¤tigungsdialog und lÃƒÂ¶scht die Karte bei BestÃƒÂ¤tigung."""
        if messagebox.askyesno("BestÃƒÂ¤tigen", f"MÃƒÂ¶chten Sie die Karte\n'{card.question}'\nwirklich lÃƒÂ¶schen?"):
            try:
                card_deleted = self.data_manager.delete_flashcard(card)
                if card_deleted:
                    # *** Leitner-System synchronisieren ***
                    if hasattr(self, 'leitner_system'):
                        try:
                            self.leitner_system.reload_cards() # Reload nach Löschen
                            logging.info("Leitner-System nach KartenlÃƒÂ¶schung aktualisiert.")
                        except Exception as reload_error:
                            logging.warning(f"Leitner-System Reload fehlgeschlagen: {reload_error}")

                    # Wende Filter erneut an, um die Liste zu aktualisieren
                    # Wichtig: Filtere basierend auf der *aktuellen* Seite und den Suchbegriffen
                    self.apply_card_management_filters()
                    messagebox.showinfo("Erfolg", "Karte wurde gelöscht.")
                else:
                    messagebox.showerror("Fehler", "Karte konnte nicht gelöscht werden (nicht gefunden).")
            except Exception as e:
                logging.error(f"Fehler beim Löschen der Karte: {e}")
                import traceback
                logging.error(traceback.format_exc())
                messagebox.showerror("Fehler", f"Fehler beim Löschen der Karte: {e}")
        def update_subcategories(*args):
            """Aktualisiert die Unterkategorien basierend auf der gewÃƒÂ¤hlten Kategorie."""
            selected_category = self.category_var.get()
            
            if selected_category == "Bitte wÃƒÂ¤hlen...":
                subcategory_menu.configure(state="disabled", values=["Bitte zuerst Kategorie wÃƒÂ¤hlen"])
                self.subcategory_var.set("Bitte zuerst Kategorie wÃƒÂ¤hlen")
                content_container.pack_forget()
                return
                
            subcategories = sorted(self.data_manager.categories.get(selected_category, {}).keys())
            if subcategories:
                subcategory_menu.configure(state="normal", values=["Bitte wÃƒÂ¤hlen..."] + subcategories)
                self.subcategory_var.set("Bitte wÃƒÂ¤hlen...")
            else:
                subcategory_menu.configure(state="disabled", values=["Keine Unterkategorien verfügbar"])
                self.subcategory_var.set("Keine Unterkategorien verfügbar")
            
            display_filtered_cards(selected_category, self.subcategory_var.get())

        def on_subcategory_change(*args):
            """Aktualisiert die Kartenanzeige bei Änderung der Unterkategorie."""
            current_category = self.category_var.get()
            current_subcategory = self.subcategory_var.get()
            
            if current_category != "Bitte wÃƒÂ¤hlen..." and current_subcategory not in ["Bitte wÃƒÂ¤hlen...", "Bitte zuerst Kategorie wÃƒÂ¤hlen", "Keine Unterkategorien verfügbar"]:
                display_filtered_cards(current_category, current_subcategory)
            elif current_subcategory == "Bitte wÃƒÂ¤hlen...":
                display_filtered_cards(current_category, None)
            else:
                content_container.pack_forget()

        # Event-Bindungen
        self.category_var.trace_add('write', update_subcategories)
        self.subcategory_var.trace_add('write', on_subcategory_change)
    def show_remove_cards(self):
        """Zeigt eine Übersicht aller Karten mit der Option zum Löschen."""
        self._clear_content_frame()

        CARDS_PER_PAGE = 20  # Anzahl der Karten pro Seite
        current_page = {'value': 0}  # Als dict für Referenz in inneren Funktionen

        # Moderner Header mit Gradient-Hintergrund
        header_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='#ef4444',
            corner_radius=0,
            height=110
        )
        header_container.pack(fill='x', pady=(0, 20))
        header_container.pack_propagate(False)

        header_content = ctk.CTkFrame(header_container, fg_color='transparent')
        header_content.place(relx=0.5, rely=0.5, anchor='center')

        # Icon und Titel
        icon_title_frame = ctk.CTkFrame(header_content, fg_color='transparent')
        icon_title_frame.pack()

        ctk.CTkLabel(
            icon_title_frame,
            text="🗂️",
            font=ctk.CTkFont(size=36),
            text_color='#ffffff'
        ).pack(side='left', padx=(0, 15))

        title_frame = ctk.CTkFrame(icon_title_frame, fg_color='transparent')
        title_frame.pack(side='left')

        ctk.CTkLabel(
            title_frame,
            text="Karten entfernen",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color='#ffffff'
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_frame,
            text="Wähle Karten aus, die du aus deiner Sammlung entfernen möchtest",
            font=ctk.CTkFont(size=13),
            text_color='#fee2e2'
        ).pack(anchor='w')

        # Filter Frame mit modernem Design
        filter_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='#ffffff',
            corner_radius=15,
            border_width=2,
            border_color='#ef4444'
        )
        filter_container.pack(fill='x', padx=20, pady=(0, 15))

        filter_frame = ctk.CTkFrame(filter_container, fg_color='transparent')
        filter_frame.pack(padx=20, pady=15)

        # Icon
        ctk.CTkLabel(
            filter_frame,
            text="🔍",
            font=ctk.CTkFont(size=20)
        ).pack(side='left', padx=(0, 15))

        # Kategoriefilter
        ctk.CTkLabel(
            filter_frame,
            text="Kategorie:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#374151'
        ).pack(side='left', padx=(0, 8))

        category_var = tk.StringVar(value="Alle")
        categories = ["Alle"] + sorted(self.data_manager.categories.keys())
        category_menu = ctk.CTkOptionMenu(
            filter_frame,
            variable=category_var,
            values=categories,
            width=200,
            height=36,
            corner_radius=10,
            fg_color='#ef4444',
            button_color='#dc2626',
            button_hover_color='#b91c1c',
            font=ctk.CTkFont(size=13)
        )
        category_menu.pack(side='left', padx=(0, 20))

        # Subkategoriefilter
        ctk.CTkLabel(
            filter_frame,
            text="Unterkategorie:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#374151'
        ).pack(side='left', padx=(0, 8))

        subcategory_var = tk.StringVar(value="Alle")
        subcategory_menu = ctk.CTkOptionMenu(
            filter_frame,
            variable=subcategory_var,
            values=["Alle"],
            width=200,
            height=36,
            corner_radius=10,
            fg_color='#ef4444',
            button_color='#dc2626',
            button_hover_color='#b91c1c',
            font=ctk.CTkFont(size=13)
        )
        subcategory_menu.pack(side='left')

        # Scrollbarer Container für Karten
        cards_frame = ctk.CTkScrollableFrame(self.content_frame)
        cards_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Frame für den "Mehr laden" Button
        load_more_frame = ctk.CTkFrame(self.content_frame)
        load_more_frame.pack(fill='x', padx=20, pady=(0, 10))

        def update_subcategories(*args):
            selected_category = category_var.get()
            if selected_category == "Alle":
                subcategories = ["Alle"]
            else:
                subcategories = ["Alle"] + sorted(self.data_manager.categories.get(selected_category, {}).keys())
            subcategory_menu.configure(values=subcategories)
            subcategory_var.set("Alle")
            current_page['value'] = 0  # Reset Seite bei Kategoriewechsel
            display_cards()

        def delete_card(card):
                    if messagebox.askyesno("BestÃƒÂ¤tigen", f"MÃƒÂ¶chten Sie die Karte\n'{card.question}'\nwirklich lÃƒÂ¶schen?"):
                        success = self.data_manager.delete_flashcard(card)
                        if success:
                            # *** NEU: Leitner-System synchronisieren ***
                            if hasattr(self, 'leitner_system'):
                                try:
                                    self.leitner_system.reload_cards() # Reload nach Löschen
                                    logging.info("Leitner-System nach KartenlÃƒÂ¶schung aktualisiert (aus 'Karten entfernen').")
                                except Exception as reload_error:
                                    logging.warning(f"Leitner-System Reload fehlgeschlagen: {reload_error}")

                            messagebox.showinfo("Erfolg", "Karte wurde gelöscht.")
                            current_page['value'] = 0  # Reset Seite nach Löschen
                            display_cards() # Liste neu anzeigen
                        else:
                            messagebox.showerror("Fehler", "Karte konnte nicht gelöscht werden.")
        def display_cards():
            # Lösche alte Karten und den alten "Mehr laden" Button
            for widget in cards_frame.winfo_children():
                widget.destroy()
            for widget in load_more_frame.winfo_children():
                widget.destroy()

            # Hole gefilterte Karten
            if category_var.get() == "Alle":
                filtered_cards = self.data_manager.flashcards.copy()
            else:
                filtered_cards = self.data_manager.filter_flashcards_by_category_and_subcategory(
                    category=category_var.get(),
                    subcategory=None if subcategory_var.get() == "Alle" else subcategory_var.get()
                )

            if not filtered_cards:
                ctk.CTkLabel(
                    cards_frame,
                    text="Keine Karten gefunden.",
                    font=ctk.CTkFont(size=14)
                ).pack(pady=20)
                return

            # Berechne Start- und Endindex für die aktuelle Seite
            start_idx = current_page['value'] * CARDS_PER_PAGE
            end_idx = start_idx + CARDS_PER_PAGE
            current_cards = filtered_cards[start_idx:end_idx]

            # Zeige die Karten der aktuellen Seite
            for idx, card in enumerate(current_cards, start_idx + 1):
                card_frame = ctk.CTkFrame(
                    cards_frame,
                    fg_color='#ffffff',
                    corner_radius=12,
                    border_width=2,
                    border_color='#fecaca'
                )
                card_frame.pack(fill='x', padx=5, pady=8)

                # Linker Bereich mit Nummer
                number_section = ctk.CTkFrame(
                    card_frame,
                    fg_color='#fee2e2',
                    corner_radius=10,
                    width=50
                )
                number_section.pack(side='left', fill='y', padx=10, pady=10)
                number_section.pack_propagate(False)

                ctk.CTkLabel(
                    number_section,
                    text=str(idx),
                    font=ctk.CTkFont(size=18, weight="bold"),
                    text_color='#dc2626'
                ).place(relx=0.5, rely=0.5, anchor='center')

                # Info-Bereich
                info_frame = ctk.CTkFrame(card_frame, fg_color='transparent')
                info_frame.pack(side='left', fill='both', expand=True, padx=15, pady=12)

                # Frage
                question_label = ctk.CTkLabel(
                    info_frame,
                    text=f"❓ {card.question[:80]}{'...' if len(card.question) > 80 else ''}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color='#111827',
                    anchor='w'
                )
                question_label.pack(anchor='w', pady=(0, 6))

                # Antwort
                answer_text = card.answer[:60] + '...' if len(card.answer) > 60 else card.answer
                ctk.CTkLabel(
                    info_frame,
                    text=f"✓  {answer_text}",
                    font=ctk.CTkFont(size=12),
                    text_color='#6b7280',
                    anchor='w'
                ).pack(anchor='w', pady=(0, 6))

                # Kategorie
                category_frame = ctk.CTkFrame(info_frame, fg_color='transparent')
                category_frame.pack(anchor='w', pady=(0, 4))

                ctk.CTkLabel(
                    category_frame,
                    text="🏷️",
                    font=ctk.CTkFont(size=11)
                ).pack(side='left', padx=(0, 5))

                ctk.CTkLabel(
                    category_frame,
                    text=f"{card.category} › {card.subcategory}",
                    font=ctk.CTkFont(size=11),
                    text_color='#9ca3af'
                ).pack(side='left')

                # Tags
                if card.tags:
                    tags_frame = ctk.CTkFrame(info_frame, fg_color='transparent')
                    tags_frame.pack(anchor='w')

                    for tag in card.tags[:3]:  # Maximal 3 Tags anzeigen
                        tag_badge = ctk.CTkFrame(
                            tags_frame,
                            fg_color='#fee2e2',
                            corner_radius=8,
                            height=22
                        )
                        tag_badge.pack(side='left', padx=(0, 5))

                        ctk.CTkLabel(
                            tag_badge,
                            text=tag,
                            font=ctk.CTkFont(size=10),
                            text_color='#dc2626'
                        ).pack(padx=8, pady=2)

                # Löschen-Button
                delete_btn = ctk.CTkButton(
                    card_frame,
                    text="🗑️  Löschen",
                    command=lambda c=card: delete_card(c),
                    fg_color="#ef4444",
                    hover_color="#dc2626",
                    width=120,
                    height=45,
                    corner_radius=10,
                    font=ctk.CTkFont(size=13, weight="bold")
                )
                delete_btn.pack(side='right', padx=15)

            # "Mehr laden" Button anzeigen, wenn es weitere Karten gibt
            if end_idx < len(filtered_cards):
                load_more_btn = ctk.CTkButton(
                    load_more_frame,
                    text=f"↓  Weitere Karten laden ({len(filtered_cards) - end_idx} übrig)",
                    command=lambda: [current_page.update({'value': current_page['value'] + 1}), display_cards()],
                    fg_color="#f3f4f6",
                    hover_color="#e5e7eb",
                    text_color='#374151',
                    height=45,
                    width=300,
                    corner_radius=12,
                    border_width=2,
                    border_color='#d1d5db',
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                load_more_btn.pack(pady=10)

        # Event-Bindungen
        category_var.trace_add('write', update_subcategories)
        subcategory_var.trace_add('write', lambda *args: [current_page.update({'value': 0}), display_cards()])

        # Initiale Anzeige
        display_cards()

        # Moderner Zurück-Button
        back_frame = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        back_frame.pack(pady=15)

        back_btn = ctk.CTkButton(
            back_frame,
            text="←  Zurück zum Karten-Menü",
            command=self.show_card_management,
            fg_color="#f3f4f6",
            hover_color="#e5e7eb",
            text_color='#374151',
            height=45,
            width=250,
            corner_radius=12,
            border_width=2,
            border_color='#d1d5db',
            font=ctk.CTkFont(size=14, weight="bold")
        )
        back_btn.pack()

        # Setze den aktiven Button
        self.highlight_active_button('Karten entfernen')
            # -----------------------------------------------------------------------------------
    # KATEGORIEN & KARTENVERWALTUNG
    # -----------------------------------------------------------------------------------
    def manage_categories(self):
        """Moderne Kategorieverwaltung mit verbessertem Design."""
        self._clear_content_frame()

        # Moderner Header mit Gradient-Hintergrund
        header_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='#8b5cf6',
            corner_radius=0,
            height=110
        )
        header_container.pack(fill='x', pady=(0, 25))
        header_container.pack_propagate(False)

        header_content = ctk.CTkFrame(header_container, fg_color='transparent')
        header_content.place(relx=0.5, rely=0.5, anchor='center')

        # Icon und Titel
        icon_title_frame = ctk.CTkFrame(header_content, fg_color='transparent')
        icon_title_frame.pack()

        ctk.CTkLabel(
            icon_title_frame,
            text="📂",
            font=ctk.CTkFont(size=36),
            text_color='#ffffff'
        ).pack(side='left', padx=(0, 15))

        title_frame = ctk.CTkFrame(icon_title_frame, fg_color='transparent')
        title_frame.pack(side='left')

        ctk.CTkLabel(
            title_frame,
            text="Kategorien verwalten",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color='#ffffff'
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_frame,
            text="Organisiere deine Lernkarten in Kategorien und Unterkategorien",
            font=ctk.CTkFont(size=13),
            text_color='#ede9fe'
        ).pack(anchor='w')

        # Hauptcontainer
        main_container = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        main_container.pack(fill='both', expand=True, padx=30, pady=0)

        # Top-Bereich: Suchleiste und Aktionsbuttons
        top_bar = ctk.CTkFrame(main_container, fg_color='#ffffff', corner_radius=15, border_width=2, border_color='#8b5cf6')
        top_bar.pack(fill='x', pady=(0, 20))

        top_content = ctk.CTkFrame(top_bar, fg_color='transparent')
        top_content.pack(fill='x', padx=20, pady=15)

        # Suchbereich links
        search_frame = ctk.CTkFrame(top_content, fg_color='transparent')
        search_frame.pack(side='left', fill='x', expand=True)

        ctk.CTkLabel(
            search_frame,
            text="🔍",
            font=ctk.CTkFont(size=18),
            text_color='#8b5cf6'
        ).pack(side='left', padx=(0, 10))

        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=search_var,
            width=300,
            height=40,
            corner_radius=12,
            border_width=2,
            border_color='#e9d5ff',
            placeholder_text="Kategorie oder Unterkategorie suchen...",
            font=ctk.CTkFont(size=13)
        )
        search_entry.pack(side='left', padx=(0, 12))

        # Buttons rechts
        button_container = ctk.CTkFrame(top_content, fg_color='transparent')
        button_container.pack(side='right')

        # Hauptcontainer mit Grid-Layout für Tree und Buttons
        content_frame = ctk.CTkFrame(main_container, fg_color='transparent')
        content_frame.pack(fill='both', expand=True)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Scrollable Frame für die Kategorien
        scroll_container = ctk.CTkScrollableFrame(
            content_frame,
            fg_color='#ffffff',
            corner_radius=15,
            border_width=2,
            border_color='#e9d5ff'
        )
        scroll_container.grid(row=0, column=0, sticky='nsew', pady=(0, 15))

        # Container für die Kategorien-Cards
        categories_container = ctk.CTkFrame(scroll_container, fg_color='transparent')
        categories_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Performance-Optimierung: Cache für Kategorien-Daten
        _last_categories_data = None
        _search_timer = None

        def refresh_categories_display(force=False):
            """Aktualisiert die Kategorien-Anzeige mit Performance-Optimierung."""
            nonlocal _last_categories_data

            # Performance-Optimierung: Nur aktualisieren wenn sich Daten geändert haben
            current_data = dict(self.data_manager.categories)
            query = search_var.get().strip().lower()

            if not force and _last_categories_data == current_data and not query:
                return

            _last_categories_data = current_data.copy()

            # Batch-Delete: Alle Widgets auf einmal löschen (schneller als einzeln)
            for widget in categories_container.winfo_children():
                widget.destroy()

            # Vorfilterung: Kategorien frühzeitig filtern
            categories = sorted(current_data.keys())

            # Optimierte Kategorie-Erstellung
            for cat_name in categories:
                subcats = sorted(current_data[cat_name].keys())

                # Filter-Logik optimiert
                if query:
                    cat_matches = query in cat_name.lower()
                    matching_subcats = [sc for sc in subcats if query in sc.lower()]
                    if not cat_matches and not matching_subcats:
                        continue
                    display_subcats = matching_subcats if matching_subcats else subcats
                else:
                    display_subcats = subcats

                # Optimierte Widget-Erstellung mit weniger Verschachtelung
                cat_card = ctk.CTkFrame(
                    categories_container,
                    fg_color='#faf5ff',
                    corner_radius=12,
                    border_width=2,
                    border_color='#e9d5ff'
                )
                cat_card.pack(fill='x', pady=8)

                # Header der Kategorie - direkt ohne extra Content-Frame
                cat_header = ctk.CTkFrame(cat_card, fg_color='#8b5cf6', corner_radius=10)
                cat_header.pack(fill='x', padx=3, pady=3)

                # Direkte Pack-Anordnung ohne extra Frame
                ctk.CTkLabel(
                    cat_header,
                    text=f"📁  {cat_name}",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color='#ffffff'
                ).pack(side='left', padx=15, pady=12)

                # Badge mit Anzahl
                badge = ctk.CTkLabel(
                    cat_header,
                    text=f"{len(display_subcats)} Unterkategorien",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color='#5b21b6',
                    fg_color='#c4b5fd',
                    corner_radius=10,
                    padx=10,
                    pady=3
                )
                badge.pack(side='left', padx=10)

                # Löschen-Button optimiert
                def delete_main_category(c=cat_name):
                    if messagebox.askyesno("Bestätigen", f"Möchten Sie die Kategorie '{c}' und alle zugehörigen Unterkategorien löschen?"):
                        success = self.data_manager.delete_category(c)
                        if success:
                            messagebox.showinfo("Info", f"Kategorie '{c}' wurde gelöscht.")
                            logging.info(f"Kategorie '{c}' gelöscht.")
                            refresh_categories_display(force=True)
                        else:
                            messagebox.showerror("Fehler", "Fehler beim Löschen der Kategorie.")

                ctk.CTkButton(
                    cat_header,
                    text="🗑️ Löschen",
                    command=delete_main_category,
                    width=100,
                    height=32,
                    corner_radius=10,
                    fg_color='#dc2626',
                    hover_color='#b91c1c',
                    font=ctk.CTkFont(size=12, weight="bold")
                ).pack(side='right', padx=15)

                # Unterkategorien optimiert anzeigen
                if display_subcats:
                    subcat_container = ctk.CTkFrame(cat_card, fg_color='transparent')
                    subcat_container.pack(fill='x', padx=15, pady=(0, 12))

                    for subcat_name in display_subcats:
                        # Vereinfachte Subkategorie-Darstellung
                        subcat_frame = ctk.CTkFrame(
                            subcat_container,
                            fg_color='#ffffff',
                            corner_radius=8,
                            border_width=1,
                            border_color='#e9d5ff'
                        )
                        subcat_frame.pack(fill='x', pady=4, ipady=8)

                        ctk.CTkLabel(
                            subcat_frame,
                            text=f"📄  {subcat_name}",
                            font=ctk.CTkFont(size=13),
                            text_color='#374151'
                        ).pack(side='left', padx=12)

                        # Löschen-Button für Unterkategorie
                        def delete_subcat(c=cat_name, sc=subcat_name):
                            if messagebox.askyesno("Bestätigen", f"Möchten Sie die Unterkategorie '{sc}' in '{c}' löschen?"):
                                success = self.data_manager.delete_subcategory(c, sc)
                                if success:
                                    messagebox.showinfo("Info", f"Unterkategorie '{sc}' wurde gelöscht.")
                                    logging.info(f"Unterkategorie '{sc}' in '{c}' gelöscht.")
                                    refresh_categories_display(force=True)
                                else:
                                    messagebox.showerror("Fehler", "Fehler beim Löschen der Unterkategorie.")

                        ctk.CTkButton(
                            subcat_frame,
                            text="🗑️",
                            command=delete_subcat,
                            width=60,
                            height=28,
                            corner_radius=8,
                            fg_color='#fef2f2',
                            hover_color='#fee2e2',
                            text_color='#dc2626',
                            font=ctk.CTkFont(size=12)
                        ).pack(side='right', padx=12)

        # Aktionsbuttons
        def add_category():
            self.create_add_category_view()

        # Optimierte Suchfunktion mit Debouncing
        def search_action(*args):
            nonlocal _search_timer
            # Vorheriges Timer abbrechen falls vorhanden
            if _search_timer:
                self.after_cancel(_search_timer)
            # Neuen Timer setzen (300ms Verzögerung für bessere Performance)
            _search_timer = self.after(300, lambda: refresh_categories_display(force=True))

        # Such-Eingabe mit automatischer Suche beim Tippen
        search_var.trace_add('write', search_action)

        search_btn = ctk.CTkButton(
            button_container,
            text="🔍 Suchen",
            command=lambda: refresh_categories_display(force=True),
            width=110,
            height=40,
            corner_radius=12,
            fg_color='#8b5cf6',
            hover_color='#7c3aed',
            font=ctk.CTkFont(size=13, weight="bold")
        )
        search_btn.pack(side='left', padx=5)

        add_btn = ctk.CTkButton(
            button_container,
            text="➕ Hinzufügen",
            command=add_category,
            width=130,
            height=40,
            corner_radius=12,
            fg_color='#10b981',
            hover_color='#059669',
            font=ctk.CTkFont(size=13, weight="bold")
        )
        add_btn.pack(side='left', padx=5)

        refresh_btn = ctk.CTkButton(
            button_container,
            text="🔄 Aktualisieren",
            command=refresh_categories_display,
            width=140,
            height=40,
            corner_radius=12,
            fg_color='#3b82f6',
            hover_color='#2563eb',
            font=ctk.CTkFont(size=13, weight="bold")
        )
        refresh_btn.pack(side='left', padx=5)

        # Enter-Taste für Suche binden
        search_entry.bind("<Return>", lambda e: search_action())

        # Initiale Anzeige
        refresh_categories_display()

        # Setze den aktiven Button auf 'verwaltung'
        self.highlight_active_button('verwaltung')

    def create_add_category_view(self):
        self._clear_content_frame()

        # Moderner Header mit Gradient-Hintergrund ähnlich wie manage_categories
        header_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='#10b981',
            corner_radius=0,
            height=110
        )
        header_container.pack(fill='x', pady=(0, 25))
        header_container.pack_propagate(False)

        header_content = ctk.CTkFrame(header_container, fg_color='transparent')
        header_content.place(relx=0.5, rely=0.5, anchor='center')

        # Icon und Titel
        icon_title_frame = ctk.CTkFrame(header_content, fg_color='transparent')
        icon_title_frame.pack()

        ctk.CTkLabel(
            icon_title_frame,
            text="➕",
            font=ctk.CTkFont(size=36),
            text_color='#ffffff'
        ).pack(side='left', padx=(0, 15))

        title_frame = ctk.CTkFrame(icon_title_frame, fg_color='transparent')
        title_frame.pack(side='left')

        ctk.CTkLabel(
            title_frame,
            text="Kategorien hinzufügen",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color='#ffffff'
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_frame,
            text="Erstelle neue Kategorien und Unterkategorien für deine Lernkarten",
            font=ctk.CTkFont(size=13),
            text_color='#d1fae5'
        ).pack(anchor='w')

        # Hauptcontainer
        main_container = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        main_container.pack(fill='both', expand=True, padx=30, pady=0)

        # Notebook für Tabs (behalte ttk.Notebook, da CTk kein Notebook hat)
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill='both', expand=True, pady=(0, 20))

        # Tab 1: Neue Hauptkategorie
        new_cat_frame = ctk.CTkFrame(notebook, fg_color='#fafafa')
        notebook.add(new_cat_frame, text="📁 Neue Hauptkategorie")

        # Tab 2: Unterkategorie hinzufügen
        add_subcat_frame = ctk.CTkFrame(notebook, fg_color='#fafafa')
        notebook.add(add_subcat_frame, text="📄 Unterkategorie hinzufügen")

        # Inhalt Tab 1: Neue Hauptkategorie - Moderneres Layout
        tab1_container = ctk.CTkFrame(new_cat_frame, fg_color='#ffffff', corner_radius=15, border_width=2, border_color='#10b981')
        tab1_container.pack(fill='both', expand=True, padx=40, pady=40)

        # Beschreibung
        ctk.CTkLabel(
            tab1_container,
            text="🎯 Erstelle eine neue Hauptkategorie",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color='#10b981'
        ).pack(pady=(25, 10))

        ctk.CTkLabel(
            tab1_container,
            text="Gib einen eindeutigen Namen für deine neue Kategorie an und füge optional Unterkategorien hinzu.",
            font=ctk.CTkFont(size=12),
            text_color='#6b7280',
            wraplength=400
        ).pack(pady=(0, 25))

        # Eingabefelder mit verbessertem Design
        ctk.CTkLabel(
            tab1_container,
            text="Kategorie-Name:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color='#374151'
        ).pack(pady=(10, 5), anchor='w', padx=50)

        new_cat_entry = ctk.CTkEntry(
            tab1_container,
            width=400,
            height=40,
            corner_radius=10,
            border_width=2,
            border_color='#d1fae5',
            placeholder_text="z.B. Mathematik, Geschichte, Programmierung...",
            font=ctk.CTkFont(size=13)
        )
        new_cat_entry.pack(pady=(0, 20), padx=50)

        ctk.CTkLabel(
            tab1_container,
            text="Unterkategorien (kommagetrennt, optional):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color='#374151'
        ).pack(pady=(10, 5), anchor='w', padx=50)

        subcats_entry = ctk.CTkEntry(
            tab1_container,
            width=400,
            height=40,
            corner_radius=10,
            border_width=2,
            border_color='#d1fae5',
            placeholder_text="z.B. Algebra, Geometrie, Analysis",
            font=ctk.CTkFont(size=13)
        )
        subcats_entry.pack(pady=(0, 30), padx=50)

        # Moderner Speichern-Button
        save_main_btn = ctk.CTkButton(
            tab1_container,
            text="✓  Hauptkategorie speichern",
            command=lambda: self.save_new_category(new_cat_entry.get().strip(), subcats_entry.get()),
            width=240,
            height=45,
            corner_radius=12,
            fg_color='#10b981',
            hover_color='#059669',
            font=ctk.CTkFont(size=14, weight="bold")
        )
        save_main_btn.pack(pady=(0, 25))

        # Inhalt Tab 2: Unterkategorie hinzufügen - Moderneres Layout
        tab2_container = ctk.CTkFrame(add_subcat_frame, fg_color='#ffffff', corner_radius=15, border_width=2, border_color='#10b981')
        tab2_container.pack(fill='both', expand=True, padx=40, pady=40)

        # Beschreibung
        ctk.CTkLabel(
            tab2_container,
            text="🗂️ Unterkategorie hinzufügen",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color='#10b981'
        ).pack(pady=(25, 10))

        ctk.CTkLabel(
            tab2_container,
            text="Erweitere eine bestehende Kategorie mit einer neuen Unterkategorie.",
            font=ctk.CTkFont(size=12),
            text_color='#6b7280',
            wraplength=400
        ).pack(pady=(0, 25))

        # Hauptkategorie auswählen
        ctk.CTkLabel(
            tab2_container,
            text="Hauptkategorie auswählen:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color='#374151'
        ).pack(pady=(10, 5), anchor='w', padx=50)

        existing_categories = sorted(self.data_manager.categories.keys())
        category_var = tk.StringVar(value=existing_categories[0] if existing_categories else "")

        category_dropdown = ctk.CTkOptionMenu(
            tab2_container,
            values=existing_categories if existing_categories else ["Keine Kategorien"],
            variable=category_var,
            width=400,
            height=40,
            corner_radius=10,
            fg_color='#10b981',
            button_color='#059669',
            button_hover_color='#047857',
            font=ctk.CTkFont(size=13)
        )
        category_dropdown.pack(pady=(0, 20), padx=50)

        # Neue Unterkategorie
        ctk.CTkLabel(
            tab2_container,
            text="Neue Unterkategorie:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color='#374151'
        ).pack(pady=(10, 5), anchor='w', padx=50)

        new_subcat_entry = ctk.CTkEntry(
            tab2_container,
            width=400,
            height=40,
            corner_radius=10,
            border_width=2,
            border_color='#d1fae5',
            placeholder_text="Name der neuen Unterkategorie",
            font=ctk.CTkFont(size=13)
        )
        new_subcat_entry.pack(pady=(0, 20), padx=50)

        # Info-Box für existierende Unterkategorien
        info_frame = ctk.CTkFrame(tab2_container, fg_color='#f0fdf4', corner_radius=12, border_width=1, border_color='#bbf7d0')
        info_frame.pack(fill='x', pady=(0, 20), padx=50)

        info_label = ctk.CTkLabel(
            info_frame,
            text="📋 Existierende Unterkategorien:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#059669'
        )
        info_label.pack(pady=(15, 8))

        current_subcats_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color='#374151',
            wraplength=380
        )
        current_subcats_label.pack(pady=(0, 15), padx=20)

        def update_subcats_display(*args):
            selected_cat = category_var.get()
            if selected_cat and selected_cat in self.data_manager.categories:
                subcats = sorted(self.data_manager.categories[selected_cat].keys())
                if subcats:
                    current_subcats_label.configure(
                        text=", ".join(subcats)
                    )
                else:
                    current_subcats_label.configure(
                        text="Keine Unterkategorien vorhanden"
                    )
            else:
                current_subcats_label.configure(
                    text="Keine Kategorien verfügbar"
                )

        # Statt trace_add verwenden wir command im OptionMenu
        category_dropdown.configure(command=update_subcats_display)
        update_subcats_display()

        # Funktion zum Speichern und Aktualisieren
        def save_and_update_subcat():
            if self.save_new_subcategory(
                category_var.get(),
                new_subcat_entry.get().strip(),
                new_subcat_entry,
                current_subcats_label
            ):
                update_subcats_display()
                new_subcat_entry.delete(0, 'end')

        # Moderner Speichern Button
        save_subcat_btn = ctk.CTkButton(
            tab2_container,
            text="✓  Unterkategorie speichern",
            command=save_and_update_subcat,
            width=240,
            height=45,
            corner_radius=12,
            fg_color='#10b981',
            hover_color='#059669',
            font=ctk.CTkFont(size=14, weight="bold")
        )
        save_subcat_btn.pack(pady=(0, 25))

        # Moderner Zurück Button - zurück zu Kategorien Verwalten statt Hauptmenü
        back_button_frame = ctk.CTkFrame(main_container, fg_color='transparent')
        back_button_frame.pack(pady=(0, 0))

        back_btn = ctk.CTkButton(
            back_button_frame,
            text="←  Zurück zu Kategorien verwalten",
            command=self.manage_categories,
            height=45,
            width=260,
            font=ctk.CTkFont(size=14),
            fg_color="#f3f4f6",
            hover_color="#e5e7eb",
            text_color="#374151",
            corner_radius=12,
            border_width=2,
            border_color="#d1d5db"
        )
        back_btn.pack()

        logging.info("Kategorie hinzufügen Ansicht angezeigt.")
    def save_new_category(self, new_cat, subcats_entry_str):
        """
        Speichert eine neue Kategorie mit den eingegebenen Unterkategorien.
        """
        logging.debug(f"save_new_category aufgerufen mit Kategorie: '{new_cat}', Subkategorien: '{subcats_entry_str}'")

        # Diese Zeile war falsch, da 'subcats' noch nicht definiert war.
        # Korrektur:
        subcats = [s.strip().lower() for s in subcats_entry_str.split(",") if s.strip()]  # Lowercase für Konsistenz

        logging.debug(f"Subkategorien nach split und strip: {subcats}")

        if not new_cat:
            messagebox.showwarning("Warnung", "Bitte einen Kategorienamen eingeben.")
            logging.warning("Es wurde kein Kategoriename eingegeben.")
            return

        # Validiere Kategorienamen
        is_valid, error_msg = self.data_manager.validate_category_name(new_cat)
        if not is_valid:
            messagebox.showerror("Fehler", f"UngÃƒÂ¼ltiger Kategoriename: {error_msg}")
            logging.error(f"UngÃƒÂ¼ltiger Kategoriename: {new_cat}. Fehler: {error_msg}")
            return

        # Validiere Subkategorienamen
        for subcat in subcats:
            is_valid, error_msg = self.data_manager.validate_category_name(subcat)
            if not is_valid:
                messagebox.showerror("Fehler", f"UngÃƒÂ¼ltige Subkategorie '{subcat}': {error_msg}")
                logging.error(f"UngÃƒÂ¼ltiger Subkategoriename: {subcat}. Fehler: {error_msg}")
                return

        logging.debug(f"Validiere Kategorie: '{new_cat}'")

        try:
            success = self.data_manager.add_category(new_cat, subcats)
            if success:
                messagebox.showinfo("Erfolg", f"Kategorie '{new_cat}' wurde hinzugefügt.")
                logging.info(f"Kategorie '{new_cat}' erfolgreich hinzugefügt.")
                self.manage_categories()  # Wechsle zurück zur Kategorieverwaltung
            else:
                # Diese Meldung wird wahrscheinlich nicht mehr angezeigt, da der Fehler jetzt weiter oben behandelt wird
                messagebox.showerror("Fehler", "Kategorie konnte nicht hinzugefügt werden.")
                logging.error(f"Kategorie '{new_cat}' konnte nicht hinzugefügt werden.")
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen der Kategorie: {str(e)}")
            messagebox.showerror("Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}") # Zeige die Exception-Nachricht an
    def add_subcategory_to_existing(self):
        """FÃƒÂ¼gt eine neue Unterkategorie zu einer bestehenden Kategorie hinzu"""
        selected_item = self.category_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warnung", "Bitte eine Hauptkategorie auswÃƒÂ¤hlen.")
            return

        # PrÃƒÂ¼fe, ob eine Hauptkategorie ausgewÃƒÂ¤hlt wurde
        parent = self.category_tree.parent(selected_item)
        if parent:
            messagebox.showwarning("Warnung", "Bitte eine Hauptkategorie auswÃƒÂ¤hlen, nicht eine Unterkategorie.")
            return

        category = self.category_tree.item(selected_item)["text"]
        
        # Dialog zum Hinzufügen der Unterkategorie
        dialog = ctk.CTkToplevel(self.master)
        dialog.title("Unterkategorie hinzufügen")
        dialog.geometry("400x250")
        dialog.transient(self.master)
        dialog.grab_set()

        # Zentriere das Fenster
        dialog.geometry(f"+{self.master.winfo_rootx() + self.master.winfo_width()//2 - 200}+{self.master.winfo_rooty() + self.master.winfo_height()//2 - 125}")

        # Dialog-Inhalt
        content_frame = ctk.CTkFrame(dialog)
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)

        header_label = ctk.CTkLabel(
            content_frame,
            text=f"Neue Unterkategorie für '{category}':",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header_label.pack(pady=(0, 20))
        
        subcat_entry = ctk.CTkEntry(
            content_frame,
            width=300,
            height=35,
            placeholder_text="Name der neuen Unterkategorie"
        )
        subcat_entry.pack(pady=(0, 20))
        subcat_entry.focus_set()

        def save_and_close():
            """Speichert die neue Unterkategorie und schlieÃƒÅ¸t den Dialog"""
            if self.save_new_subcategory(
                category, 
                subcat_entry.get().strip(), 
                subcat_entry, 
                None  # Kein Update-Label nötig, da Dialog geschlossen wird
            ):
                dialog.destroy()
                self.refresh_category_tree()

        # Button-Frame
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill='x', pady=(20, 0))

        # Speichern Button
        save_btn = ctk.CTkButton(
            button_frame,
            text="Speichern",
            command=save_and_close,
            width=120,
            height=35
        )
        save_btn.pack(side='left', padx=5)

        # Abbrechen Button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            command=dialog.destroy,
            fg_color="gray",
            hover_color="darkgray",
            width=120,
            height=35
        )
        cancel_btn.pack(side='left', padx=5)

        # Tastatur-Shortcuts
        dialog.bind('<Return>', lambda e: save_and_close())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
    def save_new_subcategory(self, category: str, subcategory: str, entry_widget=None, update_label=None):
        """
        Speichert eine neue Unterkategorie.
        
        Args:
            category (str): Die Hauptkategorie
            subcategory (str): Die neue Unterkategorie
            entry_widget: Optional - Das Eingabefeld zum Zurücksetzen
            update_label: Optional - Das Label zum Aktualisieren der Anzeige
        """
        if not category or not subcategory:
            messagebox.showwarning("Warnung", "Bitte Kategorie und Unterkategorie auswÃƒÂ¤hlen/eingeben.")
            return False

        # Validiere den Namen
        is_valid, error_msg = self.data_manager.validate_category_name(subcategory)
        if not is_valid:
            messagebox.showerror("Fehler", f"UngÃƒÂ¼ltiger Name: {error_msg}")
            return False

        # PrÃƒÂ¼fe, ob die Unterkategorie bereits existiert
        if subcategory in self.data_manager.categories.get(category, {}):
            messagebox.showerror("Fehler", f"Die Unterkategorie '{subcategory}' existiert bereits in '{category}'.")
            return False

        try:
            success = self.data_manager.add_subcategory(category, subcategory)
            if success:
                messagebox.showinfo("Erfolg", f"Unterkategorie '{subcategory}' wurde zu '{category}' hinzugefügt.")
                
                # Eingabefeld zurücksetzen, falls vorhanden
                if entry_widget:
                    if isinstance(entry_widget, ctk.CTkEntry):
                        entry_widget.delete(0, 'end')
                    else:
                        entry_widget.delete(0, 'end')
                
                # Label aktualisieren, falls vorhanden
                if update_label:
                    subcats = sorted(self.data_manager.categories.get(category, {}).keys())
                    if isinstance(update_label, ctk.CTkLabel):
                        update_label.configure(text=f"Aktuelle Unterkategorien:\n{', '.join(subcats)}")
                    else:
                        update_label.config(text=f"Aktuelle Unterkategorien:\n{', '.join(subcats)}")
                
                return True
            else:
                messagebox.showerror("Fehler", "Unterkategorie konnte nicht hinzugefügt werden.")
                return False
                
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen der Unterkategorie: {str(e)}")
            messagebox.showerror("Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}")
            return False
    def add_card(self):
        """Optimierte Methode zum Hinzufügen neuer Karten mit mehrzeiligen Textfeldern und Bild-Support für Frage."""
        self._clear_content_frame()

        # Moderner Header mit Gradient-Hintergrund
        header_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='#10b981',
            corner_radius=0,
            height=120
        )
        header_container.pack(fill='x', pady=(0, 25))
        header_container.pack_propagate(False)

        header_content = ctk.CTkFrame(header_container, fg_color='transparent')
        header_content.place(relx=0.5, rely=0.5, anchor='center')

        # Icon und Titel
        icon_title_frame = ctk.CTkFrame(header_content, fg_color='transparent')
        icon_title_frame.pack()

        ctk.CTkLabel(
            icon_title_frame,
            text="✨",
            font=ctk.CTkFont(size=36),
            text_color='#ffffff'
        ).pack(side='left', padx=(0, 15))

        title_frame = ctk.CTkFrame(icon_title_frame, fg_color='transparent')
        title_frame.pack(side='left')

        ctk.CTkLabel(
            title_frame,
            text="Neue Karte hinzufügen",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color='#ffffff'
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_frame,
            text="Erstelle eine neue Lernkarte mit Frage, Antwort und Bildern",
            font=ctk.CTkFont(size=13),
            text_color='#d1fae5'
        ).pack(anchor='w')

        # Hauptcontainer mit Scrollbar
        main_container = ctk.CTkScrollableFrame(self.content_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # === FRAGE SEKTION ===
        question_section = ctk.CTkFrame(
            main_container,
            fg_color='#ffffff',
            corner_radius=15,
            border_width=2,
            border_color='#10b981'
        )
        question_section.pack(fill='x', pady=(0, 20))

        # Header mit Icon
        question_header = ctk.CTkFrame(question_section, fg_color='#ecfdf5', corner_radius=13)
        question_header.pack(fill='x', pady=3, padx=3)

        question_header_content = ctk.CTkFrame(question_header, fg_color='transparent')
        question_header_content.pack(pady=12, padx=15, fill='x')

        ctk.CTkLabel(
            question_header_content,
            text="❓",
            font=ctk.CTkFont(size=24)
        ).pack(side='left', padx=(0, 10))

        ctk.CTkLabel(
            question_header_content,
            text="FRAGE",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color='#047857'
        ).pack(side='left')

        # Frage-Text (mehrzeilig)
        content_frame = ctk.CTkFrame(question_section, fg_color='transparent')
        content_frame.pack(fill='x', padx=15, pady=15)

        ctk.CTkLabel(
            content_frame,
            text="Frage-Text:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#374151'
        ).pack(anchor='w', pady=(0, 8))

        question_textbox = ctk.CTkTextbox(
            content_frame,
            width=600,
            height=110,
            wrap='word',
            font=ctk.CTkFont(size=14),
            border_width=2,
            border_color='#d1d5db',
            corner_radius=10
        )
        question_textbox.pack(fill='x', pady=(0, 5))

        # Bild für Frage
        ctk.CTkLabel(
            content_frame,
            text="Bild zur Frage (optional):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#374151'
        ).pack(anchor='w', pady=(15, 8))

        self.question_image_path_var = tk.StringVar()

        question_image_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        question_image_frame.pack(fill='x', pady=(0, 0))

        question_image_entry = ctk.CTkEntry(
            question_image_frame,
            textvariable=self.question_image_path_var,
            state='readonly',
            height=40,
            corner_radius=10,
            border_width=2,
            border_color='#d1d5db',
            font=ctk.CTkFont(size=12)
        )
        question_image_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))

        def choose_question_image():
            file_path = filedialog.askopenfilename(
                title="Bild für Frage auswählen",
                filetypes=[
                    ("Bilder", "*.jpg *.jpeg *.png *.gif *.bmp"),
                    ("Alle Dateien", "*.*")
                ]
            )
            if file_path:
                self.question_image_path_var.set(file_path)

        ctk.CTkButton(
            question_image_frame,
            text="📁 Auswählen",
            command=choose_question_image,
            width=130,
            height=40,
            corner_radius=10,
            fg_color='#10b981',
            hover_color='#059669',
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side='left', padx=(0, 10))

        ctk.CTkButton(
            question_image_frame,
            text="✕",
            command=lambda: self.question_image_path_var.set(""),
            width=40,
            height=40,
            corner_radius=10,
            fg_color="#ef4444",
            hover_color="#dc2626",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side='left')

        # === ANTWORT SEKTION ===
        answer_section = ctk.CTkFrame(
            main_container,
            fg_color='#ffffff',
            corner_radius=15,
            border_width=2,
            border_color='#3b82f6'
        )
        answer_section.pack(fill='x', pady=(0, 20))

        # Header mit Icon
        answer_header = ctk.CTkFrame(answer_section, fg_color='#dbeafe', corner_radius=13)
        answer_header.pack(fill='x', pady=3, padx=3)

        answer_header_content = ctk.CTkFrame(answer_header, fg_color='transparent')
        answer_header_content.pack(pady=12, padx=15, fill='x')

        ctk.CTkLabel(
            answer_header_content,
            text="✓",
            font=ctk.CTkFont(size=24),
            text_color='#1e40af'
        ).pack(side='left', padx=(0, 10))

        ctk.CTkLabel(
            answer_header_content,
            text="ANTWORT",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color='#1e40af'
        ).pack(side='left')

        # Antwort-Text (mehrzeilig)
        answer_content_frame = ctk.CTkFrame(answer_section, fg_color='transparent')
        answer_content_frame.pack(fill='x', padx=15, pady=15)

        ctk.CTkLabel(
            answer_content_frame,
            text="Antwort-Text:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#374151'
        ).pack(anchor='w', pady=(0, 8))

        answer_textbox = ctk.CTkTextbox(
            answer_content_frame,
            width=600,
            height=110,
            wrap='word',
            font=ctk.CTkFont(size=14),
            border_width=2,
            border_color='#d1d5db',
            corner_radius=10
        )
        answer_textbox.pack(fill='x', pady=(0, 5))

        # Bild für Antwort
        ctk.CTkLabel(
            answer_content_frame,
            text="Bild zur Antwort (optional):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#374151'
        ).pack(anchor='w', pady=(15, 8))

        self.answer_image_path_var = tk.StringVar()

        answer_image_frame = ctk.CTkFrame(answer_content_frame, fg_color="transparent")
        answer_image_frame.pack(fill='x', pady=(0, 0))

        answer_image_entry = ctk.CTkEntry(
            answer_image_frame,
            textvariable=self.answer_image_path_var,
            state='readonly',
            height=40,
            corner_radius=10,
            border_width=2,
            border_color='#d1d5db',
            font=ctk.CTkFont(size=12)
        )
        answer_image_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))

        def choose_answer_image():
            file_path = filedialog.askopenfilename(
                title="Bild für Antwort auswählen",
                filetypes=[
                    ("Bilder", "*.jpg *.jpeg *.png *.gif *.bmp"),
                    ("Alle Dateien", "*.*")
                ]
            )
            if file_path:
                self.answer_image_path_var.set(file_path)

        ctk.CTkButton(
            answer_image_frame,
            text="📁 Auswählen",
            command=choose_answer_image,
            width=130,
            height=40,
            corner_radius=10,
            fg_color='#3b82f6',
            hover_color='#2563eb',
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side='left', padx=(0, 10))

        ctk.CTkButton(
            answer_image_frame,
            text="✕",
            command=lambda: self.answer_image_path_var.set(""),
            width=40,
            height=40,
            corner_radius=10,
            fg_color="#ef4444",
            hover_color="#dc2626",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side='left')

        # === KATEGORIEN & TAGS SEKTION ===
        meta_section = ctk.CTkFrame(
            main_container,
            fg_color='#ffffff',
            corner_radius=15,
            border_width=2,
            border_color='#f59e0b'
        )
        meta_section.pack(fill='x', pady=(0, 20))

        # Header mit Icon
        meta_header = ctk.CTkFrame(meta_section, fg_color='#fef3c7', corner_radius=13)
        meta_header.pack(fill='x', pady=3, padx=3)

        meta_header_content = ctk.CTkFrame(meta_header, fg_color='transparent')
        meta_header_content.pack(pady=12, padx=15, fill='x')

        ctk.CTkLabel(
            meta_header_content,
            text="🏷️",
            font=ctk.CTkFont(size=24)
        ).pack(side='left', padx=(0, 10))

        ctk.CTkLabel(
            meta_header_content,
            text="KATEGORISIERUNG",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color='#b45309'
        ).pack(side='left')

        # Content Frame
        meta_content_frame = ctk.CTkFrame(meta_section, fg_color='transparent')
        meta_content_frame.pack(fill='x', padx=15, pady=15)

        # Kategorie
        cat_frame = ctk.CTkFrame(meta_content_frame, fg_color="transparent")
        cat_frame.pack(fill='x', pady=(0, 12))

        ctk.CTkLabel(
            cat_frame,
            text="Kategorie:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#374151',
            width=140
        ).pack(side='left')

        self.category_var = tk.StringVar()
        all_categories = sorted(self.data_manager.categories.keys()) if self.data_manager.categories else []
        category_menu = ctk.CTkOptionMenu(
            cat_frame,
            variable=self.category_var,
            values=all_categories if all_categories else ["Keine Kategorien"],
            width=250,
            height=38,
            corner_radius=10,
            fg_color='#f59e0b',
            button_color='#d97706',
            button_hover_color='#b45309',
            font=ctk.CTkFont(size=13)
        )
        category_menu.pack(side='left', padx=10)

        # Unterkategorie
        subcat_frame = ctk.CTkFrame(meta_content_frame, fg_color="transparent")
        subcat_frame.pack(fill='x', pady=(0, 12))

        ctk.CTkLabel(
            subcat_frame,
            text="Unterkategorie:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#374151',
            width=140
        ).pack(side='left')

        self.subcategory_var = tk.StringVar()
        subcategory_menu = ctk.CTkOptionMenu(
            subcat_frame,
            variable=self.subcategory_var,
            values=["Bitte Kategorie wählen"],
            width=250,
            height=38,
            corner_radius=10,
            fg_color='#f59e0b',
            button_color='#d97706',
            button_hover_color='#b45309',
            font=ctk.CTkFont(size=13)
        )
        subcategory_menu.pack(side='left', padx=10)
        
        def update_subcategories(*args):
            selected_category = self.category_var.get()
            if selected_category and selected_category != "Keine Kategorien":
                subcats = sorted(self.data_manager.categories.get(selected_category, {}).keys())
                subcategory_menu.configure(values=subcats if subcats else ["Keine Unterkategorien"])
                if subcats:
                    self.subcategory_var.set(subcats[0])
            else:
                subcategory_menu.configure(values=["Bitte Kategorie wählen"])
                self.subcategory_var.set("Bitte Kategorie wÃƒÂ¤hlen")
        
        self.category_var.trace_add('write', update_subcategories)
        if all_categories:
            self.category_var.set(all_categories[0])
            update_subcategories()

        # Tags
        tags_frame = ctk.CTkFrame(meta_content_frame, fg_color="transparent")
        tags_frame.pack(fill='x', pady=(0, 0))

        ctk.CTkLabel(
            tags_frame,
            text="Tags (kommagetrennt):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#374151',
            width=140
        ).pack(side='left')

        tags_entry = ctk.CTkEntry(
            tags_frame,
            width=350,
            height=38,
            corner_radius=10,
            border_width=2,
            border_color='#d1d5db',
            font=ctk.CTkFont(size=13)
        )
        tags_entry.pack(side='left', padx=10)

        # === BUTTONS ===
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(pady=20)
        
        def save_card():
            # Hole Text aus Textboxen (nicht Entry!)
            question = question_textbox.get("1.0", "end-1c").strip()
            answer = answer_textbox.get("1.0", "end-1c").strip()
            category = self.category_var.get()
            subcat = self.subcategory_var.get()
            tags_text = tags_entry.get().strip()
            question_image_path = self.question_image_path_var.get()
            answer_image_path = self.answer_image_path_var.get()
            
            # Validierung
            if not question:
                messagebox.showwarning("Warnung", "Bitte eine Frage eingeben.")
                return
                
            if not answer and not answer_image_path:
                messagebox.showwarning("Warnung", "Bitte eine Antwort (Text oder Bild) eingeben.")
                return
                
            if not category or category == "Keine Kategorien":
                messagebox.showwarning("Warnung", "Bitte eine Kategorie auswÃƒÂ¤hlen.")
                return
                
            if not subcat or subcat in ["Bitte Kategorie wÃƒÂ¤hlen", "Keine Unterkategorien"]:
                messagebox.showwarning("Warnung", "Bitte eine Unterkategorie auswÃƒÂ¤hlen.")
                return
            
            # Tags verarbeiten
            tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
            
            try:
                # Bilder kopieren (falls vorhanden)
                final_question_image = None
                final_answer_image = None
                
                if question_image_path:
                    final_question_image = self.data_manager.handle_image(question_image_path)
                    
                if answer_image_path:
                    final_answer_image = self.data_manager.handle_image(answer_image_path)
                
                # Erstelle neue Flashcard
                from data_manager import Flashcard
                new_card = Flashcard(
                    question=question,
                    answer=answer,
                    category=category,
                    subcategory=subcat,
                    tags=tags,
                    question_image_path=final_question_image,  # NEU!
                    image_path=final_answer_image  # Antwort-Bild
                )
                
                if self.data_manager.add_flashcard(new_card):
                    messagebox.showinfo("Erfolg", "Karte wurde erfolgreich hinzugefügt!")
                    
                    # Leitner-System aktualisieren
                    if hasattr(self, 'leitner_system'):
                        try:
                            self.leitner_system.reload_cards()
                        except Exception as e:
                            logging.warning(f"Leitner-System Reload fehlgeschlagen: {e}")
                    
                    # Felder zurücksetzen
                    question_textbox.delete("1.0", "end")
                    answer_textbox.delete("1.0", "end")
                    tags_entry.delete(0, tk.END)
                    self.question_image_path_var.set("")
                    self.answer_image_path_var.set("")
                    question_textbox.focus()
                else:
                    messagebox.showwarning("Warnung", "Karte existiert bereits.")
                    
            except Exception as e:
                logging.error(f"Fehler beim Hinzufügen der Karte: {e}")
                import traceback
                logging.error(traceback.format_exc())
                messagebox.showerror("Fehler", f"Beim Hinzufügen ist ein Fehler aufgetreten: {e}")
        
        # Moderner Button-Container
        button_container = ctk.CTkFrame(
            button_frame,
            fg_color='#f9fafb',
            corner_radius=12,
            border_width=1,
            border_color='#e5e7eb'
        )
        button_container.pack(pady=10)

        button_inner = ctk.CTkFrame(button_container, fg_color='transparent')
        button_inner.pack(padx=20, pady=20)

        ctk.CTkButton(
            button_inner,
            text="✓  Karte speichern",
            command=save_card,
            width=180,
            height=50,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color='#10b981',
            hover_color='#059669',
            corner_radius=12
        ).pack(side='left', padx=8)

        ctk.CTkButton(
            button_inner,
            text="↻  Felder leeren",
            command=lambda: [
                question_textbox.delete("1.0", "end"),
                answer_textbox.delete("1.0", "end"),
                tags_entry.delete(0, tk.END),
                self.question_image_path_var.set(""),
                self.answer_image_path_var.set(""),
                question_textbox.focus()
            ],
            width=180,
            height=50,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#6b7280",
            hover_color="#4b5563",
            corner_radius=12
        ).pack(side='left', padx=8)

        ctk.CTkButton(
            button_inner,
            text="←  Zurück",
            command=self.create_main_menu,
            width=180,
            height=50,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#f3f4f6",
            hover_color="#e5e7eb",
            text_color='#374151',
            corner_radius=12,
            border_width=2,
            border_color='#d1d5db'
        ).pack(side='left', padx=8)

    def _update_date_selection(self, *args):
        """Aktualisiert die Datumsauswahl basierend auf dem gewÃƒÂ¤hlten Zeitraum."""
        # Entferne alle vorhandenen Widgets im date_selection_frame
        for widget in self.date_selection_frame.winfo_children():
            widget.destroy()

        period = self.time_period_var.get()

        if period in ["Tag", "Woche", "Monat"]:
            # Einzelnes Datum für Tag/Woche/Monat
            date_frame = ttk.Frame(self.date_selection_frame)
            date_frame.pack(fill='x', pady=5)

            ttk.Label(date_frame, text="Datum:", width=10).pack(side=tk.LEFT, padx=(0, 5))
            date_entry = ttk.Entry(date_frame, textvariable=self.date_var, state='readonly', width=15)
            date_entry.pack(side=tk.LEFT, padx=(0, 5))

            pick_date_btn = ModernButton(
                date_frame,
                text="Datum wÃƒÂ¤hlen",
                command=lambda: self._pick_calendar_date(self.date_var),
                style=ButtonStyle.SECONDARY.value,
                width=15
            )
            pick_date_btn.pack(side=tk.LEFT)

        elif period == "Benutzerdefiniert":
            # Start-Datum
            start_frame = ttk.Frame(self.date_selection_frame)
            start_frame.pack(fill='x', pady=5)
            
            ttk.Label(start_frame, text="Von:", width=10).pack(side=tk.LEFT, padx=(0, 5))
            start_entry = ttk.Entry(start_frame, textvariable=self.start_date_var, state='readonly', width=15)
            start_entry.pack(side=tk.LEFT, padx=(0, 5))

            pick_start_btn = ModernButton(
                start_frame,
                text="Startdatum wÃƒÂ¤hlen",
                command=lambda: self._pick_calendar_date(self.start_date_var),
                style=ButtonStyle.SECONDARY.value,
                width=15
            )
            pick_start_btn.pack(side=tk.LEFT)

            # End-Datum
            end_frame = ttk.Frame(self.date_selection_frame)
            end_frame.pack(fill='x', pady=5)

            ttk.Label(end_frame, text="Bis:", width=10).pack(side=tk.LEFT, padx=(0, 5))
            end_entry = ttk.Entry(end_frame, textvariable=self.end_date_var, state='readonly', width=15)
            end_entry.pack(side=tk.LEFT, padx=(0, 5))

            pick_end_btn = ModernButton(
                end_frame,
                text="Enddatum wÃƒÂ¤hlen",
                command=lambda: self._pick_calendar_date(self.end_date_var),
                style=ButtonStyle.SECONDARY.value,
                width=15
            )
            pick_end_btn.pack(side=tk.LEFT)


    def bind_mousewheel(self, widget):
        """Mausrad-Bindings für Windows/Linux, um das Canvas zu scrollen."""
        widget.bind("<MouseWheel>", self._on_mousewheel)      # Windows
        widget.bind("<Button-4>", self._on_mousewheel)        # Linux
        widget.bind("<Button-5>", self._on_mousewheel)        # Linux

    def _on_mousewheel(self, event):
        """Wird aufgerufen, wenn das Mausrad gedreht wird."""
        if event.num == 4 or event.delta > 0:
            event.widget.yview_scroll(-1, "units")  # Scroll aufwÃƒÂ¤rts
        elif event.num == 5 or event.delta < 0:
            event.widget.yview_scroll(1, "units")   # Scroll abwÃƒÂ¤rts
    def _pick_calendar_date(self, target_var: tk.StringVar):
        """
        Zeigt ein kleines Fenster mit tkcalendar an,
        um target_var (Start oder End) zu setzen.
        """
        top = tk.Toplevel(self.master)
        top.title("Datum auswÃƒÂ¤hlen")
        top.grab_set()  # Modal machen

        current_date = datetime.datetime.now()
        cal = Calendar(top, font="Arial 14", selectmode='day',
                    locale='de_DE', cursor="hand1",
                    year=current_date.year, month=current_date.month,
                    day=current_date.day, date_pattern="dd.mm.yyyy")
        cal.pack(pady=15, padx=15)

        def set_date():
            dt_str = cal.get_date()
            try:
                datetime.datetime.strptime(dt_str, "%d.%m.%Y")  # Validierung
                target_var.set(dt_str)
                top.destroy()
            except ValueError:
                messagebox.showerror("Fehler", "Ungültiges Datum.")

        btn_frame = ttk.Frame(top)
        btn_frame.pack(pady=5)

        ModernButton(btn_frame, text="OK", command=set_date, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ModernButton(btn_frame, text="Abbrechen", command=top.destroy, style="Secondary.TButton").pack(side=tk.LEFT, padx=5)


    def update_progress_stats(self, *args):
        """Aktualisiert die Statistik-Anzeige basierend auf den gewÃƒÂ¤hlten Filtern."""
        for child in self.progress_chart_frame.winfo_children():
            if not isinstance(child, ttk.LabelFrame) or child != self.filter_frame:
                child.destroy()

        display_frame = ttk.Frame(self.progress_chart_frame)
        display_frame.pack(pady=10, fill='both', expand=True)

        # Hole die Statistiken
        stats = self.data_manager.stats
        if not stats:
            ttk.Label(
                display_frame,
                text="Keine Statistikdaten verfügbar",
                font=(self.appearance_settings.font_family, 12)
            ).pack(pady=20)
            return

        # Filter anwenden
        filtered_stats = []
        comparison_stats = []

        for stat in stats:
            if not isinstance(stat, dict) or 'details' not in stat:
                continue

            # Zeitfilter anwenden
            if not self.passes_time_filter(stat):
                continue

            # Kategorie-Filter anwenden
            category = None if self.selected_category_var.get() == "Alle" else self.selected_category_var.get()
            subcategory = None if self.subcategory_var.get() == "Alle" else self.subcategory_var.get()

            # Statistiken für Hauptkategorie filtern
            filtered_details = []
            for detail in stat.get('details', []):
                matches_category = True if category is None else detail.get('category', '').lower() == category.lower()
                matches_subcategory = True if subcategory is None else detail.get('subcategory', '').lower() == subcategory.lower()
                
                if matches_category and matches_subcategory:
                    filtered_details.append(detail)

            if filtered_details:
                new_stat = stat.copy()
                new_stat['details'] = filtered_details
                new_stat['cards_total'] = len(filtered_details)
                new_stat['cards_correct'] = sum(1 for d in filtered_details if d.get('correct', False))
                filtered_stats.append(new_stat)

            # Vergleichskategorie verarbeiten
            if self.second_category_var.get() != "Keine":
                comp_category = self.second_category_var.get()
                comp_subcategory = None if self.second_subcategory_var.get() == "Alle" else self.second_subcategory_var.get()
                
                comp_details = []
                for detail in stat.get('details', []):
                    matches_category = detail.get('category', '').lower() == comp_category.lower()
                    matches_subcategory = True if comp_subcategory is None else detail.get('subcategory', '').lower() == comp_subcategory.lower()
                    
                    if matches_category and matches_subcategory:
                        comp_details.append(detail)

                if comp_details:
                    comp_stat = stat.copy()
                    comp_stat['details'] = comp_details
                    comp_stat['cards_total'] = len(comp_details)
                    comp_stat['cards_correct'] = sum(1 for d in comp_details if d.get('correct', False))
                    comparison_stats.append(comp_stat)

        # Diagramm basierend auf Typ erstellen
        chart_type = self.chart_type_var.get()
        fig, ax = plt.subplots(figsize=(12, 5))
        plt.style.use('bmh')

        # Chart zeichnen
        draw_methods = {
            "Gesamt": self._draw_total_stats,
            "Richtig/Falsch": self._draw_correct_incorrect,
            "Nach Kategorie": self._draw_category_stats,
            "Kategorien (Kartenzahl)": self._draw_category_card_count,
            "Kategorien (Richtig/Falsch)": self._draw_category_correct_incorrect,
            "Lernzeit": self._draw_learning_time,
            "Heatmap": self._draw_heatmap_extended
        }

        draw_method = draw_methods.get(chart_type, self._draw_total_stats)
        draw_method(ax, filtered_stats, comparison_stats)

        plt.tight_layout()
        
        # Canvas erstellen
        canvas = FigureCanvasTkAgg(fig, master=display_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

        # Zusammenfassende Statistiken anzeigen
        self._show_summary(filtered_stats, comparison_stats, parent_frame=display_frame)

    def passes_time_filter(self, stat):
        """PrÃƒÂ¼ft, ob eine Statistik den Zeitfilter erfÃƒÂ¼llt."""
        time_period = self.time_period_var.get()
        
        if time_period == "Gesamt":
            return True
            
        try:
            stat_date = datetime.datetime.strptime(stat['date'], "%d.%m.%Y").date()
            today = datetime.date.today()
            
            if time_period == "Tag":
                filter_date = datetime.datetime.strptime(self.date_var.get(), "%d.%m.%Y").date()
                return stat_date == filter_date
                
            elif time_period == "Woche":
                filter_date = datetime.datetime.strptime(self.date_var.get(), "%d.%m.%Y").date()
                week_start = filter_date - datetime.timedelta(days=filter_date.weekday())
                week_end = week_start + datetime.timedelta(days=6)
                return week_start <= stat_date <= week_end
                
            elif time_period == "Monat":
                filter_date = datetime.datetime.strptime(self.date_var.get(), "%d.%m.%Y").date()
                return stat_date.year == filter_date.year and stat_date.month == filter_date.month
                
            elif time_period == "Benutzerdefiniert":
                start_date = datetime.datetime.strptime(self.start_date_var.get(), "%d.%m.%Y").date()
                end_date = datetime.datetime.strptime(self.end_date_var.get(), "%d.%m.%Y").date()
                return start_date <= stat_date <= end_date
                
        except (ValueError, KeyError, AttributeError) as e:
            logging.error(f"Fehler bei der Zeitfilterung: {e}")
            return False
            
        return True
    def _get_chart_labels(self):
        """
        Gibt zwei Strings zurück:
        - main_label: Beschriftung für die ausgewÃƒÂ¤hlte Hauptkategorie / Unterkategorie
        - comp_label: Beschriftung für die ausgewÃƒÂ¤hlte Vergleichskategorie / Unterkategorie
        """
        main_cat = self.selected_category_var.get()
        main_subcat = self.subcategory_var.get()
        
        second_cat = self.second_category_var.get()
        second_subcat = self.second_subcategory_var.get()

        # Hauptbeschriftung
        if main_cat == "Alle":
            main_label = "Alle Kategorien"
        else:
            main_label = main_cat
            if main_subcat != "Alle":
                main_label += f" > {main_subcat}"  # z. B. "Chemie > Grundlagen"

        # Vergleichsbeschriftung
        if second_cat == "Keine":
            comp_label = ""
        else:
            comp_label = second_cat
            if second_subcat != "Alle":
                comp_label += f" > {second_subcat}"

        return main_label, comp_label

    def _draw_total_stats(self, ax, stats, comparison_stats=None):
        """Zeichnet die Gesamtstatistik der gelernten Karten."""

        # ---------- Hauptkategorie-Daten aggregieren ----------
        daily_stats = defaultdict(lambda: {"total": 0, "correct": 0})
        for stat in stats:
            if isinstance(stat, dict) and 'date' in stat:
                date = stat['date']
                # Direkt summieren von cards_total und cards_correct
                daily_stats[date]["total"] += stat.get('cards_total', 0)
                daily_stats[date]["correct"] += stat.get('cards_correct', 0)

        # Sortierte Datumsstrings
        dates = sorted(daily_stats.keys(), key=lambda d: datetime.datetime.strptime(d, "%d.%m.%Y"))
        totals = [daily_stats[d]["total"] for d in dates]
        corrects = [daily_stats[d]["correct"] for d in dates]

        # In datetime konvertieren, damit matplotlib die X-Achse korrekt formatiert
        x_dates = [datetime.datetime.strptime(d, "%d.%m.%Y") for d in dates]

        # Hole Labels für Hauptkategorie und Vergleich
        main_label, comp_label = self._get_chart_labels()

        # ---------- Hauptlinien zeichnen ----------
        ax.plot(x_dates, totals, '-o', color='#4a90e2',
                label=f"{main_label} - Gesamt",
                linewidth=2, markersize=8)
        ax.plot(x_dates, corrects, '-s', color='#2ecc71',
                label=f"{main_label} - Korrekt",
                linewidth=2, markersize=8)

        # ---------- Vergleich, falls ausgewÃƒÂ¤hlt ----------
        if comparison_stats and self.second_category_var.get() != "Keine":
            comp_daily_stats = defaultdict(lambda: {"total": 0, "correct": 0})
            for stat in comparison_stats:
                if isinstance(stat, dict) and 'date' in stat:
                    date = stat['date']
                    comp_daily_stats[date]["total"] += stat.get('cards_total', 0)
                    comp_daily_stats[date]["correct"] += stat.get('cards_correct', 0)

            comp_dates = sorted(comp_daily_stats.keys(), key=lambda d: datetime.datetime.strptime(d, "%d.%m.%Y"))
            comp_totals = [comp_daily_stats[d]["total"] for d in comp_dates]
            comp_corrects = [comp_daily_stats[d]["correct"] for d in comp_dates]
            comp_x_dates = [datetime.datetime.strptime(d, "%d.%m.%Y") for d in comp_dates]

            ax.plot(comp_x_dates, comp_totals, '--o', color='#e74c3c',
                    label=f"{comp_label} - Gesamt",
                    linewidth=2, markersize=6, alpha=0.7)
            ax.plot(comp_x_dates, comp_corrects, '--s', color='#f1c40f',
                    label=f"{comp_label} - Korrekt",
                    linewidth=2, markersize=6, alpha=0.7)

        # ---------- Dynamischer Titel ----------
        if self.second_category_var.get() != "Keine":
            ax.set_title(f"Vergleich: {main_label} vs. {comp_label}")
        else:
            if main_label.lower().startswith("alle"):
                ax.set_title("Gesamtstatistik")
            else:
                ax.set_title(f"Statistik: {main_label}")

        # ---------- Achsen- und Layout-Format ----------
        ax.set_xlabel("Datum")
        ax.set_ylabel("Anzahl Karten")

        # X-Achse formatieren
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())

        # Werte annotieren
        for xd, t, c in zip(x_dates, totals, corrects):
            ax.annotate(f'{t}', (xd, t), textcoords="offset points", xytext=(0, 10),
                        ha='center', fontsize=8)
            ax.annotate(f'{c}', (xd, c), textcoords="offset points", xytext=(0, -15),
                        ha='center', fontsize=8)

        # Legende, Grid, Ticks
        ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1))
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        plt.tight_layout()

        # Y-Achse bei 0 starten und etwas Puffer nach oben
        y_max_main = max(totals + corrects) if (totals and corrects) else 0

        y_max_comp = 0
        if comparison_stats:
            if comp_totals and comp_corrects:
                y_max_comp = max(comp_totals + comp_corrects)

        overall_y_max = max(y_max_main, y_max_comp)
        ax.set_ylim(bottom=0, top=overall_y_max * 1.1 if overall_y_max > 0 else 1)

    def _draw_category_card_count(self, ax, stats, comparison_stats=None):
        """
        Zeichnet ein Balkendiagramm mit der Anzahl der aktuell verfügbaren Karten pro Kategorie.
        """
        category_counts = defaultdict(int)

        # Hole die aktuelle Liste der Kategorien aus dem data_manager
        valid_categories = set(self.data_manager.categories.keys())

        # ZÃƒÂ¤hle nur Karten in aktuell existierenden Kategorien
        for card in self.data_manager.flashcards:
            if (isinstance(card, Flashcard) and 
                card.category in valid_categories):  # PrÃƒÂ¼fe, ob die Kategorie noch existiert
                category_counts[card.category] += 1

        # Wenn eine spezifische Kategorie ausgewÃƒÂ¤hlt ist
        selected_category = self.selected_category_var.get()
        if selected_category != "Alle":
            if selected_category in valid_categories:  # ZusÃƒÂ¤tzliche PrÃƒÂ¼fung
                category_counts = {k: v for k, v in category_counts.items() 
                                if k.lower() == selected_category.lower()}

        # Wenn eine Subkategorie ausgewÃƒÂ¤hlt ist
        selected_subcategory = self.subcategory_var.get()
        if selected_subcategory != "Alle":
            category_counts = defaultdict(int)
            # PrÃƒÂ¼fe, ob die Subkategorie in der ausgewÃƒÂ¤hlten Kategorie noch existiert
            valid_subcategories = set()
            if selected_category != "Alle":
                valid_subcategories = set(self.data_manager.categories.get(selected_category, {}).keys())
            else:
                # Sammle alle gÃƒÂ¼ltigen Subkategorien aus allen Kategorien
                for cat_subcats in self.data_manager.categories.values():
                    valid_subcategories.update(cat_subcats.keys())

            for card in self.data_manager.flashcards:
                if (isinstance(card, Flashcard) and 
                    card.category in valid_categories and
                    card.subcategory in valid_subcategories and
                    (selected_category == "Alle" or card.category.lower() == selected_category.lower()) and
                    card.subcategory.lower() == selected_subcategory.lower()):
                    category_counts[card.category] += 1

        if not category_counts:
            ax.text(0.5, 0.5, "Keine Karten verfügbar", ha='center', va='center')
            return

        categories = list(category_counts.keys())
        counts = list(category_counts.values())

        # Erstelle das Balkendiagramm
        bars = ax.bar(categories, counts, color='#4a90e2', alpha=0.7)
        
        # Setze Titel und Labels
        if selected_subcategory != "Alle":
            ax.set_title(f'Aktuelle Kartenanzahl in Subkategorie "{selected_subcategory}"')
        elif selected_category != "Alle":
            ax.set_title(f'Aktuelle Kartenanzahl in Kategorie "{selected_category}"')
        else:
            ax.set_title('Aktuelle Kartenanzahl pro Kategorie')
        
        ax.set_xlabel('Kategorie')
        ax.set_ylabel('Anzahl Karten')
        ax.set_ylim(bottom=0)

        # FÃƒÂ¼ge Werte über den Balken hinzu
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom')

        # Rotiere die x-Achsen-Labels für bessere Lesbarkeit
        plt.xticks(rotation=45, ha='right')

    def _draw_category_correct_incorrect(self, ax, stats, comparison_stats=None):
        """Zeichnet ein gestapeltes Balkendiagramm mit der Anzahl der richtigen und falschen Karten pro Kategorie."""
        # Datenaggregation mit Pandas
        data = []
        for stat in stats:
            if 'details' in stat:
                for detail in stat['details']:
                    if isinstance(detail, dict) and 'category' in detail:
                        data.append({
                            'category': detail['category'],
                            'correct': detail.get('correct', 0),
                            'incorrect': not detail.get('correct', 0)
                        })

        if not data:
            ax.text(0.5, 0.5, "Keine Daten verfügbar", ha='center', va='center')
            return

        df = pd.DataFrame(data)
        grouped = df.groupby('category').agg({
            'correct': 'sum',
            'incorrect': 'sum'
        }).reset_index()

        categories = grouped['category']
        correct = grouped['correct']
        incorrect = grouped['incorrect']

        bar_width = 0.6
        bars_correct = ax.bar(categories, correct, bar_width, label='Richtig', color='green', alpha=0.7)
        bars_incorrect = ax.bar(categories, incorrect, bar_width, bottom=correct, label='Falsch', color='red', alpha=0.7)

        ax.set_title('Richtig/Falsch-Statistik nach Kategorie')
        ax.set_xlabel('Kategorie')
        ax.set_ylabel('Anzahl Karten')
        ax.legend()
        plt.xticks(rotation=45, ha='right')

        # FÃƒÂ¼ge Werte über den Balken hinzu
        for rect_correct, rect_incorrect in zip(bars_correct, bars_incorrect):
            height_correct = rect_correct.get_height()
            height_incorrect = rect_incorrect.get_height()
            ax.text(rect_correct.get_x() + rect_correct.get_width()/2., height_correct + height_incorrect + 0.5,
                    f'{height_correct}\n{height_incorrect}', ha='center', va='bottom', fontsize=8)

    def filter_stats_by_date(self, stats, time_period, date_str=None, start_date=None, end_date=None):
        """
        Filtert Statistiken basierend auf dem gewÃƒÂ¤hlten Zeitraum.
        
        Args:
            stats: Die zu filternden Statistiken
            time_period: Der Zeitraum ('Tag', 'Woche', 'Monat', 'Benutzerdefiniert', 'Gesamt')
            date_str: Das ausgewÃƒÂ¤hlte Datum (für Tag/Woche/Monat)
            start_date: Startdatum für benutzerdefinierten Zeitraum
            end_date: Enddatum für benutzerdefinierten Zeitraum
        
        Returns:
            List: Gefilterte Statistiken
        """
        filtered_stats = []
        
        # Wenn kein Datum ausgewÃƒÂ¤hlt wurde und ein Datum benötigt wird, zeige eine Warnung
        if time_period in ['Tag', 'Woche', 'Monat'] and not date_str:
            messagebox.showwarning("Warnung", "Bitte wÃƒÂ¤hlen Sie ein Datum aus.")
            return []

        # Für benutzerdefinierten Zeitraum beide Daten prÃƒÂ¼fen
        if time_period == 'Benutzerdefiniert' and (not start_date or not end_date):
            messagebox.showwarning("Warnung", "Bitte wÃƒÂ¤hlen Sie Start- und Enddatum aus.")
            return []

        try:
            # Verarbeitung des ausgewÃƒÂ¤hlten Datums
            selected_date = None
            week_start = None
            week_end = None
            month_start = None
            month_end = None

            if time_period in ['Tag', 'Woche', 'Monat'] and date_str:
                selected_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
                
                if time_period == 'Woche':
                    # Berechne Start und Ende der Woche
                    week_start = selected_date - datetime.timedelta(days=selected_date.weekday())
                    week_end = week_start + datetime.timedelta(days=6)
                
                elif time_period == 'Monat':
                    # Berechne Start und Ende des Monats
                    month_start = selected_date.replace(day=1)
                    if month_start.month == 12:
                        month_end = month_start.replace(year=month_start.year + 1, month=1) - datetime.timedelta(days=1)
                    else:
                        month_end = month_start.replace(month=month_start.month + 1) - datetime.timedelta(days=1)

            elif time_period == 'Benutzerdefiniert':
                start = datetime.datetime.strptime(start_date, "%d.%m.%Y").date()
                end = datetime.datetime.strptime(end_date, "%d.%m.%Y").date()
                if start > end:
                    start, end = end, start  # Tausche Start und Ende, wenn Start spÃƒÂ¤ter als Ende

            # Filtere die Statistiken
            for stat in stats:
                if not isinstance(stat, dict) or 'date' not in stat:
                    continue

                try:
                    stat_date = datetime.datetime.strptime(stat['date'], "%d.%m.%Y").date()
                except ValueError as e:
                    logging.error(f"Ungültiges Datum in Statistik: {stat.get('date', '')}: {e}")
                    continue

                # Filterlogik basierend auf dem Zeitraum
                if time_period == 'Tag' and selected_date:
                    if stat_date == selected_date:
                        filtered_stats.append(stat)
                
                elif time_period == 'Woche' and week_start and week_end:
                    if week_start <= stat_date <= week_end:
                        filtered_stats.append(stat)
                
                elif time_period == 'Monat' and month_start and month_end:
                    if month_start <= stat_date <= month_end:
                        filtered_stats.append(stat)
                
                elif time_period == 'Benutzerdefiniert' and start and end:
                    if start <= stat_date <= end:
                        filtered_stats.append(stat)
                
                elif time_period == 'Gesamt':
                    filtered_stats.append(stat)

        except ValueError as e:
            logging.error(f"Fehler bei der Datumsverarbeitung: {e}")
            messagebox.showerror("Fehler", f"Ungültiges Datumsformat: {e}")
            return []
        
        except Exception as e:
            logging.error(f"Unerwarteter Fehler bei der Statistikfilterung: {e}")
            messagebox.showerror("Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}")
            return []

        logging.info(f"Statistiken gefiltert für Zeitraum {time_period}: {len(filtered_stats)} EintrÃƒÂ¤ge gefunden")
        return filtered_stats
    def update_time_range_labels(self, stats):
        """Bestimmt das geeignete Datumformat basierend auf der Zeitspanne."""
        if not stats:
            return "%d.%m"
            
        dates = [datetime.datetime.strptime(stat['date'], "%d.%m.%Y").date() for stat in stats]
        min_date = min(dates)
        max_date = max(dates)
        
        # Berechne die Zeitspanne
        time_delta = (max_date - min_date).days
        
        if time_delta <= 7:  # Weniger als eine Woche
            return "%d.%m"
        elif time_delta <= 31:  # Weniger als ein Monat
            return "%d.%m"
        elif time_delta <= 365:  # Weniger als ein Jahr
            return "%b %Y"  # Monat und Jahr
        else:  # Mehr als ein Jahr
            return "%d.%m.%Y"



    def _draw_heatmap_extended(self, ax, stats, comparison_stats=None, time_period="Gesamt"):
        """Zeichnet ein erweitertes WÃƒÂ¤rmediagramm mit dynamischer Aggregation und angepasster X- und Y-Achse."""

        # Definiere Erfolgsrate-Bins
        bins = [0, 25, 50, 75, 100]
        labels = ["0-25%", "25-50%", "50-75%", "75-100%"]

        data = []

        if time_period != "Gesamt":
            # Normalfall: Heatmap mit Binning
            for stat in stats:
                if 'date' not in stat or 'details' not in stat:
                    continue
                try:
                    date = datetime.datetime.strptime(stat['date'], "%d.%m.%Y")
                    correct = stat.get('cards_correct', 0)
                    total = stat.get('cards_total', 0)
                    success_rate = (correct / total * 100) if total > 0 else 0

                    # Bestimme den AggregationsschlÃƒÂ¼ssel basierend auf dem Zeitfilter
                    if time_period == "Tag":
                        date_key = date.strftime("%d.%m")
                    elif time_period == "Woche":
                        # Korrektur für Wochennummer
                        week = date.isocalendar()[1]
                        year = date.year
                        date_key = f"W{week:02}-{year}"  # FÃƒÂ¼ge fÃƒÂ¼hrende Null für Wochennummer hinzu
                    elif time_period == "Monat":
                        date_key = date.strftime("%m.%Y")
                    else:  # Andere Zeitfilter
                        date_key = date.strftime("%d.%m")  # Behalte das Format für Konsistenz

                    # Weisen Sie die Erfolgsrate einem Bin zu
                    bin_label = pd.cut([success_rate], bins=bins, labels=labels, include_lowest=True)[0]

                    data.append({
                        'success_rate_bin': bin_label,
                        'date': date_key
                    })
                except ValueError:
                    logging.error(f"Ungültiges Datum in Statistik: {stat.get('date', '')}")
                    continue

            if not data:
                ax.text(0.5, 0.5, "Keine Daten für Heatmap verfügbar", ha='center', va='center')
                return

            df = pd.DataFrame(data)

            # Definiere 'success_rate_bin' als Categorical, um sicherzustellen, dass alle Labels vorhanden sind
            df['success_rate_bin'] = pd.Categorical(df['success_rate_bin'], categories=labels, ordered=True)

            # ZÃƒÂ¤hle Vorkommen pro Erfolgsrate-Bin und Datum
            heatmap_data = df.groupby(['success_rate_bin', 'date']).size().unstack(fill_value=0)

            # Reindex, um sicherzustellen, dass alle Bins vorhanden sind
            heatmap_data = heatmap_data.reindex(labels, fill_value=0)

            # Sortiere die Spalten (Datum) basierend auf der Aggregation
            try:
                if time_period == "Monat":
                    # Konvertiere Spalten in datetime und sortiere
                    heatmap_data.columns = pd.to_datetime(heatmap_data.columns, format="%m.%Y")
                    heatmap_data = heatmap_data.sort_index(axis=1)
                    heatmap_data.columns = heatmap_data.columns.strftime("%m.%Y")
                elif time_period == "Woche":
                    # ISO Kalenderwoche: W{week}-{year}, setze auf Montag der Woche
                    def parse_week_label(week_label):
                        try:
                            week_num, year = map(int, week_label[1:].split('-'))
                            return datetime.datetime.strptime(f'{year}-W{week_num}-1', "%Y-W%W-%w")
                        except Exception as e:
                            logging.error(f"Fehler beim Parsen von Woche {week_label}: {e}")
                            return pd.NaT

                    heatmap_data.columns = heatmap_data.columns.map(parse_week_label)
                    heatmap_data = heatmap_data.sort_index(axis=1)
                    heatmap_data.columns = heatmap_data.columns.strftime("W%W-%Y")
                elif time_period == "Tag":
                    # Konvertiere Spalten in datetime und sortiere
                    heatmap_data.columns = pd.to_datetime(heatmap_data.columns, format="%d.%m")
                    heatmap_data = heatmap_data.sort_index(axis=1)
                    heatmap_data.columns = heatmap_data.columns.strftime("%d.%m")
                else:
                    # Andere Zeitfilter: Behalte Tag-Monat
                    heatmap_data.columns = pd.to_datetime(heatmap_data.columns, format="%d.%m", errors='coerce')
                    heatmap_data = heatmap_data.sort_index(axis=1)
                    heatmap_data.columns = heatmap_data.columns.strftime("%d.%m")
            except Exception as e:
                logging.error(f"Fehler beim Sortieren der Pivot-Tabelle: {e}")
                # Fallback: Sortiere als String
                heatmap_data = heatmap_data.sort_index(axis=1)

            # Erstelle die Heatmap
            sns.heatmap(
                heatmap_data,
                cmap='YlOrRd',
                ax=ax,
                annot=True,
                fmt='d',
                cbar_kws={'label': 'Anzahl'},
                linewidths=.5,
                linecolor='gray'
            )

            ax.set_title('Anzahl der Erfolgsquoten nach Datum')
            ax.set_xlabel('Datum')
            ax.set_ylabel('Erfolgsrate (%)')

            # Setze die Y-Achsen-Beschriftungen in 25%-Schritten
            ax.set_yticks(np.arange(len(labels)) + 0.5)  # Positionen in der Mitte der Bins
            ax.set_yticklabels(labels, rotation=0)

            # Setze die Y-Achsen-Limits
            ax.set_ylim(0, len(labels))

        else:
            # Spezialfall: "Gesamt" - Zeige die Erfolgsrate direkt als Heatmap ohne Binning
            for stat in stats:
                if 'date' not in stat or 'details' not in stat:
                    continue
                try:
                    date = datetime.datetime.strptime(stat['date'], "%d.%m.%Y")
                    correct = stat.get('cards_correct', 0)
                    total = stat.get('cards_total', 0)
                    success_rate = (correct / total * 100) if total > 0 else 0

                    # Bestimme den AggregationsschlÃƒÂ¼ssel basierend auf dem Zeitfilter
                    if time_period == "Tag":
                        date_key = date.strftime("%d.%m")
                    elif time_period == "Woche":
                        # Korrektur für Wochennummer
                        week = date.isocalendar()[1]
                        year = date.year
                        date_key = f"W{week:02}-{year}"  # FÃƒÂ¼ge fÃƒÂ¼hrende Null für Wochennummer hinzu
                    elif time_period == "Monat":
                        date_key = date.strftime("%m.%Y")
                    else:  # "Gesamt" oder andere
                        date_key = date.strftime("%d.%m")  # Behalte das Format für Konsistenz

                    data.append({
                        'date': date_key,
                        'success_rate': success_rate
                    })
                except ValueError:
                    logging.error(f"Ungültiges Datum in Statistik: {stat.get('date', '')}")
                    continue

            if not data:
                ax.text(0.5, 0.5, "Keine Daten für Heatmap verfügbar", ha='center', va='center')
                return

            df = pd.DataFrame(data)

            # Gruppiere die Daten nach Datum und berechne den Durchschnitt (falls nötig)
            heatmap_data = df.groupby('date')['success_rate'].mean()

            # Sortiere die Daten basierend auf dem Zeitfilter
            try:
                if time_period == "Monat":
                    heatmap_data.index = pd.to_datetime(heatmap_data.index, format="%m.%Y")
                elif time_period == "Woche":
                    # ISO Kalenderwoche: W{week}-{year}, setze auf Montag der Woche
                    def parse_week_label(week_label):
                        try:
                            week_num, year = map(int, week_label[1:].split('-'))
                            return datetime.datetime.strptime(f'{year}-W{week_num}-1', "%Y-W%W-%w")
                        except Exception as e:
                            logging.error(f"Fehler beim Parsen von Woche {week_label}: {e}")
                            return pd.NaT

                    heatmap_data.index = heatmap_data.index.map(parse_week_label)
                elif time_period == "Tag":
                    heatmap_data.index = pd.to_datetime(heatmap_data.index, format="%d.%m")
                else:
                    heatmap_data.index = pd.to_datetime(heatmap_data.index, format="%d.%m", errors='coerce')

                heatmap_data = heatmap_data.sort_index()
            except Exception as e:
                logging.error(f"Fehler beim Sortieren der Pivot-Tabelle: {e}")
                # Fallback: Sortiere als String
                heatmap_data = heatmap_data.sort_index()

            # Nach der Sortierung die Index wieder in das gewÃƒÂ¼nschte Format bringen
            if time_period == "Monat":
                heatmap_data.index = heatmap_data.index.strftime("%m.%Y")
            elif time_period == "Woche":
                heatmap_data.index = heatmap_data.index.strftime("W%W-%Y")
            elif time_period == "Tag":
                heatmap_data.index = heatmap_data.index.strftime("%d.%m")
            else:
                heatmap_data.index = heatmap_data.index.strftime("%d.%m")

            # Reshape heatmap_data to have a single row
            heatmap_df = heatmap_data.to_frame().T  # Single row DataFrame

            # Erstelle die Heatmap
            sns.heatmap(
                heatmap_df,
                cmap='YlOrRd',
                ax=ax,
                annot=True,
                fmt='.1f',
                cbar_kws={'label': 'Erfolgsquote (%)'},
                linewidths=.5,
                linecolor='gray'
            )

            ax.set_title('Erfolgsquote nach Datum')
            ax.set_xlabel('Datum')
            ax.set_ylabel('Erfolgsquote (%)')  # Nur ein einziges Label

            # Kein Y-Tick-Label notwendig, da nur eine Zeile vorhanden ist
            ax.set_yticks([])  # Entferne Y-Ticks

            # Setze die Y-Achsen-Limits
            ax.set_ylim(0, 1)

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

            

    def _draw_learning_time(self, ax, stats, comparison_stats=None):
        """Zeichnet die Lernzeitstatistik."""
        main_label, comp_label = self._get_chart_labels()

        # ---------- Haupt-Lernzeit pro Tag aggregieren ----------
        daily_times = defaultdict(float)
        for stat in stats:
            if isinstance(stat, dict) and 'date' in stat:
                date = stat['date']
                daily_times[date] += stat.get('total_time', 0)

        dates = sorted(daily_times.keys())
        times = [daily_times[d] for d in dates]
        x_dates = [datetime.datetime.strptime(d, "%d.%m.%Y") for d in dates]

        # Zeichne Hauptlinie
        ax.plot(x_dates, times, '-o', label=f"Lernzeit: {main_label}", linewidth=2)

        # ---------- Vergleich, falls vorhanden ----------
        if comparison_stats and self.second_category_var.get() != "Keine":
            comp_daily_times = defaultdict(float)
            for stat in comparison_stats:
                if isinstance(stat, dict) and 'date' in stat:
                    date = stat['date']
                    comp_daily_times[date] += stat.get('total_time', 0)

            comp_dates = sorted(comp_daily_times.keys())
            comp_times = [comp_daily_times[d] for d in comp_dates]
            comp_x = [datetime.datetime.strptime(d, "%d.%m.%Y") for d in comp_dates]

            ax.plot(comp_x, comp_times, '--s', label=f"Lernzeit: {comp_label}", linewidth=2)

        # ---------- Titel ----------
        if self.second_category_var.get() != "Keine":
            ax.set_title(f"Lernzeit-Verlauf: {main_label} vs. {comp_label}")
        else:
            if main_label.lower().startswith("alle"):
                ax.set_title("Lernzeit-Verlauf (alle Kategorien)")
            else:
                ax.set_title(f"Lernzeit-Verlauf: {main_label}")

        ax.set_xlabel("Datum")
        ax.set_ylabel("Lernzeit (Minuten)")

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())

        ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1))
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        plt.tight_layout()

        ax.set_ylim(bottom=0)
        if times:
            y_max = max(times)
            ax.set_ylim(top=y_max * 1.1)

    def _draw_correct_incorrect(self, ax, stats, comparison_stats=None):
        """Zeichnet die Richtig/Falsch-Statistik."""
        daily_stats = defaultdict(lambda: {"correct": 0, "total": 0})
        for stat in stats:
            if isinstance(stat, dict) and 'date' in stat and 'details' in stat:
                date = stat['date']
                details = stat.get('details', [])
                daily_stats[date]["correct"] += sum(1 for d in details if d.get('correct', False))
                daily_stats[date]["total"] += len(details)

        # Sortieren
        dates = sorted(daily_stats.keys())
        corrects = [daily_stats[d]["correct"] for d in dates]
        totals = [daily_stats[d]["total"] for d in dates]
        incorrects = [t - c for t, c in zip(totals, corrects)]

        x_dates = [datetime.datetime.strptime(d, "%d.%m.%Y") for d in dates]
        main_label, comp_label = self._get_chart_labels()

        # ---------- Balkenplot für richtig/falsch ----------
        ax.bar(x_dates, corrects, label=f"{main_label} - Richtig", color='green', alpha=0.7)
        ax.bar(x_dates, incorrects, bottom=corrects, label=f"{main_label} - Falsch", color='red', alpha=0.7)

        # ---------- Vergleich -----------
        if comparison_stats and self.second_category_var.get() != "Keine":
            # Aggregation
            comp_daily_stats = defaultdict(lambda: {"correct": 0, "total": 0})
            for stat in comparison_stats:
                if isinstance(stat, dict) and 'date' in stat and 'details' in stat:
                    date = stat['date']
                    details = stat.get('details', [])
                    comp_daily_stats[date]["correct"] += sum(1 for d in details if d.get('correct', False))
                    comp_daily_stats[date]["total"] += len(details)

            comp_dates = sorted(comp_daily_stats.keys())
            comp_corrects = [comp_daily_stats[d]["correct"] for d in comp_dates]
            comp_totals = [comp_daily_stats[d]["total"] for d in comp_dates]
            comp_x = [datetime.datetime.strptime(d, "%d.%m.%Y") for d in comp_dates]

            # Kleine Linien oder Punkte zum Vergleich
            ax.plot(comp_x, comp_corrects, '--s', color='darkgreen',
                    label=f"{comp_label} - Richtig", linewidth=2, markersize=6, alpha=0.8)
            ax.plot(comp_x, comp_totals, '--o', color='darkred',
                    label=f"{comp_label} - Gesamt", linewidth=2, markersize=6, alpha=0.8)

        # ---------- Titel festlegen ----------
        if self.second_category_var.get() != "Keine":
            ax.set_title(f"Richtig/Falsch Vergleich: {main_label} vs. {comp_label}")
        else:
            if main_label.lower().startswith("alle"):
                ax.set_title("Richtig/Falsch (alle Kategorien)")
            else:
                ax.set_title(f"Richtig/Falsch: {main_label}")

        ax.set_xlabel("Datum")
        ax.set_ylabel("Anzahl Karten")

        # X-Achse
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())

        # Legende, Grid
        ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1))
        ax.grid(True, linestyle='--', alpha=0.7)

        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        plt.tight_layout()

        # Y-Achse bei 0 starten
        ax.set_ylim(bottom=0)
        if totals:
            y_max = max(max(totals), max(corrects))
            ax.set_ylim(top=y_max * 1.1)
        
    def _draw_category_stats(self, ax, stats, comparison_stats=None):
        """Zeichnet die Statistik nach Kategorien."""
        if not stats:
            return
        
        # Sammle Daten pro Kategorie
        category_data = {}
        for stat in stats:
            if 'details' in stat:
                for detail in stat.get('details', []):
                    category = detail.get('category', 'Unbekannt')
                    if category not in category_data:
                        category_data[category] = {
                            'total': 0,
                            'correct': 0
                        }
                    category_data[category]['total'] += 1
                    if detail.get('correct'):
                        category_data[category]['correct'] += 1

        # Bereite Daten für das Diagramm vor
        categories = list(category_data.keys())
        success_rates = []
        for cat in categories:
            total = category_data[cat]['total']
            correct = category_data[cat]['correct']
            rate = (correct / total * 100) if total > 0 else 0
            success_rates.append(rate)

        # Erstelle das Balkendiagramm
        bars = ax.bar(categories, success_rates)
        
        ax.set_title('Erfolgsquote nach Kategorien')
        ax.set_xlabel('Kategorie')
        ax.set_ylabel('Erfolgsquote (%)')
        ax.set_ylim(0, 100)
        plt.xticks(rotation=45, ha='right')

        # FÃƒÂ¼ge Werte über den Balken hinzu
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom')

        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        return ax

    def _show_summary(self, stats, comparison_stats=None, parent_frame=None):
        """Zeigt eine kompakte Zusammenfassung der Statistiken als Caption."""
        if parent_frame is None:
            parent_frame = self.progress_chart_frame

        # Erstelle ein Frame für die Caption
        caption_frame = ttk.Frame(parent_frame)
        caption_frame.pack(fill='x', pady=5, padx=10)

        # Berechne die Statistiken
        total_cards = sum(stat.get('cards_total', 0) for stat in stats)
        correct_cards = sum(stat.get('cards_correct', 0) for stat in stats)
        success_rate = (correct_cards / total_cards * 100) if total_cards > 0 else 0
        total_time = sum(stat.get('total_time', 0) for stat in stats)
        unique_dates = len(set(stat['date'] for stat in stats if 'date' in stat))

        # Hauptstatistiken
        main_stats = (
            f"Sitzungen: {unique_dates}\n"
            f"Karten: {total_cards}\n"
            f"Korrekt: {correct_cards}\n"
            f"Erfolgsquote: {success_rate:.1f}%\n"
            f"Lernzeit: {total_time} Min."
        )

        ttk.Label(
            caption_frame, 
            text=main_stats,
            font=(self.appearance_settings.font_family, 10, 'bold'),
            justify='left',
            background="#f0f0f0",
            padding=10
        ).pack(anchor='w', fill='x', pady=2)

        # Vergleichsstatistiken, falls vorhanden
        if comparison_stats:
            comp_total = sum(stat.get('cards_total', 0) for stat in comparison_stats)
            comp_correct = sum(stat.get('cards_correct', 0) for stat in comparison_stats)
            comp_rate = (comp_correct / comp_total * 100) if comp_total > 0 else 0
            comp_time = sum(stat.get('total_time', 0) for stat in comparison_stats)

            comp_stats = (
                f"Vergleich:\n"
                f"Karten: {comp_total}\n"
                f"Korrekt: {comp_correct}\n"
                f"Erfolgsquote: {comp_rate:.1f}%\n"
                f"Lernzeit: {comp_time} Min."
            )

            ttk.Label(
                caption_frame,
                text=comp_stats,
                font=(self.appearance_settings.font_family, 10),
                justify='left',
                background="#e0e0e0",
                padding=10
            ).pack(anchor='w', fill='x', pady=(2, 0))


    def _match_year_month(self, date_str: str, year: int, month: int):
        """
        Hilfsfunktion: PrÃƒÂ¼ft, ob das Datumsformat dd.mm.yyyy
        mit 'year' und 'month' übereinstimmt.
        """
        try:
            d = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
            return (d.year == year and d.month == month)
        except:
            return False

    def enable_touch_scrolling(self, canvas):
        """Aktiviert Drag/Touch-Scrolling via 'scan_mark' und 'scan_dragto'."""
        def on_mouse_down(event):
            canvas.scan_mark(event.x, event.y)

        def on_mouse_move(event):
            canvas.scan_dragto(event.x, event.y, gain=1)

        # Plattformübergreifende Bindings
        if platform.system() == 'Windows':
            canvas.bind("<Button-1>", on_mouse_down)
            canvas.bind("<B1-Motion>", on_mouse_move)
        elif platform.system() == 'Darwin':  # macOS
            canvas.bind("<Button-1>", on_mouse_down)
            canvas.bind("<B1-Motion>", on_mouse_move)
        else:  # Linux und andere
            canvas.bind("<Button-1>", on_mouse_down)
            canvas.bind("<B1-Motion>", on_mouse_move)

    # -----------------------------------------------------------------------------------
    # STYLE KONFIGURATION (inklusive der aktualisierten Methoden und ButtonStyles)
    # -----------------------------------------------------------------------------------
    def configure_styles(self):
        """
        Konfiguriert benutzerdefinierte Styles für ttk-Widgets, einschlieÃƒÅ¸lich Hover-Effekten für Buttons.
        """
        self.style.theme_use('default')

        # Primary Button Style
        self.style.configure(ButtonStyle.PRIMARY.value,
                            background=self.appearance_settings.button_bg_color,
                            foreground=self.appearance_settings.button_fg_color,
                            font=(self.appearance_settings.font_family, self.appearance_settings.font_size, "bold"),
                            relief="flat")
        self.style.map(ButtonStyle.PRIMARY.value,
                    background=[('active', COLORS["hover"]), ('pressed', COLORS["active"])],
                    relief=[('pressed', 'sunken')])

        # Active Primary Button Style
        self.style.configure(ButtonStyle.ACTIVE_PRIMARY.value,
                            background=COLORS["active"],
                            foreground=self.appearance_settings.button_fg_color,
                            font=(self.appearance_settings.font_family, self.appearance_settings.font_size, "bold"),
                            relief="flat")

        # Secondary Button Style
        self.style.configure(ButtonStyle.SECONDARY.value,
                            background=BUTTON_STYLES['secondary']['bg'],
                            foreground=BUTTON_STYLES['secondary']['fg'],
                            font=BUTTON_STYLES['secondary']['font'],
                            relief="flat")
        self.style.map(ButtonStyle.SECONDARY.value,
                    background=[('active', COLORS["hover"]), ('pressed', COLORS["active"])],
                    relief=[('pressed', 'sunken')])

        # Active Secondary Button Style
        self.style.configure(ButtonStyle.ACTIVE_SECONDARY.value,
                            background=COLORS.get("active_secondary", "#34495e"),  # Definiere diese Farbe in COLORS
                            foreground=BUTTON_STYLES['secondary']['fg'],
                            font=BUTTON_STYLES['secondary']['font'],
                            relief="flat")

        # Danger Button Style
        self.style.configure(ButtonStyle.DANGER.value,
                            background=BUTTON_STYLES['danger']['bg'],
                            foreground=BUTTON_STYLES['danger']['fg'],
                            font=BUTTON_STYLES['danger']['font'],
                            relief="flat")
        self.style.map(ButtonStyle.DANGER.value,
                    background=[('active', COLORS["hover"]), ('pressed', COLORS["active"])],
                    relief=[('pressed', 'sunken')])

        # Active Danger Button Style
        self.style.configure(ButtonStyle.ACTIVE_DANGER.value,
                            background=COLORS.get("active_danger", "#c0392b"),  # Definiere diese Farbe in COLORS
                            foreground=BUTTON_STYLES['danger']['fg'],
                            font=BUTTON_STYLES['danger']['font'],
                            relief="flat")

        # Combobox Styles
        self.style.configure('ModernCombobox.TCombobox',
                            fieldbackground=self.appearance_settings.text_bg_color,
                            background=self.appearance_settings.text_bg_color,
                            foreground=self.appearance_settings.text_fg_color,
                            arrowsize=20,
                            padding=10,
                            relief="solid",
                            borderwidth=1,
                            font=(self.appearance_settings.font_family, self.appearance_settings.font_size))

        self.style.map('ModernCombobox.TCombobox',
                    fieldbackground=[
                        ('readonly', self.appearance_settings.text_bg_color),
                        ('disabled', '#e0e0e0')
                    ],
                    selectbackground=[
                        ('readonly', COLORS["active"])
                    ],
                    selectforeground=[
                        ('readonly', '#ffffff')
                    ],
                    background=[
                        ('readonly', self.appearance_settings.text_bg_color),
                        ('active', COLORS["hover"])
                    ])

        # Listbox Style für Combobox-Dropdown
        self.style.configure('ComboboxListbox',
                            background=self.appearance_settings.text_bg_color,
                            foreground=self.appearance_settings.text_fg_color,
                            selectbackground=COLORS["active"],
                            selectforeground='#ffffff',
                            font=(self.appearance_settings.font_family, self.appearance_settings.font_size),
                            relief="solid",
                            borderwidth=1)

        # Treeview Style
        self.style.configure("Treeview",
                            background=self.appearance_settings.text_bg_color,
                            foreground=self.appearance_settings.text_fg_color,
                            fieldbackground=self.appearance_settings.text_bg_color,
                            font=(self.appearance_settings.font_family, self.appearance_settings.font_size),
                            borderwidth=1,
                            relief="solid")

        self.style.map('Treeview',
                    background=[
                        ('selected', COLORS["active"]),
                        ('active', COLORS["hover"])
                    ],
                    foreground=[
                        ('selected', '#ffffff')
                    ])

        # ZusÃƒÂ¤tzliche Optionen für Combobox-Dropdown
        self.master.option_add('*TCombobox*Listbox.font', (self.appearance_settings.font_family, self.appearance_settings.font_size))
        self.master.option_add('*TCombobox*Listbox.background', self.appearance_settings.text_bg_color)
        self.master.option_add('*TCombobox*Listbox.foreground', self.appearance_settings.text_fg_color)
        self.master.option_add('*TCombobox*Listbox.selectBackground', COLORS["active"])
        self.master.option_add('*TCombobox*Listbox.selectForeground', '#ffffff')

    # -----------------------------------------------------------------------------------
    # APPEARANCE SETTINGS
    # -----------------------------------------------------------------------------------
    def apply_appearance_settings(self):
        """
        Wendet die aktuellen Erscheinungseinstellungen auf alle relevanten Widgets an.
        """
        self.master.configure(bg=self.default_bg)
        self.content_frame.configure(bg=self.default_bg)

        def apply_to_widget(widget):
            if isinstance(widget, tk.Label):
                widget.configure(
                    bg=self.appearance_settings.text_bg_color,
                    fg=self.appearance_settings.text_fg_color,
                    font=(self.appearance_settings.font_family, self.appearance_settings.font_size)
                )
            elif isinstance(widget, ModernButton):
                widget.set_style(widget.original_style)
            
            elif isinstance(widget, ttk.Button):
                widget.configure(
                    style=ButtonStyle.PRIMARY.value
                )
            
            elif isinstance(widget, tk.Checkbutton):
                widget.configure(
                    bg=self.appearance_settings.text_bg_color,
                    fg=self.appearance_settings.text_fg_color,
                    selectcolor=COLORS["hover"]
                )
            
            elif isinstance(widget, ttk.Treeview):
                widget.configure(
                    background=self.appearance_settings.text_bg_color,
                    foreground=self.appearance_settings.text_fg_color,
                    fieldbackground=self.appearance_settings.text_bg_color,
                    font=(self.appearance_settings.font_family, self.appearance_settings.font_size)
                )
            
            elif isinstance(widget, ModernCombobox):
                widget.configure(
                    style='ModernCombobox.TCombobox'
                )

        def apply_recursively(parent):
            for child in parent.winfo_children():
                apply_to_widget(child)
                apply_recursively(child)

        apply_recursively(self.content_frame)

        if self.bg_canvas:
            self.bg_canvas.configure(bg=self.appearance_settings.text_bg_color)

        logging.info("Erscheinungseinstellungen erfolgreich angewendet.")

    # -----------------------------------------------------------------------------------
    # APPEARANCE SETTINGS (Fortsetzung in configure_appearance)
    # -----------------------------------------------------------------------------------
    def configure_appearance(self):
        """Moderne Einstellungsseite mit customtkinter Design."""
        self._clear_content_frame()

        # Moderner Header mit Gradient-Hintergrund
        header_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='#3b82f6',
            corner_radius=0,
            height=110
        )
        header_container.pack(fill='x', pady=(0, 20))
        header_container.pack_propagate(False)

        header_content = ctk.CTkFrame(header_container, fg_color='transparent')
        header_content.place(relx=0.5, rely=0.5, anchor='center')

        # Icon und Titel
        icon_title_frame = ctk.CTkFrame(header_content, fg_color='transparent')
        icon_title_frame.pack()

        ctk.CTkLabel(
            icon_title_frame,
            text="⚙️",
            font=ctk.CTkFont(size=36),
            text_color='#ffffff'
        ).pack(side='left', padx=(0, 15))

        title_frame = ctk.CTkFrame(icon_title_frame, fg_color='transparent')
        title_frame.pack(side='left')

        ctk.CTkLabel(
            title_frame,
            text="Einstellungen",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color='#ffffff'
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_frame,
            text="Personalisiere Design, Darstellung und Funktionen deiner Lern-App",
            font=ctk.CTkFont(size=13),
            text_color='#dbeafe'
        ).pack(anchor='w')

        # Scrollbarer Container
        main_container = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color='transparent'
        )
        main_container.pack(fill='both', expand=True, padx=20, pady=10)

        # === DARSTELLUNGSEINSTELLUNGEN SEKTION ===
        appearance_section = ctk.CTkFrame(
            main_container,
            fg_color='#f0f9ff',
            corner_radius=15,
            border_width=2,
            border_color='#3b82f6'
        )
        appearance_section.pack(fill='x', pady=(0, 15))

        # Header der Darstellungs-Sektion
        appearance_header = ctk.CTkFrame(appearance_section, fg_color='transparent')
        appearance_header.pack(fill='x', pady=(15, 10), padx=15)

        ctk.CTkLabel(
            appearance_header,
            text="🎨",
            font=ctk.CTkFont(size=24)
        ).pack(side='left', padx=(0, 10))

        ctk.CTkLabel(
            appearance_header,
            text="DARSTELLUNG & FARBEN",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color='#1e40af'
        ).pack(side='left')

        # Farbeinstellungen Frame
        colors_frame = ctk.CTkFrame(
            appearance_section,
            fg_color='white',
            corner_radius=10
        )
        colors_frame.pack(fill='x', padx=15, pady=(0, 15))

        def create_color_button(parent, text, setting_type, row):
            """Erstellt eine moderne Farbwahl-Zeile."""
            # Label
            ctk.CTkLabel(
                parent,
                text=text,
                font=ctk.CTkFont(size=13),
                text_color='#1f2937',
                anchor='w',
                width=200
            ).grid(row=row, column=0, sticky='w', padx=15, pady=8)

            # Farbvorschau
            current_color = getattr(self.appearance_settings, f"{setting_type}_color", "#ffffff")
            preview_frame = ctk.CTkFrame(
                parent,
                width=40,
                height=30,
                corner_radius=8,
                border_width=2,
                border_color='#d1d5db',
                fg_color=current_color
            )
            preview_frame.grid(row=row, column=1, padx=10, pady=8)
            preview_frame.grid_propagate(False)

            def update_color():
                from tkinter import colorchooser
                initial_color = getattr(self.appearance_settings, f"{setting_type}_color", "#ffffff")
                color = colorchooser.askcolor(title=f"Wähle {text}", initialcolor=initial_color)
                if color and color[1]:
                    setattr(self.appearance_settings, f"{setting_type}_color", color[1])
                    preview_frame.configure(fg_color=color[1])
                    self.configure_styles()
                    self.apply_appearance_settings()

            # Ändern Button
            ctk.CTkButton(
                parent,
                text="Farbe wählen",
                command=update_color,
                width=120,
                height=30,
                corner_radius=8,
                fg_color='#3b82f6',
                hover_color='#2563eb',
                font=ctk.CTkFont(size=12)
            ).grid(row=row, column=2, padx=10, pady=8)

        # Erstelle Farbwahl-Buttons
        create_color_button(colors_frame, "📄 Text-Hintergrundfarbe", "text_bg", 0)
        create_color_button(colors_frame, "✏️ Textfarbe", "text_fg", 1)
        create_color_button(colors_frame, "🔘 Button-Hintergrundfarbe", "button_bg", 2)
        create_color_button(colors_frame, "🔤 Button-Textfarbe", "button_fg", 3)

        # === LERNEINSTELLUNGEN SEKTION ===
        learning_section = ctk.CTkFrame(
            main_container,
            fg_color='#f0fdf4',
            corner_radius=15,
            border_width=2,
            border_color='#10b981'
        )
        learning_section.pack(fill='x', pady=(0, 15))

        # Header der Lern-Sektion
        learning_header = ctk.CTkFrame(learning_section, fg_color='transparent')
        learning_header.pack(fill='x', pady=(15, 10), padx=15)

        ctk.CTkLabel(
            learning_header,
            text="📚",
            font=ctk.CTkFont(size=24)
        ).pack(side='left', padx=(0, 10))

        ctk.CTkLabel(
            learning_header,
            text="LERNEINSTELLUNGEN",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color='#047857'
        ).pack(side='left')

        # Lernzeitmessung
        time_tracking_frame = ctk.CTkFrame(
            learning_section,
            fg_color='white',
            corner_radius=10
        )
        time_tracking_frame.pack(fill='x', padx=15, pady=(0, 15))

        track_time_var = ctk.BooleanVar(value=self.appearance_settings.track_learning_time)

        time_check = ctk.CTkCheckBox(
            time_tracking_frame,
            text="⏱️ Lernzeitmessung aktivieren",
            variable=track_time_var,
            command=lambda: self.toggle_learning_time(track_time_var.get()),
            font=ctk.CTkFont(size=14),
            fg_color='#10b981',
            hover_color='#059669',
            border_color='#10b981'
        )
        time_check.pack(anchor='w', padx=15, pady=15)

        ctk.CTkLabel(
            time_tracking_frame,
            text="Erfasst die Zeit, die du mit dem Lernen verbringst, und zeigt detaillierte Statistiken.",
            font=ctk.CTkFont(size=12),
            text_color='#6b7280',
            wraplength=500,
            justify='left'
        ).pack(anchor='w', padx=15, pady=(0, 15))

        # === SCHRIFTEINSTELLUNGEN SEKTION ===
        font_section = ctk.CTkFrame(
            main_container,
            fg_color='#fef3c7',
            corner_radius=15,
            border_width=2,
            border_color='#f59e0b'
        )
        font_section.pack(fill='x', pady=(0, 15))

        # Header der Schrift-Sektion
        font_header = ctk.CTkFrame(font_section, fg_color='transparent')
        font_header.pack(fill='x', pady=(15, 10), padx=15)

        ctk.CTkLabel(
            font_header,
            text="🔤",
            font=ctk.CTkFont(size=24)
        ).pack(side='left', padx=(0, 10))

        ctk.CTkLabel(
            font_header,
            text="SCHRIFTEINSTELLUNGEN",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color='#92400e'
        ).pack(side='left')

        # Schriftart anpassen
        font_adjust_frame = ctk.CTkFrame(
            font_section,
            fg_color='white',
            corner_radius=10
        )
        font_adjust_frame.pack(fill='x', padx=15, pady=(0, 15))

        font_button = ctk.CTkButton(
            font_adjust_frame,
            text="🖋️ Schriftart anpassen",
            command=self.configure_font,
            width=200,
            height=40,
            corner_radius=10,
            fg_color='#f59e0b',
            hover_color='#d97706',
            font=ctk.CTkFont(size=14, weight="bold")
        )
        font_button.pack(padx=15, pady=15)

        ctk.CTkLabel(
            font_adjust_frame,
            text="Passe Schriftart und -größe für die gesamte Anwendung an.",
            font=ctk.CTkFont(size=12),
            text_color='#6b7280'
        ).pack(padx=15, pady=(0, 15))

        # === DATENOPERATIONEN SEKTION ===
        data_section = ctk.CTkFrame(
            main_container,
            fg_color='#fce7f3',
            corner_radius=15,
            border_width=2,
            border_color='#ec4899'
        )
        data_section.pack(fill='x', pady=(0, 15))

        # Header der Daten-Sektion
        data_header = ctk.CTkFrame(data_section, fg_color='transparent')
        data_header.pack(fill='x', pady=(15, 10), padx=15)

        ctk.CTkLabel(
            data_header,
            text="🔧",
            font=ctk.CTkFont(size=24)
        ).pack(side='left', padx=(0, 10))

        ctk.CTkLabel(
            data_header,
            text="DATENOPERATIONEN",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color='#9f1239'
        ).pack(side='left')

        # Neuplanung
        reschedule_frame = ctk.CTkFrame(
            data_section,
            fg_color='white',
            corner_radius=10
        )
        reschedule_frame.pack(fill='x', padx=15, pady=(0, 15))

        ctk.CTkLabel(
            reschedule_frame,
            text="📅 Fälligkeiten neu planen",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color='#1f2937',
            anchor='w'
        ).pack(anchor='w', padx=15, pady=(15, 5))

        ctk.CTkLabel(
            reschedule_frame,
            text="Verteilt alle Karten neu basierend auf ihrem Leitner-Level, um Lernspitzen zu vermeiden.\nNützlich nach Import oder längerer Pause.",
            font=ctk.CTkFont(size=12),
            text_color='#6b7280',
            wraplength=600,
            justify='left'
        ).pack(anchor='w', padx=15, pady=(0, 10))

        ctk.CTkButton(
            reschedule_frame,
            text="🔄 Planung starten",
            command=self.confirm_and_reschedule,
            width=180,
            height=36,
            corner_radius=10,
            fg_color='#ec4899',
            hover_color='#db2777',
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(padx=15, pady=(0, 15))

        # === AKTIONEN SEKTION ===
        actions_frame = ctk.CTkFrame(
            main_container,
            fg_color='white',
            corner_radius=15,
            border_width=2,
            border_color='#6b7280'
        )
        actions_frame.pack(fill='x', pady=(0, 0))

        actions_content = ctk.CTkFrame(actions_frame, fg_color='transparent')
        actions_content.pack(fill='x', padx=15, pady=15)

        def reset_settings():
            """Setzt alle Darstellungseinstellungen auf die Standardwerte zurück."""
            from tkinter import messagebox
            confirm = messagebox.askyesno(
                "Bestätigung",
                "Möchten Sie alle Darstellungseinstellungen auf die Standardwerte zurücksetzen?"
            )
            if confirm:
                self.appearance_settings = AppearanceSettings()
                try:
                    self.load_theme("light")
                except Exception as e:
                    logging.error(f"Fehler beim Laden des Standard-Themes nach Reset: {e}")
                self.configure_styles()
                self.apply_appearance_settings()
                self.configure_appearance()
                messagebox.showinfo("Info", "Darstellungseinstellungen wurden zurückgesetzt.")

        # Buttons nebeneinander
        button_container = ctk.CTkFrame(actions_content, fg_color='transparent')
        button_container.pack(expand=True)

        ctk.CTkButton(
            button_container,
            text="🔄 Darstellung zurücksetzen",
            command=reset_settings,
            width=220,
            height=40,
            corner_radius=10,
            fg_color='#6b7280',
            hover_color='#4b5563',
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side='left', padx=10)

        ctk.CTkButton(
            button_container,
            text="🏠 Zurück zum Hauptmenü",
            command=self.create_main_menu,
            width=220,
            height=40,
            corner_radius=10,
            fg_color='#3b82f6',
            hover_color='#2563eb',
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side='left', padx=10)

        logging.info("Moderne Einstellungsseite angezeigt.")


    def show_theme_manager(self):
        """Moderne Theme-Verwaltung mit verbessertem Design."""
        self._clear_content_frame()

        # Moderner Header mit Gradient-Hintergrund
        header_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='#f59e0b',
            corner_radius=0,
            height=110
        )
        header_container.pack(fill='x', pady=(0, 25))
        header_container.pack_propagate(False)

        header_content = ctk.CTkFrame(header_container, fg_color='transparent')
        header_content.place(relx=0.5, rely=0.5, anchor='center')

        # Icon und Titel
        icon_title_frame = ctk.CTkFrame(header_content, fg_color='transparent')
        icon_title_frame.pack()

        ctk.CTkLabel(
            icon_title_frame,
            text="🎨",
            font=ctk.CTkFont(size=36),
            text_color='#ffffff'
        ).pack(side='left', padx=(0, 15))

        title_frame = ctk.CTkFrame(icon_title_frame, fg_color='transparent')
        title_frame.pack(side='left')

        ctk.CTkLabel(
            title_frame,
            text="Theme-Verwaltung",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color='#ffffff'
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_frame,
            text="Personalisiere das Erscheinungsbild deiner Anwendung",
            font=ctk.CTkFont(size=13),
            text_color='#fef3c7'
        ).pack(anchor='w')

        # Hauptcontainer
        main_container = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        main_container.pack(fill='both', expand=True, padx=30, pady=0)

        # Top-Aktionsleiste
        actions_bar = ctk.CTkFrame(main_container, fg_color='#ffffff', corner_radius=15, border_width=2, border_color='#f59e0b')
        actions_bar.pack(fill='x', pady=(0, 20))

        actions_content = ctk.CTkFrame(actions_bar, fg_color='transparent')
        actions_content.pack(fill='x', padx=20, pady=15)

        ctk.CTkLabel(
            actions_content,
            text="⚡ Schnellaktionen",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color='#92400e'
        ).pack(side='left', padx=(0, 20))

        def create_new_theme_dialog():
            self.create_new_theme_inline(themes_container)

        ctk.CTkButton(
            actions_content,
            text="➕ Neues Theme",
            command=create_new_theme_dialog,
            width=140,
            height=40,
            corner_radius=12,
            fg_color='#10b981',
            hover_color='#059669',
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            actions_content,
            text="📥 Importieren",
            command=self.import_theme_file,
            width=130,
            height=40,
            corner_radius=12,
            fg_color='#3b82f6',
            hover_color='#2563eb',
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            actions_content,
            text="📤 Exportieren",
            command=self.export_current_theme,
            width=130,
            height=40,
            corner_radius=12,
            fg_color='#8b5cf6',
            hover_color='#7c3aed',
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side='left', padx=5)

        # Scrollable Frame für Themes
        scroll_container = ctk.CTkScrollableFrame(
            main_container,
            fg_color='#ffffff',
            corner_radius=15,
            border_width=2,
            border_color='#fed7aa'
        )
        scroll_container.pack(fill='both', expand=True, pady=(0, 15))

        # Container für Theme-Cards
        themes_container = ctk.CTkFrame(scroll_container, fg_color='transparent')
        themes_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Themes laden und anzeigen
        themes = self.data_manager.theme_manager.themes

        for theme_name, theme_data in themes.items():
            # Theme-Card erstellen
            theme_card = ctk.CTkFrame(
                themes_container,
                fg_color='#fffbeb',
                corner_radius=15,
                border_width=2,
                border_color='#fed7aa'
            )
            theme_card.pack(fill='x', pady=10)

            # Card Content
            card_content = ctk.CTkFrame(theme_card, fg_color='transparent')
            card_content.pack(fill='x', padx=20, pady=15)

            # Linke Seite: Theme-Info
            left_section = ctk.CTkFrame(card_content, fg_color='transparent')
            left_section.pack(side='left', fill='x', expand=True)

            # Theme-Name und Badge
            name_frame = ctk.CTkFrame(left_section, fg_color='transparent')
            name_frame.pack(anchor='w', pady=(0, 8))

            ctk.CTkLabel(
                name_frame,
                text=theme_name.capitalize(),
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color='#78350f'
            ).pack(side='left')

            # Farbvorschau-Palette
            color_preview_frame = ctk.CTkFrame(left_section, fg_color='transparent')
            color_preview_frame.pack(anchor='w')

            # Zeige die wichtigsten Farben als kleine Vorschau
            preview_colors = [
                theme_data.get('button_bg_color', '#ffffff'),
                theme_data.get('button_fg_color', '#000000'),
                theme_data.get('text_bg_color', '#f0f0f0'),
                theme_data.get('default_bg', '#ffffff')
            ]

            for color in preview_colors[:4]:
                color_box = ctk.CTkFrame(
                    color_preview_frame,
                    fg_color=color,
                    width=40,
                    height=40,
                    corner_radius=8,
                    border_width=2,
                    border_color='#d1d5db'
                )
                color_box.pack(side='left', padx=3)
                color_box.pack_propagate(False)

            # Rechte Seite: Aktionsbuttons
            right_section = ctk.CTkFrame(card_content, fg_color='transparent')
            right_section.pack(side='right')

            button_container = ctk.CTkFrame(right_section, fg_color='transparent')
            button_container.pack()

            def apply_theme(t=theme_name):
                self.quick_apply_theme(t)

            def edit_theme(t=theme_name, d=theme_data):
                self.edit_theme_inline(themes_container, t, d)

            # Aktivieren-Button
            ctk.CTkButton(
                button_container,
                text="✓ Aktivieren",
                command=apply_theme,
                width=120,
                height=40,
                corner_radius=12,
                fg_color='#f59e0b',
                hover_color='#d97706',
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(pady=3)

            # Bearbeiten-Button
            ctk.CTkButton(
                button_container,
                text="✏️ Bearbeiten",
                command=edit_theme,
                width=120,
                height=40,
                corner_radius=12,
                fg_color='#6b7280',
                hover_color='#4b5563',
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(pady=3)

    def quick_apply_theme(self, theme_name):
        """Wendet ein Theme direkt an."""
        try:
            self.load_theme(theme_name)
            messagebox.showinfo("Theme aktiviert", f"Das Theme '{theme_name}' wurde aktiviert.")
            self.show_theme_manager()  # Aktualisiert die Ansicht
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Aktivieren des Themes: {str(e)}")
            logging.error(f"Fehler beim Aktivieren des Themes {theme_name}: {str(e)}")

    def edit_theme_inline(self, parent_frame, theme_name, theme_data):
        """Bearbeitet ein Theme mit modernem Design."""
        # Entfernt eventuell vorhandene Edit-Frames
        for widget in parent_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                widget_name = str(widget)
                if 'edit_theme_' in widget_name or 'create_theme' in widget_name:
                    widget.destroy()

        # Theme-Bearbeitungsframe mit modernem Design
        edit_frame = ctk.CTkFrame(
            parent_frame,
            fg_color='#fef3c7',
            corner_radius=15,
            border_width=3,
            border_color='#f59e0b'
        )
        edit_frame.pack(fill='x', pady=15, padx=0)

        # Header
        header_frame = ctk.CTkFrame(edit_frame, fg_color='#f59e0b', corner_radius=12)
        header_frame.pack(fill='x', padx=3, pady=3)

        ctk.CTkLabel(
            header_frame,
            text=f"✏️ Theme '{theme_name}' bearbeiten",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color='#ffffff'
        ).pack(pady=12)

        # Scrollable Content für Farbeinstellungen
        scroll_content = ctk.CTkScrollableFrame(
            edit_frame,
            fg_color='transparent',
            height=300
        )
        scroll_content.pack(fill='both', expand=True, padx=15, pady=(10, 15))

        color_vars = {}
        preview_labels = {}

        for key, value in theme_data.items():
            row = ctk.CTkFrame(scroll_content, fg_color='#ffffff', corner_radius=10, border_width=1, border_color='#fcd34d')
            row.pack(fill='x', pady=5, padx=5)

            row_content = ctk.CTkFrame(row, fg_color='transparent')
            row_content.pack(fill='x', padx=12, pady=10)

            # Label
            ctk.CTkLabel(
                row_content,
                text=key.replace('_', ' ').title(),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color='#78350f',
                width=180,
                anchor='w'
            ).pack(side='left', padx=(0, 10))

            # Color Entry
            color_vars[key] = tk.StringVar(value=value)
            color_entry = ctk.CTkEntry(
                row_content,
                textvariable=color_vars[key],
                width=100,
                height=32,
                corner_radius=8
            )
            color_entry.pack(side='left', padx=5)

            # Preview Label
            preview_frame = ctk.CTkFrame(
                row_content,
                fg_color=value,
                width=40,
                height=32,
                corner_radius=8,
                border_width=2,
                border_color='#d1d5db'
            )
            preview_frame.pack(side='left', padx=5)
            preview_frame.pack_propagate(False)
            preview_labels[key] = preview_frame

            def update_color(k=key):
                color = colorchooser.askcolor(color=color_vars[k].get())[1]
                if color:
                    color_vars[k].set(color)
                    preview_labels[k].configure(fg_color=color)

            # Color Picker Button
            ctk.CTkButton(
                row_content,
                text="🎨 Wählen",
                command=lambda k=key: update_color(k),
                width=100,
                height=32,
                corner_radius=8,
                fg_color='#8b5cf6',
                hover_color='#7c3aed',
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(side='left', padx=5)

        def save_changes():
            """Speichert die Änderungen am Theme."""
            try:
                new_theme_data = {k: v.get() for k, v in color_vars.items()}
                self.data_manager.theme_manager.add_or_update_theme(theme_name, new_theme_data)
                edit_frame.destroy()
                self.show_theme_manager()
                messagebox.showinfo("Erfolg", f"Theme '{theme_name}' wurde aktualisiert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Speichern des Themes: {str(e)}")
                logging.error(f"Fehler beim Speichern des Themes {theme_name}: {str(e)}")

        def cancel_edit():
            """Bricht die Theme-Bearbeitung ab."""
            edit_frame.destroy()

        # Button-Frame
        btn_frame = ctk.CTkFrame(edit_frame, fg_color='transparent')
        btn_frame.pack(fill='x', padx=15, pady=(0, 15))

        # Speichern-Button
        ctk.CTkButton(
            btn_frame,
            text="💾 Speichern",
            command=save_changes,
            width=140,
            height=40,
            corner_radius=12,
            fg_color='#10b981',
            hover_color='#059669',
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side='left', padx=5)

        # Abbrechen-Button
        ctk.CTkButton(
            btn_frame,
            text="✖ Abbrechen",
            command=cancel_edit,
            width=140,
            height=40,
            corner_radius=12,
            fg_color='#dc2626',
            hover_color='#b91c1c',
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side='left', padx=5)

    def create_new_theme_inline(self, parent_frame):
        """Erstellt ein neues Theme mit modernem Design."""
        # Entfernt eventuell vorhandene Create-Frames
        for widget in parent_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                widget_name = str(widget)
                if 'create_theme' in widget_name or 'edit_theme_' in widget_name:
                    widget.destroy()
                    return

        # Theme-Erstellungsframe mit modernem Design
        create_frame = ctk.CTkFrame(
            parent_frame,
            fg_color='#dbeafe',
            corner_radius=15,
            border_width=3,
            border_color='#3b82f6'
        )
        create_frame.pack(fill='x', pady=15, padx=0)

        # Header
        header_frame = ctk.CTkFrame(create_frame, fg_color='#3b82f6', corner_radius=12)
        header_frame.pack(fill='x', padx=3, pady=3)

        ctk.CTkLabel(
            header_frame,
            text="✨ Neues Theme erstellen",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color='#ffffff'
        ).pack(pady=12)

        # Content Frame
        content_frame = ctk.CTkFrame(create_frame, fg_color='transparent')
        content_frame.pack(fill='both', expand=True, padx=15, pady=(10, 15))

        # Name-Eingabe
        name_container = ctk.CTkFrame(content_frame, fg_color='#ffffff', corner_radius=10, border_width=1, border_color='#93c5fd')
        name_container.pack(fill='x', pady=(0, 15))

        name_content = ctk.CTkFrame(name_container, fg_color='transparent')
        name_content.pack(fill='x', padx=15, pady=12)

        ctk.CTkLabel(
            name_content,
            text="Theme-Name:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#1e3a8a',
            width=120,
            anchor='w'
        ).pack(side='left', padx=(0, 10))

        name_var = tk.StringVar()
        name_entry = ctk.CTkEntry(
            name_content,
            textvariable=name_var,
            height=36,
            corner_radius=10,
            placeholder_text="z.B. Mein Custom Theme",
            font=ctk.CTkFont(size=13)
        )
        name_entry.pack(side='left', fill='x', expand=True)

        # Scrollable Content für Farbeinstellungen
        ctk.CTkLabel(
            content_frame,
            text="Farbeinstellungen:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color='#1e3a8a',
            anchor='w'
        ).pack(anchor='w', pady=(5, 10))

        scroll_content = ctk.CTkScrollableFrame(
            content_frame,
            fg_color='transparent',
            height=250
        )
        scroll_content.pack(fill='both', expand=True)

        # Standard-Farben
        default_colors = {
            'default_bg': '#ffffff',
            'text_bg_color': '#ffffff',
            'text_fg_color': '#000000',
            'button_bg_color': '#4a90e2',
            'button_fg_color': '#ffffff'
        }

        color_vars = {}
        preview_labels = {}

        for key, value in default_colors.items():
            row = ctk.CTkFrame(scroll_content, fg_color='#ffffff', corner_radius=10, border_width=1, border_color='#93c5fd')
            row.pack(fill='x', pady=5, padx=5)

            row_content = ctk.CTkFrame(row, fg_color='transparent')
            row_content.pack(fill='x', padx=12, pady=10)

            # Label
            ctk.CTkLabel(
                row_content,
                text=key.replace('_', ' ').title(),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color='#1e3a8a',
                width=180,
                anchor='w'
            ).pack(side='left', padx=(0, 10))

            # Color Entry
            color_vars[key] = tk.StringVar(value=value)
            color_entry = ctk.CTkEntry(
                row_content,
                textvariable=color_vars[key],
                width=100,
                height=32,
                corner_radius=8
            )
            color_entry.pack(side='left', padx=5)

            # Preview Label
            preview_frame = ctk.CTkFrame(
                row_content,
                fg_color=value,
                width=40,
                height=32,
                corner_radius=8,
                border_width=2,
                border_color='#d1d5db'
            )
            preview_frame.pack(side='left', padx=5)
            preview_frame.pack_propagate(False)
            preview_labels[key] = preview_frame

            def update_color(k=key):
                color = colorchooser.askcolor(color=color_vars[k].get())[1]
                if color:
                    color_vars[k].set(color)
                    preview_labels[k].configure(fg_color=color)

            # Color Picker Button
            ctk.CTkButton(
                row_content,
                text="🎨 Wählen",
                command=lambda k=key: update_color(k),
                width=100,
                height=32,
                corner_radius=8,
                fg_color='#8b5cf6',
                hover_color='#7c3aed',
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(side='left', padx=5)

        def save_new_theme():
            theme_name = name_var.get().strip()
            if not theme_name:
                messagebox.showerror("Fehler", "Bitte geben Sie einen Theme-Namen ein.")
                return

            try:
                new_theme_data = {k: v.get() for k, v in color_vars.items()}
                self.data_manager.theme_manager.add_or_update_theme(theme_name, new_theme_data)
                create_frame.destroy()
                self.show_theme_manager()
                messagebox.showinfo("Erfolg", f"Theme '{theme_name}' wurde erstellt.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Erstellen des Themes: {str(e)}")
                logging.error(f"Fehler beim Erstellen des Themes {theme_name}: {str(e)}")

        def cancel_create():
            create_frame.destroy()

        # Button-Frame
        btn_frame = ctk.CTkFrame(content_frame, fg_color='transparent')
        btn_frame.pack(fill='x', pady=(15, 0))

        # Speichern-Button
        ctk.CTkButton(
            btn_frame,
            text="💾 Speichern",
            command=save_new_theme,
            width=140,
            height=40,
            corner_radius=12,
            fg_color='#10b981',
            hover_color='#059669',
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side='left', padx=5)

        # Abbrechen-Button
        ctk.CTkButton(
            btn_frame,
            text="✖ Abbrechen",
            command=cancel_create,
            width=140,
            height=40,
            corner_radius=12,
            fg_color='#dc2626',
            hover_color='#b91c1c',
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side='left', padx=5)

    def toggle_learning_time(self, is_enabled):
        """Schaltet die Lernzeitmessung ein oder aus."""
        self.appearance_settings.track_learning_time = is_enabled
        self.apply_appearance_settings()
        logging.info(f"Lernzeitmessung {'aktiviert' if is_enabled else 'deaktiviert'}.")
        messagebox.showinfo("Info", f"Lernzeitmessung {'aktiviert' if is_enabled else 'deaktiviert'}.")

    # -----------------------------------------------------------------------------------
    # MENÃƒÅ“ & NAVIGATION
    # -----------------------------------------------------------------------------------
    def init_navigation(self):
        """Initialisiert die Navigationshistorie und setzt die aktuelle Ansicht."""
        self.navigation_history = []
        self.current_view = 'main'

    def navigate_to(self, view_name: str):
        """
        Navigiert zu einer neuen Ansicht und fÃƒÂ¼gt die aktuelle Ansicht zur Historie hinzu.

        Args:
            view_name (str): Name der neuen Ansicht.
        """
        self.navigation_history.append(self.current_view)
        self.current_view = view_name

        view_methods = {
            'main': self.create_main_menu,
            'learning_session': self.show_card_window,
            'tag_search': self.show_tag_search_interface,
            'learning_time_overview': self.show_learning_time_overview,
            # Fügen Sie weitere Ansichten hier hinzu
        }

        view_method = view_methods.get(view_name)
        if view_method:
            view_method()
            logging.info(f"Navigiert zu {view_name}.")
        else:
            logging.warning(f"Unbekannte Ansicht: {view_name}")

    def navigate_back(self):
        """Navigiert zurück zur vorherigen Ansicht."""
        if self.navigation_history:
            previous_view = self.navigation_history.pop()
            self.current_view = previous_view

            view_methods = {
                'main': self.create_main_menu,
                'learning_session': self.show_card_window,
                'tag_search': self.show_tag_search_interface,
                'learning_time_overview': self.show_learning_time_overview,
                # Fügen Sie weitere Ansichten hier hinzu
            }

            view_method = view_methods.get(previous_view)
            if view_method:
                view_method()
                logging.info(f"Zurück navigiert zu {previous_view}.")
            else:
                logging.warning(f"Unbekannte vorherige Ansicht: {previous_view}")
        else:
            logging.info("Keine vorherige Ansicht zum Zurücknavigieren vorhanden.")
            self.create_main_menu()


    # -----------------------------------------------------------------------------------
    # MAIN MENU ERSTELLEN
    # -----------------------------------------------------------------------------------
    def create_main_menu(self):
        self._clear_content_frame()

        # Modernes Design mit einfachem Hintergrund

        # Container Frame über dem Canvas
        container = ctk.CTkFrame(
            self.content_frame,
            fg_color='#ffffff',  # Weißer Hintergrund
            corner_radius=20,
            border_width=2,
            border_color='#4A90E2'
        )
        container.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.85, relheight=0.85)

        # Header
        header_frame = ctk.CTkFrame(container, fg_color='transparent')
        header_frame.pack(fill='x', pady=(30, 20))

        header_label = ctk.CTkLabel(
            header_frame,
            text="🎓 Hauptmenü",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color='#2C3E50'
        )
        header_label.pack()

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Wähle eine Option",
            font=ctk.CTkFont(size=14),
            text_color='#7F8C8D'
        )
        subtitle.pack(pady=(5, 0))

        # Grid Frame für 2x2 Layout
        grid_frame = ctk.CTkFrame(container, fg_color='transparent')
        grid_frame.pack(pady=30, fill=tk.BOTH, expand=True, padx=50)

        # Configure grid rows and columns to expand
        grid_frame.grid_rowconfigure(0, weight=1)
        grid_frame.grid_rowconfigure(1, weight=1)
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)

        # Oben Links: Wochenkalender
        btn_calendar = ctk.CTkButton(
            grid_frame,
            text="📅 Wochenkalender",
            command=self.show_weekly_calendar,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color='#4A90E2',
            hover_color='#357ABD',
            corner_radius=15,
            border_width=2,
            border_color='#2980B9',
            height=120
        )
        btn_calendar.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        # Oben Rechts: Leitner-Lernsession
        btn_leitner = ctk.CTkButton(
            grid_frame,
            text="🎯 Leitner-Lernsession",
            command=self.show_learning_options,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color='#27AE60',
            hover_color='#229954',
            corner_radius=15,
            border_width=2,
            border_color='#1E8449',
            height=120
        )
        btn_leitner.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        # Unten Links: Kategorien hinzufügen
        btn_categories = ctk.CTkButton(
            grid_frame,
            text="📚 Kategorien hinzufügen",
            command=self.manage_categories,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color='#E67E22',
            hover_color='#D35400',
            corner_radius=15,
            border_width=2,
            border_color='#BA4A00',
            height=120
        )
        btn_categories.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")

        # Unten Rechts: Karten verwalten
        btn_cards = ctk.CTkButton(
            grid_frame,
            text="🗂️ Karten verwalten",
            command=self.show_card_management,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color='#8E44AD',
            hover_color='#7D3C98',
            corner_radius=15,
            border_width=2,
            border_color='#6C3483',
            height=120
        )
        btn_cards.grid(row=1, column=1, padx=15, pady=15, sticky="nsew")

        # Setze den aktiven Button auf 'Home'
        self.highlight_active_button('Home')
    def select_cards_with_category(self, category):
        """
        Ãƒâ€“ffnet die Kartenauswahl mit vorausgewÃƒÂ¤hlter Kategorie
        """
        self.current_category = category  # Speichern der aktuellen Kategorie
        self.select_cards_submenu()  # Ãƒâ€“ffnet die Kartenauswahl
        
        # VerzÃƒÂ¶gere das Setzen der Kategorie leicht, um sicherzustellen, 
        # dass die UI vollständig geladen ist
        self.master.after(100, lambda: self.category_var.set(category) if hasattr(self, 'category_var') else None)
    def _clear_content_frame(self):
        """Entfernt alle Widgets aus dem content_frame."""
        if hasattr(self, 'content_frame'):
            for widget in self.content_frame.winfo_children():
                widget.destroy()
        else:
            logging.warning("content_frame ist nicht definiert.")


    # -----------------------------------------------------------------------------------
    # LERN-FUNKTIONALITÃƒâ€žT
    # -----------------------------------------------------------------------------------

    def open_subcategories(self, category):
        self._clear_content_frame()
        self.current_category = category
        subcats = self.data_manager.categories.get(category, {})
        
        if not isinstance(subcats, dict):
            logging.error(f"Subkategorien für '{category}' sind nicht als Dictionary strukturiert.")
            messagebox.showerror("Fehler", f"Subkategorien für '{category}' sind fehlerhaft strukturiert.")
            self.navigate_back()
            return

        if not subcats:
            messagebox.showinfo("Info", "Keine Subkategorien vorhanden.")
            self.navigate_back()
            return

        # Header
        header_label = tk.Label(
            self.content_frame,
            text=f"Subkategorien von {category}",
            font=(self.appearance_settings.font_family, 18),
            bg=self.appearance_settings.text_bg_color,
            fg=self.appearance_settings.text_fg_color
        )
        header_label.pack(pady=10)

        # Grid-Layout für Subkategorien
        grid_frame = tk.Frame(self.content_frame, bg=self.appearance_settings.text_bg_color)
        grid_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)
        columns = 3

        for idx, subcat in enumerate(sorted(subcats.keys())):
            row = idx // columns
            col = idx % columns
            button = ModernButton(
                grid_frame,
                text=subcat,
                command=lambda s=subcat: self.navigate_to('learning_session'),  # Verwenden Sie navigate_to
                width=20,
                style=ButtonStyle.PRIMARY.value
            )
            button.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

        for col in range(columns):
            grid_frame.grid_columnconfigure(col, weight=1)

        # Zurück-Button
        back_btn = ModernButton(
            self.content_frame,
            text="Zurück zum Hauptmenü",
            command=self.navigate_back,  # Verwenden Sie navigate_back
            width=15,
            style=ButtonStyle.SECONDARY.value
        )
        back_btn.pack(pady=20)
        self.sidebar_buttons["back_to_main_from_subcategories"] = back_btn

        # Setze den aktiven Button auf 'lernen'
        self.highlight_active_button('lernen')

    def start_learning_session(self, category, subcategory):
        """
        Startet eine Lernsitzung basierend auf der ausgewählten Kategorie und Subkategorie.
        """
        # Verwenden der DataManager-Methode, um fällige Flashcards zu erhalten
        due_flashcards = self.data_manager.get_due_flashcards(category=category, subcategory=subcategory)

        if not due_flashcards:
            messagebox.showinfo("Info", "Keine Karten zur Überprüfung fällig.")
            self.navigate_back()
            return

        # Begrenze die Anzahl der Karten basierend auf SESSION_LIMIT
        if len(due_flashcards) > self.session_limit:
            try:
                self.cards_this_session = random.sample(due_flashcards, self.session_limit)
            except ValueError as e:
                logging.error(f"Fehler bei der Kartenauswahl: {e}")
                messagebox.showerror("Fehler", f"Fehler bei der Kartenauswahl: {e}")
                self.navigate_back()
                return
        else:
            self.cards_this_session = due_flashcards.copy()

        self.session_results = []
        
        # Starte die Zeitmessung nur wenn sie aktiviert ist
        if self.appearance_settings.track_learning_time:
            self.session_start_time = datetime.datetime.now()
            logging.info(f"Lernsitzung gestartet um: {self.session_start_time}")
        else:
            self.session_start_time = None
            logging.info("Zeitmessung deaktiviert - keine Startzeit gesetzt")

        # Navigation aktualisieren
        self.navigate_to('learning_session')


    def show_learning_options(self):
        """Zeigt die verschiedenen Lernmethoden zur Auswahl an."""
        self._clear_content_frame()

        # Hauptcontainer mit modernem Design
        main_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='transparent'
        )
        main_container.pack(fill='both', expand=True, padx=40, pady=30)

        # Header
        header = ctk.CTkLabel(
            main_container,
            text="Lernmethode auswählen",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#2c3e50"
        )
        header.pack(pady=(0, 30))

        # Container für die Lernmethoden mit Grid-Layout
        methods_container = ctk.CTkFrame(main_container, fg_color='transparent')
        methods_container.pack(fill='both', expand=True)

        # 1. Intelligentes Lernen (SRS) - Moderne Karte
        srs_card = ctk.CTkFrame(
            methods_container,
            fg_color='#ffffff',
            corner_radius=15,
            border_width=2,
            border_color='#4A90E2'
        )
        srs_card.pack(fill='x', pady=(0, 20))

        # SRS Icon/Emoji
        ctk.CTkLabel(
            srs_card,
            text="🧠",
            font=ctk.CTkFont(size=40)
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            srs_card,
            text="Intelligentes Lernen (SRS)",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#2c3e50"
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            srs_card,
            text="Optimierte Wiederholungen basierend auf deiner Lernleistung",
            font=ctk.CTkFont(size=13),
            text_color="#7f8c8d",
            wraplength=500
        ).pack(pady=(0, 15), padx=20)

        ctk.CTkButton(
            srs_card,
            text="Starten",
            command=self.show_srs_learning_options,
            height=40,
            width=200,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4A90E2",
            hover_color="#3a7bc8",
            corner_radius=10
        ).pack(pady=(0, 20))

        # 2. Leitner System - Moderne Karte
        leitner_card = ctk.CTkFrame(
            methods_container,
            fg_color='#ffffff',
            corner_radius=15,
            border_width=2,
            border_color='#27ae60'
        )
        leitner_card.pack(fill='x', pady=(0, 20))

        # Leitner Icon/Emoji
        ctk.CTkLabel(
            leitner_card,
            text="📦",
            font=ctk.CTkFont(size=40)
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            leitner_card,
            text="Leitner System",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#2c3e50"
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            leitner_card,
            text="Systematisches Lernen mit bewährtem Box-System",
            font=ctk.CTkFont(size=13),
            text_color="#7f8c8d",
            wraplength=500
        ).pack(pady=(0, 15), padx=20)

        ctk.CTkButton(
            leitner_card,
            text="Starten",
            command=self.show_leitner_options,
            height=40,
            width=200,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27ae60",
            hover_color="#1e8449",
            corner_radius=10
        ).pack(pady=(0, 20))

        # Zurück-Button mit modernem Design
        back_btn = ctk.CTkButton(
            main_container,
            text="← Zurück zum Hauptmenü",
            command=self.create_main_menu,
            height=40,
            width=200,
            font=ctk.CTkFont(size=13),
            fg_color="#95a5a6",
            hover_color="#7f8c8d",
            corner_radius=10
        )
        back_btn.pack(pady=(10, 0))

        # Setze aktiven Button (für optische Markierung in Sidebar)
        self.highlight_active_button('Lernsession')

 # Code-Snippet für main.py - show_leitner_options Methode
# Ersetze die rules_info Liste mit dieser neuen 10-Level Version:
    def show_mixed_learning_options(self):
        """
        Zeigt die Optionen für gemischtes Lernen an.
        Kombiniert Karten aus verschiedenen Kategorien für verschachteltes ÃƒÅ“ben.
        """
        self._clear_content_frame()
        
        # Header
        header = ctk.CTkLabel(
            self.content_frame,
            text="Gemischtes Lernen",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=20)
        
        # Info-Text
        info_frame = ctk.CTkFrame(self.content_frame)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text="Verschachteltes Lernen verbessert das LangzeitgedÃƒÂ¤chtnis",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            info_frame,
            text="WÃƒÂ¤hle mehrere Kategorien aus, deren Karten gemischt werden sollen.",
            font=ctk.CTkFont(size=12),
            wraplength=600
        ).pack(pady=(0, 10))
        
        # Hauptcontainer
        main_container = ctk.CTkScrollableFrame(self.content_frame)
        main_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Kategorien-Auswahl
        ctk.CTkLabel(
            main_container,
            text="Kategorien auswÃƒÂ¤hlen:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor='w', pady=(10, 5))
        
        # Dictionary zum Speichern der Checkbox-Variablen
        self.mixed_category_vars = {}
        
        # Erstelle Checkboxen für alle Kategorien
        all_categories = sorted(self.data_manager.categories.keys())
        
        if not all_categories:
            ctk.CTkLabel(
                main_container,
                text="Ã¢Å¡Â  Keine Kategorien vorhanden!",
                font=ctk.CTkFont(size=14),
                text_color="orange"
            ).pack(pady=20)
            
            ctk.CTkButton(
                self.content_frame,
                text="Zurück",
                command=self.show_learning_options,
                height=35,
                fg_color="gray",
                hover_color="darkgray"
            ).pack(pady=20)
            return
        
        for category in all_categories:
            var = tk.BooleanVar(value=False)
            self.mixed_category_vars[category] = var
            
            ctk.CTkCheckBox(
                main_container,
                text=category,
                variable=var,
                font=ctk.CTkFont(size=12)
            ).pack(anchor='w', padx=20, pady=5)
        
        # Anzahl der Karten
        settings_frame = ctk.CTkFrame(main_container)
        settings_frame.pack(fill='x', pady=20)
        
        ctk.CTkLabel(
            settings_frame,
            text="Anzahl der Karten:",
            font=ctk.CTkFont(size=12)
        ).pack(side='left', padx=(10, 10))
        
        self.mixed_cards_limit_var = tk.IntVar(value=20)
        ctk.CTkEntry(
            settings_frame,
            textvariable=self.mixed_cards_limit_var,
            width=80
        ).pack(side='left', padx=5)
        
        # Button-Frame
        button_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        button_frame.pack(pady=20)
        def start_mixed_session():
            """Startet eine gemischte Lernsession."""
            selected_categories = [
                cat for cat, var in self.mixed_category_vars.items() 
                if var.get()
            ]
        
            if len(selected_categories) < 2:
                messagebox.showwarning(
                    "Warnung", 
                    "Bitte mindestens 2 Kategorien auswÃƒÂ¤hlen für gemischtes Lernen!"
                )
                return
        
            # Sammle Karten aus allen ausgewÃƒÂ¤hlten Kategorien
            mixed_cards = []
            for category in selected_categories:
                cards = self.data_manager.get_due_flashcards(category=category)
                mixed_cards.extend(cards)
        
            if not mixed_cards:
                messagebox.showinfo("Info", "Keine fälligen Karten in den ausgewählten Kategorien.")
                return
        
            # Mische die Karten
            import random
            random.shuffle(mixed_cards)
        
            # Begrenze auf die gewÃƒÂ¼nschte Anzahl
            limit = self.mixed_cards_limit_var.get()
            self.cards_this_session = mixed_cards[:limit]
        
            # Session starten
            if self.appearance_settings.track_learning_time:
                self.session_start_time = datetime.datetime.now()
        
            self.session_results = []
            messagebox.showinfo(
                "Session gestartet",
                f"{len(self.cards_this_session)} gemischte Karten aus {len(selected_categories)} Kategorien"
            )
            self.show_card_window()
    
        ctk.CTkButton(
            button_frame,
            text="Session starten",
            command=start_mixed_session,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side='left', padx=10)
    
        ctk.CTkButton(
            button_frame,
            text="Zurück",
            command=self.show_learning_options,
            width=150,
            height=40,
            fg_color="gray",
            hover_color="darkgray"
        ).pack(side='left', padx=10)
    
        # Setze aktiven Button
        self.highlight_active_button('Lernsession')
    def show_leitner_options(self):
        """Zeigt die Leitner-System Lernoptionen an mit optimiertem 10-Level System."""
        self._clear_content_frame()
        self.leitner_rules_visible = False  # Regeln sind standardmäßig eingeklappt

        # Haupt-Container, der das Grid-Layout steuert
        main_container = ctk.CTkFrame(self.content_frame)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        # Reihe für Kartenvorschau soll sich ausdehnen
        main_container.grid_rowconfigure(3, weight=1)

        # --- Reihe 0: Header und Button zum Ein-/Ausklappen ---
        header_container = ctk.CTkFrame(main_container)
        header_container.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 5))
        header_container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(header_container, text="Leitner-System (10 Level - Optimiert)", 
                            font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, sticky="w", pady=10)

        self.toggle_rules_btn = ctk.CTkButton(
            header_container,
            text="Regeln anzeigen ▼",
            command=self._toggle_leitner_rules,
            width=180
        )
        self.toggle_rules_btn.grid(row=0, column=1, sticky="e", padx=10)

        # --- Reihe 1: Der einklappbare Frame für die Regeln ---
        self.leitner_rules_frame = ctk.CTkFrame(main_container, fg_color="#f8fafc", corner_radius=12)

        # Moderne Überschrift
        rules_header_frame = ctk.CTkFrame(self.leitner_rules_frame, fg_color="transparent")
        rules_header_frame.pack(fill='x', pady=(15, 10), padx=15)
        ctk.CTkLabel(
            rules_header_frame,
            text="📖 Leitner-System Regeln",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1e293b"
        ).pack(side='left')

        # Beschreibung mit modernen Info-Cards
        info_container = ctk.CTkFrame(self.leitner_rules_frame, fg_color="transparent")
        info_container.pack(fill='x', pady=10, padx=15)

        # Info-Karten für die Hauptkonzepte
        info_cards = [
            ("📈", "Exponentielle Erfolgsquote", "0%→0x | 50%→1x | 85%→2x | 100%→3x", "#3b82f6"),
            ("🔥", "Streak-Bonus System", "5er: ×1.5 | 10er: ×2.0 | 15er: ×2.5 | 20er: ×3.0", "#ef4444"),
            ("⚡", "Intelligenter Punktabzug", "Gesamtfehler × Level-Faktor × Streak-Verlust", "#f59e0b"),
            ("🏆", "Meisterschaft Level 10", "Schwer zu erreichen und zu halten!", "#8b5cf6")
        ]

        for icon, title, desc, color in info_cards:
            card = ctk.CTkFrame(info_container, fg_color="#ffffff", corner_radius=8, border_width=1, border_color=color)
            card.pack(fill='x', pady=4)

            card_content = ctk.CTkFrame(card, fg_color="transparent")
            card_content.pack(fill='x', padx=12, pady=10)

            # Icon und Title
            title_frame = ctk.CTkFrame(card_content, fg_color="transparent")
            title_frame.pack(fill='x')

            ctk.CTkLabel(title_frame, text=icon, font=ctk.CTkFont(size=16)).pack(side='left', padx=(0, 8))
            ctk.CTkLabel(title_frame, text=title, font=ctk.CTkFont(size=13, weight="bold"),
                        text_color=color).pack(side='left')

            # Beschreibung
            ctk.CTkLabel(card_content, text=desc, font=ctk.CTkFont(size=11),
                        text_color="#64748b", justify="left").pack(anchor='w', padx=(24, 0))

        # Moderner Level-Bereich
        level_section = ctk.CTkFrame(self.leitner_rules_frame, fg_color="transparent")
        level_section.pack(fill='x', pady=(10, 0), padx=15)

        ctk.CTkLabel(level_section, text="📊 Level-Übersicht",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color="#1e293b").pack(anchor='w', pady=(0, 10))

        # Scrollable Level Container
        level_scroll = ctk.CTkScrollableFrame(level_section, height=280, fg_color="#ffffff", corner_radius=8)
        level_scroll.pack(fill='both', expand=True)

        # NEUE 10-LEVEL REGELN MIT MODERNEN CARDS
        rules_info = [
            ("1. Grundlagen", "0-10", "Täglich", "1 Tag", "🌱", "#10b981"),
            ("2. Basis", "11-25", "2 Tage", "2 Tage", "🌿", "#22c55e"),
            ("3. Aufbau", "26-50", "4 Tage", "4 Tage", "🌳", "#84cc16"),
            ("4. Kompetent", "51-85", "Wöchentlich", "7 Tage", "💪", "#eab308"),
            ("5. Fortgeschritten", "86-120", "10 Tage", "10 Tage", "🎯", "#f59e0b"),
            ("6. Proficient", "121-175", "12 Tage", "12 Tage", "⭐", "#f97316"),
            ("7. Spezialist", "176-220", "2 Wochen", "14 Tage", "🔥", "#ef4444"),
            ("8. Experte", "221-285", "20 Tage", "20 Tage", "💎", "#ec4899"),
            ("9. Meister", "286-350", "25 Tage", "25 Tage", "👑", "#a855f7"),
            ("10. Master", "350+", "Monatlich", "30 Tage", "🏆", "#8b5cf6"),
        ]

        for level, points, interval_short, interval_long, icon, color in rules_info:
            level_card = ctk.CTkFrame(level_scroll, fg_color="#f8fafc", corner_radius=6,
                                     border_width=1, border_color=color)
            level_card.pack(fill='x', pady=3, padx=5)

            level_content = ctk.CTkFrame(level_card, fg_color="transparent")
            level_content.pack(fill='x', padx=10, pady=8)
            level_content.grid_columnconfigure(1, weight=1)

            # Icon
            ctk.CTkLabel(level_content, text=icon, font=ctk.CTkFont(size=18)).grid(row=0, column=0, rowspan=2, padx=(0, 10))

            # Level Name
            name_frame = ctk.CTkFrame(level_content, fg_color="transparent")
            name_frame.grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(name_frame, text=level, font=ctk.CTkFont(size=13, weight="bold"),
                        text_color=color).pack(side='left')
            ctk.CTkLabel(name_frame, text=f"  •  {points} Punkte",
                        font=ctk.CTkFont(size=11), text_color="#64748b").pack(side='left')

            # Intervall Info
            ctk.CTkLabel(level_content, text=f"📅 Wiederholung: {interval_long}",
                        font=ctk.CTkFont(size=10), text_color="#475569").grid(row=1, column=1, sticky="w")

        # --- Reihe 2: Filter für die Kartenauswahl ---
        filter_container = ctk.CTkFrame(main_container, fg_color="#f8fafc", corner_radius=12)
        filter_container.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Moderne Header-Sektion
        header_frame = ctk.CTkFrame(filter_container, fg_color="transparent")
        header_frame.pack(fill='x', pady=(15, 10), padx=15)
        ctk.CTkLabel(header_frame, text="🎯 Kartenauswahl",
                    font=ctk.CTkFont(size=18, weight="bold"),
                    text_color="#1e293b").pack(side='left')
        ctk.CTkLabel(header_frame, text="Wähle deine Lernkarten aus",
                    font=ctk.CTkFont(size=12),
                    text_color="#64748b").pack(side='left', padx=(10, 0))

        # Moderne Filter-Sektion mit Cards
        filters_grid = ctk.CTkFrame(filter_container, fg_color="transparent")
        filters_grid.pack(fill='x', pady=5, padx=15)

        # Kategorie & Unterkategorie Row
        cat_frame = ctk.CTkFrame(filters_grid, fg_color="#ffffff", corner_radius=8)
        cat_frame.pack(fill='x', pady=5, ipady=8)

        ctk.CTkLabel(cat_frame, text="📁 Kategorie:",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#475569").pack(side='left', padx=(15, 5))
        self.category_var = tk.StringVar(value="Alle")
        categories = ["Alle"] + sorted(self.data_manager.categories.keys())
        category_menu = ctk.CTkOptionMenu(cat_frame, variable=self.category_var,
                                        values=categories, width=180, height=32,
                                        fg_color="#3b82f6", button_color="#2563eb",
                                        button_hover_color="#1d4ed8",
                                        command=self.update_leitner_subcategories)
        category_menu.pack(side='left', padx=5)

        ctk.CTkLabel(cat_frame, text="📂 Unterkategorie:",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#475569").pack(side='left', padx=(20, 5))
        self.subcategory_var = tk.StringVar(value="Alle")
        self.subcategory_menu = ctk.CTkOptionMenu(cat_frame, variable=self.subcategory_var,
                                                values=["Alle"], width=180, height=32,
                                                fg_color="#3b82f6", button_color="#2563eb",
                                                button_hover_color="#1d4ed8",
                                                command=lambda x: self.preview_leitner_cards())
        self.subcategory_menu.pack(side='left', padx=5)

        # Level & Fälligkeit Row
        level_filter_frame = ctk.CTkFrame(filters_grid, fg_color="#ffffff", corner_radius=8)
        level_filter_frame.pack(fill='x', pady=5, ipady=8)

        ctk.CTkLabel(level_filter_frame, text="📊 Level:",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#475569").pack(side='left', padx=(15, 5))
        self.level_var = tk.StringVar(value="Alle")
        # AKTUALISIERT: 10 Level statt 7
        level_names = ["Grundlagen", "Basis", "Aufbau", "Kompetent", "Fortgeschritten",
                      "Proficient", "Spezialist", "Experte", "Meister", "Master"]
        level_options = ["Alle"] + [f"{i}. {name}" for i, name in enumerate(level_names, 1)]
        level_menu = ctk.CTkOptionMenu(level_filter_frame, variable=self.level_var,
                                    values=level_options, width=180, height=32,
                                    fg_color="#8b5cf6", button_color="#7c3aed",
                                    button_hover_color="#6d28d9",
                                    command=lambda x: self.preview_leitner_cards())
        level_menu.pack(side='left', padx=5)

        ctk.CTkLabel(level_filter_frame, text="📅 Fälligkeit:",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#475569").pack(side='left', padx=(20, 5))
        self.due_var = tk.StringVar(value="Nur fällige Karten")
        due_options = ["Nur fällige Karten", "Alle Karten", "In 7 Tagen fällig",
                    "In 14 Tagen fällig", "In 30 Tagen fällig"]
        due_menu = ctk.CTkOptionMenu(level_filter_frame, variable=self.due_var,
                                    values=due_options, width=200, height=32,
                                    fg_color="#10b981", button_color="#059669",
                                    button_hover_color="#047857",
                                    command=lambda x: self.preview_leitner_cards())
        due_menu.pack(side='left', padx=5)

        # Karten pro Session Row
        cards_frame = ctk.CTkFrame(filters_grid, fg_color="#ffffff", corner_radius=8)
        cards_frame.pack(fill='x', pady=5, ipady=8)

        ctk.CTkLabel(cards_frame, text="🎴 Karten pro Session:",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#475569").pack(side='left', padx=(15, 5))
        self.cards_per_session_var = tk.StringVar(value="20")
        cards_menu = ctk.CTkOptionMenu(cards_frame, variable=self.cards_per_session_var,
                                    values=["10", "20", "30", "40", "50", "100"],
                                    width=100, height=32,
                                    fg_color="#f59e0b", button_color="#d97706",
                                    button_hover_color="#b45309")
        cards_menu.pack(side='left', padx=5)

        # --- Reihe 3: Container für die Kartenvorschau (expandiert) ---
        self.cards_container = ctk.CTkScrollableFrame(main_container)
        self.cards_container.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        
        # --- Reihe 4: Container für die unteren Buttons ---
        bottom_container = ctk.CTkFrame(main_container, fg_color="transparent")
        bottom_container.grid(row=4, column=0, sticky="ew", padx=10, pady=10)

        self.card_count_label = ctk.CTkLabel(bottom_container,
                                            text="Filter anwenden, um Karten anzuzeigen.",
                                            font=ctk.CTkFont(size=13, weight="bold"),
                                            text_color="#475569")
        self.card_count_label.pack(side='left', padx=15)

        button_frame = ctk.CTkFrame(bottom_container, fg_color="transparent")
        button_frame.pack(side='right', padx=15)

        preview_btn = ctk.CTkButton(button_frame, text="🔍 Vorschau aktualisieren",
                                command=self.preview_leitner_cards,
                                height=40, width=180, corner_radius=8,
                                font=ctk.CTkFont(size=13, weight="bold"),
                                fg_color="#6366f1", hover_color="#4f46e5")
        preview_btn.pack(side='left', padx=5)

        start_btn = ctk.CTkButton(button_frame, text="🚀 Lernsession starten",
                                command=self.start_leitner_session,
                                height=40, width=200, corner_radius=8,
                                font=ctk.CTkFont(size=14, weight="bold"),
                                fg_color="#10b981", hover_color="#059669")
        start_btn.pack(side='left', padx=5)
        
        self.preview_leitner_cards()
        self.highlight_active_button('Lernsession')

    def _create_info_badge(self, parent, icon, text, color, column):
        """Erstellt ein modernes Info-Badge für die Kartenvorschau."""
        badge_frame = ctk.CTkFrame(parent, fg_color="transparent")
        badge_frame.pack(side='left', padx=4)

        ctk.CTkLabel(badge_frame, text=icon,
                    font=ctk.CTkFont(size=12)).pack(side='left', padx=(0, 4))
        ctk.CTkLabel(badge_frame, text=text,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=color).pack(side='left')

    def _toggle_leitner_rules(self):
        """Schaltet die Sichtbarkeit des Rahmens mit den Leitner-System-Regeln um."""
        if not hasattr(self, 'leitner_rules_frame') or not self.leitner_rules_frame.winfo_exists():
            return

        self.leitner_rules_visible = not self.leitner_rules_visible
        if self.leitner_rules_visible:
            self.leitner_rules_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
            self.toggle_rules_btn.configure(text="Regeln verbergen ▲")
        else:
            self.leitner_rules_frame.grid_remove()
            self.toggle_rules_btn.configure(text="Regeln anzeigen ▼")
    def update_leitner_subcategories(self, *args):
        """Aktualisiert die Unterkategorien für die Leitner-Optionen."""
        selected_category = self.category_var.get()
        if selected_category == "Alle":
            subcats = ["Alle"]
        else:
            subcats = ["Alle"] + sorted(self.data_manager.categories.get(selected_category, {}).keys())
        self.subcategory_menu.configure(values=subcats)
        self.subcategory_var.set("Alle")
        self.preview_leitner_cards()

    def preview_leitner_cards(self):
        """Zeigt eine Vorschau der fälligen Leitner-Karten an, inkl. Erfolgsquote."""
        for widget in self.cards_container.winfo_children():
            widget.destroy()
        
        try:
            category = None if self.category_var.get() == "Alle" else self.category_var.get()
            subcategory = None if self.subcategory_var.get() == "Alle" else self.subcategory_var.get()
            level = None
            if self.level_var.get() != "Alle":
                try:
                    level = int(self.level_var.get().split(".")[0])
                except (ValueError, IndexError):
                    level = None
            
            cards_limit = int(self.cards_per_session_var.get())
            due_filter = self.due_var.get()
            today = datetime.datetime.now().date()
            
            due_date_filter = None
            include_non_due = False
            if due_filter == "Nur fällige Karten": due_date_filter = today
            elif due_filter == "Alle Karten": include_non_due = True
            elif "In 7 Tagen fällig" in due_filter: due_date_filter = today + datetime.timedelta(days=7); include_non_due = True
            elif "In 14 Tagen fällig" in due_filter: due_date_filter = today + datetime.timedelta(days=14); include_non_due = True
            elif "In 30 Tagen fällig" in due_filter: due_date_filter = today + datetime.timedelta(days=30); include_non_due = True
            
            all_cards = list(self.leitner_system.cards.values())
            
            filtered_cards = []
            for card in all_cards:
                if category and card.category.lower() != category.lower(): continue
                if subcategory and card.subcategory.lower() != subcategory.lower(): continue
                if level is not None and self.leitner_system.get_card_status(card)['level'] != level: continue
                
                card_next_review = card.next_review_date
                if card_next_review is None:
                    card_next_review = today
                elif isinstance(card_next_review, str):
                    try: card_next_review = datetime.datetime.fromisoformat(card_next_review).date()
                    except (ValueError, TypeError): card_next_review = today
                elif isinstance(card_next_review, datetime.datetime):
                    card_next_review = card_next_review.date()
                
                if due_date_filter:
                    if card_next_review <= due_date_filter:
                        filtered_cards.append(card)
                elif include_non_due:
                    filtered_cards.append(card)

            cards_by_date = defaultdict(list)
            for card in filtered_cards:
                due_date_str = card.next_review_date.strftime("%Y-%m-%d") if isinstance(card.next_review_date, (datetime.date, datetime.datetime)) else "unknown"
                cards_by_date[due_date_str].append(card)
            
            sorted_cards = []
            for due_date in sorted(cards_by_date.keys()):
                group = cards_by_date[due_date]
                random.shuffle(group)
                sorted_cards.extend(group)
            
            display_cards = sorted_cards[:cards_limit]
            self.filtered_leitner_cards_for_session = display_cards.copy()
            
            self.card_count_label.configure(text=f"Gefilterte Karten: {len(filtered_cards)} (Angezeigt: {len(display_cards)})")
            
            if not display_cards:
                ctk.CTkLabel(self.cards_container, text="Keine Karten für die gewählten Filter gefunden.").pack(pady=20)
                return

            header_info_frame = ctk.CTkFrame(self.cards_container)
            header_info_frame.pack(fill='x', pady=(5, 0), padx=5)
            header_info_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

            ctk.CTkLabel(header_info_frame, text="Level", font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=0)
            ctk.CTkLabel(header_info_frame, text="Punkte", font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=1)
            ctk.CTkLabel(header_info_frame, text="Erfolgsquote", font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=2)
            ctk.CTkLabel(header_info_frame, text="Multiplikator", font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=3)
            ctk.CTkLabel(header_info_frame, text="Kategorie", font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=4)

            for idx, card in enumerate(display_cards):
                # Moderne Card mit hellem Design
                card_frame = ctk.CTkFrame(self.cards_container, fg_color="#ffffff",
                                         corner_radius=10, border_width=2, border_color="#e2e8f0")
                card_frame.pack(fill='x', pady=6, padx=5)

                status = self.leitner_system.get_card_status(card)

                # Header mit Priorität
                header_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
                header_frame.pack(fill="x", padx=12, pady=(10, 5))

                # Prioritäts-Badge
                priority_color, priority_text, priority_bg = "#10b981", "✓ Normal", "#d1fae5"
                if status['days_overdue'] > 0:
                    if status['days_overdue'] >= 7:
                        priority_color, priority_text, priority_bg = "#ef4444", f"⚠️ Hohe Priorität (+{status['days_overdue']} T.)", "#fee2e2"
                    elif status['days_overdue'] >= 3:
                        priority_color, priority_text, priority_bg = "#f97316", f"⚡ Mittel (+{status['days_overdue']} T.)", "#ffedd5"
                    else:
                        priority_color, priority_text, priority_bg = "#eab308", f"● Niedrig (+{status['days_overdue']} T.)", "#fef3c7"
                elif status['days_until_review'] > 0:
                    priority_color, priority_text, priority_bg = "#3b82f6", f"📅 In {status['days_until_review']} Tagen", "#dbeafe"

                # Karten-Nummer und Frage
                question_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
                question_frame.pack(side='left', fill='x', expand=True)

                ctk.CTkLabel(question_frame, text=f"#{idx+1}",
                           font=ctk.CTkFont(size=11, weight="bold"),
                           text_color="#94a3b8",
                           width=40).pack(side='left', padx=(0, 8))

                ctk.CTkLabel(question_frame, text=card.question,
                           font=ctk.CTkFont(size=13, weight="bold"),
                           text_color="#1e293b", anchor="w").pack(side='left', fill='x', expand=True)

                # Prioritäts-Badge rechts
                badge_frame = ctk.CTkFrame(header_frame, fg_color=priority_bg, corner_radius=6)
                badge_frame.pack(side='right', padx=5)
                ctk.CTkLabel(badge_frame, text=priority_text,
                           font=ctk.CTkFont(size=11, weight="bold"),
                           text_color=priority_color).pack(padx=10, pady=4)

                # Recovery-Mode Badge
                if hasattr(card, 'in_recovery_mode') and card.in_recovery_mode:
                    recovery_badge = ctk.CTkFrame(header_frame, fg_color="#fff7ed", corner_radius=6)
                    recovery_badge.pack(side='right', padx=5)
                    ctk.CTkLabel(recovery_badge, text=f"🔄 Wiederaufbau: {card.recovery_interval}d",
                               font=ctk.CTkFont(size=11, weight="bold"),
                               text_color="#f97316").pack(padx=10, pady=4)

                # Info-Grid mit modernen Badges
                info_container = ctk.CTkFrame(card_frame, fg_color="#f8fafc", corner_radius=6)
                info_container.pack(fill='x', padx=12, pady=(5, 10))

                info_grid = ctk.CTkFrame(info_container, fg_color="transparent")
                info_grid.pack(fill='x', padx=8, pady=8)

                level_name = self.leitner_system.get_level(status['points'])
                leitner_card_obj = self.leitner_system.cards.get(card.card_id)
                success_rate = leitner_card_obj.success_rate if leitner_card_obj else 0.0
                exp_mult = leitner_card_obj._get_exponential_multiplier() if leitner_card_obj else 1.0
                streak_bonus = leitner_card_obj._get_streak_bonus() if leitner_card_obj else 1.0
                pos_streak = leitner_card_obj.positive_streak if leitner_card_obj else 0

                # Level Badge
                self._create_info_badge(info_grid, "📊", level_name, "#8b5cf6", 0)
                # Punkte Badge
                self._create_info_badge(info_grid, "⭐", f"{status['points']} Pkt", "#3b82f6", 1)
                # Erfolgsquote Badge
                success_color = "#10b981" if success_rate >= 0.7 else ("#f59e0b" if success_rate >= 0.4 else "#ef4444")
                self._create_info_badge(info_grid, "📈", f"{success_rate:.0%}", success_color, 2)
                # Multiplikator Badge
                self._create_info_badge(info_grid, "✨", f"×{exp_mult:.2f}", "#f59e0b", 3)
                # Streak Badge
                self._create_info_badge(info_grid, "🔥", f"{pos_streak} (×{streak_bonus:.1f})", "#ef4444", 4)

                # Datum-Info
                date_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
                date_frame.pack(fill='x', padx=12, pady=(0, 10))
                next_review_date = status['next_review_date']
                date_str = next_review_date.strftime("%d.%m.%Y") if isinstance(next_review_date, (datetime.date, datetime.datetime)) else str(next_review_date)

                if status['days_overdue'] > 0:
                    date_text = f"📌 Fällig: {date_str} (Überfällig)"
                    date_color = "#ef4444"
                elif status['days_overdue'] == 0:
                    date_text = f"📌 Fällig: {date_str} (Heute)"
                    date_color = "#f97316"
                else:
                    date_text = f"📅 Nächste Wiederholung: {date_str} (in {status['days_until_review']} Tagen)"
                    date_color = "#10b981"

                ctk.CTkLabel(date_frame, text=date_text,
                           font=ctk.CTkFont(size=11),
                           text_color=date_color).pack(side='left', padx=5)

        except Exception as e:
            logging.error(f"Fehler bei der Leitner-Kartenvorschau: {e}", exc_info=True)
            ctk.CTkLabel(self.cards_container, text=f"Fehler bei der Anzeige der Karten: {str(e)}").pack(pady=10)

    def _get_filtered_cards(self):
        """
        Gibt alle Leitner-Karten zurück, die den Filterkriterien entsprechen.
        Wird für die Vorschau und für die Session genutzt.
        """
        filtered_cards = list(self.leitner_system.cards.values())
        if hasattr(self, 'category_var') and self.category_var.get() != "Alle":
            filtered_cards = [c for c in filtered_cards if c.category.lower() == self.category_var.get().lower()]
        if hasattr(self, 'subcategory_var') and self.subcategory_var.get() != "Alle":
            filtered_cards = [c for c in filtered_cards if c.subcategory.lower() == self.subcategory_var.get().lower()]
        if hasattr(self, 'level_var') and self.level_var.get() != "Alle":
            filtered_cards = [c for c in filtered_cards if self.leitner_system.get_level(c.points) == self.level_var.get()]
        
        today = datetime.date.today()
        if hasattr(self, 'due_var') and self.due_var.get() != "Alle":
            if self.due_var.get() == "Heute fällig":
                filtered_cards = [c for c in filtered_cards if c.next_review_date.date() <= today]
            elif self.due_var.get() == "Diese Woche":
                week_end = today + datetime.timedelta(days=7)
                filtered_cards = [c for c in filtered_cards if c.next_review_date.date() <= week_end]
            elif self.due_var.get() == "Nächste Woche":
                week_start = today + datetime.timedelta(days=7)
                week_end = today + datetime.timedelta(days=14)
                filtered_cards = [c for c in filtered_cards if week_start <= c.next_review_date.date() <= week_end]
        
        return filtered_cards




    def start_leitner_session_from_plan(self, category: str, subcategory: str, plan_id: str = None,
                                        cards_limit: int = 30):
        """
        Startet eine Leitner-Session mit vordefinierten Filtern (aus Kalender).

        Args:
            category: Die Kategorie für die Session
            subcategory: Die Unterkategorie für die Session
            plan_id: Optional - ID des Planeintrags für Tracking
            cards_limit: Maximale Anzahl Karten (Standard: 30)
        """
        try:
            # Speichere plan_id für späteres Tracking
            self.current_plan_id = plan_id

            # Filtere nur fällige Karten für diese Kategorie/Unterkategorie
            today = datetime.datetime.now()
            all_cards = list(self.leitner_system.cards.values())
            filtered_cards = []

            for card in all_cards:
                if card.category.lower() != category.lower():
                    continue
                if card.subcategory.lower() != subcategory.lower():
                    continue

                # Nur fällige Karten
                if card.next_review_date <= today:
                    filtered_cards.append(card)

            if not filtered_cards:
                messagebox.showinfo(
                    "Keine Karten fällig",
                    f"Für {category} - {subcategory} sind aktuell keine Karten fällig.\n\n"
                    f"Das Lernset wird automatisch aktualisiert, sobald wieder Karten fällig sind."
                )
                return

            # Gruppiere und mische Karten nach Fälligkeitsdatum
            from collections import defaultdict
            import random

            cards_by_date = defaultdict(list)
            for card in filtered_cards:
                due_date = card.next_review_date.strftime("%Y-%m-%d")
                cards_by_date[due_date].append(card)

            sorted_cards = []
            for due_date in sorted(cards_by_date.keys()):
                group = cards_by_date[due_date]
                random.shuffle(group)
                sorted_cards.extend(group)

            display_cards = sorted_cards[:cards_limit]

            # Setze die Karten für die Session
            self.cards_to_learn = display_cards
            self.total_cards_in_session = len(display_cards)

            # Tracking-Variablen initialisieren
            self.unique_cards_seen = set()
            self.cards_in_retry = set()
            self.cards_wrong_in_session = set()
            self.total_answers = 0
            self.correct_answers = 0

            # Initialisiere Session-Ergebnisse
            self.session_results = []

            # Starte Zeitmessung
            if self.appearance_settings.track_learning_time:
                self.session_start_time = datetime.datetime.now()

            # Starte das Kartenfenster
            self.show_card_window_dynamically()

            logging.info(f"Leitner-Session gestartet: {category}/{subcategory} mit {len(display_cards)} Karten")

        except Exception as e:
            logging.error(f"Fehler beim Starten der Leitner-Session aus Kalender: {e}", exc_info=True)
            messagebox.showerror("Fehler", f"Beim Starten der Session ist ein Fehler aufgetreten: {e}")
            self.create_main_menu()

    def start_leitner_session(self):
        """Startet eine Leitner-Lernsession mit den ausgewählten Karten."""
        try:
            category = None if self.category_var.get() == "Alle" else self.category_var.get()
            subcategory = None if self.subcategory_var.get() == "Alle" else self.subcategory_var.get()
            
            level = None
            if self.level_var.get() != "Alle":
                try:
                    level = int(self.level_var.get().split(".")[0])
                except (ValueError, IndexError):
                    level = None
            
            cards_limit = int(self.cards_per_session_var.get())
            due_filter = self.due_var.get()
            today = datetime.datetime.now().date()
            
            due_date_filter = None
            include_non_due = False
            
            if due_filter == "Nur fällige Karten":
                due_date_filter = today
            elif due_filter == "Alle Karten":
                include_non_due = True
            elif "In 7 Tagen fällig" in due_filter:
                due_date_filter = today + datetime.timedelta(days=7)
                include_non_due = True
            elif "In 14 Tagen fällig" in due_filter:
                due_date_filter = today + datetime.timedelta(days=14)
                include_non_due = True
            elif "In 30 Tagen fällig" in due_filter:
                due_date_filter = today + datetime.timedelta(days=30)
                include_non_due = True
            
            all_cards = list(self.leitner_system.cards.values())
            filtered_cards = []
            
            for card in all_cards:
                if category and card.category.lower() != category.lower():
                    continue
                if subcategory and card.subcategory.lower() != subcategory.lower():
                    continue
                if level is not None and card.level != level:
                    continue
                
                if due_date_filter:
                    next_review = card.next_review_date
                    if isinstance(next_review, str):
                        try:
                            next_review = datetime.datetime.fromisoformat(next_review).date()
                        except ValueError:
                            try:
                                next_review = datetime.datetime.strptime(next_review, "%d.%m.%Y").date()
                            except ValueError:
                                continue
                    elif isinstance(next_review, datetime.datetime):
                        next_review = next_review.date()
                    
                    if next_review <= due_date_filter:
                        filtered_cards.append(card)
                        continue
                    elif include_non_due:
                        filtered_cards.append(card)
                        continue
                else:
                    filtered_cards.append(card)
            
            # Gruppiere und mische Karten nach FÃƒÂ¤lligkeitsdatum
            from collections import defaultdict
            import random
            
            cards_by_date = defaultdict(list)
            for card in filtered_cards:
                due_date = card.next_review_date.strftime("%Y-%m-%d")
                cards_by_date[due_date].append(card)
            
            sorted_cards = []
            for due_date in sorted(cards_by_date.keys()):
                group = cards_by_date[due_date]
                random.shuffle(group)
                sorted_cards.extend(group)
            
            display_cards = sorted_cards[:cards_limit]
            
            if not display_cards:
                messagebox.showinfo("Info", "Keine Karten entsprechen den Filterkriterien.")
                return
            
            # Setze die Karten für die Session
            self.cards_to_learn = display_cards
            
            # Speichere die ursprÃƒÂ¼ngliche Anzahl
            self.total_cards_in_session = len(display_cards)
            
            # Ã¢Å“â€¦ NEU: Tracking-Variablen initialisieren
            self.unique_cards_seen = set()           # IDs aller gesehenen Karten
            self.cards_in_retry = set()              # IDs aller falsch beantworteten Karten
            self.cards_wrong_in_session = set()      # Ã¢Â¬â€¦Ã¯Â¸Â NEU: IDs der in dieser Session falsch beantworteten Karten
            self.total_answers = 0                   # Gesamtzahl Antworten
            self.correct_answers = 0                 # Anzahl richtiger Antworten
            
            # Initialisiere Session-Ergebnisse
            self.session_results = []
            
            # Starte Zeitmessung falls aktiviert
            if self.appearance_settings.track_learning_time:
                self.session_start_time = datetime.datetime.now()
            
            # Starte das dynamische Kartenfenster
            self.show_card_window_dynamically()
            
        except Exception as e:
            logging.error(f"Fehler beim Starten der Leitner-Session: {e}")
            messagebox.showerror("Fehler", f"Beim Starten der Session ist ein Fehler aufgetreten: {e}")
            self.create_main_menu()
    def handle_leitner_incorrect(self):
        """Verarbeitet eine falsche Antwort im Leitner-System."""
        if not hasattr(self, 'current_card') or self.current_card is None:
            logging.error("handle_leitner_incorrect aufgerufen ohne aktuelle LeitnerKarte.")
            self.show_card_window_dynamically()
            return

        time_spent = (datetime.datetime.now() - self.card_start_time).total_seconds() if hasattr(self, 'card_start_time') and self.card_start_time else 0

        # Speichere Level VOR der Antwort
        level_before = self.current_card.level

        # Tracking aktualisieren
        self.total_answers += 1
        if hasattr(self.current_card, 'card_id'):
            self.cards_in_retry.add(self.current_card.card_id)
            # Ã¢Å“â€¦ NEU: Markiere Karte als in dieser Session falsch
            self.cards_wrong_in_session.add(self.current_card.card_id)

        # Fange ALLE Rückgabewerte ab
        result = self.current_card.answer_incorrect()

        # Debug: Zeige was zurückgegeben wurde
        logging.info(f"answer_incorrect() gab zurück: {result} (Typ: {type(result)}, Länge: {len(result) if isinstance(result, tuple) else 'N/A'})")
        
        # Extrahiere nur die ersten 3 Werte (egal wie viele es sind)
        if isinstance(result, tuple):
            points_subtracted = result[0]
            base_points = result[1] if len(result) > 1 else 0
            multiplier = result[2] if len(result) > 2 else 1.0
        else:
            # Falls es kein Tupel ist (nur ein Wert)
            points_subtracted = result
            base_points = 0
            multiplier = 1.0
        
        # Level NACH der Antwort
        level_after = self.current_card.level
        
        logging.info(f"Leitner Karte falsch: {self.current_card.question}")
        logging.info(f"  -> Punkte: -{points_subtracted}, Basis: {base_points}, Multiplikator: {multiplier}")

        # Speichere im KORREKTEN Format (8 Werte) - WICHTIG: negative Punkte für falsche Antworten
        self.session_results.append((
            self.current_card,      # 0
            False,                  # 1
            time_spent,             # 2
            -points_subtracted,     # 3 - NEGATIV für Punktabzug
            base_points,            # 4
            multiplier,             # 5
            level_before,           # 6
            level_after             # 7
        ))

        # Flashcard aktualisieren
        flashcard_obj = self.data_manager.get_flashcard_by_id(self.current_card.card_id)
        if flashcard_obj:
            self._update_flashcard_from_leitner(flashcard_obj, self.current_card)
            self.data_manager.save_flashcards()

        # Karte wieder einfügen
        if self.cards_to_learn:
            current_card = self.cards_to_learn.pop(0)
            remaining_cards = len(self.cards_to_learn)
            insertion_pos = random.randint(min(3, remaining_cards), min(5, remaining_cards)) if remaining_cards > 0 else 0
            self.cards_to_learn.insert(insertion_pos, current_card)

        self.show_card_window_dynamically()

    def handle_leitner_correct(self):
        """Verarbeitet eine richtige Antwort im Leitner-System."""
        if not hasattr(self, 'current_card') or self.current_card is None:
            logging.error("handle_leitner_correct aufgerufen ohne aktuelle LeitnerKarte.")
            self.show_card_window_dynamically()
            return

        time_spent = (datetime.datetime.now() - self.card_start_time).total_seconds() if hasattr(self, 'card_start_time') and self.card_start_time else 0

        # Speichere Level VOR der Antwort
        level_before = self.current_card.level

        # Tracking aktualisieren
        self.total_answers += 1
        self.correct_answers += 1

        # ✓ NEU: Prüfe ob Karte bereits in dieser Session falsch war
        was_wrong_in_session = (
            hasattr(self, 'cards_wrong_in_session') and 
            self.current_card.card_id in self.cards_wrong_in_session
        )
        
        if was_wrong_in_session:
            logging.info(f"Ã¢Å¡Â Ã¯Â¸Â Karte '{self.current_card.question}' war bereits falsch in dieser Session -> +0 Punkte")

        # Ã¢Å“â€¦ GEÃƒâ€žNDERT: ÃƒÅ“bergebe den Parameter
        result = self.current_card.answer_correct(was_wrong_in_session=was_wrong_in_session)
        
        # Debug: Zeige was zurückgegeben wurde
        logging.info(f"answer_correct() gab zurück: {result} (Typ: {type(result)}, Länge: {len(result) if isinstance(result, tuple) else 'N/A'})")
        
        # Extrahiere nur die ersten 3 Werte (egal wie viele es sind)
        if isinstance(result, tuple):
            points_added = result[0]
            base_points = result[1] if len(result) > 1 else 0
            multiplier = result[2] if len(result) > 2 else 1.0
        else:
            # Falls es kein Tupel ist (nur ein Wert)
            points_added = result
            base_points = 0
            multiplier = 1.0
        
        # Level NACH der Antwort
        level_after = self.current_card.level
        
        logging.info(f"Leitner Karte korrekt: {self.current_card.question}")
        logging.info(f"  -> Punkte: +{points_added}, Basis: {base_points}, Multiplikator: {multiplier}")
        
        # Speichere im KORREKTEN Format (8 Werte)
        self.session_results.append((
            self.current_card,  # 0
            True,               # 1
            time_spent,         # 2
            points_added,       # 3
            base_points,        # 4
            multiplier,         # 5
            level_before,       # 6
            level_after         # 7
        ))
        
        # Flashcard aktualisieren
        flashcard_obj = self.data_manager.get_flashcard_by_id(self.current_card.card_id)
        if flashcard_obj:
            self._update_flashcard_from_leitner(flashcard_obj, self.current_card)
            self.data_manager.save_flashcards()

        # Entferne Karte
        if self.cards_to_learn:
            self.cards_to_learn.pop(0)

        self.show_card_window_dynamically()

    def _handle_correct_answer(self):
        """Wrapper-Methode für korrekte Antwort im Leitner-System."""
        self.handle_leitner_correct()

    def _handle_incorrect_answer(self):
        """Wrapper-Methode für inkorrekte Antwort im Leitner-System."""
        self.handle_leitner_incorrect()

    def end_leitner_session(self):
        """Beendet die aktuelle Leitner-Session vorzeitig und zeigt die Zusammenfassung."""
        if not hasattr(self, 'session_results') or not self.session_results:
            messagebox.showinfo("Info", "Keine Session-Daten vorhanden.")
            self.create_main_menu()
            return

        # Speichere alle Änderungen
        self.leitner_system.save_cards()
        self.data_manager.save_flashcards()

        # Zeige Zusammenfassung
        self.show_leitner_session_summary(force_ended=True)

    def show_leitner_session_summary(self, force_ended=False):
        """Zeigt eine detaillierte Zusammenfassung der Leitner-Session."""
        self._clear_content_frame()

        # Berechne Statistiken
        if not hasattr(self, 'session_results') or not self.session_results:
            messagebox.showinfo("Info", "Keine Session-Daten vorhanden.")
            self.create_main_menu()
            return

        total_cards = len(self.session_results)
        correct_count = sum(1 for result in self.session_results if len(result) > 1 and result[1])

        # Berechne Lernzeit
        total_time_seconds = 0
        if hasattr(self, 'session_start_time'):
            total_time_seconds = (datetime.datetime.now() - self.session_start_time).total_seconds()
        total_time_minutes = total_time_seconds / 60

        # Berechne Punkte (result[3] ist bereits korrekt vorzeichenbehaftet)
        points_gained = sum(result[3] for result in self.session_results if len(result) > 3 and result[1] and result[3] > 0)
        points_lost = abs(sum(result[3] for result in self.session_results if len(result) > 3 and not result[1]))
        net_points = sum(result[3] for result in self.session_results if len(result) > 3)

        # Erfolgsquote
        success_rate = (correct_count / total_cards * 100) if total_cards > 0 else 0

        # Haupt-Container mit modernem Design
        main_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_container.pack(fill='both', expand=True, padx=20, pady=10)

        # Hero-Sektion mit Erfolgs-Feedback
        hero_frame = ctk.CTkFrame(main_container, fg_color="#f8fafc", corner_radius=16)
        hero_frame.pack(fill='x', pady=(0, 20))

        hero_content = ctk.CTkFrame(hero_frame, fg_color="transparent")
        hero_content.pack(fill='x', padx=30, pady=25)

        # Status Icon und Text
        status_icon = "🎉" if success_rate >= 70 else ("💪" if success_rate >= 50 else "📚")
        header_text = "Großartige Leistung!" if success_rate >= 70 else ("Gute Arbeit!" if success_rate >= 50 else "Weiter so!")

        if force_ended:
            status_icon = "⏸️"
            header_text = "Session pausiert"

        ctk.CTkLabel(
            hero_content,
            text=status_icon,
            font=ctk.CTkFont(size=48)
        ).pack()

        ctk.CTkLabel(
            hero_content,
            text=header_text,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#1e293b"
        ).pack(pady=(5, 0))

        subtitle_text = "Session vorzeitig beendet" if force_ended else "Lernsession abgeschlossen"
        ctk.CTkLabel(
            hero_content,
            text=subtitle_text,
            font=ctk.CTkFont(size=14),
            text_color="#64748b"
        ).pack()

        # Moderne Statistik-Karten
        stats_container = ctk.CTkFrame(main_container, fg_color="transparent")
        stats_container.pack(fill='x', pady=(0, 20))
        stats_container.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Statistik-Karten mit Icons
        stats = [
            ("🎴", "Karten", f"{correct_count}/{total_cards}",
             "#10b981" if success_rate >= 70 else "#f59e0b"),
            ("📊", "Erfolgsquote", f"{success_rate:.0f}%",
             "#10b981" if success_rate >= 70 else ("#f59e0b" if success_rate >= 50 else "#ef4444")),
            ("⭐", "Netto-Punkte", f"{net_points:+d}",
             "#10b981" if net_points > 0 else ("#f59e0b" if net_points == 0 else "#ef4444")),
            ("⏱️", "Lernzeit", f"{total_time_minutes:.1f} min", "#3b82f6")
        ]

        for col, (icon, label, value, color) in enumerate(stats):
            stat_card = ctk.CTkFrame(stats_container, fg_color="#ffffff", corner_radius=12,
                                    border_width=2, border_color=color)
            stat_card.grid(row=0, column=col, padx=8, pady=5, sticky="nsew")

            # Icon
            ctk.CTkLabel(
                stat_card,
                text=icon,
                font=ctk.CTkFont(size=32)
            ).pack(pady=(15, 5))

            # Label
            ctk.CTkLabel(
                stat_card,
                text=label,
                font=ctk.CTkFont(size=12),
                text_color="#64748b"
            ).pack()

            # Wert
            ctk.CTkLabel(
                stat_card,
                text=value,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=color
            ).pack(pady=(5, 15))

        # Detaillierte Kartenübersicht mit modernem Design
        details_section = ctk.CTkFrame(main_container, fg_color="#f8fafc", corner_radius=12)
        details_section.pack(fill='both', expand=True)

        # Header für Details
        details_header = ctk.CTkFrame(details_section, fg_color="transparent")
        details_header.pack(fill='x', padx=20, pady=(15, 10))

        ctk.CTkLabel(
            details_header,
            text="📋 Detaillierter Verlauf",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1e293b"
        ).pack(side='left')

        # Scrollbarer Bereich für Karten
        details_scroll = ctk.CTkScrollableFrame(details_section, fg_color="transparent", height=300)
        details_scroll.pack(fill='both', expand=True, padx=15, pady=(0, 15))

        for idx, result in enumerate(self.session_results, 1):
            # Extrahiere Werte
            card = result[0]
            is_correct = result[1] if len(result) > 1 else False
            time_spent = result[2] if len(result) > 2 else 0
            points_change = result[3] if len(result) > 3 else 0
            level_before = result[6] if len(result) > 6 else getattr(card, 'level', 1)
            level_after = result[7] if len(result) > 7 else getattr(card, 'level', 1)
            level_change = level_after - level_before

            # Moderne Karten-Card
            card_color = "#10b981" if is_correct else "#ef4444"
            card_bg = "#f0fdf4" if is_correct else "#fef2f2"

            card_frame = ctk.CTkFrame(details_scroll, fg_color=card_bg, corner_radius=8,
                                     border_width=2, border_color=card_color)
            card_frame.pack(fill='x', pady=4, padx=5)

            # Hauptinhalt
            content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            content_frame.pack(fill='x', padx=12, pady=10)
            content_frame.grid_columnconfigure(1, weight=1)

            # Status Icon
            status_icon = "✓" if is_correct else "✗"
            icon_frame = ctk.CTkFrame(content_frame, fg_color=card_color, corner_radius=20, width=36, height=36)
            icon_frame.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="n")
            icon_frame.grid_propagate(False)

            ctk.CTkLabel(
                icon_frame,
                text=status_icon,
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#ffffff"
            ).place(relx=0.5, rely=0.5, anchor="center")

            # Kartennummer und Frage
            card_text = card.question[:70] + "..." if len(card.question) > 70 else card.question
            question_label = ctk.CTkLabel(
                content_frame,
                text=f"#{idx}  {card_text}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#1e293b",
                anchor="w"
            )
            question_label.grid(row=0, column=1, sticky="w")

            # Details-Info-Zeile
            details_container = ctk.CTkFrame(content_frame, fg_color="transparent")
            details_container.grid(row=1, column=1, sticky="w", pady=(5, 0))

            # Punkte-Badge
            points_badge = ctk.CTkFrame(details_container, fg_color="#ffffff", corner_radius=4)
            points_badge.pack(side='left', padx=(0, 8))
            points_text = f"{points_change:+d} Pkt"
            ctk.CTkLabel(points_badge, text=points_text, font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=card_color).pack(padx=6, pady=2)

            # Level-Badge
            level_badge = ctk.CTkFrame(details_container, fg_color="#ffffff", corner_radius=4)
            level_badge.pack(side='left', padx=(0, 8))
            level_text = f"Level {level_before} → {level_after}"
            if level_change != 0:
                level_text += f" ({level_change:+d})"
            ctk.CTkLabel(level_badge, text=level_text, font=ctk.CTkFont(size=10),
                        text_color="#64748b").pack(padx=6, pady=2)

            # Aktuelle Stats
            current_badge = ctk.CTkFrame(details_container, fg_color="#ffffff", corner_radius=4)
            current_badge.pack(side='left', padx=(0, 8))
            ctk.CTkLabel(current_badge, text=f"Gesamt: {card.points} Pkt | Level {card.level}",
                        font=ctk.CTkFont(size=10), text_color="#475569").pack(padx=6, pady=2)

            # Streak-Badge (falls vorhanden)
            if card.positive_streak > 0:
                streak_badge = ctk.CTkFrame(details_container, fg_color="#fef3c7", corner_radius=4)
                streak_badge.pack(side='left')
                ctk.CTkLabel(streak_badge, text=f"🔥 Streak: {card.positive_streak}",
                            font=ctk.CTkFont(size=10, weight="bold"),
                            text_color="#f59e0b").pack(padx=6, pady=2)

        # Moderne Button-Sektion
        button_section = ctk.CTkFrame(main_container, fg_color="transparent")
        button_section.pack(pady=(15, 0))

        button_container = ctk.CTkFrame(button_section, fg_color="#ffffff", corner_radius=12)
        button_container.pack(padx=20, pady=10)

        buttons_inner = ctk.CTkFrame(button_container, fg_color="transparent")
        buttons_inner.pack(padx=20, pady=15)

        ctk.CTkButton(
            buttons_inner,
            text="🔄 Neue Lernsession",
            command=self.show_leitner_options,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=180,
            corner_radius=8,
            fg_color="#10b981",
            hover_color="#059669"
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            buttons_inner,
            text="📊 Leitner-Optionen",
            command=self.show_leitner_options,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=180,
            corner_radius=8,
            fg_color="#3b82f6",
            hover_color="#2563eb"
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            buttons_inner,
            text="📅 Zum Kalender",
            command=self.show_weekly_calendar,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=180,
            corner_radius=8,
            fg_color="#8b5cf6",
            hover_color="#7c3aed"
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            buttons_inner,
            text="🏠 Hauptmenü",
            command=self.create_main_menu,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=150,
            corner_radius=8,
            fg_color="#64748b",
            hover_color="#475569"
        ).pack(side='left', padx=5)

        # Speichere Statistik
        session_stat = {
            "date": datetime.datetime.now().strftime("%d.%m.%Y"),
            "time": datetime.datetime.now().strftime("%H:%M"),
            "cards_total": total_cards,
            "cards_correct": correct_count,
            "total_time": total_time_minutes,
            "avg_time_per_card": total_time_minutes / total_cards if total_cards > 0 else 0,
            "success_rate": success_rate,
            "system": "Leitner",
            "force_ended": force_ended,
            "net_points": net_points
        }

        try:
            if hasattr(self, 'stats_manager'):
                self.stats_manager.add_session_summary(session_stat)
            logging.info("Leitner-Sitzungsstatistik gespeichert")
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Leitner-Statistik: {e}")

        # Update Planeintrag falls vorhanden (für Kalender-Integration)
        if hasattr(self, 'current_plan_id') and self.current_plan_id:
            try:
                updates = {
                    'status': 'erledigt',
                    'erledigt_am': datetime.datetime.now().isoformat(),
                    'tatsaechliche_karten': total_cards,
                    'erfolgsquote': success_rate,
                    'karten_korrekt': correct_count
                }
                self.data_manager.update_plan_entry(self.current_plan_id, updates)
                logging.info(f"Planeintrag {self.current_plan_id} als erledigt markiert.")
                # Lösche plan_id nach Verwendung
                delattr(self, 'current_plan_id')
            except Exception as e:
                logging.error(f"Fehler beim Aktualisieren des Planeintrags: {e}")

    def show_srs_learning_options(self):
        """Zeigt die SRS-Lernoptionen mit erweiterten Filtern an."""
        self._clear_content_frame()
        
        # Header
        header = ctk.CTkLabel(
            self.content_frame,
            text="Intelligentes Lernen (SRS)",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=20)

        # Container für Filter und Karten
        main_container = ctk.CTkFrame(self.content_frame)
        main_container.pack(fill='both', expand=True, padx=20, pady=10)

        # Filter Frame
        filter_frame = ctk.CTkFrame(main_container)
        filter_frame.pack(fill='x', pady=10)

        # Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
        # Zeile 1: Kategorie und Unterkategorie
        # Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
        row1 = ctk.CTkFrame(filter_frame)
        row1.pack(fill='x', pady=5)

        ctk.CTkLabel(row1, text="Kategorie:", font=ctk.CTkFont(size=12)).pack(side='left', padx=5)
        
        self.category_var = tk.StringVar(value="Alle")
        categories = ["Alle"] + sorted(self.data_manager.categories.keys())
        category_menu = ctk.CTkOptionMenu(
            row1,
            variable=self.category_var,
            values=categories,
            width=200,
            command=lambda x: (self.update_subcategories_srs(), self.preview_filtered_count())
        )
        category_menu.pack(side='left', padx=5)

        ctk.CTkLabel(row1, text="Unterkategorie:", font=ctk.CTkFont(size=12)).pack(side='left', padx=5)

        self.subcategory_var = tk.StringVar(value="Alle")
        self.subcategory_menu = ctk.CTkOptionMenu(
            row1,
            variable=self.subcategory_var,
            values=["Alle"],
            width=200,
            command=lambda x: self.preview_filtered_count()
        )
        self.subcategory_menu.pack(side='left', padx=5)

        # NEU: Mehrfachauswahl für Unterkategorien
        self.multi_select_active = tk.BooleanVar(value=False)
        self.selected_subcategories = set()

        multi_frame = ctk.CTkFrame(filter_frame)
        multi_frame.pack(fill='x', pady=5)

        # Checkbox für Mehrfachauswahl
        multi_select_cb = ctk.CTkCheckBox(
            multi_frame,
            text="Mehrere Unterkategorien auswÃƒÂ¤hlen",
            variable=self.multi_select_active,
            command=self.toggle_subcategory_mode
        )
        multi_select_cb.pack(side='left', padx=5)

        # Button zum Ãƒâ€“ffnen der Mehrfachauswahl
        self.select_subcats_btn = ctk.CTkButton(
            multi_frame,
            text="Unterkategorien wÃƒÂ¤hlen",
            command=self.open_subcategory_selector,
            width=150,
            state="disabled"  # Initial deaktiviert
        )
        self.select_subcats_btn.pack(side='left', padx=5)

        # Label für ausgewÃƒÂ¤hlte Unterkategorien
        self.multi_select_label = ctk.CTkLabel(
            multi_frame,
            text="Keine Unterkategorien ausgewÃƒÂ¤hlt",
            font=ctk.CTkFont(size=12)
        )
        self.multi_select_label.pack(side='left', padx=20)


        # Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
        # Zeile 2: Erweiterte Filter
        # Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
        row2 = ctk.CTkFrame(filter_frame)
        row2.pack(fill='x', pady=5)

        # Erfolgsquoten-Filter
        ctk.CTkLabel(row2, text="Erfolgsquote:", font=ctk.CTkFont(size=12)).pack(side='left', padx=5)

        self.success_rate_var = tk.StringVar(value="Filter aus")
        self.success_rate_menu = ctk.CTkOptionMenu(
            row2,
            variable=self.success_rate_var,
            values=["Filter aus", "unter 25%", "unter 50%", "unter 75%", "unter 90%"],
            width=120,
            command=lambda x: self.preview_filtered_count()
        )
        self.success_rate_menu.pack(side='left', padx=5)

        # Zeit seit letztem Lernen
        ctk.CTkLabel(row2, text="Nicht gelernt seit:", font=ctk.CTkFont(size=12)).pack(side='left', padx=5)

        self.last_learned_var = tk.StringVar(value="Filter aus")
        self.last_learned_menu = ctk.CTkOptionMenu(
            row2,
            variable=self.last_learned_var,
            values=["Filter aus", "3 Tagen", "5 Tagen", "7 Tagen", "10 Tagen"],
            width=120,
            command=lambda x: self.preview_filtered_count()
        )
        self.last_learned_menu.pack(side='left', padx=5)

        # FÃƒÂ¤llige/Neue Karten Filter
        ctk.CTkLabel(row2, text="Kartenstatus:", font=ctk.CTkFont(size=12)).pack(side='left', padx=5)

        self.card_status_var = tk.StringVar(value="Filter aus")
        self.card_status_menu = ctk.CTkOptionMenu(
            row2,
            variable=self.card_status_var,
            values=["Filter aus", "Fällige Karten", "Neue Karten"],
            width=120,
            command=lambda x: self.preview_filtered_count()
        )
        self.card_status_menu.pack(side='left', padx=5)

        # Container für die Kartenanzeige (initial leer)
        self.cards_container = ctk.CTkScrollableFrame(main_container)
        self.cards_container.pack(fill='both', expand=True, pady=10)

        # Initial-Nachricht
        ctk.CTkLabel(
            self.cards_container,
            text="WÃƒÂ¤hle deine Filter und klicke 'Filter anwenden' um Karten zu laden.",
            font=ctk.CTkFont(size=14)
        ).pack(pady=20)

        # Button Frame
        button_frame = ctk.CTkFrame(main_container)
        button_frame.pack(fill='x', pady=10)

        # Filter anwenden Button
        self.apply_filter_btn = ctk.CTkButton(
            button_frame,
            text="Filter anwenden",
            command=self.apply_srs_filters,
            font=ctk.CTkFont(size=14),
            height=35,
            fg_color="#4a90e2",  # Blau
        )
        self.apply_filter_btn.pack(side='left', padx=5)

        # Anzeige der Kartenanzahl
        self.card_count_label = ctk.CTkLabel(
            button_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.card_count_label.pack(side='left', padx=10)

        # Rechte Seite der Button-Leiste
        right_buttons = ctk.CTkFrame(button_frame, fg_color="transparent")
        right_buttons.pack(side='right')

        # Session starten Button mit dezenteren Farben
        self.start_btn = ctk.CTkButton(
            right_buttons,
            text="Lernsession starten",
            command=self.start_srs_session,
            font=ctk.CTkFont(size=14),
            height=35,
            fg_color="#34495e",     # Dunkelgrau-Blau
            hover_color="#2c3e50",  # Etwas dunklerer Hover-Effekt
        )
        self.start_btn.pack(side='left', padx=5)

        # Dynamische SRS Button mit dezenteren Farben
        self.dynamic_srs_btn = ctk.CTkButton(
            right_buttons,
            text="Dynamische SRS",
            command=self.start_dynamic_srs_session,
            font=ctk.CTkFont(size=14),
            height=35,
            fg_color="#4a6984",     # Dezentes Blau-Grau
            hover_color="#3d5a75",  # Dunklerer Hover-Effekt
        )
        self.dynamic_srs_btn.pack(side='left', padx=5)

        # Zurück Button
        back_btn = ctk.CTkButton(
            self.content_frame,
            text="Zurück zur Methodenauswahl",
            command=self.show_learning_options,
            font=ctk.CTkFont(size=14),
            height=35,
            fg_color="gray",
            hover_color="darkgray"
        )
        back_btn.pack(pady=10)

        # Initial Vorschau
        self.preview_filtered_count()
    def toggle_subcategory_mode(self):
        """Wechselt zwischen Einzel- und Mehrfachauswahl für Unterkategorien."""
        if self.multi_select_active.get():
            if self.category_var.get() == "Alle":
                messagebox.showwarning("Warnung", "Bitte zuerst eine Kategorie auswÃƒÂ¤hlen.")
                self.multi_select_active.set(False)
                return
                
            self.subcategory_menu.configure(state="disabled")
            self.select_subcats_btn.configure(state="normal")
            self.selected_subcategories.clear()
            self.multi_select_label.configure(text="Keine Unterkategorien ausgewÃƒÂ¤hlt")
        else:
            self.subcategory_menu.configure(state="normal")
            self.select_subcats_btn.configure(state="disabled")
            self.selected_subcategories.clear()
            self.multi_select_label.configure(text="Keine Unterkategorien ausgewÃƒÂ¤hlt")
        
        self.preview_filtered_count()

    def open_subcategory_selector(self):
        """Ãƒâ€“ffnet Dialog für Unterkategorie-Mehrfachauswahl."""
        popup = tk.Toplevel(self.master)
        popup.title("Unterkategorien auswÃƒÂ¤hlen")
        popup.geometry("400x500")
        popup.transient(self.master)
        popup.grab_set()

        # Haupt-Container
        main_container = ctk.CTkFrame(popup)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Suchfeld
        search_var = tk.StringVar()
        search_frame = ctk.CTkFrame(main_container)
        search_frame.pack(fill='x', pady=(0, 10))
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Suchen...",
            textvariable=search_var
        )
        search_entry.pack(fill='x', padx=5, pady=5)

        # Scrollbarer Frame für Checkboxen
        scroll_frame = ctk.CTkScrollableFrame(main_container)
        scroll_frame.pack(fill='both', expand=True, pady=(0, 10))

        # "Alle auswÃƒÂ¤hlen" Checkbox
        select_all_var = tk.BooleanVar(value=False)
        checkbox_widgets = {}  # Dictionary: {subcat: (checkbox, BooleanVar)}


        def toggle_all():
            state = select_all_var.get()
            for (cb, var) in checkbox_widgets.values():
                var.set(state)

        select_all_cb = ctk.CTkCheckBox(
            scroll_frame,
            text="Alle auswÃƒÂ¤hlen/abwÃƒÂ¤hlen",
            variable=select_all_var,
            command=toggle_all
        )
        select_all_cb.pack(pady=5)

        # Hole Unterkategorien der gewÃƒÂ¤hlten Kategorie
        category = self.category_var.get()
        subcategories = sorted(self.data_manager.categories.get(category, {}).keys())

        for subcat in subcategories:
            var = tk.BooleanVar(value=(subcat in self.selected_subcategories))
            cb = ctk.CTkCheckBox(
                scroll_frame,
                text=subcat,
                variable=var
            )
            cb.pack(pady=2, padx=5, anchor='w')
            checkbox_widgets[subcat] = (cb, var)

        # Suchfunktion: Filtert die Checkboxen anhand des Suchbegriffs
        def filter_subcategories(*args):
            search_text = search_var.get().lower()
            for subcat, (cb, var) in checkbox_widgets.items():
                if search_text in subcat.lower():
                    cb.pack(pady=2, padx=5, anchor='w')
                else:
                    cb.pack_forget()

        search_var.trace_add("write", filter_subcategories)

        # Button Frame am unteren Rand des Dialogs
        button_frame = ctk.CTkFrame(main_container)
        button_frame.pack(fill='x', pady=(0, 5))
        def confirm_selection():
            """BestÃƒÂ¤tigt die Auswahl und aktualisiert die Ansicht."""
            # Aktualisiere die ausgewÃƒÂ¤hlten Unterkategorien
            self.selected_subcategories = {subcat for subcat, (cb, var) in checkbox_widgets.items() if var.get()}
            
            try:
                if hasattr(self, 'selection_label'):
                    if self.selection_label.winfo_exists():
                        if self.selected_subcategories:
                            count = len(self.selected_subcategories)
                            self.selection_label.configure(text=f"{count} Unterkategorien ausgewÃƒÂ¤hlt")
                        else:
                            self.selection_label.configure(text="Keine Unterkategorien ausgewÃƒÂ¤hlt")
            except Exception as e:
                logging.error(f"Fehler beim Aktualisieren des Selection Labels: {e}")
                
            popup.destroy()
            self.preview_filtered_count()  # Aktualisiere die Vorschau

        # Buttons im button_frame hinzufügen
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="BestÃƒÂ¤tigen",
            command=confirm_selection,  # Hier wird die Funktion verbunden
            width=120
        )
        confirm_btn.pack(side='left', padx=5, pady=5)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            command=popup.destroy,
            fg_color="gray",
            hover_color="darkgray",
            width=120
        )
        cancel_btn.pack(side='right', padx=5, pady=5)



    def preview_filtered_count(self):
        """Zeigt die Anzahl der gefilterten Karten, ohne sie zu laden."""
        try:
            category = None if self.category_var.get() == "Alle" else self.category_var.get()
            
            # Initialer Filter für Kategorien/Subkategorien
            if self.multi_select_active.get() and self.selected_subcategories:
                filtered_cards = [
                    card for card in self.data_manager.filter_flashcards_by_category_and_subcategory(category, None)
                    if card.subcategory in self.selected_subcategories
                ]
            else:
                subcategory = None if self.subcategory_var.get() == "Alle" else self.subcategory_var.get()
                filtered_cards = self.data_manager.filter_flashcards_by_category_and_subcategory(category, subcategory)

            today = datetime.date.today()

            # Erfolgsquoten-Filter
            if self.success_rate_var.get() != "Filter aus":
                threshold = float(self.success_rate_var.get().split()[1].strip('%'))
                filtered_cards = [
                    c for c in filtered_cards
                    if c.repetitions > 0 and 
                    (c.success_count / c.repetitions * 100) < threshold
                ]

            # Zeit seit letztem Lernen
            if self.last_learned_var.get() != "Filter aus":
                days = int(self.last_learned_var.get().split()[0])
                threshold_date = today - datetime.timedelta(days=days)
                filtered_cards = [
                    c for c in filtered_cards
                    if self.safe_parse_date(c.last_reviewed) <= threshold_date
                ]

            # Kartenstatus
            card_status = self.card_status_var.get()
            if card_status != "Filter aus":
                if card_status == "Fällige Karten":
                    filtered_cards = [
                        c for c in filtered_cards
                        if self.safe_parse_date(c.next_review) <= today
                    ]
                elif card_status == "Neue Karten":
                    filtered_cards = [c for c in filtered_cards if c.repetitions == 0]

            # UI aktualisieren
            if hasattr(self, 'apply_filter_btn') and self.apply_filter_btn.winfo_exists():
                self.apply_filter_btn.configure(text=f"Filter anwenden ({len(filtered_cards)} Karten)")
            
            if hasattr(self, 'card_count_label') and self.card_count_label.winfo_exists():
                self.card_count_label.configure(text=f"Gefilterte Karten verfügbar: {len(filtered_cards)}")
            
            # Session-Buttons Status aktualisieren
            if hasattr(self, 'start_btn') and self.start_btn.winfo_exists():
                self.start_btn.configure(state="normal" if filtered_cards else "disabled")
                
            if hasattr(self, 'dynamic_srs_btn') and self.dynamic_srs_btn.winfo_exists():
                self.dynamic_srs_btn.configure(state="normal" if filtered_cards else "disabled")

        except Exception as e:
            logging.error(f"Fehler bei der Kartenvorschau: {e}")
            if hasattr(self, 'card_count_label') and self.card_count_label.winfo_exists():
                self.card_count_label.configure(text="Fehler bei der Vorschau")
    def update_subcategories_srs(self, *args):
        """Aktualisiert die Unterkategorien und setzt Mehrfachauswahl zurück."""
        selected_category = self.category_var.get()
        if selected_category == "Alle":
            subcats = ["Alle"]
        else:
            subcats = ["Alle"] + sorted(self.data_manager.categories.get(selected_category, {}).keys())
        
        self.subcategory_menu.configure(values=subcats)
        self.subcategory_var.set("Alle")
        
        # Setze Mehrfachauswahl zurück
        self.selected_subcategories.clear()
        self.multi_select_active.set(False)
        self.multi_select_label.configure(text="Keine Unterkategorien ausgewÃƒÂ¤hlt")
        self.preview_filtered_count()


    def safe_parse_date(self, date_str):
        """
        Parst ein Datum sicher und handhabt verschiedene Formate.
        
        Args:
            date_str (str): Das zu parsende Datum
            
        Returns:
            datetime.date: Das geparste Datum oder heute bei Fehler
        """
        if not date_str:
            return datetime.date.today()
            
        try:
            # Ersetze Bindestriche durch Punkte für einheitliches Format
            date_str = date_str.replace("-", ".")
            parts = date_str.split(".")
            
            if len(parts) != 3:
                raise ValueError("Ungültiges Datumsformat")
                
            # Wenn das Jahr am Anfang steht (YYYY.MM.DD)
            if len(parts[0]) == 4:
                year, month, day = parts
                date_str = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
                
            return datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
        except Exception as e:
            logging.error(f"Fehler beim Parsen des Datums {date_str}: {e}")
            return datetime.date.today()

    def apply_srs_filters(self):
        """
        Wendet die ausgewÃƒÂ¤hlten Filter an und zeigt die gefilterten Karten.
        """
        # 1) Alte Inhalte entfernen
        for widget in self.cards_container.winfo_children():
            widget.destroy()

        try:
            # 2) Basisfilter (Kategorie/Unterkategorie)
            category = None if self.category_var.get() == "Alle" else self.category_var.get()

            # PrÃƒÂ¼fe ob Mehrfachauswahl aktiv ist
            if self.multi_select_active.get() and self.selected_subcategories:
                # Bei Mehrfachauswahl filtern wir die Karten manuell
                filtered_cards = [
                    card for card in self.data_manager.filter_flashcards_by_category_and_subcategory(category, None)
                    if card.subcategory in self.selected_subcategories
                ]
            else:
                # Normale Einzelauswahl
                subcategory = None if self.subcategory_var.get() == "Alle" else self.subcategory_var.get()
                filtered_cards = self.data_manager.filter_flashcards_by_category_and_subcategory(category, subcategory)
            # 3) Heute als Referenzdatum
            today = datetime.date.today()

            # 3a) Erfolgsquoten-Filter
            if self.success_rate_var.get() != "Filter aus":
                threshold = float(self.success_rate_var.get().split()[1].strip('%'))
                filtered_cards = [
                    card for card in filtered_cards
                    if card.repetitions > 0 and 
                    (card.success_count / card.repetitions * 100) < threshold
                ]

            # 3b) Zeit seit letztem Lernen
            if self.last_learned_var.get() != "Filter aus":
                days = int(self.last_learned_var.get().split()[0])
                threshold_date = today - datetime.timedelta(days=days)
                filtered_cards = [
                    card for card in filtered_cards
                    if self.safe_parse_date(card.last_reviewed) <= threshold_date
                ]

            # 3c) Kartenstatus (Fällig/Neu)
            card_status = self.card_status_var.get()
            if card_status != "Filter aus":
                if card_status == "Fällige Karten":
                    filtered_cards = [
                        card for card in filtered_cards
                        if self.safe_parse_date(card.next_review_date) <= today
                    ]
                elif card_status == "Neue Karten":
                    filtered_cards = [card for card in filtered_cards if card.repetitions == 0]
            #4) Kartenanzeige aktualisieren
            if not filtered_cards:
                ctk.CTkLabel(
                    self.cards_container,
                    text="Keine Karten für die gewÃƒÂ¤hlten Filter gefunden.",
                    font=ctk.CTkFont(size=14)
                ).pack(pady=20)
                self.card_count_label.configure(text="Gefundene Karten: 0")
                return

            # 5) Kartenanzahl aktualisieren
            self.card_count_label.configure(text=f"Gefundene Karten: {len(filtered_cards)}")

            # 6) Karten-Dictionary initialisieren
            self.card_checkboxes = {}
            self.filtered_cards_srs = filtered_cards

            # 7) "Alle auswÃƒÂ¤hlen" Option
            select_frame = ctk.CTkFrame(self.cards_container)
            select_frame.pack(fill='x', pady=5, padx=5)
            
            self.select_all_var = tk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                select_frame,
                text="Alle auswÃƒÂ¤hlen/abwÃƒÂ¤hlen",
                variable=self.select_all_var,
                command=self.toggle_all_cards,
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(side='left', padx=5)

            # 8) Karten auflisten
            for idx, card in enumerate(filtered_cards):
                try:
                    card_frame = ctk.CTkFrame(self.cards_container)
                    card_frame.pack(fill='x', pady=5, padx=5)

                    # Checkbox für Kartenauswahl
                    self.card_checkboxes[idx] = tk.BooleanVar(value=False)
                    ctk.CTkCheckBox(
                        card_frame,
                        text=f"{idx + 1}. {card.question}",
                        variable=self.card_checkboxes[idx],
                        font=ctk.CTkFont(size=12, weight="bold")
                    ).pack(fill='x', padx=5, pady=2)

                    # Kartendetails berechnen
                    success_rate = (card.success_count/card.repetitions*100) if card.repetitions > 0 else 0
                    next_review_date = self.safe_parse_date(card.next_review)
                    days_until_review = (next_review_date - today).days
                    review_status = f'in {days_until_review} Tagen' if days_until_review > 0 else 'FÃƒâ€žLLIG'


                    # Detailierte Karteninfo
                    info = (
                        f"Kategorie: {card.category} > {card.subcategory}\n"
                        f"Erfolgsquote: {success_rate:.1f}% | "
                        f"Richtig in Folge: {card.consecutive_correct} | "
                        f"Wiederholungen: {card.repetitions} | "
                        f"Nächste Wiederholung: {review_status}"
                    )
                    
                    ctk.CTkLabel(
                        card_frame,
                        text=info,
                        font=ctk.CTkFont(size=10)
                    ).pack(pady=5, padx=10)
                    
                except Exception as e:
                    logging.error(f"Fehler beim Anzeigen der Karte {idx}: {e}")
                    continue

        except Exception as e:
            logging.error(f"Fehler beim Filtern der Karten: {e}")
            self.card_count_label.configure(text="Fehler beim Filtern")
            ctk.CTkLabel(
                self.cards_container,
                text=f"Fehler beim Filtern der Karten: {str(e)}",
                font=ctk.CTkFont(size=14)
            ).pack(pady=20)

    def toggle_all_cards(self):
        """Setzt bei allen gefilterten Karten den gleichen BooleanÃ¢â‚¬ÂWert wie `select_all_var`."""
        is_selected = self.select_all_var.get()
        for idx in self.card_checkboxes:
            self.card_checkboxes[idx].set(is_selected)


    def start_srs_session(self):
        """
        Startet eine SRSÃ¢â‚¬ÂLernsession mit den ausgewÃƒÂ¤hlten Karten
        (die aktuell gefiltert wurden).
        """
        if not hasattr(self, 'card_checkboxes') or not hasattr(self, 'filtered_cards_srs'):
            messagebox.showinfo("Info", "Keine Karten zum Lernen verfügbar.")
            return

        selected_cards = []
        for idx, var in self.card_checkboxes.items():
            if var.get():
                selected_cards.append(self.filtered_cards_srs[idx])

        if not selected_cards:
            messagebox.showinfo("Info", "Bitte wÃƒÂ¤hlen Sie mindestens eine Karte aus.")
            return

        self.cards_this_session = selected_cards
        self.session_results = []

        if self.appearance_settings.track_learning_time:
            self.session_start_time = datetime.datetime.now()

        # Methode, die das eigentliche LernÃ¢â‚¬ÂUI zeigt
        self.show_card_window()
        
    
        ############################################
    # DYNAMISCHE SRS SESSION (NEU) - CODE BLOCK
    ############################################

    def start_dynamic_srs_session(self):
        """
        Startet eine neue, vereinfachte SRS-Session mit zufÃƒÂ¤llig gemischten Karten.
        """
        # 1) PrÃƒÂ¼fe ob Karten ausgewÃƒÂ¤hlt wurden
        if not hasattr(self, 'card_checkboxes') or not hasattr(self, 'filtered_cards_srs'):
            messagebox.showwarning("Warnung", "Keine Karten ausgewÃƒÂ¤hlt.")
            return
        
        # 2) Sammle ausgewÃƒÂ¤hlte Karten
        selected_cards = []
        for idx, var in self.card_checkboxes.items():
            if var.get():
                selected_cards.append(self.filtered_cards_srs[idx])

        if not selected_cards:
            messagebox.showinfo("Info", "Bitte mindestens eine Karte auswÃƒÂ¤hlen.")
            return

        # 3) Mische die Karten zufÃƒÂ¤llig
        random.shuffle(selected_cards)
        self.cards_to_learn = selected_cards
        
        # NEU: Session-Ergebnisse zurücksetzen
        self.session_results = []
        
        # 4) Starte Zeitmessung falls aktiviert
        if self.appearance_settings.track_learning_time:
            self.session_start_time = datetime.datetime.now()
        
        # 5) Beginne mit erster Karte
        self.show_card_window_dynamically()

    def show_card_window_dynamically(self):
        """
        Zeigt die aktuelle Karte mit UnterstÃƒÂ¼tzung für Bilder bei Frage UND Antwort.
        """
        if not self.cards_to_learn:
            self.show_leitner_session_summary()
            return

        self._clear_content_frame()

        # Aktuelle Karte laden (NICHT pop, da das in handle_leitner_correct/incorrect gemacht wird)
        self.current_card = self.cards_to_learn[0]

        # Session beenden Button (fixiert unten links) - Modernisiert
        fixed_bottom_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        fixed_bottom_frame.pack(side='bottom', fill='x', padx=20, pady=10)

        ctk.CTkButton(
            fixed_bottom_frame,
            text="🚪 Session beenden",
            command=self.end_leitner_session,
            width=180,
            height=38,
            corner_radius=8,
            fg_color="#64748b",
            hover_color="#475569",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side='left')

        # Hauptcontainer mit hellerem Hintergrund
        scroll_container = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color="#f8fafc"  # Heller, moderner Hintergrund
        )
        scroll_container.pack(fill='both', expand=True, padx=20, pady=(20, 10))

        # Moderne Session-Statistik mit Cards
        stats_container = ctk.CTkFrame(scroll_container, fg_color="#ffffff",
                                      corner_radius=12, border_width=2, border_color="#e2e8f0")
        stats_container.pack(fill='x', pady=(0, 20))

        stats_inner = ctk.CTkFrame(stats_container, fg_color="transparent")
        stats_inner.pack(fill='x', padx=15, pady=12)

        # Berechne Statistiken
        total = self.total_cards_in_session
        current_card_num = total - len(self.cards_to_learn)
        retry_count = len(self.cards_in_retry) if hasattr(self, 'cards_in_retry') else 0

        # Erfolgsquote berechnen
        if hasattr(self, 'total_answers') and self.total_answers > 0:
            success_rate = (self.correct_answers / self.total_answers) * 100
            success_text = f"{success_rate:.0f}%"
            success_color = "#10b981" if success_rate >= 70 else ("#f59e0b" if success_rate >= 40 else "#ef4444")
        else:
            success_text = "-"
            success_color = "#64748b"

        # Fortschritts-Card
        progress_card = ctk.CTkFrame(stats_inner, fg_color="#dbeafe", corner_radius=8)
        progress_card.pack(side='left', padx=5, ipadx=12, ipady=8)
        ctk.CTkLabel(progress_card, text="📚 Fortschritt",
                    font=ctk.CTkFont(size=10),
                    text_color="#1e40af").pack()
        ctk.CTkLabel(progress_card, text=f"{current_card_num}/{total}",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color="#1e3a8a").pack()

        # Wiederholungen-Card
        retry_card = ctk.CTkFrame(stats_inner, fg_color="#fef3c7", corner_radius=8)
        retry_card.pack(side='left', padx=5, ipadx=12, ipady=8)
        ctk.CTkLabel(retry_card, text="🔄 Wiederholungen",
                    font=ctk.CTkFont(size=10),
                    text_color="#92400e").pack()
        ctk.CTkLabel(retry_card, text=str(retry_count),
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color="#78350f").pack()

        # Erfolgsquote-Card
        success_card = ctk.CTkFrame(stats_inner, fg_color="#d1fae5", corner_radius=8)
        success_card.pack(side='right', padx=5, ipadx=12, ipady=8)
        ctk.CTkLabel(success_card, text="📈 Erfolgsquote",
                    font=ctk.CTkFont(size=10),
                    text_color="#065f46").pack()
        ctk.CTkLabel(success_card, text=success_text,
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=success_color).pack()
        
        # === FRAGE CONTAINER === (Modernes Design)
        question_container = ctk.CTkFrame(scroll_container, fg_color="#ffffff",
                                         corner_radius=12, border_width=2, border_color="#bfdbfe")
        question_container.pack(fill='both', pady=10)

        # Frage-Header mit Icon
        header_frame = ctk.CTkFrame(question_container, fg_color="#dbeafe", corner_radius=10)
        header_frame.pack(fill='x', padx=2, pady=2)

        ctk.CTkLabel(
            header_frame,
            text="❓ FRAGE",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1e3a8a"
        ).pack(pady=12)

        # Frage-Text
        question_label = ctk.CTkLabel(
            question_container,
            text=self.current_card.question,
            font=ctk.CTkFont(size=20, weight="bold"),
            wraplength=650,
            text_color="#1e293b"
        )
        question_label.pack(pady=20, padx=25)
        
        # Frage-Bild (NEU!)
        if hasattr(self.current_card, 'question_image_path') and self.current_card.question_image_path:
            self._display_image(
                question_container, 
                self.current_card.question_image_path,
                max_size=(500, 300),
                label_text="Bild zur Frage:"
            )
        
        # "Antwort zeigen" Button (Modern)
        show_answer_btn = ctk.CTkButton(
            scroll_container,
            text="👁️ Antwort anzeigen",
            command=lambda: self._show_answer_and_rating(
                answer_container,
                show_answer_btn,
                rating_frame
            ),
            width=250,
            height=50,
            corner_radius=10,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#6366f1",
            hover_color="#4f46e5"
        )
        show_answer_btn.pack(pady=25)
        
        # === ANTWORT CONTAINER (initial versteckt) === (Modernes Design)
        answer_container = ctk.CTkFrame(scroll_container, fg_color="#ffffff",
                                       corner_radius=12, border_width=2, border_color="#86efac")
        answer_container.pack(fill='both', pady=10)
        answer_container.pack_forget()

        # Antwort-Header mit Icon
        answer_header_frame = ctk.CTkFrame(answer_container, fg_color="#d1fae5", corner_radius=10)
        answer_header_frame.pack(fill='x', padx=2, pady=2)

        ctk.CTkLabel(
            answer_header_frame,
            text="✅ ANTWORT",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#065f46"
        ).pack(pady=12)

        # Antwort-Text
        if self.current_card.answer:
            answer_label = ctk.CTkLabel(
                answer_container,
                text=self.current_card.answer,
                font=ctk.CTkFont(size=20, weight="bold"),
                wraplength=650,
                text_color="#1e293b"
            )
            answer_label.pack(pady=20, padx=25)
        
        # Antwort-Bild
        if hasattr(self.current_card, 'image_path') and self.current_card.image_path:
            self._display_image(
                answer_container,
                self.current_card.image_path,
                max_size=(500, 300),
                label_text="Bild zur Antwort:"
            )
        
        # === BEWERTUNGS-FRAME (initial versteckt) === (Modernes Design)
        rating_frame = ctk.CTkFrame(scroll_container, fg_color="transparent")
        rating_frame.pack(pady=25)
        rating_frame.pack_forget()

        # Bewertungs-Buttons mit modernem Design
        button_container = ctk.CTkFrame(rating_frame, fg_color="transparent")
        button_container.pack(pady=10)

        # Richtig Button
        correct_btn = ctk.CTkButton(
            button_container,
            text="✓ Richtig",
            command=lambda: self._handle_correct_answer(),
            width=180,
            height=60,
            corner_radius=12,
            fg_color="#10b981",
            hover_color="#059669",
            font=ctk.CTkFont(size=18, weight="bold"),
            border_width=2,
            border_color="#6ee7b7"
        )
        correct_btn.pack(side='left', padx=15)

        # Falsch Button
        incorrect_btn = ctk.CTkButton(
            button_container,
            text="✗ Falsch",
            command=lambda: self._handle_incorrect_answer(),
            width=180,
            height=60,
            corner_radius=12,
            fg_color="#ef4444",
            hover_color="#dc2626",
            font=ctk.CTkFont(size=18, weight="bold"),
            border_width=2,
            border_color="#fca5a5"
        )
        incorrect_btn.pack(side='left', padx=15)


    def _display_image(self, parent_frame, image_path, max_size=(500, 300), label_text=None):
        """
        Hilfsfunktion zum Anzeigen von Bildern in der Review-Session.
        
        Args:
            parent_frame: Der Frame, in dem das Bild angezeigt werden soll
            image_path: Pfad zum Bild (relativ oder absolut)
            max_size: Maximale GrÃƒÂ¶ÃƒÅ¸e (width, height)
            label_text: Optional ein Label-Text über dem Bild
        """
        try:
            from PIL import Image, ImageTk
            
            # VollstÃƒÂ¤ndigen Pfad erstellen, falls relativ
            if not os.path.isabs(image_path):
                full_path = os.path.join(self.data_manager.images_dir, image_path)
            else:
                full_path = image_path
            
            # PrÃƒÂ¼fen ob Datei existiert
            if not os.path.exists(full_path):
                logging.warning(f"Bilddatei nicht gefunden: {full_path}")
                ctk.CTkLabel(
                    parent_frame,
                    text=f"Ã¢Å¡Â  Bild nicht gefunden: {os.path.basename(image_path)}",
                    text_color="orange"
                ).pack(pady=5)
                return
            
            # Optional: Label vor dem Bild
            if label_text:
                ctk.CTkLabel(
                    parent_frame,
                    text=label_text,
                    font=ctk.CTkFont(size=12, weight="bold")
                ).pack(pady=(10, 5))
            
            # Bild laden und skalieren
            image = Image.open(full_path)
            max_width, max_height = max_size
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # PhotoImage erstellen
            photo = ImageTk.PhotoImage(image)
            
            # Bild-Label erstellen
            image_label = ctk.CTkLabel(parent_frame, image=photo, text="")
            image_label.image = photo  # Referenz behalten!
            image_label.pack(pady=10)
            
            # Click-Handler für Vollbild-Ansicht
            image_label.bind("<Button-1>", lambda e: self._show_fullscreen_image(full_path))
            image_label.configure(cursor="hand2")
            
            # Hinweis unter dem Bild
            ctk.CTkLabel(
                parent_frame,
                text="(Klick zum Vergrößern)",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            ).pack()
            
        except Exception as e:
            logging.error(f"Fehler beim Laden des Bildes {image_path}: {e}")
            ctk.CTkLabel(
                parent_frame,
                text=f"Ã¢ÂÅ’ Fehler beim Laden: {str(e)}",
                text_color="red"
            ).pack(pady=5)


    def _show_fullscreen_image(self, image_path):
        """Zeigt ein Bild vergrößert innerhalb der App (Overlay) mit optimierter Qualität."""
        try:
            from PIL import Image, ImageTk

            # Erstelle ein modernes Overlay-Frame mit Blur-Effekt-Simulation
            overlay = ctk.CTkFrame(
                self.content_frame,
                fg_color=("#f5f5f5", "#1a1a1e"),  # Modernes Design
                corner_radius=0
            )
            overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

            # Lade das Bild OHNE Größenanpassung zuerst
            image = Image.open(image_path)
            original_width, original_height = image.size

            # Bestimme die maximale Größe (95% der Content-Frame-Größe für mehr Platz)
            max_width = int(self.content_frame.winfo_width() * 0.95)
            max_height = int(self.content_frame.winfo_height() * 0.95)

            # Fallback falls Frame noch nicht gerendert wurde
            if max_width < 100:
                max_width = 1200  # Größerer Fallback für bessere Qualität
            if max_height < 100:
                max_height = 900

            # Intelligente Skalierung: Nur verkleinern wenn nötig, NIE vergrößern (verhindert Unschärfe)
            if original_width <= max_width and original_height <= max_height:
                # Bild ist klein genug - KEINE Skalierung für maximale Schärfe!
                display_image = image
            else:
                # Nur wenn nötig skalieren, mit höchster Qualität
                display_image = image.copy()
                display_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(display_image)

            # Moderner Container mit Schatten-Effekt
            image_outer_container = ctk.CTkFrame(
                overlay,
                fg_color="transparent"
            )
            image_outer_container.place(relx=0.5, rely=0.5, anchor="center")

            # Innerer Container mit Schatten und Rundung
            image_container = ctk.CTkFrame(
                image_outer_container,
                fg_color=("white", "gray20"),
                corner_radius=20,
                border_width=3,
                border_color=("#8b5cf6", "#a78bfa")  # Violetter Akzent
            )
            image_container.pack(padx=20, pady=20)

            # Bild-Label
            image_label = ctk.CTkLabel(
                image_container,
                image=photo,
                text="",
                corner_radius=17
            )
            image_label.image = photo  # Referenz behalten
            image_label.pack(padx=5, pady=5)

            # Moderner Hinweis-Container am unteren Rand
            hint_container = ctk.CTkFrame(
                image_outer_container,
                fg_color=("#8b5cf6", "#7c3aed"),
                corner_radius=25,
                height=45
            )
            hint_container.pack(pady=(10, 0))
            hint_container.pack_propagate(False)

            hint_label = ctk.CTkLabel(
                hint_container,
                text="✕  Klicken zum Schließen  ✕",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="white"
            )
            hint_label.pack(expand=True, padx=30)

            # Schließen bei Klick auf das Overlay oder das Bild
            def close_overlay(event=None):
                overlay.destroy()

            overlay.bind("<Button-1>", close_overlay)
            image_container.bind("<Button-1>", close_overlay)
            image_label.bind("<Button-1>", close_overlay)
            hint_container.bind("<Button-1>", close_overlay)
            hint_label.bind("<Button-1>", close_overlay)

            # Cursor-Stil für alle klickbaren Elemente
            overlay.configure(cursor="hand2")
            image_container.configure(cursor="hand2")
            image_label.configure(cursor="hand2")
            hint_container.configure(cursor="hand2")
            hint_label.configure(cursor="hand2")

        except Exception as e:
            logging.error(f"Fehler in Vollbild-Ansicht: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Laden des Bildes:\n{e}")



    def show_fullscreen_image(self, image_path):
        """Alias für _show_fullscreen_image."""
        return self._show_fullscreen_image(image_path)
    def _show_answer_and_rating(self, answer_container, show_btn, rating_frame):
        """Zeigt die Antwort und Bewertungs-Buttons."""
        show_btn.pack_forget()
        answer_container.pack(fill='both', pady=10)
        rating_frame.pack(pady=20)
        
        # Startzeit für Karte
        if self.appearance_settings.track_learning_time:
            self.card_start_time = datetime.datetime.now()

    def handle_correct(self):
        """Behandelt eine richtige Antwort - entfernt die Karte aus dem Deck."""
        # 1) Zeit-Tracking
        if hasattr(self, 'card_start_time'):
            time_spent = (datetime.datetime.now() - self.card_start_time).total_seconds()
        else:
            time_spent = 0

        # 2) Aktualisiere Statistiken
        self.current_card.repetitions += 1
        self.current_card.success_count += 1
        self.current_card.consecutive_correct += 1

        # 3) Karte wurde richtig beantwortet -> aus der Liste entfernen
        self.session_results.append((self.current_card, True, time_spent))
        self.cards_to_learn.pop(0)  # Entferne die erste Karte (war die aktuelle)

        # 4) Speichern & nÃƒÂ¤chste Karte
        self.data_manager.save_flashcards()
        self.show_card_window_dynamically()

    def handle_incorrect(self):
        """Behandelt eine falsche Antwort - reiht die Karte intelligent wieder ein."""
        # Zeit-Tracking wie bisher
        if hasattr(self, 'card_start_time'):
            time_spent = (datetime.datetime.now() - self.card_start_time).total_seconds()
        else:
            time_spent = 0

        # Statistiken aktualisieren
        self.current_card.repetitions += 1
        self.current_card.consecutive_correct = 0

        # Intelligente Wiedereinreihung
        current_card = self.cards_to_learn.pop(0)
        remaining_cards = len(self.cards_to_learn)

        if remaining_cards > 0:
            # Berechne eine Position basierend auf der Erfolgsquote
            success_rate = current_card.success_count / current_card.repetitions if current_card.repetitions > 0 else 0
            
            # Je niedriger die Erfolgsquote, desto früher kommt die Karte wieder
            if success_rate < 0.3:  # Sehr schwierige Karte
                # Wiederholung nach 3-5 Karten oder früher falls weniger Karten übrig
                min_pos = min(3, remaining_cards)
                max_pos = min(5, remaining_cards)
            elif success_rate < 0.5:  # Schwierige Karte
                # Wiederholung nach 5-8 Karten oder früher falls weniger Karten übrig
                min_pos = min(5, remaining_cards)
                max_pos = min(8, remaining_cards)
            elif success_rate < 0.65:  # Mittelschwere Karte
                # Wiederholung nach 8-10 Karten oder früher falls weniger Karten übrig
                min_pos = min(8, remaining_cards)
                max_pos = min(10, remaining_cards)
            else:  # Einfachere Karte
                # Wiederholung nach 15-30 Karten oder früher falls weniger Karten übrig
                min_pos = min(15, remaining_cards)
                max_pos = min(30, remaining_cards)

            # Bestimme zufällige Position innerhalb des berechneten Bereichs
            insert_pos = random.randint(min_pos, max_pos)
            self.cards_to_learn.insert(insert_pos, current_card)
        else:
            self.cards_to_learn.append(current_card)

        # Statistik und weiter wie bisher
        self.session_results.append((current_card, False, time_spent))
        self.data_manager.save_flashcards()
        self.show_card_window_dynamically()

    def show_session_summary_dynamic_srs(self, force_ended=False):
        """Zeigt eine übersichtliche und optimierte Zusammenfassung der Lernsession an."""
        self._clear_content_frame()

        # --- 1. Statistiken berechnen ---
        total_cards = len(self.session_results)
        correct_answers = sum(1 for r in self.session_results if r[1])  # r[1] = is_correct
        
        # Lernzeit
        total_time_seconds = sum(r[2] for r in self.session_results)  # r[2] = time_spent
        total_time_minutes = total_time_seconds / 60
        avg_time_per_card = total_time_minutes / total_cards if total_cards > 0 else 0
        
        # Erfolgsquote
        success_rate = (correct_answers / total_cards * 100) if total_cards > 0 else 0
        
        # Punkte-Statistiken (mit korrekten Werten!)
        points_gained = sum(r[3] for r in self.session_results if r[1] and len(r) > 3)  # r[3] = points_change
        points_lost = sum(r[3] for r in self.session_results if not r[1] and len(r) > 3)
        net_points = points_gained - points_lost

        # --- 2. Header ---
        header_text = "Session vorzeitig beendet!" if force_ended else "Session abgeschlossen!"
        header = ctk.CTkLabel(
            self.content_frame,
            text=header_text,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=20)

        # --- 3. Zusammenfassung (Kompakt in Grid) ---
        summary_frame = ctk.CTkFrame(self.content_frame)
        summary_frame.pack(padx=20, pady=10)
        summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Statistik-Karten
        stats = [
            ("Karten", f"{correct_answers}/{total_cards}", "#28a745" if success_rate >= 70 else "#ffa500"),
            ("Erfolgsquote", f"{success_rate:.0f}%", "#28a745" if success_rate >= 70 else ("#ffa500" if success_rate >= 50 else "#dc3545")),
            ("Netto-Punkte", f"{net_points:+d}", "#28a745" if net_points > 0 else ("#ffa500" if net_points == 0 else "#dc3545")),
            ("Lernzeit", f"{total_time_minutes:.1f} min", "#4a90e2")
        ]

        for col, (label, value, color) in enumerate(stats):
            stat_frame = ctk.CTkFrame(summary_frame)
            stat_frame.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")
            
            ctk.CTkLabel(
                stat_frame,
                text=label,
                font=ctk.CTkFont(size=12)
            ).pack(pady=(10, 0))
            
            ctk.CTkLabel(
                stat_frame,
                text=value,
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=color
            ).pack(pady=(0, 10))

        # --- 4. Detaillierte Kartenübersicht (OPTIMIERT) ---
        details_header_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        details_header_frame.pack(fill='x', padx=25, pady=(15, 5))
        ctk.CTkLabel(
            details_header_frame,
            text="Detaillierter Verlauf:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side='left')

        details_frame = ctk.CTkScrollableFrame(self.content_frame)
        details_frame.pack(fill='both', expand=True, padx=20, pady=10)

        for idx, result in enumerate(self.session_results, 1):
            card_frame = ctk.CTkFrame(details_frame, border_width=1, border_color=("gray80", "gray30"))
            card_frame.pack(fill='x', pady=4, padx=5)
            card_frame.grid_columnconfigure(0, weight=3)
            card_frame.grid_columnconfigure(1, weight=2)

            # Extrahiere Werte aus result-Tupel
            card = result[0]
            is_correct = result[1]
            time_spent = result[2]
            points_change = result[3] if len(result) > 3 else 0
            base_points = result[4] if len(result) > 4 else 0
            multiplier = result[5] if len(result) > 5 else 1.0
            level_before = result[6] if len(result) > 6 else getattr(card, 'level', 1)
            level_after = result[7] if len(result) > 7 else getattr(card, 'level', 1)
            level_change = level_after - level_before

            # --- Linke Spalte: Status, Frage & Punkteberechnung ---
            info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            info_frame.grid(row=0, column=0, sticky="w", padx=10, pady=8)
            
            status_symbol = "✓" if is_correct else "✗"
            color = "#28a745" if is_correct else "#dc3545"
            card_text = card.question[:55] + "..." if len(card.question) > 55 else card.question
            
            # Status und Frage in einer Zeile
            status_question_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            status_question_frame.pack(anchor='w')
            
            ctk.CTkLabel(
                status_question_frame,
                text=f"{idx}. {status_symbol}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=color
            ).pack(side='left')
            
            ctk.CTkLabel(
                status_question_frame,
                text=card_text,
                font=ctk.CTkFont(size=13)
            ).pack(side='left', padx=(5, 10))

            # Ã¢Å“â€¦ NEU: Korrekte Punkteberechnung mit tatsächlichen Werten
            sign = "+" if is_correct else "-"
            calc_text = f"Punkte: {sign}{points_change} (Basis: {base_points}, Multiplikator: Ãƒâ€”{multiplier:.1f})"
            
            ctk.CTkLabel(
                info_frame,
                text=calc_text,
                font=ctk.CTkFont(size=11, slant="italic"),
                text_color=("gray30", "gray70")
            ).pack(anchor='w', padx=(28, 0))

            # Ã¢Å“â€¦ NEU: Level-Änderung anzeigen
            if level_change != 0:
                if level_change > 0:
                    level_text = f"↑ Level aufgestiegen: {level_before} → {level_after}"
                    level_color = "#28a745"  # Grün
                else:
                    level_text = f"↓ Level abgestiegen: {level_before} → {level_after}"
                    level_color = "#dc3545"  # Rot
                
                ctk.CTkLabel(
                    info_frame,
                    text=level_text,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=level_color
                ).pack(anchor='w', padx=(28, 0))

            # --- Rechte Spalte: Übersichtliche Stats ---
            stats_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            stats_frame.grid(row=0, column=1, sticky="e", padx=10, pady=8)
            
            # Gesamtpunkte
            ctk.CTkLabel(
                stats_frame,
                text="Gesamtpunkte:",
                font=ctk.CTkFont(size=12)
            ).pack(anchor='e')
            ctk.CTkLabel(
                stats_frame,
                text=f"{card.points}",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(anchor='e')

            # Level
            level_name = self.leitner_system.get_level(card.points) if hasattr(self, 'leitner_system') else f"Level {card.level}"
            ctk.CTkLabel(
                stats_frame,
                text="Level:",
                font=ctk.CTkFont(size=12)
            ).pack(anchor='e', pady=(5, 0))
            ctk.CTkLabel(
                stats_frame,
                text=level_name,
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(anchor='e')

            # Erfolgsquote
            success_rate_card = card.success_rate if hasattr(card, 'success_rate') else 0
            ctk.CTkLabel(
                stats_frame,
                text="Erfolgsquote:",
                font=ctk.CTkFont(size=12)
            ).pack(anchor='e', pady=(5, 0))
            ctk.CTkLabel(
                stats_frame,
                text=f"{success_rate_card:.0%}",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(anchor='e')

        # --- 5. Untere Buttons ---
        button_frame = ctk.CTkFrame(self.content_frame)
        button_frame.pack(pady=20)

        ctk.CTkButton(
            button_frame,
            text="Zurück zum Hauptmenü",
            command=self.create_main_menu,
            height=35,
            width=180
        ).pack(side='left', padx=10)

        ctk.CTkButton(
            button_frame,
            text="Neue Leitner-Session",
            command=self.show_leitner_options,
            height=35,
            width=180,
            fg_color="#4a90e2"
        ).pack(side='left', padx=10)

        ctk.CTkButton(
            button_frame,
            text="Zur Statistik",
            command=self.show_statistics,
            height=35,
            width=180,
            fg_color="#2ecc71"
        ).pack(side='left', padx=10)

        # --- 6. Session-Statistik speichern ---
        try:
            session_stat = {
                "date": datetime.datetime.now().strftime("%d.%m.%Y"),
                "time": datetime.datetime.now().strftime("%H:%M"),
                "cards_total": total_cards,
                "cards_correct": correct_answers,
                "total_time": total_time_minutes,
                "avg_time_per_card": avg_time_per_card,
                "success_rate": success_rate,
                "points_gained": points_gained,
                "points_lost": points_lost,
                "net_points": net_points,
                "force_ended": force_ended,
                "details": [
                    {
                        "question": r[0].question,
                        "category": getattr(r[0], 'category', 'N/A'),
                        "subcategory": getattr(r[0], 'subcategory', 'N/A'),
                        "correct": r[1],
                        "learning_time": r[2],
                        "points_change": r[3] if len(r) > 3 else 0,
                        "base_points": r[4] if len(r) > 4 else 0,
                        "multiplier": r[5] if len(r) > 5 else 1.0,
                        "level_before": r[6] if len(r) > 6 else 1,
                        "level_after": r[7] if len(r) > 7 else 1,
                        "tags": getattr(r[0], 'tags', [])
                    } for r in self.session_results
                ],
                "method": "leitner"
            }
            self.stats_manager.add_session_summary(session_stat)
            logging.info("Leitner Session-Statistik gespeichert")
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Leitner-Statistik: {e}")
    def show_card_window(self):
        """Zeigt das eigentliche Kartenfenster an (Frage/Antwort)."""
        self._clear_content_frame()

        if not self.cards_this_session:
            # Keine Karten mehr ÃƒÂ¼brig => Zeige Zusammenfassung
            self.show_session_summary()
            return

        # Container
        main_container = tk.Frame(self.content_frame, bg=self.default_bg)
        main_container.pack(fill='both', expand=True)

        # Scrollbereich
        canvas = tk.Canvas(main_container, bg=self.default_bg)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Frame im Canvas, das zentriert wird
        center_container = tk.Frame(canvas, bg=self.default_bg)
        center_container.pack(fill='both', expand=True)

        canvas_window = canvas.create_window((0, 0), window=center_container, anchor="n", width=canvas.winfo_width())

        # Callback zum dynamischen Anpassen
        def configure_canvas(event=None):
            """Passt Canvas und Textbreite dynamisch an."""
            # Berechne verfügbare Breite
            canvas_width = event.width if event else canvas.winfo_width()
            window_width = center_container.winfo_width()
            x_position = max((canvas_width - window_width) // 2, 0)
            
            # Update Canvas
            canvas.coords(canvas_window, x_position, 0)
            canvas.itemconfig(canvas_window, width=canvas_width)
            canvas.configure(scrollregion=canvas.bbox("all"))
            
            # Aggressivere Textbreiten-Begrenzung
            # Nutze 70% der verfügbaren Canvas-Breite, maximal aber 600px
            wrap_width = min(600, int(canvas_width * 0.7))
            
            try:
                question_label.configure(wraplength=wrap_width)
                answer_label.configure(wraplength=wrap_width)
            except:
                pass

        canvas.bind('<Configure>', configure_canvas)
        center_container.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))




        # Progress text
        total_cards = getattr(self, 'total_cards_in_session', len(self.session_results) + len(self.cards_to_learn))
        current_card_number = len(self.session_results) + 1
        progress_text = f"Karte {current_card_number} von {total_cards}"
        progress_label = tk.Label(
            center_container,
            text=progress_text,
            font=(self.appearance_settings.font_family, 14),
            bg=self.default_bg
        )
        progress_label.pack(pady=20)

        # Aktuelle Karte setzen
        self.current_card = self.cards_this_session.pop(0)
        
        if self.appearance_settings.track_learning_time:
            self.card_start_time = datetime.datetime.now()
            logging.info(f"Startzeit für Karte '{self.current_card.question}' gesetzt: {self.card_start_time}")
        else:
            self.card_start_time = None
            logging.info("Lernzeitmessung ist deaktiviert.")

        # Frage
        question_label = tk.Label(
            center_container,
            text=self.current_card.question,
            font=(self.appearance_settings.font_family, 24, "bold"),
            bg=self.default_bg,
            wraplength=600,
            justify="center"
        )
        question_label.pack(pady=(0, 30))

        # Antwortcontainer (initial versteckt)
        self.answer_container = tk.Frame(center_container, bg=self.default_bg)
        self.answer_container.pack(pady=(0, 20))
        self.answer_container.pack_forget()

        # Antworttext
        answer_label = tk.Label(
            self.answer_container,
            text=self.current_card.answer,
            font=(self.appearance_settings.font_family, 20),
            bg=self.default_bg,
            wraplength=600,
            justify="center"
        )
        answer_label.pack(pady=(0, 20))

        # Bild, falls vorhanden
        if self.current_card.image_path:
            try:
                # Frame für Bild und Button
                image_frame = tk.Frame(self.answer_container, bg=self.default_bg)
                image_frame.pack(pady=(0, 20))

                # Bild laden und anzeigen
                image = Image.open(self.current_card.image_path)
                max_width, max_height = 500, 300
                width, height = image.size
                scale = min(max_width / width, max_height / height)

                if scale < 1:
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    image = image.resize((new_width, new_height), Image.LANCZOS)

                photo = ImageTk.PhotoImage(image)
                image_label = tk.Label(
                    image_frame,
                    image=photo,
                    bg=self.default_bg,
                    cursor="hand2"  # Zeigt Hand-Cursor beim Überfahren
                )
                image_label.image = photo
                image_label.pack()
                canvas.after(100, configure_canvas)
                # Funktion für Vollbildanzeige
                def show_fullscreen():
                    fullscreen_window = tk.Toplevel(self.master)
                    fullscreen_window.title("Bildansicht")
                    fullscreen_window.state('zoomed')  # Maximiert das Fenster
                    fullscreen_window.configure(bg='black')  # Schwarzer Hintergrund

                    # SchlieÃƒÅ¸en-Hinweis
                    close_label = tk.Label(
                        fullscreen_window,
                        text="ESC oder Klick zum SchlieÃƒÅ¸en",
                        fg='white',
                        bg='black',
                        font=(self.appearance_settings.font_family, 10)
                    )
                    close_label.pack(pady=10)

                    # Canvas für das Bild
                    canvas = tk.Canvas(
                        fullscreen_window,
                        bg='black',
                        highlightthickness=0
                    )
                    canvas.pack(fill='both', expand=True)

                    def resize_image(event=None):
                        # FenstermaÃƒÅ¸e
                        win_width = canvas.winfo_width()
                        win_height = canvas.winfo_height() - 40  # Platz für close_label

                        if win_width <= 1 or win_height <= 1:  # Verhindere Division durch 0
                            return

                        # Original BildmaÃƒÅ¸e
                        img = Image.open(self.current_card.image_path)
                        img_width, img_height = img.size

                        # Skalierungsfaktor berechnen
                        scale = min(win_width/img_width, win_height/img_height)
                        
                        # Neue BildmaÃƒÅ¸e
                        new_width = int(img_width * scale)
                        new_height = int(img_height * scale)

                        # Bild resizen
                        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(resized)

                        # Altes Bild lÃƒÂ¶schen und neues zeichnen
                        canvas.delete('all')
                        
                        # Bild zentriert platzieren
                        x = (win_width - new_width) // 2
                        y = (win_height - new_height) // 2
                        canvas.create_image(x, y, image=photo, anchor='nw')
                        
                        # Reference speichern
                        canvas.image = photo

                    # Event Bindings
                    fullscreen_window.bind('<Configure>', resize_image)
                    fullscreen_window.bind('<Escape>', lambda e: fullscreen_window.destroy())
                    fullscreen_window.bind('<Button-1>', lambda e: fullscreen_window.destroy())

                    # Initiales Resize
                    fullscreen_window.update()
                    resize_image()

                # Button zum VergrÃƒÂ¶ÃƒÅ¸ern
                expand_button = ModernButton(
                    image_frame,
                    text="Ã°Å¸â€Â Bild vergrÃƒÂ¶ÃƒÅ¸ern",
                    command=show_fullscreen,
                    width=15,
                    style=ButtonStyle.SECONDARY.value
                )
                expand_button.pack(pady=5)

                # Bild auch klickbar machen
                image_label.bind('<Button-1>', lambda e: show_fullscreen())

            except Exception as e:
                logging.error(f"Fehler beim Laden des Bildes: {e}")

        # Toggle-Button zum Anzeigen der Antwort
        self.answer_visible = False
        self.toggle_btn = ModernButton(
            center_container,
            text="Antwort anzeigen",
            command=self.toggle_answer,
            width=20,
            style=ButtonStyle.PRIMARY.value
        )
        self.toggle_btn.pack(pady=(0, 20))

        # Bewertungsframe (initial versteckt)
        self.rating_frame = tk.Frame(center_container, bg=self.default_bg)
        self.setup_rating_widgets()
        self.rating_frame.pack_forget()

    def toggle_answer(self):
        """Schaltet die Anzeige der Antwort ein/aus."""
        if self.answer_visible:
            self.answer_container.pack_forget()
            self.rating_frame.pack_forget()
            self.toggle_btn.configure(text="Antwort anzeigen")
        else:
            self.answer_container.pack(fill='x', pady=(0, 20))
            self.rating_frame.pack(pady=(0, 20))
            self.toggle_btn.configure(text="Antwort verbergen")
        
        self.answer_visible = not self.answer_visible
        
        # Wenn die Antwort versteckt wird, verstecken wir auch die Bewertungsoptionen
        if not self.answer_visible:
            self.rating_frame.pack_forget()
    def setup_new_card_widgets(self):
        """Erstellt und initialisiert alle Widgets für eine neue Karte."""
        if not self.cards_this_session:
            self.show_session_summary()
            return

        self.current_card = self.cards_this_session.pop(0)

        # Tracking der aktuellen Widgets
        self.current_widgets = {}

        # Hauptframes erstellen
        self.current_widgets['question_frame'] = tk.Frame(self.content_frame, bg=self.appearance_settings.text_bg_color)
        self.current_widgets['question_frame'].pack(pady=20, padx=20, fill='x')

        self.current_widgets['answer_frame'] = tk.Frame(self.content_frame, bg=self.appearance_settings.text_bg_color)
        self.current_widgets['answer_frame'].pack(pady=20, padx=20, fill='x')

        self.current_widgets['rating_frame'] = tk.Frame(self.content_frame, bg=self.appearance_settings.text_bg_color)
        self.current_widgets['rating_frame'].pack(pady=20, padx=20)
        self.current_widgets['rating_frame'].pack_forget()

        # Startzeit
        if self.appearance_settings.track_learning_time:
            self.card_start_time = datetime.datetime.now()

        # Frage
        self.current_widgets['question_label'] = tk.Label(
            self.current_widgets['question_frame'],
            text=self.current_card.question,
            font=(self.appearance_settings.font_family, 24),
            bg=self.appearance_settings.text_bg_color,
            fg=self.appearance_settings.text_fg_color,
            wraplength=self.master.winfo_width() - 100
        )
        self.current_widgets['question_label'].pack()

        # Antwort
        self.current_widgets['answer_label'] = tk.Label(
            self.current_widgets['answer_frame'],
            text=self.current_card.answer,
            font=(self.appearance_settings.font_family, 20),
            bg=self.appearance_settings.text_bg_color,
            fg=self.appearance_settings.text_fg_color,
            wraplength=self.master.winfo_width() - 100
        )
        self.current_widgets['answer_label'].pack_forget()

        # Bild
        if self.current_card.image_path:
            try:
                image = Image.open(self.current_card.image_path)
                max_width, max_height = 500, 300
                width, height = image.size
                scale = min(max_width / width, max_height / height)

                if scale < 1:
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    image = image.resize((new_width, new_height), Image.LANCZOS)

                self.current_widgets['photo'] = ImageTk.PhotoImage(image)
                self.current_widgets['image_label'] = tk.Label(
                    self.current_widgets['answer_frame'],
                    image=self.current_widgets['photo'],
                    bg=self.appearance_settings.text_bg_color
                )
                self.current_widgets['image_label'].pack_forget()
            except Exception as e:
                logging.error(f"Fehler beim Laden des Bildes: {e}")

        # Antwort Button
        self.current_widgets['show_answer_btn'] = ModernButton(
            self.content_frame,
            text="Antwort anzeigen",
            command=self.reveal_answer,
            width=20,
            style=ButtonStyle.PRIMARY.value
        )
        self.current_widgets['show_answer_btn'].pack(pady=10)

        # Rating Frame Setup
        self.setup_rating_widgets()

    def setup_rating_widgets(self):
        """Erstellt die Bewertungswidgets."""
        # Schwierigkeitsgrad Label
        ttk.Label(
            self.rating_frame,
            text="Schwierigkeitsgrad:",
            font=(self.appearance_settings.font_family, 12)
        ).pack(pady=5)

        # Slider Container
        self.rating_var = tk.IntVar(value=3)
        slider_container = tk.Frame(self.rating_frame, bg="white")
        slider_container.pack(fill='x', padx=100)

        # Label für aktuellen Wert über dem Slider
        self.rating_label = tk.Label(  # Hier wurde die Änderung vorgenommen
            slider_container,
            text="3",
            font=(self.appearance_settings.font_family, 14, "bold"),
            bg="white"
        )
        self.rating_label.pack(pady=(0, 5)) 

        # Slider
        rating_scale = ttk.Scale(
            slider_container,
            from_=1,
            to=5,
            orient=tk.HORIZONTAL,
            variable=self.rating_var,
            command=self.update_rating_label,
            length=285
        )
        rating_scale.pack(pady=5)

        # Scale Labels Frame
        scale_labels_frame = tk.Frame(slider_container, bg="white")
        scale_labels_frame.pack(fill='x', pady=(0, 10))

        # Min/Max Labels
        ttk.Label(
            scale_labels_frame,
            text="1 = Sehr leicht",
            font=(self.appearance_settings.font_family, 10)
        ).pack(side=tk.LEFT)

        ttk.Label(
            scale_labels_frame,
            text="5 = Sehr schwer",
            font=(self.appearance_settings.font_family, 10)
        ).pack(side=tk.RIGHT)

        # Button Frame
        button_frame = tk.Frame(self.rating_frame, bg="white")
        button_frame.pack(pady=(20, 0), fill='x')

        # Richtig/Falsch Buttons
        incorrect_btn = ModernButton(
            button_frame,
            text="Ã¢Å“â€” Falsch",
            command=lambda: self.handle_answer(False),
            width=20,
            style=ButtonStyle.DANGER.value
        )
        incorrect_btn.pack(side=tk.LEFT, padx=(20, 10))

        correct_btn = ModernButton(
            button_frame,
            text="Ã¢Å“â€œ Richtig",
            command=lambda: self.handle_answer(True),
            width=20,
            style=ButtonStyle.PRIMARY.value
        )
        correct_btn.pack(side=tk.RIGHT, padx=(10, 20))

    def update_rating_label(self, val):
        """Aktualisiert das Label für die Schwierigkeitsanzeige"""
        try:
            # Konvertiere zu float und stelle sicher, dass der Wert korrekt gerundet wird
            float_val = float(val)
            # Runde auf die nÃƒÂ¤chste ganze Zahl
            rounded_value = int(float_val + 0.5)
            # Stelle sicher, dass der Wert im gÃƒÂ¼ltigen Bereich liegt
            rounded_value = max(1, min(5, rounded_value))
            
            # Aktualisiere sowohl Label als auch Variable
            self.rating_label.config(text=str(rounded_value))
            self.rating_var.set(rounded_value)
            
        except (ValueError, AttributeError) as e:
            logging.error(f"Fehler beim Aktualisieren des Rating Labels: {e}")
            # Setze Standardwert bei Fehler
            self.rating_label.config(text="3")
            self.rating_var.set(3)
    def _clear_content_frame(self):
        """Bereinigt alle Widgets und Referenzen."""
        try:
            if hasattr(self, 'current_widgets'):
                for widget in self.current_widgets.values():
                    if widget and isinstance(widget, (tk.Widget, ttk.Widget)):
                        widget.destroy()
                self.current_widgets.clear()
            
            if hasattr(self, 'content_frame'):
                for widget in self.content_frame.winfo_children():
                    widget.destroy()
        except Exception as e:
            logging.error(f"Fehler beim AufrÃƒÂ¤umen der Widgets: {e}")

    def reveal_answer(self):
        """Zeigt die Antwort und Bewertungsoptionen an."""
        try:
            if 'show_answer_btn' in self.current_widgets:
                self.current_widgets['show_answer_btn'].pack_forget()
            
            if 'answer_label' in self.current_widgets and self.current_card.answer.strip():
                self.current_widgets['answer_label'].pack()
            
            if 'image_label' in self.current_widgets:
                self.current_widgets['image_label'].pack(pady=10)
            
            if 'rating_frame' in self.current_widgets:
                self.current_widgets['rating_frame'].pack()
                
            if 'button_frame' in self.current_widgets:
                self.current_widgets['button_frame'].pack(pady=45, fill='x', padx=41)
        except Exception as e:
            logging.error(f"Fehler beim Aufdecken der Antwort: {e}")
    def handle_answer(self, is_correct: bool):
        """
        Verarbeitet die Richtig/Falsch Bewertung und die Schwierigkeitsbewertung.
        Aktualisiert die Kartenstatistiken und steuert den Session-Verlauf.
        """
        try:
            # Erfasse die Schwierigkeit vom Slider (1-5)
            difficulty = float(self.rating_var.get())
            
            # Berechne die Quality basierend auf Schwierigkeit und Korrektheit
            if is_correct:
                quality = int(6 - difficulty)
            else:
                quality = min(2, int((difficulty - 1) / 2))
                # Verarbeite falsche Antworten im Session-Kontext
                if hasattr(self, 'session_state'):
                    # Sicherheitscheck für Session-State-Keys
                    if 'incorrect_current' not in self.session_state:
                        self.session_state['incorrect_current'] = []
                    if 'incorrect_all' not in self.session_state:
                        self.session_state['incorrect_all'] = []
                    
                    # FÃƒÂ¼ge Karte zu den entsprechenden Listen hinzu
                    self.session_state['incorrect_current'].append(self.current_card)
                    if not self.session_state.get('is_repeating', False):
                        self.session_state['incorrect_all'].append(self.current_card)

            # Erfasse die Lernzeit
            learning_time = 0
            if self.appearance_settings.track_learning_time:
                if hasattr(self, 'card_start_time') and self.card_start_time:
                    learning_time_delta = datetime.datetime.now() - self.card_start_time
                    learning_time = round(learning_time_delta.total_seconds(), 2)
                    logging.info(f"Lernzeit für Karte '{self.current_card.question}': {learning_time} Sekunden")
                else:
                    logging.warning("Startzeit nicht gesetzt. Lernzeit wird auf 0 gesetzt.")
            
            # Update Kartenstatistiken
            if not hasattr(self.current_card, 'difficulty_history'):
                self.current_card.difficulty_history = []
            self.current_card.difficulty_history.append(difficulty)
            recent_difficulties = self.current_card.difficulty_history[-7:]  # Letzte 7 Bewertungen
            self.current_card.difficulty_rating = sum(recent_difficulties) / len(recent_difficulties)
            
            # Update SRS-Parameter und speichere
            self.data_manager.update_srs_sm2(self.current_card, quality)
            self.data_manager.save_flashcards()

            # Speichere Session-Ergebnis
            self.session_results.append((self.current_card, quality, learning_time, is_correct))
            
            # Bestimme nÃƒÂ¤chsten Schritt basierend auf Session-Status
            if not self.cards_this_session:
                if hasattr(self, 'session_state'):
                    if self.session_state.get('repeat_in_progress'):
                        self.show_session_summary()  # Ende der Wiederholung
                    elif not self.session_state.get('is_repeating'):
                        self.show_break_menu()      # Ende eines normalen Teils
                    else:
                        self.show_session_summary() # Ende einer Wiederholungssession
                else:
                    self.show_session_summary()     # Ende einer Standalone-Session
            else:
                self.show_card_window()            # Nächste Karte zeigen

        except Exception as e:
            logging.error(f"Fehler bei der Kartenverarbeitung: {e}")
            messagebox.showerror("Fehler", f"Fehler bei der Kartenverarbeitung: {e}")
            self.create_main_menu()


    def create_date_filter(self, filter_frame):
        """
        Erstellt ein modernes FiltermenÃƒÂ¼ für die Datumsauswahl und Statistik-Filterung.
        EnthÃƒÂ¤lt Diagrammtyp, Kategoriefilter und Zeitraumfilter mit dynamischer Datumsauswahl.
        """
        try:
            # 1. Hauptcontainer
            main_container = tk.Frame(filter_frame, bg="#2c3e50")
            main_container.pack(fill='both', expand=True, padx=10, pady=5)

            # 2. Header
            header_frame = tk.Frame(main_container, bg="#2c3e50")
            header_frame.pack(fill='x', pady=(0, 10))
            tk.Label(
                header_frame,
                text="Filter & Einstellungen",
                font=ctk.CTkFont(size=14, weight="bold"),
                bg="#2c3e50",
                fg="#ecf0f1"
            ).pack(side='left')

            # 3. Diagrammtyp-Bereich
            options_container = tk.Frame(main_container, bg="#2c3e50")
            options_container.pack(fill='x', pady=5)

            diagram_frame = tk.Frame(options_container, bg="#2c3e50")
            diagram_frame.pack(fill='x', pady=5)
            
            tk.Label(
                diagram_frame,
                text="Diagrammtyp:",
                font=ctk.CTkFont(size=10),
                bg="#2c3e50",
                fg="#ecf0f1"
            ).pack(side=tk.LEFT, padx=(0, 5))
            
            # Diagrammtyp-Auswahl
            self.chart_type_var = tk.StringVar(value="Gesamt")
            chart_types = [
                "Gesamt", "Richtig/Falsch", "Nach Kategorie", 
                "Kategorien (Kartenzahl)", "Kategorien (Richtig/Falsch)", 
                "Lernzeit", "Heatmap"
            ]
            
            chart_type_cbx = ModernCombobox(
                diagram_frame, 
                textvariable=self.chart_type_var,
                values=chart_types,
                state="readonly",
                width=25
            )
            chart_type_cbx.configure_style()
            chart_type_cbx.pack(side=tk.LEFT, fill='x', expand=True)

            # 4. Kategoriefilter-Bereich
            category_container = tk.Frame(main_container, bg="#2c3e50")
            category_container.pack(fill='x', pady=10)
            
            tk.Label(
                category_container,
                text="Kategoriefilter",
                font=ctk.CTkFont(size=12, weight="bold"),
                bg="#2c3e50",
                fg="#ecf0f1"
            ).pack(anchor='w')
            
            # Hauptkategorie
            cat_frame = tk.Frame(category_container, bg="#2c3e50")
            cat_frame.pack(fill='x', pady=5)
            
            tk.Label(
                cat_frame,
                text="Kategorie:",
                font=ctk.CTkFont(size=10),
                bg="#2c3e50",
                fg="#ecf0f1"
            ).pack(side=tk.LEFT, padx=(0, 5))
            
            self.selected_category_var = tk.StringVar(value="Alle")
            cat_list = ["Alle"] + sorted(self.data_manager.categories.keys())
            category_cbx = ModernCombobox(
                cat_frame,
                textvariable=self.selected_category_var,
                values=cat_list,
                state="readonly",
                width=25
            )
            category_cbx.configure_style()
            category_cbx.pack(side=tk.LEFT, fill='x', expand=True)

            # Vergleichskategorie
            comp_frame = tk.Frame(category_container, bg="#2c3e50")
            comp_frame.pack(fill='x', pady=5)
            
            tk.Label(
                comp_frame,
                text="Vergleich mit:",
                font=ctk.CTkFont(size=10),
                bg="#2c3e50",
                fg="#ecf0f1"
            ).pack(side=tk.LEFT, padx=(0, 5))
            
            cat_list_2 = ["Keine"] + sorted(self.data_manager.categories.keys())
            second_category_cbx = ModernCombobox(
                comp_frame,
                textvariable=self.second_category_var,
                values=cat_list_2,
                state="readonly",
                width=25
            )
            second_category_cbx.configure_style()
            second_category_cbx.pack(side=tk.LEFT, fill='x', expand=True)

            # 5. Zeitraumfilter-Bereich
            time_container = tk.Frame(main_container, bg="#2c3e50")
            time_container.pack(fill='x', pady=10)
            
            tk.Label(
                time_container,
                text="Zeitraumfilter",
                font=ctk.CTkFont(size=12, weight="bold"),
                bg="#2c3e50",
                fg="#ecf0f1"
            ).pack(anchor='w')
            
            time_frame = tk.Frame(time_container, bg="#2c3e50")
            time_frame.pack(fill='x', pady=5)
            
            tk.Label(
                time_frame,
                text="Ansicht:",
                font=ctk.CTkFont(size=10),
                bg="#2c3e50",
                fg="#ecf0f1"
            ).pack(side=tk.LEFT, padx=(0, 5))

            # Zeitraum-Auswahl        
            self.time_period_var = tk.StringVar(value="Gesamt")
            time_periods = ["Gesamt", "Tag", "Woche", "Monat", "Benutzerdefiniert"]
            time_period_cbx = ModernCombobox(
                time_frame,
                textvariable=self.time_period_var,
                values=time_periods,
                state="readonly",
                width=25,
                command=self._update_date_selection
            )
            time_period_cbx.configure_style()
            time_period_cbx.pack(side=tk.LEFT, fill='x', expand=True)

            # 6. Dynamischer Datumsauswahl-Frame
            self.date_selection_frame = tk.Frame(time_container, bg="#2c3e50")
            self.date_selection_frame.pack(fill='x', pady=5)
            
            # Datumsvariablen initialisieren
            self.date_var = tk.StringVar()
            self.start_date_var = tk.StringVar()
            self.end_date_var = tk.StringVar()

            # Event-Bindings für die Filter
            self.selected_category_var.trace_add('write', self.update_filter_status)
            self.chart_type_var.trace_add('write', self.update_filter_status)
            self.time_period_var.trace_add('write', self.update_filter_status)

            # Initial Update
            self._update_date_selection()
            
        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Datumsfilters: {e}")
            messagebox.showerror("Fehler", "Filter konnten nicht erstellt werden")

    def update_filter_status(self, *args):
        """Aktualisiert den Status der Filter und ermöglicht/deaktiviert entsprechende Optionen."""
        try:
            selected_period = self.time_period_var.get()
            selected_category = self.selected_category_var.get()
            
            # Aktiviere/Deaktiviere Vergleichskategorie basierend auf Hauptkategorie
            if selected_category == "Alle":
                self.second_category_var.set("Keine")
                # Deaktiviere Vergleichskategorie
                for child in self.second_category_frame.winfo_children():
                    if isinstance(child, (ttk.Combobox, ModernCombobox)):
                        child.configure(state="disabled")
            else:
                # Aktiviere Vergleichskategorie
                for child in self.second_category_frame.winfo_children():
                    if isinstance(child, (ttk.Combobox, ModernCombobox)):
                        child.configure(state="readonly")
            
            # Update Datumsauswahl wenn nötig
            if selected_period in ["Tag", "Woche", "Monat", "Benutzerdefiniert"]:
                self._update_date_selection()
                
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren des Filter-Status: {e}")

        def update_date_widgets(*args):
            """Aktualisiert die Datumsauswahlwidgets basierend auf dem gewÃƒÂ¤hlten Zeitraum."""
            # Entferne alte Widgets
            for widget in self.date_selection_frame.winfo_children():
                widget.destroy()

            period = self.time_period_var.get()
            
            if period in ["Tag", "Woche", "Monat"]:
                # Einzelnes Datum für Tag/Woche/Monat
                date_frame = tk.Frame(self.date_selection_frame, bg="#2c3e50")
                date_frame.pack(fill='x', pady=2)
                tk.Label(
                    date_frame,
                    text="Datum:",
                    font=("Segoe UI", 10),
                    bg="#2c3e50",
                    fg="#ecf0f1"
                ).pack(side=tk.LEFT, padx=(0, 5))
                
                date_entry = ttk.Entry(
                    date_frame,
                    textvariable=self.date_var,
                    width=12,
                    state='readonly'
                )
                date_entry.pack(side=tk.LEFT, padx=(0, 5))
                
                ModernButton(
                    date_frame,
                    text="Datum wÃƒÂ¤hlen",
                    command=lambda: self._pick_calendar_date(self.date_var),
                    style="Secondary.TButton",
                    width=15
                ).pack(side=tk.LEFT)
                
            elif period == "Benutzerdefiniert":
                # Start-Datum
                start_frame = tk.Frame(self.date_selection_frame, bg="#2c3e50")
                start_frame.pack(fill='x', pady=2)
                tk.Label(
                    start_frame,
                    text="Von:",
                    font=("Segoe UI", 10),
                    bg="#2c3e50",
                    fg="#ecf0f1"
                ).pack(side=tk.LEFT, padx=(0, 5))
                
                ttk.Entry(
                    start_frame,
                    textvariable=self.start_date_var,
                    width=12,
                    state='readonly'
                ).pack(side=tk.LEFT, padx=(0, 5))
                
                ModernButton(
                    start_frame,
                    text="Datum wÃƒÂ¤hlen",
                    command=lambda: self._pick_calendar_date(self.start_date_var),
                    style="Secondary.TButton",
                    width=15
                ).pack(side=tk.LEFT)

                # End-Datum
                end_frame = tk.Frame(self.date_selection_frame, bg="#2c3e50")
                end_frame.pack(fill='x', pady=2)
                tk.Label(
                    end_frame,
                    text="Bis:",
                    font=("Segoe UI", 10),
                    bg="#2c3e50",
                    fg="#ecf0f1"
                ).pack(side=tk.LEFT, padx=(0, 5))
                
                ttk.Entry(
                    end_frame,
                    textvariable=self.end_date_var,
                    width=12,
                    state='readonly'
                ).pack(side=tk.LEFT, padx=(0, 5))
                
                ModernButton(
                    end_frame,
                    text="Datum wÃƒÂ¤hlen",
                    command=lambda: self._pick_calendar_date(self.end_date_var),
                    style="Secondary.TButton",
                    width=15
                ).pack(side=tk.LEFT)

        # Registriere den Callback für Änderungen am Zeitraum
        self.time_period_var.trace_add('w', update_date_widgets)

        # Button-Frame
        button_frame = tk.Frame(main_container, bg="#2c3e50")
        button_frame.pack(fill='x', pady=10)

        # Filter anwenden Button
        ModernButton(
            button_frame,
            text="Filter anwenden",
            command=self.update_progress_stats,
            style="Primary.TButton",
            width=20
        ).pack(side=tk.RIGHT)

        # Initialisiere die Datumsauswahl
        update_date_widgets()

    def show_session_summary(self):
        """Zeigt eine übersichtliche Zusammenfassung der Lernsession."""
        self._clear_content_frame()

        # Sammle alle Ergebnisse der Session (inkl. Wiederholungen)
        all_results = []
        
        # FÃƒÂ¼ge Ergebnisse aus der Hauptsession und allen Teilen hinzu
        if hasattr(self, 'session_state'):
            # Hauptsession-Ergebnisse
            all_results.extend(self.session_state.get('session_results', []))
            
            # Aktuelle Ergebnisse (falls vorhanden)
            if self.session_results:
                all_results.extend(self.session_results)
                
            # Wiederholungs-Ergebnisse
            all_results.extend(self.session_state.get('repeat_results', []))
        else:
            all_results = self.session_results

        # Berechne die Gesamtstatistiken
        correct_count = sum(1 for _, _, _, is_correct in all_results if is_correct)
        total = len(all_results)
        
        # Sammle die nicht gekonnten Karten
        incorrect_cards = [card for card, _, _, is_correct in all_results if not is_correct]

        # Berechne die Gesamtzeit
        session_time_minutes = 0
        if self.appearance_settings.track_learning_time:
            total_card_time = sum(lt for _, _, lt, _ in all_results)
            session_time_minutes = round(total_card_time / 60.0, 2)
            logging.info(f"Gesamtdauer der Sitzung: {session_time_minutes:.2f} Minuten")

        # Header
        summary_header = tk.Label(
            self.content_frame,
            text="Sitzung beendet!",
            font=(self.appearance_settings.font_family, 24),
            bg=self.appearance_settings.text_bg_color,
            fg=self.appearance_settings.text_fg_color
        )
        summary_header.pack(pady=20)

        # Zusammenfassung der Statistiken
        stats_text = f"Richtig: {correct_count}/{total}\n"
        stats_text += f"Gesamte Lernzeit: {session_time_minutes:.2f} Minuten"
        
        if hasattr(self, 'session_state'):
            stats_text += f"\nAbgeschlossene Teile: {self.session_state['current_part']}/{self.session_state['total_parts']}"
            
        summary_stats = tk.Label(
            self.content_frame,
            text=stats_text,
            font=(self.appearance_settings.font_family, 18),
            bg=self.appearance_settings.text_bg_color,
            fg=self.appearance_settings.text_fg_color
        )
        summary_stats.pack(pady=10)

        # Detaillierte Anzeige der Kartenbewertungen
        summary_frame = ttk.Frame(self.content_frame)
        summary_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(summary_frame, bg='white')
        scrollbar = ttk.Scrollbar(summary_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Zeige alle Karten mit Status an
        for idx, (card, quality, lt, is_correct) in enumerate(all_results, 1):
            status = "Ã¢Å“â€Ã¯Â¸Â" if is_correct else "Ã¢ÂÅ’"
            card_text = f"{idx}. {card.question} - {status}"
            
            # ZusÃƒÂ¤tzliche Informationen
            if self.appearance_settings.track_learning_time:
                card_text += f" - Lernzeit: {lt:.2f} Sek"
            card_text += f" - KomplexitÃƒÂ¤t: {card.difficulty_rating:.1f}/5.0"
            
            # Zeige an, ob es eine Wiederholung war
            if hasattr(self, 'session_state') and self.session_state.get('is_repeating'):
                if card in self.session_state.get('incorrect_all', []):
                    card_text += " (Wiederholung)"
            
            ttk.Label(
                scrollable_frame,
                text=card_text,
                font=(self.appearance_settings.font_family, 12),
                background='white'
            ).pack(anchor='w')

        # Button Frame für Navigation
        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(pady=20)

        # Buttons basierend auf Session-Status
        if hasattr(self, 'session_state'):
            # Wenn wir in einer geteilten Session sind
            if self.session_state['current_part'] < self.session_state['total_parts']:
                # Noch nicht alle Teile abgeschlossen
                ModernButton(
                    button_frame,
                    text="Weiter zum nÃƒÂ¤chsten Teil",
                    command=self.continue_session,
                    width=20,
                    style=ButtonStyle.PRIMARY.value
                ).pack(side='left', padx=5)
            elif incorrect_cards:
                # Alle Teile abgeschlossen, aber es gibt nicht gekonnte Karten
                ModernButton(
                    button_frame,
                    text=f"Nicht gekonnte Karten wiederholen ({len(incorrect_cards)})",
                    command=lambda: self.start_repeat_session(incorrect_cards),
                    width=30,
                    style=ButtonStyle.PRIMARY.value
                ).pack(side='left', padx=5)
        elif incorrect_cards:
            # Normale Session (nicht geteilt) mit nicht gekonnten Karten
            ModernButton(
                button_frame,
                text=f"Nicht gekonnte Karten wiederholen ({len(incorrect_cards)})",
                command=lambda: self.start_repeat_session(incorrect_cards),
                width=30,
                style=ButtonStyle.PRIMARY.value
            ).pack(side='left', padx=5)

        # Standard-Buttons
        ModernButton(
            button_frame,
            text="Neue Lernsession",
            command=self.select_cards_submenu,
            width=20,
            style=ButtonStyle.PRIMARY.value
        ).pack(side='left', padx=5)

        ModernButton(
            button_frame,
            text="Zurück zum Hauptmenü",
            command=lambda: self.navigate_to('main'),
            width=20,
            style=ButtonStyle.SECONDARY.value
        ).pack(side='left', padx=5)

        # Sitzungsstatistik vorbereiten und speichern
        session_stat = {
            "date": datetime.datetime.now().strftime("%d.%m.%Y"),
            "time": datetime.datetime.now().strftime("%H:%M"),
            "cards_total": total,
            "cards_correct": correct_count,
            "total_time": session_time_minutes,
            "avg_time_per_card": session_time_minutes / total if total > 0 else 0,
            "success_rate": (correct_count / total * 100) if total > 0 else 0,
            "is_split_session": hasattr(self, 'session_state'),
            "total_parts": self.session_state['total_parts'] if hasattr(self, 'session_state') else 1,
            "details": []
        }

        # Details für jede Karte
        for card, quality, lt, is_correct in all_results:
            card_detail = {
                "question": card.question,
                "category": card.category,
                "subcategory": card.subcategory,
                "correct": is_correct,
                "learning_time": lt,
                "quality": quality,
                "difficulty": card.difficulty_rating,
                "tags": card.tags,
                "is_repeat": card in (self.session_state.get('incorrect_all', []) if hasattr(self, 'session_state') else [])
            }
            session_stat["details"].append(card_detail)

        try:
            self.stats_manager.add_session_summary(session_stat)
            logging.info("Sitzungsstatistik gespeichert")
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Sitzungsstatistik: {e}")
            messagebox.showerror("Fehler", f"Beim Speichern der Sitzungsstatistik ist ein Fehler aufgetreten:\n{e}")

        # Session zurücksetzen, aber nur wenn wir komplett fertig sind
        if not hasattr(self, 'session_state') or self.session_state['current_part'] >= self.session_state['total_parts']:
            self.session_results.clear()
            if hasattr(self, 'session_state'):
                self.session_state.clear()

    def start_repeat_session(self, cards_to_repeat):
        """Startet eine Wiederholungssession mit nicht gekonnten Karten."""
        # Sichere bisherige Ergebnisse in der session_state
        if hasattr(self, 'session_state'):
            # Speichere die ursprünglichen Session-Parameter
            original_total_parts = self.session_state.get('total_parts', 1)
            original_current_part = self.session_state.get('current_part', 1)

            if self.session_results:
                # FÃƒÂ¼ge aktuelle Ergebnisse zu den bestehenden hinzu
                self.session_state['session_results'].extend(self.session_results)
                self.session_results = []  # Liste für neue Ergebnisse leeren

            # Aktualisiere session_state für die Wiederholung, behalte aber wichtige Parameter
            self.session_state.update({
                'incorrect_current': [],     # Für neue nicht-gekannte Karten
                'is_repeating': True,        # Markiere als Wiederholung
                'repeat_in_progress': True,  # Markiere laufende Wiederholung
                'current_part': original_current_part,  # Behalte den ursprünglichen Wert
                'total_parts': original_total_parts     # Behalte den ursprünglichen Wert
            })
        else:
            # Erstelle session_state für finale Wiederholungen
            self.session_state = {
                'session_results': self.session_results.copy(),  # Sichere bisherige Ergebnisse
                'incorrect_current': [],     # Für neue nicht-gekannte Karten
                'incorrect_all': [],         # Für alle nicht-gekannte Karten
                'is_repeating': True,        # Markiere als Wiederholung
                'repeat_in_progress': True,  # Markiere laufende Wiederholung
                'repeat_results': [],        # Für Wiederholungsergebnisse
                'current_part': 1,           # Für neue Sessions
                'total_parts': 1             # Für neue Sessions
            }
            self.session_results = []  # Liste für neue Ergebnisse leeren
            
        # Setze die zu wiederholenden Karten
        self.cards_this_session = cards_to_repeat.copy()
            
        # Zeitmessung weiterfÃƒÂ¼hren falls aktiviert
        if self.appearance_settings.track_learning_time and not hasattr(self, 'session_start_time'):
            self.session_start_time = datetime.datetime.now()

        self.show_card_window()
    def calculate_learning_time(self):
        """
        Berechnet die Lernzeit für eine Karte.
        Verwendet die gespeicherte Startzeit und die aktuelle Zeit.
        
        Returns:
            int: Lernzeit in Minuten.
        """
        if self.appearance_settings.track_learning_time and hasattr(self, 'card_start_time') and self.card_start_time:
            learning_time_delta = datetime.datetime.now() - self.card_start_time
            learning_time = int(learning_time_delta.total_seconds() // 60)  # Ganze Minuten
            return learning_time
        return 0


    # -----------------------------------------------------------------------------------
    # EINSTELLUNGEN (Session Limit, Appearance, Font, BG, etc.)
    # -----------------------------------------------------------------------------------
    def set_session_limit_interface(self):
        self._clear_content_frame()
        header_frame = tk.Frame(self.content_frame, bg=self.appearance_settings.text_bg_color)
        header_frame.pack(fill='x', pady=(30, 20))
        tk.Label(
            header_frame,
            text="Sitzungseinstellungen",
            font=(self.appearance_settings.font_family, 16, "bold"),
            bg=self.appearance_settings.text_bg_color,
            fg=self.appearance_settings.text_fg_color
        ).pack()

        main_frame = ttk.Frame(self.content_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(
            main_frame,
            text="SitzungslÃƒÂ¤nge (Anzahl Karten):",
            font=(self.appearance_settings.font_family, 12)
        ).pack(pady=10)

        session_entry = tk.Entry(main_frame, width=10)
        session_entry.insert(0, str(self.session_limit))
        session_entry.pack(pady=5)

        def apply_session_limit():
            try:
                val = int(session_entry.get().strip())
                if val > 0 and val <= MAX_SESSION_LIMIT:  # Definieren Sie MAX_SESSION_LIMIT entsprechend
                    self.session_limit = val
                    messagebox.showinfo("Info", f"SitzungslÃƒÂ¤nge auf {val} Karten gesetzt.")
                    self.navigate_to('main')  # Verwenden Sie navigate_to für Konsistenz
                else:
                    messagebox.showwarning("Warnung", f"Wert muss zwischen 1 und {MAX_SESSION_LIMIT} liegen.")
            except ValueError:
                messagebox.showwarning("Warnung", "Bitte eine gÃƒÂ¼ltige Zahl eingeben.")

        save_btn = ModernButton(
            main_frame,
            text="ÃƒÅ“bernehmen",
            command=apply_session_limit,
            width=15,
            style=ButtonStyle.PRIMARY.value
        )
        save_btn.pack(pady=10)

        # Zurück-Button
        back_btn = ModernButton(
            main_frame,
            text="Zurück zum Hauptmenü",
            command=self.navigate_back,  # Verwenden Sie navigate_back statt create_main_menu
            width=15,
            style=ButtonStyle.SECONDARY.value
        )
        back_btn.pack(pady=10)
        self.sidebar_buttons["back_to_session_limit"] = back_btn


    def configure_font(self):
        """Moderne Schrifteinstellungsseite mit customtkinter Design."""
        self._clear_content_frame()

        # Moderner Header mit Gradient-Hintergrund
        header_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='#f59e0b',
            corner_radius=0,
            height=110
        )
        header_container.pack(fill='x', pady=(0, 20))
        header_container.pack_propagate(False)

        header_content = ctk.CTkFrame(header_container, fg_color='transparent')
        header_content.place(relx=0.5, rely=0.5, anchor='center')

        # Icon und Titel
        icon_title_frame = ctk.CTkFrame(header_content, fg_color='transparent')
        icon_title_frame.pack()

        ctk.CTkLabel(
            icon_title_frame,
            text="🔤",
            font=ctk.CTkFont(size=36),
            text_color='#ffffff'
        ).pack(side='left', padx=(0, 15))

        title_frame = ctk.CTkFrame(icon_title_frame, fg_color='transparent')
        title_frame.pack(side='left')

        ctk.CTkLabel(
            title_frame,
            text="Schrifteinstellungen",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color='#ffffff'
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_frame,
            text="Passe Schriftart und -größe für die gesamte Anwendung an",
            font=ctk.CTkFont(size=13),
            text_color='#fef3c7'
        ).pack(anchor='w')

        # Hauptcontainer für Schrifteinstellungen
        main_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color='#fef3c7',
            corner_radius=15,
            border_width=2,
            border_color='#f59e0b'
        )
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Innerer Container mit weißem Hintergrund
        inner_frame = ctk.CTkFrame(
            main_frame,
            fg_color='white',
            corner_radius=10
        )
        inner_frame.pack(fill='both', expand=True, padx=15, pady=15)

        # Schrifteinstellungen mit modernem Design

        # Aktuelle Einstellungen
        current_settings_frame = ctk.CTkFrame(inner_frame, fg_color='#f9fafb', corner_radius=10)
        current_settings_frame.pack(fill='x', padx=15, pady=(15, 20))

        ctk.CTkLabel(
            current_settings_frame,
            text="📋 Aktuelle Einstellungen",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color='#1f2937'
        ).pack(pady=(10, 5))

        current_info = ctk.CTkLabel(
            current_settings_frame,
            text=f"Schriftart: {self.appearance_settings.font_family}  |  Größe: {self.appearance_settings.font_size}",
            font=ctk.CTkFont(size=14),
            text_color='#6b7280'
        )
        current_info.pack(pady=(0, 10))

        # Schriftart auswählen
        font_family_frame = ctk.CTkFrame(inner_frame, fg_color='transparent')
        font_family_frame.pack(fill='x', padx=15, pady=10)

        ctk.CTkLabel(
            font_family_frame,
            text="🖋️ Schriftart auswählen:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color='#1f2937',
            anchor='w'
        ).pack(anchor='w', pady=(0, 5))

        font_families = sorted(tkfont.families())
        self.selected_font = tk.StringVar(value=self.appearance_settings.font_family)

        font_dropdown = ctk.CTkComboBox(
            font_family_frame,
            variable=self.selected_font,
            values=font_families,
            state="readonly",
            width=400,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12),
            button_color='#f59e0b',
            button_hover_color='#d97706',
            border_color='#f59e0b'
        )
        font_dropdown.pack(fill='x', pady=(0, 5))

        ctk.CTkLabel(
            font_family_frame,
            text="Wähle eine Schriftart aus der Liste der verfügbaren System-Schriftarten",
            font=ctk.CTkFont(size=11),
            text_color='#9ca3af'
        ).pack(anchor='w')

        # Schriftgröße auswählen
        font_size_frame = ctk.CTkFrame(inner_frame, fg_color='transparent')
        font_size_frame.pack(fill='x', padx=15, pady=10)

        ctk.CTkLabel(
            font_size_frame,
            text="📏 Schriftgröße auswählen:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color='#1f2937',
            anchor='w'
        ).pack(anchor='w', pady=(0, 5))

        size_control_frame = ctk.CTkFrame(font_size_frame, fg_color='transparent')
        size_control_frame.pack(fill='x', pady=(0, 5))

        self.selected_font_size = tk.IntVar(value=self.appearance_settings.font_size)

        # Slider für Schriftgröße
        size_slider = ctk.CTkSlider(
            size_control_frame,
            from_=8,
            to=72,
            number_of_steps=64,
            variable=self.selected_font_size,
            width=300,
            button_color='#f59e0b',
            button_hover_color='#d97706',
            progress_color='#f59e0b'
        )
        size_slider.pack(side='left', fill='x', expand=True, padx=(0, 15))

        # Anzeige der aktuellen Größe
        size_display = ctk.CTkLabel(
            size_control_frame,
            text=f"{self.selected_font_size.get()}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color='#f59e0b',
            width=60
        )
        size_display.pack(side='left')

        # Update Funktion für die Anzeige
        def update_size_display(*args):
            size_display.configure(text=f"{self.selected_font_size.get()}")

        self.selected_font_size.trace('w', update_size_display)

        ctk.CTkLabel(
            font_size_frame,
            text="Wähle eine Größe zwischen 8 und 72 Punkten",
            font=ctk.CTkFont(size=11),
            text_color='#9ca3af'
        ).pack(anchor='w')

        # Vorschau
        preview_frame = ctk.CTkFrame(inner_frame, fg_color='#f9fafb', corner_radius=10)
        preview_frame.pack(fill='x', padx=15, pady=(20, 15))

        ctk.CTkLabel(
            preview_frame,
            text="👁️ Vorschau",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color='#1f2937'
        ).pack(pady=(10, 5))

        preview_text = ctk.CTkLabel(
            preview_frame,
            text="Die schnelle braune Fuchs springt über den faulen Hund",
            font=ctk.CTkFont(family=self.selected_font.get(), size=self.selected_font_size.get()),
            text_color='#1f2937',
            wraplength=500
        )
        preview_text.pack(pady=(5, 15), padx=15)

        # Vorschau aktualisieren
        def update_preview(*args):
            try:
                preview_text.configure(
                    font=ctk.CTkFont(
                        family=self.selected_font.get(),
                        size=self.selected_font_size.get()
                    )
                )
            except:
                pass

        self.selected_font.trace('w', update_preview)
        self.selected_font_size.trace('w', update_preview)

        # Übernehmen Button
        def apply_font_changes():
            font_family = self.selected_font.get()
            try:
                font_size = int(self.selected_font_size.get())
                if 8 <= font_size <= 72:
                    self.appearance_settings.font_family = font_family
                    self.appearance_settings.font_size = font_size
                    self.configure_styles()
                    self.apply_appearance_settings()
                    current_info.configure(text=f"Schriftart: {font_family}  |  Größe: {font_size}")
                    messagebox.showinfo("Erfolg", f"Schriftart auf '{font_family}' und Größe {font_size} gesetzt.")
                else:
                    messagebox.showwarning("Warnung", "Schriftgröße muss zwischen 8 und 72 liegen.")
            except ValueError:
                messagebox.showwarning("Warnung", "Bitte eine gültige Schriftgröße eingeben.")

        # Buttons
        button_frame = ctk.CTkFrame(inner_frame, fg_color='transparent')
        button_frame.pack(fill='x', padx=15, pady=20)

        ctk.CTkButton(
            button_frame,
            text="✓ Änderungen übernehmen",
            command=apply_font_changes,
            width=200,
            height=40,
            corner_radius=10,
            fg_color='#f59e0b',
            hover_color='#d97706',
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side='left', padx=5)

        back_btn = ctk.CTkButton(
            button_frame,
            text="← Zurück zu Einstellungen",
            command=self.configure_appearance,
            width=200,
            height=40,
            corner_radius=10,
            fg_color='#6b7280',
            hover_color='#4b5563',
            font=ctk.CTkFont(size=14, weight="bold")
        )
        back_btn.pack(side='left', padx=5)
        self.sidebar_buttons["back_to_main_from_font"] = back_btn

        logging.info("Schrifteinstellungen angezeigt.")

    # -----------------------------------------------------------------------------------
    # BACKGROUND IMAGES & COLORS
    # -----------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------
# BACKGROUND IMAGES & COLORS
# -----------------------------------------------------------------------------------
    def choose_bg_color(self):
        color_code = colorchooser.askcolor(title="Hintergrundfarbe auswÃƒÂ¤hlen")
        if color_code and color_code[1]:
            self.set_bg_color(color_code[1])

    def set_bg_color(self, color):
        # Entfernen Sie eventuell gesetzte Hintergrundbilder
        self.reset_bg_image()

        self.master.configure(bg=color)
        self.default_bg = color
        self.content_frame.configure(bg=color)
        logging.info(f"Hintergrundfarbe auf {color} gesetzt.")
        self.apply_appearance_settings()

    def choose_bg_image(self):
        file_path = filedialog.askopenfilename(
            title="Hintergrundbild auswÃƒÂ¤hlen",
            filetypes=[
                ("Bilder", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("Alle Dateien", "*.*")
            ]
        )
        if file_path:
            self.set_bg_image(file_path)

    def set_bg_image(self, image_path):
        try:
            image = Image.open(image_path)
            
            # Optional: Validierung der BildgrÃƒÂ¶ÃƒÅ¸e
            max_size = (1920, 1080)  # Beispielhafte maximale GrÃƒÂ¶ÃƒÅ¸e
            image.thumbnail(max_size, Image.ANTIALIAS)
            
            self.current_bg_image = image
            self.update_bg_image()

            if not hasattr(self, 'bg_canvas') or self.bg_canvas is None:
                self.bg_canvas = tk.Canvas(self.master, highlightthickness=0)
                self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

            self.content_frame.lift()
            self.master.bind("<Configure>", self.resize_bg_image)
            logging.info(f"Hintergrundbild erfolgreich gesetzt: {image_path}")
        except Exception as e:
            logging.error(f"Fehler beim Laden des Hintergrundbildes: {e}")
            messagebox.showerror("Fehler", f"Bild konnte nicht geladen werden: {e}")

    def update_bg_image(self):
        if self.current_bg_image:
            try:
                img = self.current_bg_image.resize(
                    (self.master.winfo_width(), self.master.winfo_height()),
                    Image.ANTIALIAS
                )
                self.bg_photo_image = ImageTk.PhotoImage(img)
                self.bg_canvas.create_image(0, 0, image=self.bg_photo_image, anchor="nw")
            except Exception as e:
                logging.error(f"Fehler beim Aktualisieren des Hintergrundbildes: {e}")

    def resize_bg_image(self, event=None):
        if self.current_bg_image and event is not None:
            try:
                img = self.current_bg_image.resize((event.width, event.height), Image.ANTIALIAS)
                self.bg_photo_image = ImageTk.PhotoImage(img)
                self.bg_canvas.create_image(0, 0, image=self.bg_photo_image, anchor="nw")
                logging.info("Hintergrundbild erfolgreich angepasst.")
            except Exception as e:
                logging.error(f"Fehler beim Anpassen des Hintergrundbildes: {e}")

    def reset_bg_image(self):
        """Entfernt das gesetzte Hintergrundbild."""
        if hasattr(self, 'bg_canvas') and self.bg_canvas:
            self.bg_canvas.delete("all")
            self.bg_canvas.destroy()
            self.bg_canvas = None
        self.current_bg_image = None
        self.bg_photo_image = None

    def reset_bg(self):
        """Setzt den Hintergrund auf die Standardfarbe zurück und entfernt Bilder."""
        self.reset_bg_image()
        self.default_bg = DEFAULT_BG_COLOR  # Stellen Sie sicher, dass DEFAULT_BG_COLOR definiert ist
        self.master.configure(bg=self.default_bg)
        self.content_frame.configure(bg=self.default_bg)
        self.apply_appearance_settings()
        logging.info("Hintergrund zurückgesetzt.")

    # -----------------------------------------------------------------------------------
    # TASTATUR & EVENT STEUERUNG
    # -----------------------------------------------------------------------------------
    def setup_keyboard_shortcuts(self):
        """Richtet TastaturkÃƒÂ¼rzel für verschiedene Aktionen ein."""
        self.master.bind('<Escape>', lambda e: self.toggle_fullscreen())
        self.master.bind('<F5>', lambda e: self.reset_bg())
        self.master.bind('<Control-s>', lambda e: self.save_current_state())
        self.master.bind('<Control-q>', lambda e: self.confirm_quit())

    def toggle_fullscreen(self):
        """Schaltet den Vollbildmodus um."""
        self.fullscreen = not self.fullscreen
        self.master.attributes("-fullscreen", self.fullscreen)
        logging.info(f"Vollbildmodus {'aktiviert' if self.fullscreen else 'deaktiviert'}.")
        # Optional: Fügen Sie eine Statusmeldung hinzu
        status = "Vollbildmodus aktiviert." if self.fullscreen else "Vollbildmodus deaktiviert."
        messagebox.showinfo("Vollbildmodus", status)

    def save_current_state(self, event=None):
        """Speichert den aktuellen Zustand der Anwendung."""
        try:
            self.data_manager.save_categories()
            self.data_manager.save_flashcards()
            self.data_manager.save_stats()
            logging.info("Aktueller Zustand erfolgreich gespeichert.")
            messagebox.showinfo("Erfolg", "Aktueller Zustand erfolgreich gespeichert.")
        except Exception as e:
            logging.error(f"Fehler beim Speichern des aktuellen Zustands: {e}")
            messagebox.showerror(
                "Fehler",
                "Beim Speichern des aktuellen Zustands ist ein Fehler aufgetreten."
            )

    def confirm_quit(self, event=None):
        """BestÃƒÂ¤tigt das Beenden der Anwendung und speichert alle Daten."""
        if messagebox.askyesno("Beenden", "MÃƒÂ¶chten Sie die Anwendung wirklich beenden?"):
            try:
                # Explizit den Leitner-Status speichern
                if hasattr(self, 'leitner_system'):
                    logging.info("Speichere Leitner-System vor Beenden...")
                    self.leitner_system.save_cards()
                    logging.info("Leitner-System gespeichert")
                
                # Dann weitere Daten speichern
                self.save_current_state()
                
                logging.info("Anwendung wird beendet.")
                self.master.quit()
            except Exception as e:
                logging.error(f"Fehler beim Beenden der Anwendung: {e}")
                import traceback
                logging.error(traceback.format_exc())
                
                # Trotz Fehler versuchen zu beenden
                self.master.quit()

    # -----------------------------------------------------------------------------------
    # IMPORT / EXPORT FLASHCARDS
    # -----------------------------------------------------------------------------------
    def export_flashcards(self):
        """Exportiert Flashcards in eine CSV-Datei."""
        file_path = filedialog.asksaveasfilename(
            title="Flashcards exportieren",
            defaultextension=".csv",
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")]
        )
        if not file_path:
            return  # Abbrechen

        try:
            success = self.data_manager.export_flashcards_to_csv(file_path)
            if success:
                messagebox.showinfo("Erfolg", f"Flashcards wurden erfolgreich nach\n{file_path}\nexportiert.")
                self.backup_flashcards("export")
                logging.info(f"Flashcards erfolgreich exportiert nach {file_path}.")
            else:
                messagebox.showerror("Fehler", "Fehler beim Exportieren der Flashcards.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Export: {e}")
            logging.error(f"Fehler beim Exportieren der Flashcards: {e}")

    def import_flashcards(self):
            """Importiert Flashcards aus einer CSV-Datei."""
            file_path = filedialog.askopenfilename(
                title="Flashcards importieren",
                filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")]
            )
            if not file_path:
                return  # Abbrechen

            try:
                # Verwende die Methode aus dem DataManager
                imported_cards = self.data_manager.import_flashcards_from_csv(file_path)

                if imported_cards:
                    # *** NEU: Leitner-System synchronisieren ***
                    if hasattr(self, 'leitner_system'):
                        try:
                            self.leitner_system.reload_cards() # Reload nach Import
                            logging.info("Leitner-System nach Kartenimport aktualisiert.")
                        except Exception as reload_error:
                            logging.warning(f"Leitner-System Reload fehlgeschlagen: {reload_error}")

                    messagebox.showinfo("Erfolg", f"{len(imported_cards)} Flashcards wurden erfolgreich importiert.")
                    self.backup_flashcards("import") # Backup nach erfolgreichem Import
                    logging.info(f"{len(imported_cards)} Flashcards erfolgreich importiert von {file_path}.")
                    # Optional: Aktualisiere die aktuelle Ansicht, falls nötig
                    # self.create_main_menu() oder self.show_card_details_manager()
                else:
                    messagebox.showinfo("Info", "Keine neuen Karten importiert (möglicherweise bereits vorhanden oder Datei fehlerhaft).")

            except FileNotFoundError:
                messagebox.showerror("Fehler", f"Datei nicht gefunden: {file_path}")
                logging.error(f"Importdatei nicht gefunden: {file_path}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Import: {e}")
                logging.error(f"Fehler beim Importieren der Flashcards: {e}")

    # -----------------------------------------------------------------------------------
    # BACKUP SYSTEME
    # -----------------------------------------------------------------------------------
    def backup_flashcards(self, reason="update"):
        """Erstellt ein Backup der Flashcards."""
        timestamp = datetime.datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
        backup_filename = f"flashcards_backup_{reason}_{timestamp}.json"
        backup_path = os.path.join(self.flashcards_backup_dir, backup_filename)
        
        # Sicherstellen, dass das Backup-Verzeichnis existiert
        os.makedirs(self.flashcards_backup_dir, exist_ok=True)
        
        try:
            self.data_manager.save_flashcards(backup_path)
            logging.info(f"Flashcards-Backup erstellt: {backup_path}")
        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Flashcards-Backups: {e}")
            messagebox.showerror("Fehler", f"Beim Erstellen des Flashcards-Backups ist ein Fehler aufgetreten:\n{e}")

    def backup_themes(self, reason="update"):
        """Erstellt ein Backup der Themes."""
        # Ãƒâ€žndere das Datumsformat zu "%d.%m.%Y_%H-%M-%S"
        timestamp = datetime.datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
        backup_filename = f"theme_backup_{reason}_{timestamp}.json"
        backup_path = os.path.join(self.theme_backup_dir, backup_filename)
        
        # Sicherstellen, dass das Backup-Verzeichnis existiert
        os.makedirs(self.theme_backup_dir, exist_ok=True)
        
        try:
            self.data_manager.theme_manager.export_themes(backup_path)
            logging.info(f"Theme-Backup erstellt: {backup_path}")
        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Theme-Backups: {e}")
            messagebox.showerror("Fehler", f"Beim Erstellen des Theme-Backups ist ein Fehler aufgetreten:\n{e}")


    # -----------------------------------------------------------------------------------
    # THEME BACKUP SYSTEM
    # -----------------------------------------------------------------------------------
    def apply_theme(self, theme_name):
        """Wechselt zu dem angegebenen Theme."""
        self.load_theme(theme_name)
        messagebox.showinfo("Theme gewechselt", f"Das Theme '{theme_name}' wurde angewendet.")
        self.navigate_to('main')  # Verwenden Sie navigate_to für Konsistenz

    def load_theme(self, theme_name):
        """LÃƒÂ¤dt und wendet das angegebene Theme an."""
        if theme_name.lower() == "system":
            # System Theme Logik (bereits vorhanden)
            if sys.platform == "win32":
                try:
                    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                    key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    dark_mode, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    theme_data = self.data_manager.theme_manager.get_theme("dark") if dark_mode == 0 else self.data_manager.theme_manager.get_theme("light")
                except Exception as e:
                    logging.error(f"Fehler beim Erkennen des System-Themes: {e}")
                    theme_data = self.data_manager.theme_manager.get_theme("light")
            else:
                # Für andere Betriebssysteme: Setze auf light als Standard
                theme_data = self.data_manager.theme_manager.get_theme("light")
        else:
            theme_data = self.data_manager.theme_manager.get_theme(theme_name.lower())

        if not theme_data:
            messagebox.showerror("Fehler", f"Theme '{theme_name}' nicht gefunden.")
            return
        # ÃƒÅ“berprÃƒÂ¼fung und Setzen der Theme-Daten mit Standardwerten
        self.default_bg = theme_data.get("default_bg", self.appearance_settings.text_bg_color)
        self.appearance_settings.text_bg_color = theme_data.get("text_bg_color", self.appearance_settings.text_bg_color)
        self.appearance_settings.text_fg_color = theme_data.get("text_fg_color", self.appearance_settings.text_fg_color)
        self.appearance_settings.button_bg_color = theme_data.get("button_bg_color", self.appearance_settings.button_bg_color)
        self.appearance_settings.button_fg_color = theme_data.get("button_fg_color", self.appearance_settings.button_fg_color)

        # Aktualisiere Styles mit den neuen Theme-Einstellungen
        self.configure_styles()

        self.apply_appearance_settings()

    def import_theme_file(self):
        """Importiert Themes aus einer JSON-Datei."""
        file_path = filedialog.askopenfilename(
            title="Theme importieren",
            filetypes=[("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*")]
        )
        if not file_path:
            return
        try:
            success = self.data_manager.theme_manager.import_themes(file_path)
            if success:
                messagebox.showinfo("Erfolg", f"Themes aus {file_path} importiert.")
                self.backup_themes("import")
                self.refresh_theme_menu()
                logging.info(f"Themes aus {file_path} erfolgreich importiert.")
            else:
                messagebox.showerror("Fehler", "Import fehlgeschlagen.")
        except Exception as e:
            logging.error(f"Fehler beim Importieren der Themes: {e}")
            messagebox.showerror("Fehler", f"Import fehlgeschlagen: {e}")

    def export_current_theme(self):
        """Exportiert das aktuelle Theme in eine JSON-Datei."""
        file_path = filedialog.asksaveasfilename(
            title="Theme exportieren",
            defaultextension=".json",
            filetypes=[("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*")]
        )
        if not file_path:
            return
        try:
            self.data_manager.theme_manager.export_themes(file_path)
            messagebox.showinfo("Erfolg", f"Themes wurden nach {file_path} exportiert.")
            self.backup_themes("export")
            logging.info(f"Themes erfolgreich exportiert nach {file_path}.")
        except Exception as e:
            logging.error(f"Fehler beim Exportieren der Themes: {e}")
            messagebox.showerror("Fehler", f"Beim Exportieren der Themes ist ein Fehler aufgetreten:\n{e}")

    def refresh_theme_menu(self):
        """
        Aktualisiert das Theme-MenÃƒÂ¼ in der Sidebar, um neue Themes anzuzeigen.
        Entfernt alte dynamische EintrÃƒÂ¤ge und erstellt sie neu.
        """
        # SchlieÃƒÅ¸t bestehende MenÃƒÂ¼s, falls eines geÃƒÂ¶ffnet ist
        self.close_theme_menu()

        # Initialisiert die Liste, falls nicht vorhanden
        if not hasattr(self, 'theme_menu_items'):
            self.theme_menu_items = []

        # Separator für Themes
        sep = ttk.Separator(self.sidebar_frame, orient='horizontal')
        sep.pack(fill='x', pady=5)
        self.theme_menu_items.append(sep)  # Separator in Liste aufnehmen

        # Header mit SchlieÃƒÅ¸en-Button
        header_frame = tk.Frame(self.sidebar_frame, bg="#E8F4F8")
        header_frame.pack(fill='x', pady=5)
        self.theme_menu_items.append(header_frame)

        themes_label = ttk.Label(
            header_frame,
            text="Themes",
            foreground="#2C3E50",
            background="#E8F4F8",
            font=("Segoe UI", 12, "bold")
        )
        themes_label.pack(side='left', padx=5)
        self.theme_menu_items.append(themes_label)

        close_btn = ModernButton(
            header_frame,
            text="×",  # Unicode X symbol
            command=self.close_theme_menu,
            width=2,
            style=ButtonStyle.SECONDARY.value
        )
        close_btn.pack(side='right', padx=5)
        self.theme_menu_items.append(close_btn)

        # Dynamische Theme-Buttons hinzufügen
        for theme_name in ["light", "dark", "system"]:  # Kleinbuchstaben verwenden
            theme_button = ModernButton(
                self.sidebar_frame,
                text=f"Wechsel zu: {theme_name.capitalize()}",
                command=lambda name=theme_name: self.apply_theme(name),
                style=ButtonStyle.PRIMARY.value  # Konsistente Style-Verwendung
            )
            theme_button.pack(fill='x', padx=10, pady=(0,5))
            self.theme_menu_items.append(theme_button)

        # Import/Export Buttons
        import_btn = ModernButton(
            self.sidebar_frame,
            text="Theme importieren",
            command=self.import_theme_file,
            width=20,
            style=ButtonStyle.SECONDARY.value
        )
        import_btn.pack(pady=(5,0))
        self.theme_menu_items.append(import_btn)

        export_btn = ModernButton(
            self.sidebar_frame,
            text="Theme exportieren",
            command=self.export_current_theme,
            width=20,
            style=ButtonStyle.SECONDARY.value
        )
        export_btn.pack(pady=(5,0))
        self.theme_menu_items.append(export_btn)

        # Setze den Zustand auf "erweitert"
        self.theme_menu_expanded = True

    def close_theme_menu(self):
        """
        SchlieÃƒÅ¸t das erweiterte Theme-MenÃƒÂ¼.
        Entfernt alle dynamischen Widgets und setzt den Zustand zurück.
        """
        # Überprüfe, ob die MenÃƒÂ¼-Widgets existieren
        if hasattr(self, 'theme_menu_items'):
            for item in self.theme_menu_items:
                item.destroy()
            self.theme_menu_items.clear()

        # Setze den Zustand auf "nicht erweitert"
        self.theme_menu_expanded = False


    # -----------------------------------------------------------------------------------
    # BACKUP VERWALTUNG
    # -----------------------------------------------------------------------------------
    def show_backup_manager(self):
        self._clear_content_frame()
        header_frame = tk.Frame(self.content_frame, bg=self.default_bg)
        header_frame.pack(fill='x', pady=(30, 20))
        tk.Label(
            header_frame,
            text="Backup-Verwaltung",
            font=("Segoe UI", 16, "bold"),
            bg=self.default_bg
        ).pack()

        main_frame = ttk.Frame(self.content_frame)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Backup-Typ auswÃƒÂ¤hlen
        backup_type_var = tk.StringVar(value="flashcards")
        ttk.Label(main_frame, text="Backup-Typ:", font=(self.appearance_settings.font_family, 12)).pack(pady=5)
        backup_type_dropdown = ModernCombobox(main_frame, textvariable=backup_type_var, values=["flashcards", "themes"], state="readonly")
        backup_type_dropdown.pack(pady=5)

        # Backup-Button
        def backup_selected_type():
            backup_type = backup_type_var.get()
            if backup_type == "flashcards":
                self.backup_flashcards("manual")
                messagebox.showinfo("Erfolg", "Flashcards-Backup erstellt.")
            elif backup_type == "themes":
                self.backup_themes("manual")
                messagebox.showinfo("Erfolg", "Theme-Backup erstellt.")
            else:
                messagebox.showwarning("Warnung", "UngÃƒÂ¼ltiger Backup-Typ ausgewÃƒÂ¤hlt.")

        backup_btn = ModernButton(
            main_frame,
            text="Backup erstellen",
            command=backup_selected_type,
            width=20,
            style=ButtonStyle.PRIMARY.value
        )
        backup_btn.pack(pady=10)

        # Zurück-Button
        back_btn = ModernButton(
            self.content_frame,
            text="Zurück zum Hauptmenü",
            command=self.create_main_menu,
            width=15,
            style=ButtonStyle.SECONDARY.value
        )
        back_btn.pack(pady=20)
        self.sidebar_buttons["back_to_main_from_backup"] = back_btn

        # Setze den aktiven Button auf 'backup'
        self.highlight_active_button('backup')

    def show_help(self):
        """Zeigt die moderne Hilfe-Hauptseite mit Untermenüs."""
        self._clear_content_frame()

        # Hauptcontainer
        main_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_container.pack(fill='both', expand=True, padx=40, pady=30)

        # Header mit Gradient-Style
        header_frame = ctk.CTkFrame(main_container, corner_radius=15, fg_color=("#3b8ed0", "#1f6aa5"))
        header_frame.pack(fill='x', pady=(0, 30))

        ctk.CTkLabel(
            header_frame,
            text="📚 Hilfe & Dokumentation",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="white"
        ).pack(pady=25)

        # Einführungstext
        intro_frame = ctk.CTkFrame(main_container, corner_radius=12)
        intro_frame.pack(fill='x', pady=(0, 25), padx=10)

        ctk.CTkLabel(
            intro_frame,
            text="Willkommen im Hilfebereich!",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w"
        ).pack(pady=(20, 10), padx=25, anchor="w")

        ctk.CTkLabel(
            intro_frame,
            text="Wählen Sie unten ein Thema aus, um detaillierte Informationen und Anleitungen zu erhalten.",
            font=ctk.CTkFont(size=14),
            anchor="w",
            wraplength=700,
            text_color=("gray20", "gray80")
        ).pack(pady=(0, 20), padx=25, anchor="w")

        # Grid für Hilfe-Karten (2x2 Layout)
        cards_container = ctk.CTkFrame(main_container, fg_color="transparent")
        cards_container.pack(fill='both', expand=True, pady=10)

        # Konfiguriere Grid
        cards_container.grid_columnconfigure((0, 1), weight=1, uniform="column")
        cards_container.grid_rowconfigure((0, 1), weight=1, uniform="row")

        # Hilfe-Karten Daten
        help_topics = [
            {
                "icon": "📅",
                "title": "Wochenkalender",
                "description": "Planung, Tagesansicht und\nWochenübersicht",
                "color": ("#4a90e2", "#357abd"),
                "command": self.help_weekly_calendar
            },
            {
                "icon": "🎯",
                "title": "Leitner Session",
                "description": "Lernsystem, Punkte und\nWiederholungslogik",
                "color": ("#e24a4a", "#bd3535"),
                "command": self.help_leitner_session
            },
            {
                "icon": "📁",
                "title": "Kategorien",
                "description": "Kategorien erstellen,\nbearbeiten und löschen",
                "color": ("#4ae290", "#35bd6f"),
                "command": self.help_categories
            },
            {
                "icon": "🗂️",
                "title": "Karten",
                "description": "Karteikarten hinzufügen,\nbearbeiten und verwalten",
                "color": ("#e2a04a", "#bd8235"),
                "command": self.help_cards
            }
        ]

        # Erstelle Hilfe-Karten im Grid
        for idx, topic in enumerate(help_topics):
            row = idx // 2
            col = idx % 2

            card = ctk.CTkFrame(
                cards_container,
                corner_radius=15,
                fg_color=topic["color"],
                cursor="hand2"
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

            # Icon
            ctk.CTkLabel(
                card,
                text=topic["icon"],
                font=ctk.CTkFont(size=48)
            ).pack(pady=(30, 10))

            # Titel
            ctk.CTkLabel(
                card,
                text=topic["title"],
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color="white"
            ).pack(pady=(0, 8))

            # Beschreibung
            ctk.CTkLabel(
                card,
                text=topic["description"],
                font=ctk.CTkFont(size=13),
                text_color=("white", "gray90"),
                justify="center"
            ).pack(pady=(0, 20))

            # Button
            ctk.CTkButton(
                card,
                text="Mehr erfahren →",
                command=topic["command"],
                fg_color="white",
                text_color=topic["color"][0],
                hover_color=("gray90", "gray80"),
                height=35,
                corner_radius=8,
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(pady=(0, 25), padx=30)

        # Zurück-Button
        ctk.CTkButton(
            main_container,
            text="← Zurück zum Hauptmenü",
            command=self.create_main_menu,
            width=220,
            height=45,
            font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=10,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40")
        ).pack(pady=(25, 10))

    def help_weekly_calendar(self):
        """Zeigt detaillierte Hilfe zum Wochenkalender mit moderner interaktiver Navigation."""
        sections = [
            {
                'id': 'overview',
                'icon': '📋',
                'title': 'Übersicht',
                'content': """Der Wochenkalender hilft Ihnen, Ihre Lernziele zu planen und Ihren Fortschritt zu verfolgen.
Er zeigt Ihnen auf einen Blick, welche Aufgaben heute anstehen und wie Ihre Woche aussieht.

Hauptfunktionen:
• Tagesansicht für den aktuellen Tag
• Wochenübersicht für die kommenden 7 Tage
• Fälligkeitsstatistiken und Workload-Verteilung
• Direkter Zugriff auf Lernsessions""",
                'use_monospace': False
            },
            {
                'id': 'today',
                'icon': '☀️',
                'title': 'Tagesansicht',
                'content': """Funktionen der Tagesansicht:

• Aktuelle Aufgaben: Zeigt alle für heute fälligen Karteikarten
• Fälligkeitsstatistik: Übersicht über Karten nach Priorität
  - Überfällige Karten (rot markiert)
  - Heute fällige Karten (gelb markiert)
  - Bald fällige Karten (grün markiert)

• Session starten: Direkter Zugriff auf Ihre heutige Lernsession
• Fortschrittsanzeige: Zeigt erledigte vs. offene Karten

Methode: calendar_ui_modern.py → update_today_view()
Diese Methode lädt die aktuellen Daten und aktualisiert die Tagesansicht.""",
                'use_monospace': True
            },
            {
                'id': 'week',
                'icon': '📊',
                'title': 'Wochenübersicht',
                'content': """Die Wochenübersicht zeigt:

• 7-Tage-Kalender: Montag bis Sonntag mit täglichen Aufgaben
• Farbcodierung:
  - Grau: Keine Karten fällig
  - Gelb: 1-10 Karten fällig
  - Orange: 11-30 Karten fällig
  - Rot: Mehr als 30 Karten fällig

• Tagesdetails beim Klick: Klicken Sie auf einen Tag, um Details zu sehen
• Workload-Verteilung: Sehen Sie auf einen Blick, wo Belastungsspitzen liegen

Methoden:
• calendar_ui_modern.py → update_week_view()
  Erstellt die Wochenübersicht mit allen 7 Tagen

• calendar_ui_modern.py → get_cards_due_on_date(date)
  Ermittelt alle Karten, die an einem bestimmten Datum fällig sind

• calendar_ui_modern.py → show_day_details(date)
  Zeigt detaillierte Informationen für einen ausgewählten Tag""",
                'use_monospace': True
            },
            {
                'id': 'tips',
                'icon': '💡',
                'title': 'Tipps & Best Practices',
                'content': """1. Tägliche Routine etablieren:
   Schauen Sie jeden Morgen in die Tagesansicht, um Ihren Tag zu planen

2. Vorausplanen:
   Nutzen Sie die Wochenübersicht, um Lernzeiten für kommende Tage einzuplanen

3. Gleichmäßige Verteilung:
   Achten Sie darauf, neue Karten gleichmäßig über die Woche zu verteilen

4. Prioritäten setzen:
   Überfällige Karten (rot) sollten immer zuerst bearbeitet werden

5. Workload beachten:
   Vermeiden Sie es, zu viele neue Karten an einem Tag zu starten

6. Tagesdetails nutzen:
   Klicken Sie auf einzelne Tage, um detaillierte Informationen zu sehen""",
                'use_monospace': False
            }
        ]

        self._create_modern_help_page(
            title="Wochenkalender",
            icon="📅",
            color=("#4a90e2", "#357abd"),
            sections=sections
        )

    def help_leitner_session(self):
        """Zeigt detaillierte Hilfe zur Leitner Session mit moderner interaktiver Navigation."""
        sections = [
            {
                'id': 'about',
                'icon': '📚',
                'title': 'Was ist das Leitner-System?',
                'content': """Das Leitner-System ist eine wissenschaftlich fundierte Lernmethode, die auf dem Prinzip
der verteilten Wiederholung (Spaced Repetition) basiert.

Kernprinzip:
Karten, die Sie gut beherrschen, werden seltener wiederholt.
Karten, die Sie noch lernen, erscheinen häufiger.

Dies optimiert Ihren Lernerfolg und spart Zeit!

Vorteile:
• Wissenschaftlich belegt: Bis zu 80% bessere Langzeit-Retention
• Zeiteffizient: Konzentration auf schwierige Karten
• Automatische Anpassung: System passt sich Ihrem Fortschritt an
• Motivierend: Sichtbarer Fortschritt durch Level-System""",
                'use_monospace': False
            },
            {
                'id': 'levels',
                'icon': '📊',
                'title': 'Das 10-Level System',
                'content': """Jede Karte durchläuft 10 Level basierend auf Ihrem Punktestand:

Level  | Punkte      | Wiederholungsintervall
-------|-------------|----------------------
  1    | 0-10        | 1 Tag (täglich)
  2    | 11-25       | 2 Tage
  3    | 26-50       | 4 Tage
  4    | 51-85       | 7 Tage (wöchentlich)
  5    | 86-120      | 10 Tage
  6    | 121-175     | 12 Tage
  7    | 176-220     | 14 Tage (zweiwöchentlich)
  8    | 221-285     | 20 Tage
  9    | 286-350     | 25 Tage
  10   | 350+        | 30 Tage (monatlich)

Je höher das Level, desto besser beherrschen Sie die Karte!

Methoden:
• leitner_system.py → get_card_level(points)
  Berechnet das Level einer Karte basierend auf den Punkten

• leitner_system.py → get_next_review_interval(level)
  Gibt das Wiederholungsintervall für ein bestimmtes Level zurück""",
                'use_monospace': True
            },
            {
                'id': 'points',
                'icon': '🎯',
                'title': 'Das intelligente Punktesystem',
                'content': """Bei RICHTIGEN Antworten:
━━━━━━━━━━━━━━━━━━━━━━━━
Basis-Punkte = Ihre aktuelle Streak (Anzahl richtiger Antworten in Folge)

Diese werden verstärkt durch zwei Multiplikatoren:

1. Erfolgsquoten-Multiplikator (basiert auf letzten 10 Antworten):
   • 0-49% Erfolgsquote   → 0.0× - 1.0× Multiplikator
   • 50% Erfolgsquote     → 1.0× Multiplikator (normal)
   • 70% Erfolgsquote     → 1.5× Multiplikator
   • 85% Erfolgsquote     → 2.0× Multiplikator
   • 100% Erfolgsquote    → 3.0× Multiplikator (maximum!)

2. Streak-Bonus (belohnt lange Erfolgsserien):
   • Streak 1-4           → ×1.0 (kein Bonus)
   • Streak 5-9           → ×1.5
   • Streak 10-14         → ×2.0
   • Streak 15-19         → ×2.5
   • Streak 20+           → ×3.0 (maximum!)

Gesamtpunkte = Basis-Punkte × Erfolgsquoten-Multiplikator × Streak-Bonus

Beispiel: Streak 12, Erfolgsquote 80%
→ 12 × 1.8 × 2.0 = 43 Punkte!


Bei FALSCHEN Antworten:
━━━━━━━━━━━━━━━━━━━━━━━━
Punktabzug = Fehler-Faktor × Level-Faktor × Streak-Verlust-Faktor

• Fehler-Faktor (basiert auf Gesamtfehleranzahl dieser Karte):
   1-5 Fehler    → ×1.0       16-20 Fehler → ×4.0
   6-10 Fehler   → ×2.0       21+ Fehler   → ×5.0
   11-15 Fehler  → ×3.0

• Level-Faktor (höhere Level = größerer Verlust):
   Level 1-2   → ×1.0 - ×1.25    Level 7-8  → ×2.5 - ×2.75
   Level 3-4   → ×1.5 - ×1.75    Level 9    → ×3.0
   Level 5-6   → ×2.0 - ×2.25    Level 10   → ×4.0

• Streak-Verlust-Faktor (Strafe für unterbrochene Serie):
   Streak < 5    → ×1.0 (keine Extra-Strafe)
   Streak 5-9    → ×1.5
   Streak 10-14  → ×2.0
   Streak 15-19  → ×3.0
   Streak 20+    → ×4.0

Beispiel: Level 5, Streak 12 verloren, 8 Fehler gesamt
→ 2.0 × 2.0 × 2.0 = 8 Punkte Abzug

Methoden:
• leitner_system.py → calculate_points_on_correct(card)
  Berechnet Punkte für richtige Antworten

• leitner_system.py → calculate_points_on_incorrect(card)
  Berechnet Punktabzug für falsche Antworten

• leitner_system.py → update_card_stats(card, is_correct)
  Aktualisiert alle Statistiken einer Karte""",
                'use_monospace': True
            },
            {
                'id': 'logic',
                'icon': '🔄',
                'title': 'Wiederholungslogik & Session-Verhalten',
                'content': """Wann erscheint eine Karte wieder?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bei RICHTIGER Antwort (erste Antwort in Session):
• Karte wird aus der aktuellen Session entfernt
• Nächstes Review-Datum wird basierend auf Level gesetzt
• Karte erscheint erst wieder am Review-Datum
• Punkte werden addiert, Level steigt möglicherweise

Bei FALSCHER Antwort:
• Karte wird SOFORT wieder verfügbar (noch am selben Tag!)
• Karte erscheint 3-5 Positionen später in der Session nochmal
• Recovery-Modus wird aktiviert
• Punkte werden abgezogen, Level sinkt möglicherweise
• Streak wird auf 0 zurückgesetzt

Spezialfall - Nochmal RICHTIG nach vorherigem Fehler:
• Wenn Sie eine Karte in der Session falsch beantwortet haben
  und später in derselben Session richtig beantworten:
  → ±0 Punkte (keine Änderung)
  → Karte wird für diese Session als abgeschlossen markiert
  → Sie können sie in der nächsten Session erneut üben
  → Verhindert Punkt-Farming durch wiederholtes Üben


Wie werden Karten sortiert?
━━━━━━━━━━━━━━━━━━━━━━━━━

1. Gruppierung nach Fälligkeitsdatum:
   • Überfällige Karten haben höchste Priorität
   • Je älter die Überfälligkeit, desto höher die Priorität
   • Innerhalb eines Datums: zufällige Reihenfolge

2. Innerhalb einer Session:
   • Falsch beantwortete Karten werden wieder eingefügt
   • Position: 3-5 Karten später (verhindert sofortige Wiederholung)
   • Sorgt für verteilte Übung schwieriger Karten

3. Recovery-Modus nach Fehler:
   • Karte startet mit 1-Tag Intervall
   • Bei jeder richtigen Antwort verdoppelt sich das Intervall:
     1 Tag → 2 Tage → 4 Tage → usw.
   • Bis das normale Level-Intervall wieder erreicht ist
   • Graduelle Rehabilitation statt abrupter Levelsprünge

Methoden:
• leitner_system.py → get_due_cards(date, category_filter)
  Ermittelt alle fälligen Karten für ein Datum

• leitner_system.py → sort_cards_by_priority(cards)
  Sortiert Karten nach Priorität (Überfälligkeit, Level)

• leitner_system.py → reinsert_card_to_session(card, position_offset)
  Fügt falsch beantwortete Karte wieder in Session ein

• leitner_system.py → activate_recovery_mode(card)
  Aktiviert Recovery-Modus für eine Karte nach Fehler""",
                'use_monospace': True
            },
            {
                'id': 'session',
                'icon': '▶️',
                'title': 'Session starten & durchführen',
                'content': """So führen Sie eine effektive Lern-Session durch:

1. Session vorbereiten:
   • Wählen Sie eine oder mehrere Kategorien aus
   • Legen Sie die Anzahl der Karten fest (empfohlen: 10-20)
   • System wählt automatisch die fälligsten Karten aus

2. Während der Session:
   • Lesen Sie die Frage aufmerksam
   • Denken Sie über die Antwort nach
   • Klicken Sie auf "Antwort zeigen"
   • Bewerten Sie ehrlich: Richtig oder Falsch
   • System aktualisiert automatisch Punkte und Level

3. Session-Statistiken:
   • Live-Fortschritt: X von Y Karten abgeschlossen
   • Aktuelle Streak anzeigen
   • Erfolgsquote in dieser Session
   • Geschätzte verbleibende Zeit

4. Session beenden:
   • Automatisch nach allen Karten
   • Oder manuell mit "Session beenden"
   • Zusammenfassung mit Statistiken wird angezeigt
   • Alle Fortschritte werden gespeichert

Methoden:
• main.py → start_learning_session(category, num_cards)
  Initialisiert und startet eine neue Lernsession

• main.py → show_card(card)
  Zeigt die aktuelle Karte (Frage/Antwort)

• main.py → handle_card_response(is_correct)
  Verarbeitet die Antwort des Benutzers

• main.py → show_session_summary(stats)
  Zeigt die Session-Zusammenfassung am Ende""",
                'use_monospace': True
            },
            {
                'id': 'tips',
                'icon': '💡',
                'title': 'Tipps für effektives Lernen',
                'content': """1. Ehrlich bleiben:
   Bewerten Sie Ihre Antworten ehrlich. Nur so funktioniert das System optimal.
   Selbstbetrug schadet nur Ihrem Lernerfolg!

2. Regelmäßigkeit über Intensität:
   Lieber täglich 15 Minuten als einmal pro Woche 2 Stunden.
   Konstanz ist der Schlüssel zum Langzeiterfolg.

3. Nicht aufgeben bei schwierigen Karten:
   Wenn eine Karte oft falsch ist, ist das normal!
   Das System sorgt automatisch dafür, dass Sie sie häufiger üben.

4. Optimale Session-Größe:
   Anfänger: 10-15 Karten
   Fortgeschrittene: 20-30 Karten
   Profis: 30-50 Karten
   (Passen Sie an Ihre verfügbare Zeit an)

5. Bilder optimal nutzen:
   Nutzen Sie Bilder für komplexe Konzepte, Diagramme und Grafiken.
   Visuelle Anker verbessern die Merkfähigkeit um bis zu 60%!

6. Kategorien strategisch nutzen:
   Organisieren Sie Karten nach Themen oder Schwierigkeit.
   Lernen Sie verwandte Themen in derselben Session.

7. Pausen einplanen:
   Nach 45-60 Minuten: 10-15 Minuten Pause
   Hält die Konzentration hoch und verbessert Retention.

8. Nicht zu viele neue Karten auf einmal:
   Maximum 10-20 neue Karten pro Tag empfohlen.
   Zu viele neue Karten führen zu Überforderung.""",
                'use_monospace': False
            }
        ]

        self._create_modern_help_page(
            title="Leitner Session",
            icon="🎯",
            color=("#e24a4a", "#bd3535"),
            sections=sections
        )

    def help_categories(self):
        """Zeigt detaillierte Hilfe zu Kategorien mit moderner interaktiver Navigation."""
        sections = [
            {
                'id': 'overview',
                'icon': '📋',
                'title': 'Was sind Kategorien?',
                'content': """Kategorien helfen Ihnen, Ihre Karteikarten thematisch zu organisieren.
Sie können Karten nach Fächern, Themen oder Schwierigkeitsgraden sortieren.

Vorteile:
• Gezielte Lern-Sessions für spezifische Themen
• Bessere Übersicht bei vielen Karten
• Flexible Filterung beim Lernen
• Statistiken pro Kategorie
• Farbcodierung für schnelle Orientierung
• Hierarchische Organisation möglich""",
                'use_monospace': False
            },
            {
                'id': 'create',
                'icon': '➕',
                'title': 'Neue Kategorie erstellen',
                'content': """So erstellen Sie eine neue Kategorie:

1. Navigieren Sie zum Kategorien-Bereich
   Menü → Kategorien verwalten

2. Klicken Sie auf "Neue Kategorie"

3. Geben Sie die Kategorieinformationen ein:
   • Name: Eindeutiger Name (z.B. "Mathematik", "Geschichte")
   • Beschreibung (optional): Kurze Beschreibung des Inhalts
   • Farbe (optional): Visuelle Kennzeichnung

4. Klicken Sie auf "Erstellen"

Die neue Kategorie ist sofort verfügbar!

Methoden:
• data_manager.py → create_category(name, description, color)
  Erstellt eine neue Kategorie in der Datenbank

• data_manager.py → validate_category_name(name)
  Prüft, ob der Kategoriename gültig und einzigartig ist

• main.py → show_create_category_dialog()
  Zeigt den Dialog zur Kategorieerstellung""",
                'use_monospace': True
            },
            {
                'id': 'edit',
                'icon': '✏️',
                'title': 'Kategorie bearbeiten',
                'content': """So bearbeiten Sie eine bestehende Kategorie:

1. Öffnen Sie die Kategorieübersicht
   Menü → Kategorien verwalten

2. Wählen Sie die zu bearbeitende Kategorie aus

3. Klicken Sie auf das Bearbeiten-Symbol (✏️)

4. Ändern Sie die gewünschten Informationen:
   • Name umbenennen
   • Beschreibung aktualisieren
   • Farbe ändern

5. Klicken Sie auf "Speichern"

Wichtig:
• Alle Karten in dieser Kategorie behalten ihre Zuordnung
• Die Änderungen werden sofort übernommen
• Statistiken bleiben erhalten

Methoden:
• data_manager.py → update_category(category_id, updates)
  Aktualisiert Kategorieinformationen

• data_manager.py → get_category_stats(category_id)
  Ruft Statistiken einer Kategorie ab

• main.py → show_edit_category_dialog(category)
  Zeigt den Bearbeitungsdialog""",
                'use_monospace': True
            },
            {
                'id': 'delete',
                'icon': '🗑️',
                'title': 'Kategorie löschen',
                'content': """So löschen Sie eine Kategorie:

1. Öffnen Sie die Kategorieübersicht
   Menü → Kategorien verwalten

2. Wählen Sie die zu löschende Kategorie

3. Klicken Sie auf das Löschen-Symbol (🗑️)

4. Bestätigen Sie den Löschvorgang

Wichtig - Was passiert mit den Karten?
Sie haben zwei Optionen:

Option A: Kategorie-Zuordnung entfernen
• Karten bleiben erhalten
• Karten werden als "Nicht kategorisiert" markiert
• Alle Lernfortschritte bleiben erhalten
• Empfohlen, wenn Sie die Karten behalten möchten

Option B: Karten mit löschen
• Kategorie UND alle enthaltenen Karten werden gelöscht
• Lernfortschritte gehen verloren
• Nicht rückgängig zu machen!
• Nur wählen, wenn Sie die Karten wirklich nicht mehr brauchen

Sicherheitsabfrage:
• Bei mehr als 10 Karten: Zusätzliche Bestätigung erforderlich
• Kategoriename muss zur Bestätigung eingegeben werden
• Verhindert versehentliches Löschen

Methoden:
• data_manager.py → delete_category(category_id, delete_cards)
  Löscht Kategorie (und optional die Karten)

• data_manager.py → unassign_cards_from_category(category_id)
  Entfernt Kategorie-Zuordnung von allen Karten

• data_manager.py → get_category_card_count(category_id)
  Ermittelt Anzahl der Karten in einer Kategorie

• main.py → show_delete_category_confirmation(category)
  Zeigt Bestätigungsdialog vor dem Löschen""",
                'use_monospace': True
            },
            {
                'id': 'organize',
                'icon': '🗂️',
                'title': 'Kategorien organisieren & Tipps',
                'content': """Best Practices für Kategorien:

1. Klare Namensgebung:
   ✓ Gut: "Französisch - Vokabeln A1"
   ✗ Schlecht: "FR Vok"

   ✓ Gut: "Mathematik - Analysis"
   ✗ Schlecht: "Mathe"

2. Hierarchische Struktur (via Namenskonvention):
   • Hauptthema - Unterthema - Details
   • Beispiel: "Biologie - Zellbiologie - Mitose"
   • Ermöglicht spätere Filterung und Sortierung

3. Farbcodierung nutzen:
   • Fächer: Unterschiedliche Farben pro Fach
   • Schwierigkeit: Grün (leicht), Gelb (mittel), Rot (schwer)
   • Status: Blau (in Bearbeitung), Grün (abgeschlossen)

4. Nicht zu viele Kategorien:
   • Ideal: 5-15 Hauptkategorien
   • Zu viele Kategorien → Unübersichtlich
   • Zu wenige Kategorien → Verlust der Struktur

5. Regelmäßig aufräumen:
   • Leere Kategorien löschen
   • Ähnliche Kategorien zusammenführen
   • Veraltete Kategorien archivieren

6. Kategoriestatistiken nutzen:
   • Sehen Sie, welche Kategorien Sie vernachlässigen
   • Identifizieren Sie Ihre Stärken und Schwächen
   • Planen Sie Sessions basierend auf Kategorien

Methoden:
• data_manager.py → get_all_categories(sort_by)
  Ruft alle Kategorien sortiert ab

• data_manager.py → merge_categories(source_id, target_id)
  Führt zwei Kategorien zusammen

• data_manager.py → get_category_statistics()
  Erstellt Übersicht über alle Kategorien mit Statistiken""",
                'use_monospace': True
            }
        ]

        self._create_modern_help_page(
            title="Kategorien verwalten",
            icon="📁",
            color=("#4ae290", "#35bd6f"),
            sections=sections
        )

    def help_cards(self):
        """Zeigt detaillierte Hilfe zu Karteikarten mit moderner interaktiver Navigation."""
        sections = [
            {
                'id': 'overview',
                'icon': '📋',
                'title': 'Was sind Karteikarten?',
                'content': """Karteikarten sind das Herzstück Ihres Lernsystems.
Jede Karte besteht aus einer Frage (Vorderseite) und einer Antwort (Rückseite).

Komponenten einer Karte:
• Frage: Was Sie lernen möchten
• Antwort: Die richtige Lösung
• Kategorie: Thematische Zuordnung
• Bild (optional): Visuelle Unterstützung
• Statistiken: Punkte, Level, Erfolgsquote
• Metadaten: Erstelldatum, letzte Wiederholung, nächste Fälligkeit

Die Karten arbeiten nahtlos mit dem Leitner-System zusammen, um Ihren Lernerfolg zu maximieren.""",
                'use_monospace': False
            },
            {
                'id': 'create',
                'icon': '➕',
                'title': 'Neue Karte erstellen',
                'content': """So erstellen Sie eine neue Karteikarte:

1. Navigieren Sie zum Karten-Bereich
   Menü → Karten verwalten → Neue Karte

2. Füllen Sie die Pflichtfelder aus:
   • Frage: Formulieren Sie eine klare, präzise Frage
   • Antwort: Geben Sie die vollständige Antwort an
   • Kategorie: Wählen Sie eine passende Kategorie

3. Optional - Erweiterte Optionen:
   • Bild hinzufügen: Klicken Sie auf "Bild auswählen"
     - Unterstützte Formate: JPG, PNG, GIF
     - Empfohlene Größe: max. 800x600 Pixel
   • Tags hinzufügen: Für zusätzliche Filterung
   • Schwierigkeitsgrad: Legen Sie initiale Schwierigkeit fest

4. Klicken Sie auf "Karte erstellen"

Die neue Karte ist sofort lernbereit und startet auf Level 1!

Tipps für gute Karten:
• Fragen kurz und präzise formulieren
• Antworten vollständig, aber kompakt halten
• Eine Karte = Ein Konzept (nicht mehrere Fragen mischen)
• Bei komplexen Themen: Mehrere Karten erstellen

Methoden:
• data_manager.py → create_flashcard(question, answer, category_id, image_path)
  Erstellt eine neue Karteikarte in der Datenbank

• data_manager.py → validate_flashcard_data(question, answer)
  Prüft, ob Frage und Antwort gültig sind

• data_manager.py → process_and_store_image(image_path)
  Verarbeitet und speichert das Kartenbild

• main.py → show_create_card_dialog()
  Zeigt den Dialog zur Kartenerstellung""",
                'use_monospace': True
            },
            {
                'id': 'edit',
                'icon': '✏️',
                'title': 'Karte bearbeiten',
                'content': """So bearbeiten Sie eine bestehende Karte:

1. Öffnen Sie die Kartenübersicht
   Menü → Karten verwalten

2. Finden Sie die zu bearbeitende Karte:
   • Über Suchfunktion
   • Über Kategoriefilter
   • Über Sortierung (nach Datum, Level, etc.)

3. Klicken Sie auf das Bearbeiten-Symbol (✏️)

4. Ändern Sie die gewünschten Felder:
   • Frage korrigieren/verbessern
   • Antwort aktualisieren
   • Kategorie wechseln
   • Bild hinzufügen/ändern/entfernen
   • Tags anpassen

5. Optional - Statistiken zurücksetzen:
   ⚠️ Vorsicht: Löscht Lernfortschritt dieser Karte!
   Nur verwenden, wenn Sie die Karte komplett neu lernen möchten

6. Klicken Sie auf "Speichern"

Wichtig:
• Änderungen an Frage/Antwort beeinflussen nicht den Lernfortschritt
• Kategorie-Wechsel behält alle Statistiken
• Bild-Änderungen sind jederzeit möglich

Methoden:
• data_manager.py → update_flashcard(card_id, updates)
  Aktualisiert Karteninformationen

• data_manager.py → reset_card_statistics(card_id)
  Setzt Lernfortschritt einer Karte zurück

• data_manager.py → update_card_image(card_id, image_path)
  Aktualisiert das Kartenbild

• main.py → show_edit_card_dialog(card)
  Zeigt den Bearbeitungsdialog

• main.py → show_card_statistics(card)
  Zeigt detaillierte Statistiken einer Karte""",
                'use_monospace': True
            },
            {
                'id': 'delete',
                'icon': '🗑️',
                'title': 'Karte löschen',
                'content': """So löschen Sie eine Karteikarte:

1. Öffnen Sie die Kartenübersicht
   Menü → Karten verwalten

2. Finden Sie die zu löschende Karte

3. Klicken Sie auf das Löschen-Symbol (🗑️)

4. Bestätigen Sie den Löschvorgang

⚠️ Wichtige Hinweise:
• Gelöschte Karten können NICHT wiederhergestellt werden!
• Alle Lernstatistiken gehen verloren
• Bilder werden ebenfalls gelöscht

Alternativen zum Löschen:
• Karte deaktivieren: Vorübergehend aus dem Lernsystem entfernen
• Karte archivieren: Für zukünftige Referenz behalten
• Statistiken zurücksetzen: Karte neu lernen

Massen-Löschung:
• Mehrere Karten gleichzeitig auswählen
• "Ausgewählte löschen" klicken
• Zusätzliche Bestätigung bei mehr als 5 Karten

Methoden:
• data_manager.py → delete_flashcard(card_id)
  Löscht eine Karte permanent

• data_manager.py → delete_multiple_cards(card_ids)
  Löscht mehrere Karten auf einmal

• data_manager.py → archive_flashcard(card_id)
  Archiviert eine Karte (Alternative zum Löschen)

• data_manager.py → deactivate_flashcard(card_id)
  Deaktiviert eine Karte temporär

• main.py → show_delete_card_confirmation(card)
  Zeigt Bestätigungsdialog vor dem Löschen""",
                'use_monospace': True
            },
            {
                'id': 'search',
                'icon': '🔍',
                'title': 'Karten suchen & filtern',
                'content': """Effiziente Kartenverwaltung bei vielen Karten:

1. Suchfunktion:
   • Volltext-Suche in Fragen und Antworten
   • Suchfeld: Geben Sie Suchbegriff ein
   • Ergebnisse werden live gefiltert
   • Groß-/Kleinschreibung wird ignoriert

2. Filter-Optionen:
   • Nach Kategorie filtern
   • Nach Level filtern (1-10)
   • Nach Fälligkeit filtern:
     - Überfällig
     - Heute fällig
     - Bald fällig
     - Zukünftig fällig
   • Nach Erfolgsquote filtern

3. Sortier-Optionen:
   • Nach Erstelldatum (neueste/älteste zuerst)
   • Nach Level (niedrigste/höchste zuerst)
   • Nach Punkten
   • Nach nächster Fälligkeit
   • Alphabetisch nach Frage

4. Erweiterte Suche:
   • Kombination mehrerer Filter
   • Gespeicherte Filterprofile
   • Export der Suchergebnisse

Tastenkombinationen:
• Strg+F: Suchfeld fokussieren
• Strg+K: Filter-Optionen öffnen
• Strg+R: Filter zurücksetzen

Methoden:
• data_manager.py → search_flashcards(query, filters)
  Durchsucht Karten nach Suchkriterien

• data_manager.py → filter_cards_by_category(category_id)
  Filtert Karten nach Kategorie

• data_manager.py → filter_cards_by_level(min_level, max_level)
  Filtert Karten nach Level-Bereich

• data_manager.py → filter_cards_by_due_date(date_range)
  Filtert nach Fälligkeitsdatum

• data_manager.py → sort_cards(cards, sort_by, order)
  Sortiert Kartenliste nach Kriterium

• main.py → apply_card_filters(filters)
  Wendet ausgewählte Filter an""",
                'use_monospace': True
            },
            {
                'id': 'import',
                'icon': '📤',
                'title': 'Import & Export',
                'content': """Karten zwischen Systemen übertragen:

EXPORT:
━━━━━━
1. Wählen Sie zu exportierende Karten:
   • Alle Karten
   • Nur bestimmte Kategorie
   • Nur ausgewählte Karten

2. Wählen Sie Export-Format:
   • CSV: Für Excel, Google Sheets
   • JSON: Für Backup und Übertragung
   • Anki: Kompatibel mit Anki-Software
   • TXT: Einfaches Textformat

3. Wählen Sie Export-Optionen:
   • Mit Bildern (erhöht Dateigröße)
   • Mit Statistiken (für Backup)
   • Nur Frage/Antwort (für Austausch)

4. Klicken Sie auf "Exportieren"
   Datei wird im Download-Ordner gespeichert


IMPORT:
━━━━━━
1. Klicken Sie auf "Karten importieren"

2. Wählen Sie Datei aus:
   • Unterstützte Formate: CSV, JSON, Anki, TXT
   • Max. Dateigröße: 50 MB

3. Ordnen Sie Spalten zu:
   • Welche Spalte enthält Fragen?
   • Welche Spalte enthält Antworten?
   • Optionale Spalten: Kategorie, Tags, Bilder

4. Wählen Sie Import-Optionen:
   • Duplikate überspringen
   • Duplikate aktualisieren
   • Alle importieren (auch Duplikate)

5. Vorschau prüfen:
   • Zeigt erste 10 Karten zur Kontrolle
   • Prüfen Sie Zuordnung und Formatierung

6. Klicken Sie auf "Import starten"

Tipps:
• Erstellen Sie regelmäßig Backups (JSON-Export)
• Testen Sie Import erst mit wenigen Karten
• Prüfen Sie importierte Karten auf Formatierungsfehler

Methoden:
• export_import.py → export_flashcards(cards, format, options)
  Exportiert Karten in gewähltes Format

• export_import.py → import_flashcards(file_path, mapping, options)
  Importiert Karten aus Datei

• export_import.py → detect_file_format(file_path)
  Erkennt automatisch Dateiformat

• export_import.py → validate_import_data(data)
  Prüft Import-Daten auf Gültigkeit

• export_import.py → create_backup(include_images, include_stats)
  Erstellt vollständiges System-Backup""",
                'use_monospace': True
            },
            {
                'id': 'tips',
                'icon': '💡',
                'title': 'Best Practices für Karteikarten',
                'content': """1. Atomic Principle (Eine Karte = Ein Konzept):
   ✓ Gut: "Was ist die Hauptstadt von Frankreich?" → "Paris"
   ✗ Schlecht: "Nenne 3 Hauptstädte europäischer Länder" → "Paris, Berlin, Rom"

2. Klare, eindeutige Fragen:
   ✓ Gut: "In welchem Jahr fand die Französische Revolution statt?"
   ✗ Schlecht: "Revolution?" (zu vague)

3. Vollständige, aber kompakte Antworten:
   ✓ Gut: "1789 - Beginn der Französischen Revolution"
   ✗ Schlecht: "1789" (zu kurz, ohne Kontext)
   ✗ Schlecht: 3 Absätze Text (zu lang)

4. Bilder strategisch einsetzen:
   • Für Diagramme und Grafiken
   • Für geografische Karten
   • Für visuelle Konzepte (Anatomie, Architektur)
   • NICHT für reinen Text (schlechte Lesbarkeit)

5. Kontextinformationen nutzen:
   • Fügen Sie Hinweise in Klammern hinzu
   • Beispiel: "Wer schrieb 'Faust'? (deutscher Dichter)" → "Goethe"

6. Regelmäßig aktualisieren:
   • Korrigieren Sie Fehler sofort
   • Verbessern Sie unklare Formulierungen
   • Aktualisieren Sie veraltete Informationen

7. Qualität über Quantität:
   • 50 gut formulierte Karten > 200 schlecht formulierte
   • Nehmen Sie sich Zeit für jede Karte
   • Überprüfen Sie Karten nach dem Erstellen

8. Mnemonics und Eselsbrücken:
   • Fügen Sie Gedächtnisstützen in Antworten hinzu
   • Beispiel: "Nie Ohne Seife Waschen" für Himmelsrichtungen""",
                'use_monospace': False
            }
        ]

        self._create_modern_help_page(
            title="Karteikarten verwalten",
            icon="🗂️",
            color=("#e2a04a", "#bd8235"),
            sections=sections
        )

    def _create_help_section(self, parent, title, content, use_monospace=False):
        """Hilfsmethode zum Erstellen einer formatierten Hilfe-Sektion."""
        section_frame = ctk.CTkFrame(parent, corner_radius=12)
        section_frame.pack(fill='x', pady=(0, 20), padx=10)

        # Titel
        ctk.CTkLabel(
            section_frame,
            text=title,
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w"
        ).pack(pady=(20, 12), padx=25, anchor="w")

        # Inhalt
        font_family = "Courier" if use_monospace else None
        ctk.CTkLabel(
            section_frame,
            text=content,
            font=ctk.CTkFont(size=13, family=font_family),
            justify="left",
            anchor="w",
            wraplength=900
        ).pack(pady=(0, 20), padx=25, anchor="w")

        return section_frame

    def _create_back_button(self, parent, command):
        """Hilfsmethode zum Erstellen eines Zurück-Buttons."""
        ctk.CTkButton(
            parent,
            text="← Zurück zur Hilfe-Übersicht",
            command=command,
            width=240,
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40")
        ).pack(pady=(30, 20))

    def _create_modern_help_page(self, title, icon, color, sections):
        """
        Erstellt eine moderne Hilfe-Seite mit interaktiver Navigation.

        Args:
            title: Titel der Hilfe-Seite
            icon: Emoji-Icon für den Header
            color: Tuple mit (light_color, dark_color) für den Header
            sections: Liste von Dictionaries mit 'id', 'icon', 'title', 'content', 'use_monospace'

        Returns:
            Tuple von (main_container, content_scroll_frame, nav_buttons_dict)
        """
        self._clear_content_frame()

        # Hauptcontainer
        main_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Zwei-Spalten-Layout
        main_container.grid_columnconfigure(0, weight=0, minsize=250)  # Navigation
        main_container.grid_columnconfigure(1, weight=1)  # Content
        main_container.grid_rowconfigure(0, weight=1)

        # === LINKE SPALTE: NAVIGATION ===
        nav_container = ctk.CTkFrame(main_container, corner_radius=15, fg_color=("white", "gray17"))
        nav_container.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        # Navigation Header
        nav_header = ctk.CTkFrame(nav_container, corner_radius=12, fg_color=color)
        nav_header.pack(fill='x', padx=10, pady=10)

        ctk.CTkLabel(
            nav_header,
            text=f"{icon}\n{title}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white",
            justify="center"
        ).pack(pady=15)

        # Inhaltsverzeichnis Label mit Untertitel
        toc_frame = ctk.CTkFrame(nav_container, fg_color="transparent")
        toc_frame.pack(fill='x', pady=(15, 5), padx=15)

        ctk.CTkLabel(
            toc_frame,
            text="📑 Inhalt",
            font=ctk.CTkFont(size=17, weight="bold"),
            anchor="w",
            text_color=("gray10", "gray90")
        ).pack(anchor="w")

        ctk.CTkLabel(
            toc_frame,
            text="Wähle ein Thema aus",
            font=ctk.CTkFont(size=11),
            anchor="w",
            text_color=("gray40", "gray70")
        ).pack(anchor="w", pady=(2, 0))

        # Scrollable Navigation
        nav_scroll = ctk.CTkScrollableFrame(
            nav_container,
            fg_color="transparent",
            scrollbar_button_color=("gray60", "gray40")
        )
        nav_scroll.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Zurück-Button in Navigation - moderneres Design
        back_btn = ctk.CTkButton(
            nav_container,
            text="← Zurück zur Übersicht",
            command=self.show_help,
            width=200,
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=12,
            fg_color=color,
            hover_color=(self._darken_color(color[0], 0.85), self._lighten_color(color[1], 1.15)),
            text_color="white"
        )
        back_btn.pack(pady=12, padx=10)

        # === RECHTE SPALTE: CONTENT ===
        content_container = ctk.CTkFrame(main_container, fg_color="transparent")
        content_container.grid(row=0, column=1, sticky="nsew")

        # Content Header - Moderner Gradient-Look
        content_header = ctk.CTkFrame(
            content_container,
            corner_radius=18,
            fg_color=color,
            height=100
        )
        content_header.pack(fill='x', pady=(0, 25))

        # Header Content Container
        header_content = ctk.CTkFrame(content_header, fg_color="transparent")
        header_content.pack(fill='both', expand=True, padx=35, pady=20)

        # Icon im Header
        ctk.CTkLabel(
            header_content,
            text=icon,
            font=ctk.CTkFont(size=42)
        ).pack(side='left', padx=(0, 15))

        # Titel und Untertitel
        title_container = ctk.CTkFrame(header_content, fg_color="transparent")
        title_container.pack(side='left', fill='both', expand=True)

        ctk.CTkLabel(
            title_container,
            text=title,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white",
            anchor="w"
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_container,
            text="Detaillierte Informationen und Anleitungen",
            font=ctk.CTkFont(size=13),
            text_color=("white", "gray90"),
            anchor="w"
        ).pack(anchor='w', pady=(3, 0))

        # Scrollable Content
        content_scroll = ctk.CTkScrollableFrame(
            content_container,
            fg_color="transparent",
            scrollbar_button_color=("gray70", "gray30")
        )
        content_scroll.pack(fill='both', expand=True)

        # Dictionary zum Speichern der Navigation-Buttons und Section-Frames
        nav_buttons = {}
        section_frames = {}

        # Erstelle Sektionen und Navigation-Buttons
        for idx, section in enumerate(sections):
            section_id = section['id']

            # Section Frame im Content-Bereich - Modernes helles Design
            section_frame = ctk.CTkFrame(
                content_scroll,
                corner_radius=16,
                fg_color=("gray98", "gray14"),
                border_width=1,
                border_color=("gray88", "gray25")
            )
            section_frame.pack(fill='x', pady=(0, 18), padx=15)
            section_frames[section_id] = section_frame

            # Icon und Titel Container
            title_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            title_frame.pack(fill='x', pady=(25, 15), padx=30)

            # Icon mit farbigem Hintergrund
            light_bg = self._lighten_color(color[0], 0.85)
            dark_bg = self._darken_color(color[1], 0.7)
            icon_label = ctk.CTkLabel(
                title_frame,
                text=section['icon'],
                font=ctk.CTkFont(size=32),
                width=50,
                height=50,
                corner_radius=10,
                fg_color=(light_bg, dark_bg)
            )
            icon_label.pack(side='left', padx=(0, 15))

            # Titel
            ctk.CTkLabel(
                title_frame,
                text=section['title'],
                font=ctk.CTkFont(size=24, weight="bold"),
                anchor="w",
                text_color=color
            ).pack(side='left', fill='x', expand=True)

            # Trennlinie
            separator = ctk.CTkFrame(
                section_frame,
                height=2,
                fg_color=("gray90", "gray20")
            )
            separator.pack(fill='x', padx=30, pady=(0, 20))

            # Section Content - Bessere Lesbarkeit
            font_family = "Consolas" if section.get('use_monospace', False) else "Segoe UI"
            content_label = ctk.CTkLabel(
                section_frame,
                text=section['content'],
                font=ctk.CTkFont(size=14, family=font_family),
                justify="left",
                anchor="w",
                wraplength=750,
                text_color=("gray15", "gray90")
            )
            content_label.pack(pady=(0, 25), padx=30, anchor="w")

            # Navigation Button
            def create_scroll_command(frame):
                """Closure für scroll-to-section Command"""
                return lambda: self._scroll_to_widget(content_scroll, frame)

            nav_btn = ctk.CTkButton(
                nav_scroll,
                text=f"{section['icon']}  {section['title']}",
                command=create_scroll_command(section_frame),
                width=200,
                height=44,
                font=ctk.CTkFont(size=13, weight="normal"),
                corner_radius=10,
                anchor="w",
                fg_color=("gray95", "gray20"),
                hover_color=(self._lighten_color(color[0], 0.85), self._darken_color(color[1], 0.8)),
                text_color=("gray20", "gray90"),
                border_width=0
            )
            nav_btn.pack(pady=4, padx=8, fill='x')
            nav_buttons[section_id] = nav_btn

        return main_container, content_scroll, nav_buttons

    def _lighten_color(self, hex_color, factor=0.9):
        """Hellt eine Hex-Farbe auf."""
        try:
            # Entferne '#' falls vorhanden
            hex_color = hex_color.lstrip('#')

            # Konvertiere zu RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            # Erhöhe jeden Wert Richtung 255
            r = int(r + (255 - r) * factor)
            g = int(g + (255 - g) * factor)
            b = int(b + (255 - b) * factor)

            # Begrenze auf 0-255
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))

            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color

    def _darken_color(self, hex_color, factor=0.7):
        """Dunkelt eine Hex-Farbe ab."""
        try:
            # Entferne '#' falls vorhanden
            hex_color = hex_color.lstrip('#')

            # Konvertiere zu RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            # Reduziere jeden Wert
            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)

            # Begrenze auf 0-255
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))

            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color

    def _scroll_to_widget(self, scrollable_frame, target_widget):
        """Scrollt ein ScrollableFrame zu einem bestimmten Widget."""
        try:
            # Warte kurz, damit das Layout aktualisiert wird
            self.master.update_idletasks()

            # Hole den internen Frame des ScrollableFrame
            inner_frame = scrollable_frame._parent_frame

            # Berechne die absolute Position des Ziel-Widgets relativ zum inner_frame
            target_y = 0
            widget = target_widget
            while widget != inner_frame and widget is not None:
                target_y += widget.winfo_y()
                widget = widget.master

            # Hole den Canvas aus dem ScrollableFrame
            if hasattr(scrollable_frame, '_parent_canvas'):
                canvas = scrollable_frame._parent_canvas

                # Hole die Höhe des sichtbaren Bereichs
                canvas_height = canvas.winfo_height()

                # Hole die gesamte scrollbare Höhe
                canvas.update_idletasks()
                bbox = canvas.bbox("all")

                if bbox and canvas_height > 0:
                    total_height = bbox[3] - bbox[1]

                    if total_height > canvas_height:
                        # Berechne die Scroll-Position (normalisiert zwischen 0 und 1)
                        # Scrolle so, dass das Widget oben im sichtbaren Bereich ist
                        scroll_position = target_y / total_height

                        # Begrenze die Position auf 0-1 und füge einen kleinen Offset hinzu
                        scroll_position = max(0, min(1, scroll_position - 0.05))

                        # Scrolle zur berechneten Position
                        canvas.yview_moveto(scroll_position)
        except Exception as e:
            print(f"Scroll-Fehler: {e}")
            import traceback
            traceback.print_exc()

    # -----------------------------------------------------------------------------------
    # KATEGORIEN & KARTENVERWALTUNG
    # -----------------------------------------------------------------------------------
    # Fügen Sie diese Funktion zur FlashcardApp-Klasse hinzu
       # Diese Methoden gehÃƒÂ¶ren alle direkt in die FlashcardApp-Klasse

    # -----------------------------------------------------------------------------------
    # KARTENAUSWAHL MODERNISIEREN
    # -----------------------------------------------------------------------------------
    def select_cards_submenu(self):
        """
        Zeigt das AuswahlmenÃƒÂ¼ für Karten an, inklusive:
        - Kategoriefilter
        - Unterkategoriefilter
        - Fortschritt (Gekonnt / Nicht gekonnt)
        - Aufteilung in mehrere Session-Teile
        - Filterung nach Schwierigkeitsbereich (min/max)
        """
        # 1) Alte Inhalte entfernen
        self._clear_content_frame()

        # 2) Header
        header_frame = tk.Frame(self.content_frame, bg=self.default_bg)
        header_frame.pack(fill='x', pady=(30, 20))
        tk.Label(
            header_frame,
            text="Karten auswÃƒÂ¤hlen",
            font=("Segoe UI", 18, "bold"),
            bg=self.default_bg
        ).pack()

        # 3) Filter-Frame (Basisfilter)
        self.filter_frame = tk.Frame(self.content_frame, bg=self.default_bg)
        self.filter_frame.pack(fill='x', pady=10)

        # --- Variablen für die Filter ---
        self.category_var = tk.StringVar(value="Alle")
        self.subcategory_var = tk.StringVar(value="Alle")
        self.progress_var = tk.StringVar(value="Alle")

        # 3a) Kategorie-Dropdown
        tk.Label(self.filter_frame, text="Kategorie:", bg=self.default_bg).pack(side=tk.LEFT, padx=(0, 5))
        category_options = ["Alle"] + sorted(self.data_manager.categories.keys())
        category_dropdown = ttk.Combobox(
            self.filter_frame,
            textvariable=self.category_var,
            values=category_options,
            state="readonly"
        )
        category_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        # 3b) Unterkategorie-Dropdown
        tk.Label(self.filter_frame, text="Unterkategorie:", bg=self.default_bg).pack(side=tk.LEFT, padx=(0, 5))
        self.subcategory_dropdown = ttk.Combobox(
            self.filter_frame,
            textvariable=self.subcategory_var,
            values=["Alle"],
            state="readonly"
        )
        self.subcategory_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        # 3c) Fortschritt-Dropdown
        tk.Label(self.filter_frame, text="Fortschritt:", bg=self.default_bg).pack(side=tk.LEFT, padx=(0, 5))
        progress_options = ["Alle", "Gekonnt", "Nicht gekonnt"]
        progress_dropdown = ttk.Combobox(
            self.filter_frame,
            textvariable=self.progress_var,
            values=progress_options,
            state="readonly"
        )
        progress_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        # 4) Difficulty-Frame anlegen
        difficulty_frame = tk.Frame(self.content_frame, bg=self.default_bg)
        difficulty_frame.pack(fill='x', pady=10)

        # 4a) Inneres Frame für Session-Breaker-Auswahl
        breaker_frame = tk.Frame(difficulty_frame, bg=self.default_bg)
        breaker_frame.pack(fill='x', pady=10)

        tk.Label(
            breaker_frame,
            text="Session in Teile aufteilen:",
            bg=self.default_bg,
            font=(self.appearance_settings.font_family, 12, "bold")
        ).pack(pady=(10, 5))

        self.session_parts = tk.IntVar(value=1)
        parts_menu = ttk.Combobox(
            breaker_frame,
            textvariable=self.session_parts,
            values=[1, 2, 3, 4],
            state="readonly",
            width=10
        )
        parts_menu.pack(pady=5)

        # 4b) ÃƒÅ“berschrift für Schwierigkeitsbereich
        tk.Label(
            difficulty_frame,
            text="Schwierigkeitsbereich:",
            bg=self.default_bg,
            font=(self.appearance_settings.font_family, 12, "bold")
        ).pack(pady=(10, 5))

        # 4c) Kurze Legende
        legend_frame = tk.Frame(difficulty_frame, bg=self.default_bg)
        legend_frame.pack(fill='x', pady=(0, 10))
        tk.Label(
            legend_frame,
            text="1 = Sehr leicht | 2 = Leicht | 3 = Mittel | 4 = Schwer | 5 = Sehr schwer",
            bg=self.default_bg,
            font=(self.appearance_settings.font_family, 10)
        ).pack()

        # 4d) Scale-Frame für min-/max-Difficulty
        scale_frame = tk.Frame(difficulty_frame, bg=self.default_bg)
        scale_frame.pack(fill='x', padx=20)

        # --- Min-Difficulty ---
        min_frame = tk.Frame(scale_frame, bg=self.default_bg)
        min_frame.pack(side=tk.LEFT, expand=True)

        tk.Label(min_frame, text="Von:", bg=self.default_bg).pack(side=tk.LEFT, padx=(0, 5))
        self.min_difficulty_label = tk.Label(min_frame, text="1.0", width=3, bg=self.default_bg)
        self.min_difficulty_label.pack(side=tk.LEFT)

        self.min_difficulty_var = tk.DoubleVar(value=1.0)
        min_scale = ttk.Scale(
            min_frame,
            from_=1.0,
            to=5.0,
            variable=self.min_difficulty_var,
            orient='horizontal',
            length=200,
            command=lambda x: self.update_difficulty_label(self.min_difficulty_label, self.min_difficulty_var.get())
        )
        min_scale.pack(side=tk.LEFT, padx=5)

        # --- Max-Difficulty ---
        max_frame = tk.Frame(scale_frame, bg=self.default_bg)
        max_frame.pack(side=tk.LEFT, expand=True)

        tk.Label(max_frame, text="Bis:", bg=self.default_bg).pack(side=tk.LEFT, padx=(20, 5))
        self.max_difficulty_label = tk.Label(max_frame, text="5.0", width=3, bg=self.default_bg)
        self.max_difficulty_label.pack(side=tk.LEFT)

        self.max_difficulty_var = tk.DoubleVar(value=5.0)
        max_scale = ttk.Scale(
            max_frame,
            from_=1.0,
            to=5.0,
            variable=self.max_difficulty_var,
            orient='horizontal',
            length=200,
            command=lambda x: self.update_difficulty_label(self.max_difficulty_label, self.max_difficulty_var.get())
        )
        max_scale.pack(side=tk.LEFT, padx=5)

        # 5) Grid-Frame zur Anzeige der Karten
        self.grid_frame = tk.Frame(self.content_frame, bg=self.default_bg)
        self.grid_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)

        # 6) Button-Frame (z. B. "Alle auswählen" / "Session starten")
        button_frame = tk.Frame(self.content_frame, bg=self.default_bg)
        button_frame.pack(pady=10, fill='x', padx=20)

        self.all_selected = False  # Toggle-Variable für "Alle auswählen"
        def select_all_filtered():
            """
            Wechselt den Zustand (alle an/aus) für die gefilterten Karten.
            """
            self.all_selected = not self.all_selected
            # self.selected_cards_var = [(Flashcard, BooleanVar), ...]
            for card_var in self.selected_cards_var:
                card_var[1].set(self.all_selected)

            select_all_btn.configure(text="Alle abwÃƒÂ¤hlen" if self.all_selected else "Alle auswÃƒÂ¤hlen")

        select_all_btn = ttk.Button(
            button_frame,
            text="Alle auswÃƒÂ¤hlen",
            command=select_all_filtered
        )
        select_all_btn.pack(side=tk.LEFT, padx=5)

        # Button zum Starten der Session
        start_session_btn = ttk.Button(
            button_frame,
            text="Lernsession starten",
            command=self.confirm_card_selection
        )
        start_session_btn.pack(side=tk.RIGHT, padx=5)

        # -----------------------------
        # 7) Update-Funktionen
        # -----------------------------
        def update_filter(*args):
            """
            Wendet alle aktuellen Filter an und zeigt die Karten an.
            """
            cat = None if self.category_var.get() == "Alle" else self.category_var.get()
            subcat = None if self.subcategory_var.get() == "Alle" else self.subcategory_var.get()
            prog = None if self.progress_var.get() == "Alle" else self.progress_var.get()
            difficulty_range = (self.min_difficulty_var.get(), self.max_difficulty_var.get())

            filtered_cards = self.data_manager.filter_flashcards(
                category=cat,
                subcategory=subcat,
                progress=prog,
                difficulty_range=difficulty_range
            )

            # Anzeige der Karten in self.grid_frame
            self.display_cards(filtered_cards)

        def update_subcategories(*args):
            """
            Aktualisiert die Unterkategorien, wenn Kategorie gewechselt wird.
            """
            selected_cat = self.category_var.get()
            if selected_cat == "Alle":
                subcats = ["Alle"]
            else:
                subcats = ["Alle"] + sorted(self.data_manager.categories.get(selected_cat, {}).keys())

            self.subcategory_dropdown.config(values=subcats)
            self.subcategory_var.set("Alle")
            # Wenn Kategorie wechselt, Filter nochmal aufrufen
            update_filter()

        # -----------------------------
        # 8) Bindings und initialer Aufruf
        # -----------------------------
        self.category_var.trace_add('write', update_subcategories)
        self.subcategory_var.trace_add('write', update_filter)
        self.progress_var.trace_add('write', update_filter)
        self.min_difficulty_var.trace_add('write', update_filter)
        self.max_difficulty_var.trace_add('write', update_filter)

        # Beim ersten Ãƒâ€“ffnen gleich einmal Filter anwenden,
        # damit schon Karten angezeigt werden (z.Ã¢â‚¬Â¯B. Alle).
        update_filter()
        
        
    def init_session_with_parts(self):
        """
        Initialisiert eine neue Lernsession mit der gewÃƒÂ¤hlten Teilung.
        Verwaltet die Session-States und bereitet die ersten Karten vor.
        """
        try:
            # Hole die ausgewÃƒÂ¤hlten Karten
            selected_cards = [fc for (fc, var) in self.selected_cards_var if var.get()]
            if not selected_cards:
                messagebox.showinfo("Info", "Keine Karten ausgewÃƒÂ¤hlt.")
                return

            # Berechne die Kartenzahl pro Teil
            total_parts = self.session_parts.get()
            total_cards = len(selected_cards)
            cards_per_part = max(1, total_cards // total_parts)  # Mindestens 1 Karte pro Teil
            
            # Initialisiere erweiterte Session-Verwaltung
            self.session_state = {
                'all_cards': selected_cards.copy(),  # Kopie der Original-Liste
                'total_parts': total_parts,
                'current_part': 1,
                'cards_per_part': cards_per_part,
                'incorrect_current': [],  # Falsche Karten im aktuellen Teil
                'incorrect_all': [],      # Alle falschen Karten der Session
                'remaining_cards': selected_cards[:cards_per_part].copy(),  # Erste Teilmenge
                'session_results': [],    # Alle Ergebnisse der Session
                'is_repeating': False,    # Flag für Wiederholungsmodus
                'repeat_in_progress': False,  # Flag für laufende Wiederholung
                'repeat_results': []      # Ergebnisse der Wiederholungen
            }
            
            # Erste Teilmenge für die Session vorbereiten
            self.cards_this_session = self.session_state['remaining_cards']
            self.session_results = []

            # Zeitmessung starten falls aktiviert
            if self.appearance_settings.track_learning_time:
                self.session_start_time = datetime.datetime.now()
                logging.info(f"Lernsession gestartet: {self.session_start_time}")
            
            # Starte mit der ersten Karte
            self.show_card_window()
            
        except Exception as e:
            logging.error(f"Fehler bei Session-Initialisierung: {e}")
            messagebox.showerror("Fehler", "Session konnte nicht initialisiert werden.")
            self.create_main_menu()
        
    def confirm_card_selection(self):
        selected_cards = [fc for (fc, var) in self.selected_cards_var if var.get()]
        if not selected_cards:
            messagebox.showinfo("Info", "Keine Karten ausgewÃƒÂ¤hlt.")
            return

        # Navigation aktualisieren
        self.navigation_history.append(self.current_view)
        self.current_view = 'learning_session'

        self.init_session_with_parts()
    def show_break_menu(self):
        """Zeigt das MenÃƒÂ¼ zwischen den Session-Teilen an."""
        self._clear_content_frame()
        
        # Header
        tk.Label(
            self.content_frame,
            text=f"Teil {self.session_state['current_part']} von {self.session_state['total_parts']} abgeschlossen!",
            font=("Segoe UI", 18, "bold"),
            bg=self.default_bg
        ).pack(pady=20)

        # Status-Informationen
        status_frame = tk.Frame(self.content_frame, bg=self.default_bg)
        status_frame.pack(pady=10)

        # Zeige aktuelle Statistiken des Teils
        current_results = self.session_results
        correct_count = sum(1 for _, _, _, is_correct in current_results if is_correct)
        total = len(current_results)
        
        stats_text = f"Ergebnis dieses Teils: {correct_count}/{total} richtig"
        tk.Label(
            status_frame,
            text=stats_text,
            font=("Segoe UI", 14),
            bg=self.default_bg
        ).pack(pady=10)

        # Zeige Statistik für aktuellen Teil
        if self.session_state['incorrect_current']:
            tk.Label(
                status_frame,
                text=f"Nicht gekannte Karten in diesem Teil: {len(self.session_state['incorrect_current'])}",
                bg=self.default_bg,
                font=("Segoe UI", 12)
            ).pack(pady=5)

        # Zeige Gesamtstatistik
        if self.session_state['incorrect_all']:
            tk.Label(
                status_frame,
                text=f"Nicht gekannte Karten insgesamt: {len(self.session_state['incorrect_all'])}",
                bg=self.default_bg,
                font=("Segoe UI", 12)
            ).pack(pady=5)

        # Button Frame
        button_frame = tk.Frame(self.content_frame, bg=self.default_bg)
        button_frame.pack(pady=20)

        # Optionen Buttons
        if self.session_state['incorrect_current']:
            ModernButton(
                button_frame,
                text=f"Nicht gekannte aus Teil {self.session_state['current_part']} wiederholen",
                command=lambda: self.start_repeat_session(self.session_state['incorrect_current']),
                width=40,
                style=ButtonStyle.PRIMARY.value
            ).pack(pady=5)

        # Wenn letzter Teil
        if self.session_state['current_part'] == self.session_state['total_parts']:
            if self.session_state['incorrect_all']:
                ModernButton(
                    button_frame,
                    text="Alle nicht gekannten wiederholen",
                    command=lambda: self.start_repeat_session(self.session_state['incorrect_all']),
                    width=40,
                    style=ButtonStyle.PRIMARY.value
                ).pack(pady=5)
                
            ModernButton(
                button_frame,
                text="Zur Zusammenfassung",
                command=self.show_session_summary,
                width=40,
                style=ButtonStyle.SECONDARY.value
            ).pack(pady=5)
        else:
            # Wenn noch weitere Teile kommen
            ModernButton(
                button_frame,
                text="Weiter zum nÃƒÂ¤chsten Teil",
                command=self.continue_session,
                width=40,
                style=ButtonStyle.PRIMARY.value
            ).pack(pady=5)
    def continue_session(self):
        """Setzt die Session mit dem nÃƒÂ¤chsten Teil fort."""
        # Berechne Start- und Endindex für den nÃƒÂ¤chsten Teil
        start_idx = self.session_state['current_part'] * self.session_state['cards_per_part']
        end_idx = start_idx + self.session_state['cards_per_part']
        
        # Teil-ZÃƒÂ¤hler erhÃƒÂ¶hen
        self.session_state['current_part'] += 1
        
        # Neue Karten für diesen Teil
        self.session_state['remaining_cards'] = self.session_state['all_cards'][start_idx:end_idx].copy()
        # Liste für falsche Karten des aktuellen Teils zurücksetzen
        self.session_state['incorrect_current'] = []
        
        # Session fortsetzen
        self.cards_this_session = self.session_state['remaining_cards']
        self.show_card_window()
    def display_cards(self, flashcards):
        # Entferne zuerst alle vorhandenen Widgets aus dem grid_frame
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        # Container für die Scrollbar und Canvas
        self.grid_frame.grid_columnconfigure(0, weight=1)  # Wichtig: LÃƒÂ¤sst den Container die volle Breite nutzen
        
        # Scrollbar und Canvas
        canvas = tk.Canvas(self.grid_frame, bg=self.default_bg)
        scrollbar = ttk.Scrollbar(self.grid_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.default_bg)
        
        # Konfiguriere Scrolling
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Grid für Scrollbar und Canvas
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Erstelle scrollbaren Bereich
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_width())
        
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Passe die Breite des Fensters an die Canvas-Breite an
            width = canvas.winfo_width()
            canvas.itemconfig(canvas_frame, width=width)
            
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_frame, width=e.width))

        if not flashcards:
            tk.Label(
                scrollable_frame,
                text="Keine Flashcards verfügbar.",
                font=(self.appearance_settings.font_family, 12),
                bg=self.default_bg,
                fg="red"
            ).pack(pady=20)
            return

        self.selected_cards_var = []
        cards_per_row = 4
        for idx, fc in enumerate(flashcards):
            var = tk.BooleanVar(value=False)
            self.selected_cards_var.append((fc, var))

            # Berechne Position im Grid
            row = idx // cards_per_row
            col = idx % cards_per_row
            
            card_frame = tk.Frame(scrollable_frame, bg=self.appearance_settings.text_bg_color, relief=tk.RAISED, borderwidth=1)
            card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # Wichtig: Konfiguriere die Spaltengewichte für gleichmÃƒÂ¤ÃƒÅ¸ige Verteilung
            for i in range(cards_per_row):
                scrollable_frame.grid_columnconfigure(i, weight=1)

            # Rest des Codes bleibt unverändert
            tags_display = ", ".join(fc.tags) if fc.tags else "Keine Tags"
            tk.Label(
                card_frame,
                text=fc.question,
                wraplength=200,
                bg=self.appearance_settings.text_bg_color,
                fg=self.appearance_settings.text_fg_color,
                font=(self.appearance_settings.font_family, 12, "bold")
            ).pack(padx=5, pady=5)
            
            tk.Label(
                card_frame,
                text=f"Fortschritt: {fc.consecutive_correct}x\n" +
                    f"Schwierigkeit: {fc.difficulty_rating:.1f}/5.0\n" +
                    f"Tags: {tags_display}",
                font=(self.appearance_settings.font_family, 10, "italic"),
                bg=self.appearance_settings.text_bg_color,
                fg=self.appearance_settings.text_fg_color
            ).pack(padx=5, pady=5)

            toggle_btn = tk.Checkbutton(
                card_frame,
                variable=var,
                bg=self.appearance_settings.text_bg_color,
                fg=self.appearance_settings.text_fg_color
            )
            toggle_btn.pack(pady=5)

    # -----------------------------------------------------------------------------------
    # STATISTIK-FUNKTIONEN
    # -----------------------------------------------------------------------------------
    def show_statistics(self):
        """Hauptansicht für die Statistiken mit modernem Design."""
        self._clear_content_frame()

        # Moderner Header mit Gradient-Hintergrund
        header_container = ctk.CTkFrame(
            self.content_frame,
            fg_color='#8b5cf6',
            corner_radius=0,
            height=110
        )
        header_container.pack(fill='x', pady=(0, 20))
        header_container.pack_propagate(False)

        header_content = ctk.CTkFrame(header_container, fg_color='transparent')
        header_content.place(relx=0.5, rely=0.5, anchor='center')

        # Icon und Titel
        icon_title_frame = ctk.CTkFrame(header_content, fg_color='transparent')
        icon_title_frame.pack()

        ctk.CTkLabel(
            icon_title_frame,
            text="📊",
            font=ctk.CTkFont(size=36),
            text_color='#ffffff'
        ).pack(side='left', padx=(0, 15))

        title_frame = ctk.CTkFrame(icon_title_frame, fg_color='transparent')
        title_frame.pack(side='left')

        ctk.CTkLabel(
            title_frame,
            text="Statistiken & Auswertungen",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color='#ffffff'
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_frame,
            text="Analysiere deine Lernfortschritte und Erfolge",
            font=ctk.CTkFont(size=13),
            text_color='#e9d5ff'
        ).pack(anchor='w')

        # Hauptcontainer für Tabs
        main_container = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        main_container.pack(fill='both', expand=True, padx=20, pady=10)

        # Tab-Button Container
        tab_button_frame = ctk.CTkFrame(
            main_container,
            fg_color='#f3f4f6',
            corner_radius=12,
            height=60
        )
        tab_button_frame.pack(fill='x', pady=(0, 15))
        tab_button_frame.pack_propagate(False)

        # Content Container für die verschiedenen Tab-Inhalte
        content_container = ctk.CTkFrame(
            main_container,
            fg_color='transparent'
        )
        content_container.pack(fill='both', expand=True)

        # Tab-Frames erstellen
        overview_frame = ctk.CTkFrame(content_container, fg_color='transparent')
        category_frame = ctk.CTkFrame(content_container, fg_color='transparent')
        progress_frame = ctk.CTkFrame(content_container, fg_color='transparent')

        # Tab-State verwalten
        self.current_stats_tab = 'overview'
        self.stats_tab_buttons = {}

        def switch_tab(tab_name, frame):
            """Wechselt zwischen Tabs."""
            # Verstecke alle Frames
            overview_frame.pack_forget()
            category_frame.pack_forget()
            progress_frame.pack_forget()

            # Zeige ausgewählten Frame
            frame.pack(fill='both', expand=True)

            # Update Button-Styles
            for btn_name, btn in self.stats_tab_buttons.items():
                if btn_name == tab_name:
                    btn.configure(
                        fg_color='#8b5cf6',
                        hover_color='#7c3aed',
                        text_color='#ffffff'
                    )
                else:
                    btn.configure(
                        fg_color='transparent',
                        hover_color='#e5e7eb',
                        text_color='#6b7280'
                    )

            self.current_stats_tab = tab_name

        # Tab-Buttons erstellen
        button_container = ctk.CTkFrame(tab_button_frame, fg_color='transparent')
        button_container.place(relx=0.5, rely=0.5, anchor='center')

        tabs = [
            ('overview', '📈 Gesamtübersicht', overview_frame),
            ('category', '📁 Nach Kategorien', category_frame),
            ('progress', '📊 Fortschrittsverlauf', progress_frame)
        ]

        for tab_id, tab_text, tab_frame in tabs:
            btn = ctk.CTkButton(
                button_container,
                text=tab_text,
                command=lambda t=tab_id, f=tab_frame: switch_tab(t, f),
                width=200,
                height=40,
                corner_radius=10,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color='transparent' if tab_id != 'overview' else '#8b5cf6',
                hover_color='#e5e7eb' if tab_id != 'overview' else '#7c3aed',
                text_color='#6b7280' if tab_id != 'overview' else '#ffffff'
            )
            btn.pack(side='left', padx=5)
            self.stats_tab_buttons[tab_id] = btn

        # Tabs mit Inhalt füllen
        self._create_overview_stats(overview_frame)
        self._create_category_stats(category_frame)
        self._create_progress_stats(progress_frame)

        # Zeige initial Overview
        overview_frame.pack(fill='both', expand=True)

        # Zurück-Button
        back_btn = ctk.CTkButton(
            self.content_frame,
            text="🏠 Zurück zum Hauptmenü",
            command=self.create_main_menu,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color='#6b7280',
            hover_color='#4b5563'
        )
        back_btn.pack(pady=15)
        self.sidebar_buttons["back_to_main_from_statistics"] = back_btn
        self.highlight_active_button('statistik')

    def _create_overview_stats(self, parent_frame):
        """Erstellt die Gesamtübersicht im modernen Design."""
        # Scrollbarer Container
        stats_container = ctk.CTkScrollableFrame(parent_frame, fg_color='transparent')
        stats_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Statistiken berechnen
        total_cards_in_system = len(self.data_manager.flashcards)
        total_cards_asked = sum(stat['cards_total'] for stat in self.data_manager.stats
                            if isinstance(stat, dict) and 'cards_total' in stat)
        correct_cards = sum(stat['cards_correct'] for stat in self.data_manager.stats
                        if isinstance(stat, dict) and 'cards_correct' in stat)
        total_sessions = len([stat for stat in self.data_manager.stats
                            if isinstance(stat, dict) and 'cards_total' in stat])
        success_rate = (correct_cards / total_cards_asked * 100) if total_cards_asked > 0 else 0
        total_learning_time = sum(stat['total_time'] for stat in self.data_manager.stats
                                if isinstance(stat, dict) and 'total_time' in stat)

        # Statistik-Karten mit Icons
        stats_data = [
            ("🎯", "Lernsitzungen", f"{total_sessions}", "#3b82f6"),
            ("📚", "Karten im System", f"{total_cards_in_system}", "#10b981"),
            ("✏️", "Karten abgefragt", f"{total_cards_asked}", "#f59e0b"),
            ("✓", "Korrekt beantwortet", f"{correct_cards}", "#8b5cf6"),
            ("📈", "Erfolgsquote", f"{success_rate:.1f}%", "#ec4899"),
            ("⏱️", "Gesamte Lernzeit", self.data_manager.format_learning_time(total_learning_time), "#6366f1"),
        ]

        # Grid für Statistik-Karten (3 Spalten)
        for idx, (icon, title, value, color) in enumerate(stats_data):
            row = idx // 3
            col = idx % 3

            # Statistik-Karte
            card = ctk.CTkFrame(
                stats_container,
                fg_color=color,
                corner_radius=15,
                border_width=0
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # Icon
            ctk.CTkLabel(
                card,
                text=icon,
                font=ctk.CTkFont(size=36),
                text_color='#ffffff'
            ).pack(pady=(20, 5))

            # Titel
            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color='#ffffff'
            ).pack(pady=(0, 5))

            # Wert
            ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=32, weight="bold"),
                text_color='#ffffff'
            ).pack(pady=(5, 20))

        # Grid-Konfiguration
        for i in range(3):
            stats_container.grid_columnconfigure(i, weight=1, minsize=250)

    def _create_category_stats(self, parent_frame):
        """Erstellt die Kategoriestatistik mit Dropdown-Funktion."""
        # Container mit zwei Spalten
        container = ctk.CTkFrame(parent_frame)
        container.pack(fill='both', expand=True, padx=20, pady=20)
        container.grid_columnconfigure(1, weight=3)
        container.grid_rowconfigure(0, weight=1)
        
        # Linke Spalte: Kategorieliste mit Dropdowns
        left_frame = ctk.CTkFrame(container)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Suchfeld
        search_frame = ctk.CTkFrame(left_frame)
        search_frame.pack(fill='x', padx=10, pady=10)
        
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Kategorie suchen...",
            textvariable=search_var
        )
        search_entry.pack(fill='x', padx=5)
        
        # Scrollbare Liste für Kategorien
        list_frame = ctk.CTkScrollableFrame(left_frame)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Rechte Spalte: Detailansicht
        right_frame = ctk.CTkFrame(container)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Dictionary für die Dropdown-Status und Buttons
        self.category_dropdowns = {}
        self.category_buttons = []

        def show_subcategory_stats(category, subcategory):
            """Zeigt die Statistiken für eine Subkategorie an."""
            for widget in right_frame.winfo_children():
                widget.destroy()

            stats = self.stats_manager.get_subcategory_statistics(category, subcategory)
            cards_in_subcategory = len([card for card in self.data_manager.flashcards 
                                    if card.category.lower() == category.lower() 
                                    and card.subcategory.lower() == subcategory.lower()])

            # Header
            header_frame = ctk.CTkFrame(right_frame)
            header_frame.pack(fill='x', padx=20, pady=10)
            
            ctk.CTkLabel(
                header_frame,
                text=f"{subcategory}",
                font=ctk.CTkFont(size=24, weight="bold")
            ).pack(side='left', padx=10)
            
            ctk.CTkLabel(
                header_frame,
                text=f"in {category}",
                font=ctk.CTkFont(size=16)
            ).pack(side='left', padx=5)
            
            # Stats Grid
            stats_frame = ctk.CTkFrame(right_frame)
            stats_frame.pack(fill='both', expand=True, padx=20, pady=10)

            stats_items = [
                ("Karten in Subkategorie", cards_in_subcategory),
                ("Karten abgefragt", stats["total_attempts"]),
                ("Richtig beantwortet", stats["total_correct"]),
                ("Erfolgsquote", f"{stats['success_rate']:.1f}%"),
                ("Sitzungen", stats["total_sessions"]),
                ("Lernzeit", self.data_manager.format_learning_time(stats['total_learning_time']))
            ]

            for i, (label, value) in enumerate(stats_items):
                stats_frame.grid_columnconfigure((0, 1), weight=1)
                
                ctk.CTkLabel(
                    stats_frame,
                    text=label,
                    font=ctk.CTkFont(size=14)
                ).grid(row=i, column=0, padx=10, pady=10, sticky="w")
                
                ctk.CTkLabel(
                    stats_frame,
                    text=str(value),
                    font=ctk.CTkFont(size=14, weight="bold")
                ).grid(row=i, column=1, padx=10, pady=10, sticky="e")

 

        def show_category_stats(category):
            """Zeigt die Statistiken für eine Kategorie an."""
            for widget in right_frame.winfo_children():
                widget.destroy()
                
            stats = self.stats_manager.get_category_statistics(category)
            cards_in_category = len([card for card in self.data_manager.flashcards 
                                if card.category.lower() == category.lower()])
            
            # Titel
            ctk.CTkLabel(
                right_frame,
                text=f"Statistiken für {category}",
                font=ctk.CTkFont(size=20, weight="bold")
            ).pack(pady=20)
            
            # Stats Grid
            stats_grid = ctk.CTkFrame(right_frame)
            stats_grid.pack(fill='both', expand=True, padx=20, pady=20)
            
            stats_items = [
                ("Karten in Kategorie", cards_in_category),
                ("Karten abgefragt", stats["total_attempts"]),
                ("Richtig beantwortet", stats["total_correct"]),
                ("Erfolgsquote", f"{stats['success_rate']:.1f}%"),
                ("Sitzungen", stats["total_sessions"]),
                ("Lernzeit", self.data_manager.format_learning_time(stats['total_learning_time']))
            ]
            
            for i, (label, value) in enumerate(stats_items):
                stats_grid.grid_columnconfigure((0, 1), weight=1)
                
                ctk.CTkLabel(
                    stats_grid,
                    text=label,
                    font=ctk.CTkFont(size=14)
                ).grid(row=i, column=0, padx=10, pady=10, sticky="w")
                
                ctk.CTkLabel(
                    stats_grid,
                    text=str(value),
                    font=ctk.CTkFont(size=14, weight="bold")
                ).grid(row=i, column=1, padx=10, pady=10, sticky="e")
        
        # Kategorien mit Dropdowns erstellen
        categories = sorted(self.data_manager.categories.keys())
        for category in categories:
            # Frame für Kategorie und ihre Dropdowns mit minimaler HÃƒÂ¶he
            category_frame = ctk.CTkFrame(list_frame, fg_color="transparent", height=40)
            category_frame.pack(fill='x', pady=2)  # Minimaler Abstand zwischen Kategorien
            
            # Haupt-Kategorie-Button
            category_btn = ctk.CTkButton(
                category_frame,
                text=category,
                command=lambda c=category: show_category_stats(c),
                font=ctk.CTkFont(size=13),
                height=32,
                fg_color=("#3B82F6", "#2563EB"),
                hover_color=("#2563EB", "#1D4ED8"),
                text_color="#000000"  # Schwarze Schrift
            )
            category_btn.pack(fill='x', pady=(0, 0))  # Kein vertikaler Abstand
            self.category_buttons.append((category_btn, category))
            
            # Frame für Dropdown-Inhalt
            dropdown_frame = ctk.CTkFrame(category_frame, fg_color="transparent")
            dropdown_frame.pack(fill='x', pady=0)  # Kein vertikaler Abstand
            def toggle_subcategories(category, dropdown_frame):
                """Verbesserte Toggle-Funktion mit dynamischen Abständen"""
                if category not in self.category_dropdowns:
                    return
                    
                state = self.category_dropdowns[category]
                toggle_btn = state["toggle_btn"]
                category_frame = state["category_frame"]
                is_open = state["is_open"]
                
                if is_open:
                    # Schließen
                    toggle_btn.configure(text="▼")
                    for widget in dropdown_frame.winfo_children():
                        widget.destroy()
                    category_frame.pack_configure(pady=2)  # Minimaler Abstand beim Schließen
                    state["is_open"] = False
                else:
                    # Öffnen
                    toggle_btn.configure(text="▲")
                    subcategories = sorted(self.data_manager.categories[category].keys())
                    category_frame.pack_configure(pady=(2, 10))  # Mehr Abstand beim Öffnen
                    
                    for i, subcat in enumerate(subcategories):
                        subcat_btn = ctk.CTkButton(
                            dropdown_frame,
                            text=f"  Ã¢â€ Â³ {subcat}",
                            command=lambda c=category, s=subcat: show_subcategory_stats(c, s),
                            font=ctk.CTkFont(size=12),
                            height=25,
                            fg_color="transparent",
                            hover_color=("#E5E7EB", "#374151"),
                            text_color="#000000",  # Schwarze Schrift für Subkategorien
                            corner_radius=6,
                            anchor="w"
                        )
                        self.master.after(i * 50, lambda btn=subcat_btn: btn.pack(fill='x', pady=1, padx=(20, 0)))
                    state["is_open"] = True
            
            # Dropdown Toggle Button
            toggle_btn = ctk.CTkButton(
                category_btn,
                text="Ã¢â€“Â¼",
                width=20,
                command=lambda c=category, f=dropdown_frame: toggle_subcategories(c, f),
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                hover_color=("#E5E7EB", "#374151"),
                text_color="#000000",  # Schwarze Schrift für den Toggle-Button
                corner_radius=4
            )
            toggle_btn.place(relx=0.95, rely=0.5, anchor="center")
            
            # Speichere alle relevanten Informationen
            self.category_dropdowns[category] = {
                "is_open": False,
                "toggle_btn": toggle_btn,
                "dropdown_frame": dropdown_frame,
                "category_frame": category_frame
            }
        def filter_categories(*args):
            """Filtert die Kategorien basierend auf der Sucheingabe."""
            search_term = search_var.get().lower()
            for btn, category in self.category_buttons:
                if search_term in category.lower():
                    btn.pack(fill='x', pady=2)
                else:
                    btn.pack_forget()
        
        search_var.trace('w', filter_categories)
        
        # Initial die erste Kategorie anzeigen
        if categories:
            show_category_stats(categories[0])


    def _create_progress_stats(self, parent_frame):
        """Erstellt die Fortschrittsverlauf-Ansicht im modernen Design."""
        # Scrollbarer Container
        progress_container = ctk.CTkScrollableFrame(parent_frame, fg_color='transparent')
        progress_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Header
        header_frame = ctk.CTkFrame(
            progress_container,
            fg_color='#8b5cf6',
            corner_radius=15
        )
        header_frame.pack(fill='x', padx=10, pady=(10, 20))

        ctk.CTkLabel(
            header_frame,
            text="📊 Dein Lernfortschritt im Zeitverlauf",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color='#ffffff'
        ).pack(pady=20)

        # Berechne Statistiken nach Datum
        daily_stats = {}
        for stat in self.data_manager.stats:
            if isinstance(stat, dict) and 'date' in stat:
                date = stat['date']
                if date not in daily_stats:
                    daily_stats[date] = {
                        'total': 0,
                        'correct': 0,
                        'sessions': 0,
                        'time': 0
                    }
                daily_stats[date]['total'] += stat.get('cards_total', 0)
                daily_stats[date]['correct'] += stat.get('cards_correct', 0)
                daily_stats[date]['sessions'] += 1
                daily_stats[date]['time'] += stat.get('total_time', 0)

        if not daily_stats:
            # Keine Daten verfügbar
            no_data_frame = ctk.CTkFrame(
                progress_container,
                fg_color='#f3f4f6',
                corner_radius=15
            )
            no_data_frame.pack(fill='both', expand=True, padx=10, pady=10)

            ctk.CTkLabel(
                no_data_frame,
                text="📭",
                font=ctk.CTkFont(size=64),
                text_color='#9ca3af'
            ).pack(pady=(40, 10))

            ctk.CTkLabel(
                no_data_frame,
                text="Noch keine Lernstatistiken vorhanden",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color='#6b7280'
            ).pack(pady=(0, 5))

            ctk.CTkLabel(
                no_data_frame,
                text="Starte deine erste Lernsitzung, um Fortschritte zu sehen!",
                font=ctk.CTkFont(size=14),
                text_color='#9ca3af'
            ).pack(pady=(0, 40))
        else:
            # Sortiere Daten nach Datum
            sorted_dates = sorted(daily_stats.keys(), reverse=True)

            # Zeige letzte 10 Tage
            for date in sorted_dates[:10]:
                stats = daily_stats[date]
                success_rate = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0

                # Tag-Container
                day_frame = ctk.CTkFrame(
                    progress_container,
                    fg_color='white',
                    corner_radius=12,
                    border_width=2,
                    border_color='#e5e7eb'
                )
                day_frame.pack(fill='x', padx=10, pady=5)

                # Datum
                date_label = ctk.CTkFrame(
                    day_frame,
                    fg_color='#8b5cf6',
                    corner_radius=10,
                    width=120
                )
                date_label.pack(side='left', padx=15, pady=15)

                ctk.CTkLabel(
                    date_label,
                    text=date,
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color='#ffffff'
                ).pack(padx=15, pady=10)

                # Statistiken
                stats_frame = ctk.CTkFrame(day_frame, fg_color='transparent')
                stats_frame.pack(side='left', fill='x', expand=True, padx=15, pady=10)

                stats_grid = ctk.CTkFrame(stats_frame, fg_color='transparent')
                stats_grid.pack(fill='x')

                # Einzelne Stats
                stat_items = [
                    ("🎯", "Sitzungen", stats['sessions']),
                    ("📝", "Karten", stats['total']),
                    ("✓", "Richtig", stats['correct']),
                    ("📈", "Quote", f"{success_rate:.0f}%"),
                    ("⏱️", "Zeit", self.data_manager.format_learning_time(stats['time']))
                ]

                for idx, (icon, label, value) in enumerate(stat_items):
                    item_frame = ctk.CTkFrame(stats_grid, fg_color='transparent')
                    item_frame.grid(row=0, column=idx, padx=10)

                    ctk.CTkLabel(
                        item_frame,
                        text=icon,
                        font=ctk.CTkFont(size=16)
                    ).pack()

                    ctk.CTkLabel(
                        item_frame,
                        text=str(value),
                        font=ctk.CTkFont(size=16, weight="bold"),
                        text_color='#1f2937'
                    ).pack()

                    ctk.CTkLabel(
                        item_frame,
                        text=label,
                        font=ctk.CTkFont(size=11),
                        text_color='#6b7280'
                    ).pack()

    def get_weekly_progress(self, category, subcategory):
        """Berechnet den Fortschritt pro Woche."""
        weekly_progress = {}
        
        for stat in self.data_manager.stats:
            if (isinstance(stat, dict) and 
                stat.get('category') == category and 
                stat.get('subcategory') == subcategory):
                try:
                    date = datetime.datetime.strptime(stat['date'], "%d.%m.%Y").date()
                    week = date.isocalendar()[1]
                    
                    if week not in weekly_progress:
                        weekly_progress[week] = {
                            'total': 0,
                            'correct': 0
                        }
                        
                    weekly_progress[week]['total'] += stat.get('cards_total', 0)
                    weekly_progress[week]['correct'] += stat.get('cards_correct', 0)
                    
                except ValueError:
                    continue
        
        weekly_rates = {
            week: (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            for week, data in weekly_progress.items()
        }
        
        return weekly_rates

    

    # -----------------------------------------------------------------------------------
    # BACKUP VERWALTUNG (Fortsetzung)
    # -----------------------------------------------------------------------------------
    # Bereits implementiert

    # -----------------------------------------------------------------------------------
    # TAG-SUCHE UND FILTERUNG
    # -----------------------------------------------------------------------------------

    def show_tag_search_interface(self):
        self._clear_content_frame()
        header_frame = tk.Frame(self.content_frame, bg=self.default_bg)
        header_frame.pack(fill='x', pady=(30, 20))
        tk.Label(
            header_frame,
            text="Tag-Suche & -Filterung",
            font=("Segoe UI", 16, "bold"),
            bg=self.default_bg
        ).pack()

        main_frame = ttk.Frame(self.content_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Anzeige aller verfügbaren Tags
        all_tags = sorted({tag for card in self.data_manager.flashcards for tag in card.tags})

        tk.Label(main_frame, text="VerfÃƒÂ¼gbare Tags:", font=(self.appearance_settings.font_family, 12)).pack(pady=5)

        tags_frame = tk.Frame(main_frame, bg=self.default_bg)
        tags_frame.pack(pady=5, fill='x')

        self.tag_vars = {}
        for tag in all_tags:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(tags_frame, text=tag, variable=var, bg=self.appearance_settings.text_bg_color, fg=self.appearance_settings.text_fg_color)
            chk.pack(side=tk.LEFT, padx=5, pady=5)
            self.tag_vars[tag] = var

        # Such-Button
        search_btn = ModernButton(
            main_frame,
            text="Filtern",
            command=self.apply_tag_filter,  # Korrigierte Referenz
            width=15,
            style=ButtonStyle.PRIMARY.value
        )
        search_btn.pack(pady=10)

        # Anzeige der gefilterten Flashcards
        results_frame = tk.Frame(main_frame, bg=self.default_bg)
        results_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        self.filtered_flashcards = []

        def display_filtered_flashcards():
            # Lösche vorherige Ergebnisse
            for widget in results_frame.winfo_children():
                widget.destroy()

            if not self.filtered_flashcards:
                tk.Label(
                    results_frame,
                    text="Keine Flashcards gefunden.",
                    font=(self.appearance_settings.font_family, 12),
                    bg=self.default_bg,
                    fg="red"
                ).pack(pady=20)
            else:
                # Scrollbar hinzufügen
                canvas = tk.Canvas(results_frame, bg=self.default_bg)
                scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
                scrollable_frame = ttk.Frame(canvas)

                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )

                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)

                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

                # Anzeige der Flashcards
                for idx, card in enumerate(self.filtered_flashcards, 1):
                    frame = tk.Frame(scrollable_frame, bg=self.appearance_settings.text_bg_color, relief=tk.RAISED, borderwidth=1)
                    frame.pack(pady=5, padx=5, fill='x')

                    tk.Label(
                        frame,
                        text=f"{idx}. {card.question}",
                        wraplength=600,
                        bg=self.appearance_settings.text_bg_color,
                        fg=self.appearance_settings.text_fg_color,
                        font=(self.appearance_settings.font_family, 12, "bold")
                    ).pack(padx=5, pady=5)
                    tk.Label(
                        frame,
                        text=f"Antwort: {card.answer}",
                        wraplength=600,
                        bg=self.appearance_settings.text_bg_color,
                        fg=self.appearance_settings.text_fg_color,
                        font=(self.appearance_settings.font_family, 12)
                    ).pack(padx=5, pady=5)
                    tags_display = ", ".join(card.tags) if card.tags else "Keine Tags"
                    tk.Label(
                        frame,
                        text=f"Tags: {tags_display}",
                        bg=self.appearance_settings.text_bg_color,
                        fg=self.appearance_settings.text_fg_color,
                        font=(self.appearance_settings.font_family, 10, "italic")
                    ).pack(padx=5, pady=5)

        self.display_filtered_flashcards = display_filtered_flashcards

    def apply_tag_filter(self):
        """Filtert Flashcards basierend auf ausgewÃƒÂ¤hlten Tags."""
        selected_tags = [tag for tag, var in self.tag_vars.items() if var.get()]
        if not selected_tags:
            messagebox.showwarning("Warnung", "Bitte mindestens einen Tag auswÃƒÂ¤hlen.")
            return
        self.filtered_flashcards = self.data_manager.filter_flashcards_by_tags(selected_tags)
        self.display_filtered_flashcards()


        # Zurück-Button
        back_btn = ModernButton(
            self.content_frame,
            text="Zurück zum Hauptmenü",
            command=self.create_main_menu,
            width=15,
            style=ButtonStyle.SECONDARY.value
        )
        back_btn.pack(pady=20)
        self.sidebar_buttons["back_to_main_from_tag_search"] = back_btn

        # Setze den aktiven Button auf 'tag_search'
        self.highlight_active_button('tag_search')
    def update_difficulty_label(self, label: tk.Label, value: float):
        """Aktualisiert das Label für die Schwierigkeitsanzeige"""
        label.configure(text=f"{value:.1f}")
        
        # Optional: FÃƒÂ¼ge eine textuelle Beschreibung hinzu
        difficulty_text = {
            1.0: "Sehr leicht",
            2.0: "Leicht",
            3.0: "Mittel",
            4.0: "Schwer",
            5.0: "Sehr schwer"
        }.get(float(int(value)), "")
        
    
    def toggle_sidebar(self):
        """Klappt die Sidebar ein oder aus."""
        try:
            if self.sidebar_expanded:
                # Sidebar einklappen
                self.sidebar_frame.configure(width=self.sidebar_collapsed_width)
                if self.toggle_button.winfo_exists():
                    self.toggle_button.configure(text="►")  # Pfeil nach rechts

                # Verstecke Button-Texte komplett
                for name, button in self.sidebar_buttons.items():
                    # Prüfe ob Button noch existiert
                    if button.winfo_exists():
                        # Speichere originalen Text falls noch nicht geschehen
                        if not hasattr(button, '_original_text'):
                            button._original_text = button.cget('text')
                        # Verstecke Button komplett
                        button.pack_forget()
                    else:
                        # Entferne zerstörte Buttons aus dem Dictionary
                        del self.sidebar_buttons[name]

            else:
                # Sidebar ausklappen
                self.sidebar_frame.configure(width=self.sidebar_width)
                if self.toggle_button.winfo_exists():
                    self.toggle_button.configure(text="◄")  # Pfeil nach links

                # Zeige Button-Texte wieder
                for name, button in self.sidebar_buttons.items():
                    if button.winfo_exists():
                        button.pack_forget()
                        button.configure(width=20)  # Stelle ursprüngliche Breite wieder her
                        # Stelle originalen Text wieder her falls vorhanden
                        if hasattr(button, '_original_text'):
                            button.configure(text=button._original_text)
                        else:
                            button.configure(text=name)
                        button.pack(pady=(0,10), padx=10, fill='x')
                    else:
                        del self.sidebar_buttons[name]

            self.sidebar_expanded = not self.sidebar_expanded

        except Exception as e:
            logging.error(f"Fehler beim Umschalten der Sidebar: {e}")
            # Versuche die Sidebar in einen konsistenten Zustand zu bringen
            self.sidebar_expanded = True
            self.sidebar_frame.configure(width=self.sidebar_width)
            if self.toggle_button.winfo_exists():
                self.toggle_button.configure(text="◄")

    def add_tooltip(self, widget, text):
        def show_tooltip(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20
            
            # Creates a toplevel window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(self.tooltip, text=text, justify='left',
                            background="#ffffe0", relief='solid', borderwidth=1)
            label.pack()

        def hide_tooltip(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()

        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
    def show_reset_statistics(self):
        """Zeigt den Dialog zum Zurücksetzen der Statistiken, jetzt mit Leitner-Option."""
        self._clear_content_frame()
        
        # Header
        header = ctk.CTkLabel(
            self.content_frame,
            text="Statistiken zurücksetzen",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        header.pack(pady=20)
        
        # Main container
        main_frame = ctk.CTkFrame(self.content_frame)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Warnung
        warning_label = ctk.CTkLabel(
            main_frame,
            text="Achtung: Das Zurücksetzen von Statistiken kann nicht rÃƒÂ¼ckgÃƒÂ¤ngig gemacht werden!",
            font=ctk.CTkFont(size=12),
            text_color="red",
            wraplength=400
        )
        warning_label.pack(pady=20)
        
        # KORREKTUR: CTkLabelFrame durch CTkFrame und ein separates CTkLabel ersetzt
        # Container für den Filter-Bereich
        filter_container = ctk.CTkFrame(main_frame)
        filter_container.pack(fill='x', padx=10, pady=10)

        # Titel für den Filter-Bereich
        filter_title = ctk.CTkLabel(filter_container, text="Filter (Optional)", font=ctk.CTkFont(weight="bold"))
        filter_title.pack(anchor="w", padx=10, pady=(5, 5))

        # Frame für die eigentlichen Steuerelemente
        category_frame = ctk.CTkFrame(filter_container)
        category_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ctk.CTkLabel(category_frame, text="Nur für Kategorie zurücksetzen:").pack(side='left', padx=10)
        category_var = tk.StringVar(value="Alle")
        categories = ["Alle"] + sorted(self.data_manager.categories.keys())
        category_menu = ctk.CTkOptionMenu(
            category_frame,
            variable=category_var,
            values=categories
        )
        category_menu.pack(side='left', pady=10, padx=10)
        
        # Checkbox für Leitner-Reset
        leitner_reset_var = tk.BooleanVar(value=False)
        leitner_check = ctk.CTkCheckBox(
            main_frame,
            text="Auch Leitner-Punkte und -Level zurücksetzen",
            variable=leitner_reset_var,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        leitner_check.pack(pady=10)

        # Checkbox für Sitzungs-Statistiken
        session_stats_reset_var = tk.BooleanVar(value=True) # StandardmÃƒÂ¤ÃƒÅ¸ig an
        session_stats_check = ctk.CTkCheckBox(
            main_frame,
            text="Sitzungs-Statistiken zurücksetzen (Erfolgsquote, Lernzeit etc.)",
            variable=session_stats_reset_var,
            font=ctk.CTkFont(size=12)
        )
        session_stats_check.pack(pady=10)

        def reset_stats():
            selected_category = category_var.get()
            reset_leitner = leitner_reset_var.get()
            reset_session_stats = session_stats_reset_var.get()

            if not reset_leitner and not reset_session_stats:
                messagebox.showwarning("Aktion erforderlich", "Bitte wÃƒÂ¤hlen Sie mindestens eine Art von Daten zum Zurücksetzen aus.")
                return

            # BestÃƒÂ¤tigungsdialog
            message = "MÃƒÂ¶chten Sie die ausgewÃƒÂ¤hlten Daten wirklich zurücksetzen?\n"
            if reset_session_stats:
                message += "\n- Sitzungs-Statistiken"
            if reset_leitner:
                message += "\n- Leitner-Fortschritt (Punkte/Level)"
            
            if selected_category != "Alle":
                message += f"\n\n...nur für die Kategorie '{selected_category}'."
            
            if not messagebox.askyesno("BestÃƒÂ¤tigen", message):
                return # Benutzer hat abgebrochen

            try:
                # Sitzungs-Statistiken zurücksetzen
                if reset_session_stats:
                    if selected_category == "Alle":
                        self.data_manager.stats = []
                        logging.info("Alle Sitzungs-Statistiken wurden zurückgesetzt.")
                    else:
                        # Filtere die Statistiken, um die der ausgewÃƒÂ¤hlten Kategorie zu entfernen
                        stats_to_keep = []
                        for stat in self.data_manager.stats:
                            # Behalte eine Statistik, wenn sie KEINE Details der gewÃƒÂ¤hlten Kategorie enthÃƒÂ¤lt
                            if not any(detail.get('category', '').lower() == selected_category.lower() for detail in stat.get('details', [])):
                                stats_to_keep.append(stat)
                        self.data_manager.stats = stats_to_keep
                        logging.info(f"Sitzungs-Statistiken für Kategorie '{selected_category}' wurden zurückgesetzt.")
                    self.data_manager.save_stats()

                # Leitner-Statistiken zurücksetzen
                if reset_leitner:
                    category_to_reset = None if selected_category == "Alle" else selected_category
                    reset_count = self.data_manager.reset_leitner_stats(category=category_to_reset)
                    
                    # Wichtig: Das Leitner-System im Speicher neu laden!
                    if hasattr(self, 'leitner_system'):
                        self.leitner_system.reload_cards()
                        logging.info("Leitner-System nach Reset neu geladen.")
                
                messagebox.showinfo(
                    "Erfolg",
                    "Die ausgewÃƒÂ¤hlten Daten wurden erfolgreich zurückgesetzt."
                )
                self.create_main_menu()
                
            except Exception as e:
                logging.error(f"Fehler beim Zurücksetzen der Statistiken: {e}")
                messagebox.showerror(
                    "Fehler",
                    f"Beim Zurücksetzen der Statistiken ist ein Fehler aufgetreten:\n{e}"
                )
        
        # Reset Button
        reset_btn = ctk.CTkButton(
            main_frame,
            text="AusgewÃƒÂ¤hlte Daten zurücksetzen",
            command=reset_stats,
            fg_color="#D32F2F", # Rote Farbe für Gefahr
            hover_color="#B71C1C",
            height=40
        )
        reset_btn.pack(pady=20)
        
        # Zurück Button
        back_btn = ctk.CTkButton(
            self.content_frame,
            text="Zurück zum Hauptmenü",
            command=self.create_main_menu,
            height=35
        )
        back_btn.pack(pady=10)
        
        # Setze den aktiven Button
        self.highlight_active_button('Statistik zurücksetzen')


    # -----------------------------------------------------------------------------------
    # WOCHENPLANER
    # -----------------------------------------------------------------------------------
    def show_weekly_calendar(self, planner_id=None):
        """Zeigt den Wochenkalender mit KI-gestützten Lernempfehlungen."""
        self._clear_content_frame()

        if planner_id:
            # Direkter Aufruf mit Planer-ID -> Zeige Wochenansicht
            self.calendar_view = ModernWeeklyCalendarView(
                self.content_frame,
                self.data_manager,
                self.leitner_system,
                planner_id,
                app=self
            )
            self.calendar_view.pack(fill='both', expand=True)
        else:
            # Zeige Planer-Auswahl
            self.planner_selection = PlannerSelectionView(
                self.content_frame,
                self.data_manager,
                self.leitner_system,
                app=self
            )
            self.planner_selection.pack(fill='both', expand=True)

            # Ermögliche Navigation zurück zur Auswahl
            self.planner_selection.master.show_weekly_calendar = self.show_weekly_calendar
            self.planner_selection.master.show_planner_selection = lambda: self.show_weekly_calendar()

        self.highlight_active_button('📅 Wochenplaner')
        logging.info("Wochenplaner geöffnet.")

    # -----------------------------------------------------------------------------------
    # MAINLOOP
    # -----------------------------------------------------------------------------------
    def run(self):
        self.master.mainloop()

# -----------------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------------

    
# ------------------------------------------------------------------------------
# MAIN FUNCTION
# ------------------------------------------------------------------------------
def main():
    """
    Hauptfunktion der Anwendung.
    Initialisiert die Logging-Konfiguration, stellt die Dateien sicher und startet die App.
    """
    setup_logging()
    
    # Erstelle den DataManager ohne data_path_func
    data_manager = DataManager()
    
    # Debug: Ausgabe der verfügbaren Attribute
    print("DataManager Attribute:", dir(data_manager))
    
    # Stelle sicher, dass die Dateien existieren und initialisiere sie bei Bedarf
    ensure_initial_files(data_manager)
    
    # Migriere vorhandene Daten, falls erforderlich
    migrate_existing_data()
    
    # Initialisiere das Hauptfenster
    root = tk.Tk()
    app = FlashcardApp(root, data_manager)
    app.run()

if __name__ == "__main__":
    main()