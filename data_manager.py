#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data Manager für das Flashcard-Projekt.
Verwaltert Flashcards, Kategorien, Statistiken und Themes.
"""

import json
import os
import logging
import threading
import shutil
import sys
import uuid
import random
import platformdirs
from dataclasses import dataclass, asdict, field, fields # 'fields' hier hinzufügen
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
import datetime
from tkinter import messagebox
from threading import Lock
from logging.handlers import RotatingFileHandler

# ------------------------------------------------------------------------------
# KONFIGURATION
# ------------------------------------------------------------------------------
APP_NAME = "FlashCards"
DEFAULT_FLASHCARDS_FILE = 'flashcards.json'
DEFAULT_CATEGORIES_FILE = 'categories.json'
DEFAULT_STATS_FILE = 'stats.json'
DEFAULT_BACKUP_DIR = 'karten_backups'
DEFAULT_THEME_FILE = 'themes.json'
DEFAULT_IMAGES_DIR = 'images'

# SM2 Algorithmus Parameter (optional anpassbar)
SM2_EASE_FACTOR_INCREMENT = 0.1
SM2_EASE_FACTOR_DECREMENT = 0.2
SM2_EASE_FACTOR_MIN = 1.3
SM2_QUALITY_PENALTY_BASE = 5
SM2_QUALITY_PENALTY_SQUARE = 2

# Unterstützte Bildformate
SUPPORTED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']

# ------------------------------------------------------------------------------
# LOGGING KONFIGURATION
# ------------------------------------------------------------------------------

def initialize_logging(log_file: str = "app.log", level: int = logging.INFO):
    """
    Initialisiert das Logging-System mit einem RotatingFileHandler und einem StreamHandler.
    
    Args:
        log_file (str): Der Name der Log-Datei.
        level (int): Das minimale Log-Level.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

    # RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # StreamHandler (Konsole)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

# ------------------------------------------------------------------------------
# HELPER-FUNKTIONEN
# ------------------------------------------------------------------------------

def get_persistent_path(filename: str) -> str:
    """
    Gibt einen Pfad im Projektverzeichnis zurück,
    z.B. C:/Projects/FlashcardApp1/filename
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Verzeichnis der aktuellen Datei
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, filename)

# ------------------------------------------------------------------------------
# FLASHCARD DATACLASS
# ------------------------------------------------------------------------------

@dataclass
class Flashcard:
    """
    Erweiterte Flashcard-Klasse mit Unterstützung für Bilder bei Frage UND Antwort.
    """
    # --- Pflichtfelder OHNE Standardwert ---
    question: str
    answer: str
    category: str
    subcategory: str

    # --- Felder MIT Standardwert ---
    id: str = field(default_factory=lambda: f"card_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{random.randint(1000, 9999)}")
    tags: List[str] = field(default_factory=list)
    
    # Lern-Algorithmus Felder
    interval: int = 1
    ease_factor: float = 2.5
    repetitions: int = 0
    last_reviewed: str = ""
    next_review: str = ""
    consecutive_correct: int = 0
    success_count: int = 0
    
    # Zusätzliche Informationen
    hint: str = ""
    source: str = ""
    difficulty_rating: float = 3.0
    difficulty_history: List[float] = field(default_factory=list)
    
    # BILDER - NEU: Unterstützung für Frage UND Antwort
    question_image_path: Optional[str] = None  # ÃÂ¢Ã¢â¬Â ÃÂ NEU! Bild für die Frage
    image_path: Optional[str] = None           # Bild für die Antwort (bestehendes Feld)
    
    # Leitner-spezifische Attribute
    leitner_points: int = 0
    leitner_level: int = 1
    leitner_positive_streak: int = 0
    leitner_negative_streak: int = 0
    leitner_last_reviewed: Optional[str] = None
    leitner_next_review_date: Optional[str] = None
    leitner_in_recovery_mode: bool = False
    leitner_recovery_interval: int = 1
    leitner_success_history: List[bool] = field(default_factory=list)
    leitner_total_incorrect_count: int = 0  # NEU für Leitner

    def to_dict(self) -> Dict:
        """
        Konvertiert das Flashcard-Objekt in ein Dictionary.
        Wichtig: Muss alle neuen Felder berücksichtigen!
        """
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'subcategory': self.subcategory,
            'tags': self.tags,
            'interval': self.interval,
            'ease_factor': self.ease_factor,
            'repetitions': self.repetitions,
            'last_reviewed': self.last_reviewed,
            'next_review': self.next_review,
            'consecutive_correct': self.consecutive_correct,
            'success_count': self.success_count,
            'hint': self.hint,
            'source': self.source,
            'question_image_path': self.question_image_path,  # ÃÂ¢Ã¢â¬Â ÃÂ NEU!
            'image_path': self.image_path,
            'difficulty_rating': self.difficulty_rating,
            'difficulty_history': self.difficulty_history,
            # Leitner-Felder
            'leitner_points': self.leitner_points,
            'leitner_level': self.leitner_level,
            'leitner_positive_streak': self.leitner_positive_streak,
            'leitner_negative_streak': self.leitner_negative_streak,
            'leitner_last_reviewed': self.leitner_last_reviewed,
            'leitner_next_review_date': self.leitner_next_review_date,
            'leitner_in_recovery_mode': self.leitner_in_recovery_mode,
            'leitner_recovery_interval': self.leitner_recovery_interval,
            'leitner_success_history': self.leitner_success_history,
            'leitner_total_incorrect_count': self.leitner_total_incorrect_count
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Flashcard':
        """
        Erstellt ein Flashcard-Objekt aus einem Dictionary.
        Mit Abwärtskompatibilität für alte Daten ohne question_image_path.
        """
        # Extrahiere alle bekannten Felder mit Fallback-Werten
        return cls(
            id=data.get('id', f"card_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{random.randint(1000, 9999)}"),
            question=data.get('question', ''),
            answer=data.get('answer', ''),
            category=data.get('category', ''),
            subcategory=data.get('subcategory', ''),
            tags=data.get('tags', []),
            interval=data.get('interval', 1),
            ease_factor=data.get('ease_factor', 2.5),
            repetitions=data.get('repetitions', 0),
            last_reviewed=data.get('last_reviewed', ''),
            next_review=data.get('next_review', ''),
            consecutive_correct=data.get('consecutive_correct', 0),
            success_count=data.get('success_count', 0),
            hint=data.get('hint', ''),
            source=data.get('source', ''),
            question_image_path=data.get('question_image_path'),  # ÃÂ¢Ã¢â¬Â ÃÂ NEU! (None wenn nicht vorhanden)
            image_path=data.get('image_path'),
            difficulty_rating=data.get('difficulty_rating', 3.0),
            difficulty_history=data.get('difficulty_history', []),
            # Leitner-Felder
            leitner_points=data.get('leitner_points', 0),
            leitner_level=data.get('leitner_level', 1),
            leitner_positive_streak=data.get('leitner_positive_streak', 0),
            leitner_negative_streak=data.get('leitner_negative_streak', 0),
            leitner_last_reviewed=data.get('leitner_last_reviewed'),
            leitner_next_review_date=data.get('leitner_next_review_date'),
            leitner_in_recovery_mode=data.get('leitner_in_recovery_mode', False),
            leitner_recovery_interval=data.get('leitner_recovery_interval', 1),
            leitner_success_history=data.get('leitner_success_history', []),
            leitner_total_incorrect_count=data.get('leitner_total_incorrect_count', 0)
        )

    def update_difficulty_rating(self):
        """
        Berechnet die difficulty_rating basierend auf der difficulty_history.
        """
        if self.difficulty_history is None:
            self.difficulty_history = []
        
        if self.difficulty_history:
            recent = self.difficulty_history[-7:]  # Letzte 7 Einträge
            valid_recent = [float(d) for d in recent if isinstance(d, (int, float))]
            if valid_recent:
                self.difficulty_rating = sum(valid_recent) / len(valid_recent)
            else:
                self.difficulty_rating = 3.0
        else:
            self.difficulty_rating = 3.0
# ------------------------------------------------------------------------------
# THEME MANAGER
# ------------------------------------------------------------------------------

class ThemeManager:
    """
    Verwaltert Themes für die Flashcard-App.
    """
    def __init__(self, theme_file_path: str):
        self.theme_file_path = theme_file_path
        self.themes: Dict[str, Dict] = {}
        self.lock = Lock()
        logging.info(f"Initialisiere ThemeManager mit Pfad: {self.theme_file_path}")
        self.load_themes()

    def load_themes(self):
        """
        Lädt Themes aus der Theme-Datei.
        """
        if os.path.exists(self.theme_file_path):
            try:
                with open(self.theme_file_path, 'r', encoding='utf-8') as f:
                    self.themes = json.load(f)
                logging.info(f"Themes aus {self.theme_file_path} geladen.")
            except Exception as e:
                logging.error(f"Fehler beim Laden der Themes: {e}")
        else:
            logging.warning(f"Theme-Datei {self.theme_file_path} existiert nicht. Initialisiere leere Themes.")
            self.themes = {}

    def save_themes(self):
        """
        Speichert die aktuellen Themes in die Theme-Datei.
        """
        try:
            with self.lock: # Korrigiertes Lock
                with open(self.theme_file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.themes, f, indent=4, ensure_ascii=False)
            logging.info(f"Themes wurden in {self.theme_file_path} gespeichert.")
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Themes: {e}")

    def add_or_update_theme(self, theme_name: str, theme_data: Dict) -> bool:
        """
        Fügt ein neues Theme hinzu oder aktualisiert ein bestehendes Theme.
        
        Args:
            theme_name (str): Der Name des Themes.
            theme_data (Dict): Die Daten des Themes.
            
        Returns:
            bool: True wenn erfolgreich, False sonst.
        """
        with self.lock: # Korrigiertes Lock
            self.themes[theme_name.lower()] = theme_data
            logging.info(f"Theme '{theme_name}' hinzugefügt/aktualisiert.")
            self.save_themes()
            return True

    def delete_theme(self, theme_name: str) -> bool:
        """
        Löscht ein bestehendes Theme.
        
        Args:
            theme_name (str): Der Name des zu löschenden Themes.
            
        Returns:
            bool: True wenn erfolgreich gelöscht, False wenn das Theme nicht gefunden wurde.
        """
        with self.lock: # Korrigiertes Lock
            if theme_name.lower() in self.themes:
                del self.themes[theme_name.lower()]
                logging.info(f"Theme '{theme_name}' gelöscht.")
                self.save_themes()
                return True
            else:
                logging.warning(f"Theme '{theme_name}' nicht gefunden.")
                return False

    def get_theme(self, theme_name: str) -> Optional[Dict]:
        """
        Gibt die Daten eines bestimmten Themes zurück.
        
        Args:
            theme_name (str): Der Name des Themes.
            
        Returns:
            Optional[Dict]: Die Theme-Daten oder None, wenn das Theme nicht existiert.
        """
        return self.themes.get(theme_name.lower())

    def get_theme_names(self) -> List[str]:
        """
        Gibt eine Liste aller vorhandenen Theme-Namen zurück.
        
        Returns:
            List[str]: Die Liste der Theme-Namen.
        """
        return list(self.themes.keys())

    def import_themes(self, file_path: str) -> bool:
        """
        Importiert Themes aus einer externen Datei.
        
        Args:
            file_path (str): Der Pfad zur Importdatei.
            
        Returns:
            bool: True wenn erfolgreich, False sonst.
        """
        try:
            logging.info(f"Importiere Themes aus Datei: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_themes = json.load(f)
            with self.lock: # Korrigiertes Lock
                self.themes.update({k.lower(): v for k, v in imported_themes.items()})
                self.save_themes()
            logging.info(f"Themes aus {file_path} importiert.")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Importieren der Themes: {e}")
            return False

    def export_themes(self, file_path: str) -> bool:
        """
        Exportiert die aktuellen Themes in eine externe Datei.
        
        Args:
            file_path (str): Der Pfad zur Exportdatei.
            
        Returns:
            bool: True wenn erfolgreich, False sonst.
        """
        try:
            logging.info(f"Exportiere Themes nach Datei: {file_path}")
            with self.lock: # Korrigiertes Lock
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.themes, f, indent=4, ensure_ascii=False)
            logging.info(f"Themes wurden nach {file_path} exportiert.")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Exportieren der Themes: {e}")
            return False

# ------------------------------------------------------------------------------
# STATISTICS MANAGER
# ------------------------------------------------------------------------------

class StatisticsManager:
    """
    Verwaltert Statistiken für die Flashcard-App.
    """
    def __init__(self, data_manager: 'DataManager'):
        self.data_manager = data_manager
        self.lock = Lock()

    def add_session_summary(self, session_summary: Dict) -> bool:
        """
        Fügt eine neue Sitzungszusammenfassung hinzu und speichert die Statistiken.
        
        Args:
            session_summary (Dict): Die Zusammenfassung der Sitzung.
            
        Returns:
            bool: True wenn erfolgreich, False sonst.
        """
        try:
            with self.data_manager.stats_lock: # Korrigiertes Lock
                self.data_manager.stats.append(session_summary)
                self.data_manager.save_stats()
                logging.info("Sitzungszusammenfassung hinzugefügt und gespeichert.")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen der Sitzungszusammenfassung: {e}")
            return False

    def get_overall_statistics(self) -> Dict:
        """
        Gibt die Gesamtstatistiken über alle Zeiträume zurück.
        
        Returns:
            Dict: Die Gesamtstatistiken.
        """
        total_sessions = len(self.data_manager.stats)
        total_correct = sum(stat.get('cards_correct', 0) for stat in self.data_manager.stats)
        total_attempts = sum(stat.get('cards_total', 0) for stat in self.data_manager.stats)
        total_learning_time = sum(stat.get('total_time', 0) for stat in self.data_manager.stats)

        success_rate = (total_correct / total_attempts * 100) if total_attempts > 0 else 0

        return {
            "total_sessions": total_sessions,
            "total_correct": total_correct,
            "total_attempts": total_attempts,
            "success_rate": success_rate,
            "total_learning_time": total_learning_time
        }

    def get_filtered_statistics(self, category: Optional[str] = None, subcategory: Optional[str] = None) -> List[Dict]:
        """
        Gibt gefilterte Statistiken basierend auf Kategorie und Unterkategorie zurück.
        
        Args:
            category (Optional[str]): Die zu filternde Kategorie.
            subcategory (Optional[str]): Die zu filternde Unterkategorie.
            
        Returns:
            List[Dict]: Liste der gefilterten Statistiken.
        """
        filtered_stats = []
        
        for stat in self.data_manager.stats:
            if not isinstance(stat, dict) or 'details' not in stat:
                continue
                
            filtered_details = []
            for detail in stat['details']:
                if not isinstance(detail, dict):
                    continue
                    
                # Kategorie-Filter
                matches_category = True
                if category and category.lower() != "alle":
                    matches_category = detail.get('category', '').lower() == category.lower()
                    
                # Unterkategorie-Filter
                matches_subcategory = True
                if matches_category and subcategory and subcategory.lower() != "alle":
                    matches_subcategory = detail.get('subcategory', '').lower() == subcategory.lower()
                    
                if matches_category and matches_subcategory:
                    filtered_details.append(detail)
            
            if filtered_details:
                new_stat = stat.copy()
                new_stat['details'] = filtered_details
                new_stat['cards_total'] = len(filtered_details)
                new_stat['cards_correct'] = sum(1 for d in filtered_details if d.get('correct', False))
                filtered_stats.append(new_stat)
        
        return filtered_stats

    def get_category_statistics(self, category: str) -> Dict:
        """
        Gibt die Statistiken für eine bestimmte Kategorie zurück.
        
        Args:
            category (str): Die zu analysierende Kategorie.
            
        Returns:
            Dict: Die Statistiken für die Kategorie.
        """
        category_stats = {
            "total_sessions": 0,
            "total_correct": 0,
            "total_attempts": 0,
            "success_rate": 0,
            "total_learning_time": 0
        }
        
        unique_sessions = set()  # Set für eindeutige Sitzungen
        
        for stat in self.data_manager.stats:
            if isinstance(stat, dict) and 'details' in stat:
                category_found = False
                session_correct = 0
                session_attempts = 0
                
                for detail in stat['details']:
                    if isinstance(detail, dict) and detail.get('category', '').lower() == category.lower():
                        category_found = True
                        session_correct += detail.get('correct', 0)
                        session_attempts += 1

                if category_found:
                    # Nur wenn die Kategorie in dieser Sitzung vorkam
                    category_stats["total_correct"] += session_correct
                    category_stats["total_attempts"] += session_attempts
                    
                    # Füge das Datum zur Menge der eindeutigen Sitzungen hinzu
                    if 'date' in stat:
                        unique_sessions.add(stat['date'])
                        
                    # Anteilige Lernzeit basierend auf dem Verhältnis der Kategorie-Karten
                    if 'total_time' in stat and 'details' in stat:
                        total_cards_in_session = len(stat['details'])
                        category_cards_in_session = sum(1 for d in stat['details'] 
                                                    if d.get('category', '').lower() == category.lower())
                        
                        # Berechne den anteiligen Zeitaufwand
                        if total_cards_in_session > 0:
                            time_ratio = category_cards_in_session / total_cards_in_session
                            category_stats["total_learning_time"] += stat['total_time'] * time_ratio

        # Setze die Anzahl der Sitzungen auf die Anzahl der eindeutigen Daten
        category_stats["total_sessions"] = len(unique_sessions)
        
        # Berechne die Erfolgsquote
        if category_stats["total_attempts"] > 0:
            category_stats["success_rate"] = (category_stats["total_correct"] / 
                                            category_stats["total_attempts"] * 100)

        return category_stats

    def get_subcategory_statistics(self, category: str, subcategory: str) -> Dict:
        """
        Gibt die Statistiken für eine Subkategorie zurück.
        
        Args:
            category (str): Die Hauptkategorie.
            subcategory (str): Die zu analysierende Subkategorie.
            
        Returns:
            Dict: Die Statistiken für die Subkategorie.
        """
        subcategory_stats = {
            "total_sessions": 0,
            "total_correct": 0,
            "total_attempts": 0,
            "success_rate": 0,
            "total_learning_time": 0
        }

        unique_sessions = set()  # Set für eindeutige Sitzungen

        for stat in self.data_manager.stats:
            if isinstance(stat, dict) and 'details' in stat:
                subcategory_found = False
                session_correct = 0
                session_attempts = 0
                
                subcategory_cards = 0  # Zähler für Karten dieser Subkategorie
                total_cards = len(stat['details'])  # Gesamtzahl der Karten in dieser Sitzung
                
                # Zähle erst die relevanten Karten
                for detail in stat['details']:
                    if (isinstance(detail, dict) and 
                        detail.get('category', '').lower() == category.lower() and 
                        detail.get('subcategory', '').lower() == subcategory.lower()):
                        subcategory_found = True
                        session_correct += detail.get('correct', 0)
                        session_attempts += 1
                        subcategory_cards += 1

                if subcategory_found:
                    # Nur wenn die Subkategorie in dieser Sitzung vorkam
                    subcategory_stats["total_correct"] += session_correct
                    subcategory_stats["total_attempts"] += session_attempts
                    
                    # Füge das Datum zur Menge der eindeutigen Sitzungen hinzu
                    if 'date' in stat:
                        unique_sessions.add(stat['date'])
                    
                    # Berechne die anteilige Lernzeit
                    if 'total_time' in stat and total_cards > 0:
                        time_ratio = subcategory_cards / total_cards
                        subcategory_stats["total_learning_time"] += stat['total_time'] * time_ratio

        # Setze die Anzahl der Sitzungen auf die Anzahl der eindeutigen Daten
        subcategory_stats["total_sessions"] = len(unique_sessions)

        # Berechne die Erfolgsquote
        if subcategory_stats["total_attempts"] > 0:
            subcategory_stats["success_rate"] = (subcategory_stats["total_correct"] / 
                                            subcategory_stats["total_attempts"] * 100)

        return subcategory_stats

    def get_daily_statistics(self, date: datetime.date) -> Dict:
        """
        Gibt die Statistiken für einen bestimmten Tag zurück.
        
        Args:
            date (datetime.date): Das Datum, für das die Statistiken abgerufen werden sollen.
            
        Returns:
            Dict: Statistiken für den Tag.
        """
        day_stats = {
            "total_sessions": 0,
            "total_correct": 0,
            "total_attempts": 0,
            "success_rate": 0,
            "total_learning_time": 0,
            "details": []  # Hinzufügen von Details für diesen Tag
        }

        for stat in self.data_manager.stats:
            if isinstance(stat, dict) and 'date' in stat:
                stat_date_str = stat['date']
                try:
                    stat_date = datetime.datetime.strptime(stat_date_str, "%d.%m.%Y").date()
                except ValueError:
                    logging.error(f"Ungültiges Datumsformat in Statistik: {stat_date_str}")
                    continue

                if stat_date == date:
                    day_stats["total_sessions"] += 1
                    day_stats["total_learning_time"] += stat.get('total_time', 0)
                    if 'details' in stat:  # Stelle sicher, dass 'details' existiert
                        for detail in stat['details']:
                            if isinstance(detail, dict):
                                day_stats["total_attempts"] += 1
                                if detail.get('correct', False):
                                    day_stats["total_correct"] += 1
                                day_stats["details"].append(detail)  # Detail-Informationen hinzufügen

        day_stats["success_rate"] = (day_stats["total_correct"] / day_stats["total_attempts"] * 100) if day_stats["total_attempts"] > 0 else 0

        return day_stats  

    def get_monthly_statistics(self, year: int, month: int) -> Dict:
        """
        Gibt die Statistiken für einen bestimmten Monat zurück.
        
        Args:
            year (int): Das Jahr.
            month (int): Der Monat.
            
        Returns:
            Dict: Die Statistiken für den Monat.
        """
        month_stats = {
            "total_sessions": 0,
            "total_correct": 0,
            "total_attempts": 0,
            "success_rate": 0,
            "total_learning_time": 0,
            "days": defaultdict(lambda: {"total_correct": 0, "total_attempts": 0})
        }

        for stat in self.data_manager.stats:
            if isinstance(stat, dict) and 'date' in stat and 'details' in stat:
                try:
                    stat_date = datetime.datetime.strptime(stat['date'], "%d.%m.%Y").date()
                    if stat_date.year == year and stat_date.month == month:
                        month_stats["total_sessions"] += 1
                        month_stats["total_learning_time"] += stat.get('total_time', 0)
                        for detail in stat['details']:
                            if isinstance(detail, dict):
                                month_stats["total_attempts"] += 1
                                if detail.get('correct', False):
                                    month_stats["total_correct"] += 1
                                
                                day_str = stat_date.strftime("%d.%m.%Y")
                                month_stats["days"][day_str]["total_attempts"] += 1
                                if detail.get('correct', False):
                                    month_stats["days"][day_str]["total_correct"] += 1
                except ValueError:
                    logging.error(f"Ungültiges Datumsformat in Statistik: {stat.get('date')}")

        month_stats["success_rate"] = (month_stats["total_correct"] / month_stats["total_attempts"] * 100) if month_stats["total_attempts"] > 0 else 0

        return month_stats

    def get_overall_statistics(self) -> Dict:
        """
        Gibt die Gesamtstatistiken über alle Zeiträume zurück.
        Berücksichtigt dabei die Details der einzelnen Statistiken.
        
        Returns:
            Dict: Die Gesamtstatistiken.
        """
        total_sessions = len(self.data_manager.stats)
        total_correct = 0
        total_attempts = 0
        total_learning_time = 0
        daily_stats = defaultdict(lambda: {"total_correct": 0, "total_attempts": 0, "sessions": 0})

        for stat in self.data_manager.stats:
            if isinstance(stat, dict):
                if 'date' in stat:
                    date_str = stat['date']
                    daily_stats[date_str]["sessions"] += 1
                    
                    if 'details' in stat:
                        total_attempts += len(stat['details'])
                        total_correct += sum(1 for detail in stat['details'] 
                                        if isinstance(detail, dict) and detail.get('correct', False))
                        daily_stats[date_str]["total_attempts"] += len(stat['details'])
                        daily_stats[date_str]["total_correct"] += sum(1 for detail in stat['details'] 
                                                                    if isinstance(detail, dict) and detail.get('correct', False))
                    
                if 'total_time' in stat:
                    total_learning_time += stat['total_time']

        success_rate = (total_correct / total_attempts * 100) if total_attempts > 0 else 0

        return {
            "total_sessions": total_sessions,
            "total_correct": total_correct,
            "total_attempts": total_attempts,
            "success_rate": success_rate,
            "total_learning_time": total_learning_time,
            "daily_stats": dict(daily_stats)  # Konvertiere defaultdict zu normalem dict
        }
    def get_all_statistics(self) -> List[Dict]:
        """
        Gibt alle Statistiken zurück.
        
        Returns:
            List[Dict]: Liste aller Statistik-Einträge
        """
        with self.data_manager.stats_lock:
            return list(self.data_manager.stats)
# ------------------------------------------------------------------------------
# DATA MANAGER
# ------------------------------------------------------------------------------

class DataManager:
    """
    Verwaltert Daten für die Flashcard-App, einschließlich Flashcards, Kategorien, Statistiken und Themes.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DataManager, cls).__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        # Einheitliche Dateinamen verwenden
        self.flashcards_file  = get_persistent_path(DEFAULT_FLASHCARDS_FILE)
        self.categories_file  = get_persistent_path(DEFAULT_CATEGORIES_FILE)
        self.stats_file       = get_persistent_path(DEFAULT_STATS_FILE)
        self.backup_dir       = get_persistent_path(DEFAULT_BACKUP_DIR)
        self.theme_file       = get_persistent_path(DEFAULT_THEME_FILE)
        self.images_dir       = get_persistent_path(DEFAULT_IMAGES_DIR)

        # Stelle sicher, dass alle Verzeichnisse existieren
        os.makedirs(os.path.dirname(self.flashcards_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.categories_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.theme_file), exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

        logging.info(f"Initialisierte Dateipfade:")
        logging.info(f"Flashcards: {self.flashcards_file}")
        logging.info(f"Kategorien: {self.categories_file}")
        logging.info(f"Statistiken: {self.stats_file}")
        logging.info(f"Backup-Verzeichnis: {self.backup_dir}")
        logging.info(f"Themes: {self.theme_file}")

        # Datenstrukturen
        self.flashcards: List[Flashcard] = []
        self.categories: Dict[str, Dict[str, List[str]]] = defaultdict(dict)  # category -> subcategory -> list of tags
        self.stats: List[Dict] = []
        self.theme_manager = ThemeManager(self.theme_file)

        # Locks für Thread-Sicherheit
        self.flashcards_lock = threading.RLock()
        self.categories_lock = threading.RLock()
        self.stats_lock = threading.RLock()

        # Daten laden
        self.load_flashcards()
        self.load_categories()
        self.load_stats()
        self.theme_manager.load_themes()
        
        # Bilder-Verzeichnis initialisieren
        self.images_dir = get_persistent_path('images')
        os.makedirs(self.images_dir, exist_ok=True)
        logging.info(f"Bilder-Verzeichnis: {self.images_dir}")

        self._initialized = True

    # -----------------------------------------------------------------------------
    # FLASHCARDS VERWALTUNG
    # ------------------------------------------------------------------------------


# In data_manager.py -> DataManager.save_flashcards

    def get_flashcard_by_id(self, card_id: str) -> Optional[Flashcard]:
        """
        Sucht eine Flashcard anhand ihrer ID in der Liste der Flashcard-Objekte.

        Args:
            card_id: Die ID der gesuchten Flashcard.

        Returns:
            Das gefundene Flashcard-Objekt oder None, wenn nicht gefunden.
        """
        # Verwende das Lock für thread-sicheren Lesezugriff (wichtig!)
        with self.flashcards_lock:
            # Sicherheitscheck: Ist self.flashcards wirklich eine Liste?
            if not isinstance(self.flashcards, list):
                 logging.error(f"get_flashcard_by_id: self.flashcards ist keine Liste (Typ: {type(self.flashcards)})")
                 return None

            # Gehe die Liste der Flashcard-Objekte durch
            for card_obj in self.flashcards:
                 # Stelle sicher, dass es ein Flashcard-Objekt ist und 'id' hat
                 # Verwende getattr für sicheren Attributzugriff
                if isinstance(card_obj, Flashcard) and getattr(card_obj, 'id', None) == card_id:
                    # Gefunden! Gib das Objekt zurück.
                    return card_obj
                elif not isinstance(card_obj, Flashcard):
                    # Logge eine Warnung, falls unerwartete Elemente in der Liste sind
                    logging.warning(f"get_flashcard_by_id: Unerwartetes Element in self.flashcards gefunden (Typ: {type(card_obj)}) bei Suche nach ID {card_id}")

            # Wenn die Schleife durchläuft, ohne die ID zu finden
            logging.debug(f"get_flashcard_by_id: Keine Karte mit ID '{card_id}' in self.flashcards gefunden.")
            return None # Nicht gefunden
    def _backup_file(self, file_path: str, backup_prefix: str) -> Optional[str]:
        """
        Erstellt ein Backup einer Datei im Backup-Verzeichnis.

        Args:
            file_path (str): Der Pfad zur Originaldatei.
            backup_prefix (str): Ein Präfix für den Backup-Dateinamen (z.B. "flashcards", "themes").

        Returns:
            Optional[str]: Der Pfad zur erstellten Backup-Datei oder None bei einem Fehler.
        """
        # Nur Backup erstellen, wenn die Originaldatei existiert
        if not os.path.exists(file_path):
            logging.debug(f"_backup_file: Originaldatei '{file_path}' existiert nicht, kein Backup erstellt.")
            return None

        try:
            # Zeitstempel für eindeutigen Dateinamen
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f") # Mikrosekunden für mehr Eindeutigkeit
            # Nur den Dateinamen des Originals nehmen
            original_filename = os.path.basename(file_path)
            # Neuen Backup-Namen zusammensetzen
            backup_filename = f"{backup_prefix}_backup_{timestamp}_{original_filename}"
            # Zielpfad im Backup-Verzeichnis
            backup_path = os.path.join(self.backup_dir, backup_filename)

            # Stelle sicher, dass das Backup-Verzeichnis existiert
            os.makedirs(self.backup_dir, exist_ok=True)

            # Kopiere die Datei (copy2 erhält Metadaten wie Zeitstempel)
            shutil.copy2(file_path, backup_path)
            logging.info(f"_backup_file: Backup erfolgreich erstellt: '{backup_path}'")
            return backup_path
        except Exception as e:
            logging.error(f"_backup_file: Fehler beim Erstellen des Backups für '{file_path}': {e}", exc_info=True)
            return None # Fehler signalisieren
# In data_manager.py -> Ersetze die komplette save_flashcards Methode mit dieser Version

    def save_flashcards(self):
        """
        Speichert die aktuelle Liste der Flashcards in die JSON-Datei.
        Verwendet card.to_dict() für die korrekte Serialisierung von Datumsfeldern.
        """
        target_file_path = self.flashcards_file
        logging.info(f"Speichere Flashcards nach: '{target_file_path}'")

        # --- Pfad- und Rechteprüfung (vereinfacht) ---
        target_dir = os.path.dirname(target_file_path)
        try:
            # Stelle sicher, dass das Verzeichnis existiert
            os.makedirs(target_dir, exist_ok=True)
        except Exception as path_err:
             logging.error(f"Fehler bei Pfad-/Verzeichniserstellung für '{target_file_path}': {path_err}", exc_info=True)
             return False

        # --- Thread-sicheres Speichern ---
        with self.flashcards_lock: # Korrektes Lock verwenden
            backup_path = None
            data_to_save = [] # Initialisieren für den Fall, dass etwas schiefgeht

            try:
                logging.debug(f"Speichern: Lock für '{target_file_path}' erhalten.")

                # --- Datenaufbereitung mit card.to_dict() ---
                logging.debug(f"Speichern: Bereite Flashcard-Daten vor...")
                if not self.flashcards:
                     logging.info("Speichern: Flashcards-Liste ist leer.")
                     data_to_save = []
                elif isinstance(self.flashcards, list) and self.flashcards and isinstance(self.flashcards[0], Flashcard):
                    try:
                        # *** WICHTIGSTE ÄNDERUNG: Verwende die to_dict() Methode der Karte ***
                        data_to_save = [card.to_dict() for card in self.flashcards]
                        logging.debug(f"Speichern: {len(data_to_save)} Flashcards via card.to_dict() für JSON vorbereitet.")
                    except Exception as convert_e:
                         logging.error(f"Speichern: Fehler bei Konvertierung via card.to_dict(): {convert_e}", exc_info=True)
                         raise # Fehler weitergeben an äußeres try-except
                else:
                    logging.error(f"Speichern: Unerwarteter Datentyp in self.flashcards: {type(self.flashcards[0]) if self.flashcards else 'leer oder keine Liste'}")
                    raise TypeError("Unerwarteter Datentyp in self.flashcards beim Speichern")

                # --- Backup erstellen ---
                if os.path.exists(target_file_path):
                    logging.debug(f"Speichern: Erstelle Backup für '{target_file_path}'...")
                    if hasattr(self, '_backup_file') and callable(self._backup_file):
                         backup_path = self._backup_file(target_file_path, "flashcards")
                         if backup_path:
                            logging.debug(f"Speichern: Backup erstellt unter '{backup_path}'")
                         else:
                            logging.warning("Speichern: Backup konnte nicht erstellt werden.")
                    else:
                         logging.warning("Speichern: _backup_file Methode nicht gefunden, Backup übersprungen.")


                # --- Atomares Schreiben (Temp-Datei -> Umbenennen) ---
                temp_file_path = target_file_path + ".tmp"
                logging.debug(f"Speichern: Schreibe Daten in temporäre Datei '{temp_file_path}'...")
                try:
                    with open(temp_file_path, 'w', encoding='utf-8') as f:
                        json.dump(data_to_save, f, indent=4, ensure_ascii=False)
                        f.flush()
                        os.fsync(f.fileno())
                    logging.debug(f"Speichern: json.dump in temporäre Datei erfolgreich.")

                    shutil.move(temp_file_path, target_file_path)
                    logging.info(f"Flashcards erfolgreich gespeichert in '{target_file_path}' (atomar).")
                    return True # Erfolg signalisieren

                except TypeError as type_err:
                    logging.error(f"Speichern: !!! TypeError bei json.dump - Daten nicht JSON-serialisierbar: {type_err} !!!", exc_info=True)
                    if os.path.exists(temp_file_path):
                        try: os.remove(temp_file_path)
                        except OSError: pass
                    raise
                except (IOError, OSError) as io_err:
                     logging.error(f"Speichern: !!! IOError/OSError beim Schreiben/Verschieben von '{temp_file_path}' -> '{target_file_path}': {io_err} !!!", exc_info=True)
                     if os.path.exists(temp_file_path):
                        try: os.remove(temp_file_path)
                        except OSError: pass
                     raise


            except Exception as e:
                logging.error(f"Speichern: !!! Allgemeiner Fehler im Speicherprozess für {target_file_path}: {e} !!!", exc_info=True)
                if backup_path and os.path.exists(backup_path):
                    try:
                        logging.warning(f"Speichern: Fehler aufgetreten, versuche Wiederherstellung aus Backup: {backup_path}")
                        shutil.copy2(backup_path, target_file_path)
                        logging.info(f"Speichern: Datei aus Backup {backup_path} wiederhergestellt.")
                    except Exception as backup_restore_e:
                        logging.error(f"Speichern: !!! Konnte NICHT aus Backup wiederherstellen: {backup_restore_e} !!!")
                return False
            finally:
                 logging.debug(f"Speichern: Lock für '{target_file_path}' wird freigegeben.")
    def load_flashcards(self):
        logging.info("Versuche, Flashcards zu laden...")
        if os.path.exists(self.flashcards_file):
            try:
                with open(self.flashcards_file, 'r', encoding='utf-8') as f:
                    flashcards_data = json.load(f)

                if not isinstance(flashcards_data, list):
                     logging.error(f"Flashcards JSON ({self.flashcards_file}) ist keine Liste. Lade leere Liste.")
                     self.flashcards = []
                     self.backup_flashcards("invalid_format")
                     return False

                with self.flashcards_lock:
                    loaded_cards = []
                    seen_ids = set()

                    logging.debug(f"Beginne mit der Verarbeitung von {len(flashcards_data)} Einträgen aus JSON.")

                    for i, card_data in enumerate(flashcards_data):
                        if not isinstance(card_data, dict):
                            logging.warning(f"Eintrag {i+1}: Ungültiger Eintrag in flashcards.json (kein Dictionary): {card_data}")
                            continue

                        card_id_from_json = card_data.get('id', 'FEHLT!')
                        next_review_date_from_json = card_data.get('leitner_next_review_date', 'FEHLT!')
                        question_preview = card_data.get('question', 'Frage fehlt')[:30]
                        logging.debug(f"Eintrag {i+1}: Lade aus JSON -> ID='{card_id_from_json}', leitner_next_review_date='{next_review_date_from_json}', Frage='{question_preview}...'")

                        if card_id_from_json != 'FEHLT!':
                            if card_id_from_json in seen_ids:
                                logging.warning(f"Eintrag {i+1}: Doppelte Karten-ID '{card_id_from_json}' beim Laden gefunden. Überspringe Duplikat.")
                                continue
                            seen_ids.add(card_id_from_json)
                        else:
                             logging.warning(f"Eintrag {i+1}: Karte ohne ID in JSON gefunden: Frage='{question_preview}...'. Neue ID wird von Flashcard.from_dict (oder __init__) generiert.")

                        try:
                            card = Flashcard.from_dict(card_data)

                            if card.image_path and isinstance(card.image_path, str):
                                if not os.path.isabs(card.image_path):
                                     base_name = os.path.basename(card.image_path)
                                     abs_path = os.path.join(self.images_dir, base_name)
                                else:
                                     abs_path = card.image_path

                                if os.path.exists(abs_path):
                                    card.image_path = abs_path
                                else:
                                    logging.warning(f"Eintrag {i+1}: Bildpfad nicht gefunden für Karte ID {card.id}: {abs_path} (Original: {card_data.get('image_path')})")
                                    card.image_path = None
                            else:
                                card.image_path = None


                            loaded_cards.append(card)

                        except KeyError as e:
                            logging.error(f"Eintrag {i+1}: Fehlendes erwartetes Feld beim Laden der Karte ID '{card_id_from_json}': {e}. Überspringe Karte. Daten: {card_data}")
                            continue
                        except TypeError as e:
                            logging.error(f"Eintrag {i+1}: Typfehler beim Erstellen der Karte ID '{card_id_from_json}': {e}. Überspringe Karte. Daten: {card_data}")
                            continue
                        except Exception as e:
                            logging.error(f"Eintrag {i+1}: Allgemeiner Fehler beim Verarbeiten der Karte ID '{card_id_from_json}': {e}. Überspringe Karte.", exc_info=True)
                            continue

                    self.flashcards = loaded_cards
                    logging.info(f"{len(self.flashcards)} Flashcards erfolgreich aus {self.flashcards_file} geladen und verarbeitet.")
                    return True

            except json.JSONDecodeError as e:
                 logging.error(f"Fehler beim Parsen der JSON-Datei {self.flashcards_file}: {e}")
                 self.backup_flashcards("json_decode_error")
                 self.flashcards = []
                 return False
            except Exception as e:
                logging.error(f"Generischer Fehler beim Laden der Flashcards aus {self.flashcards_file}: {e}", exc_info=True)
                self.backup_flashcards("load_error")
                self.flashcards = []
                return False
        else:
            logging.warning(f"Flashcards-Datei {self.flashcards_file} existiert nicht. Initialisiere leere Flashcards-Liste.")
            self.flashcards = []
            return True

    def add_flashcard(self, flashcard: Flashcard) -> bool:
        try:
            with self.flashcards_lock:
                for card in self.flashcards:
                    if card.question == flashcard.question and card.answer == flashcard.answer:
                        logging.warning(f"Flashcard mit gleicher Frage und Antwort existiert bereits: '{flashcard.question}'")
                        return False
                
                if flashcard.image_path and os.path.exists(flashcard.image_path):
                    try:
                        file_extension = os.path.splitext(flashcard.image_path)[1]
                        unique_filename = f"img_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{file_extension}"
                        new_image_path = os.path.join(self.images_dir, unique_filename)
                        
                        shutil.copy2(flashcard.image_path, new_image_path)
                        flashcard.image_path = new_image_path
                        logging.info(f"Bild kopiert: {new_image_path}")
                    except Exception as e:
                        logging.error(f"Fehler beim Kopieren des Bildes: {e}")
                        flashcard.image_path = None
                
                self.flashcards.append(flashcard)
                logging.info(f"Flashcard hinzugefügt: '{flashcard.question}'")
                self.save_flashcards()
                return True
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen der Flashcard '{flashcard.question}': {e}")
            raise
    def cleanup_unused_images(self):
        """
        Entfernt Bilder, die von keiner Flashcard mehr verwendet werden.
        """
        try:
            used_images = {os.path.basename(card.image_path) for card in self.flashcards if card.image_path}
            
            for filename in os.listdir(self.images_dir):
                if filename not in used_images:
                    try:
                        file_path = os.path.join(self.images_dir, filename)
                        os.remove(file_path)
                        logging.info(f"Ungenutztes Bild entfernt: {file_path}")
                    except Exception as e:
                        logging.error(f"Fehler beim Entfernen des ungenutzten Bildes {file_path}: {e}")
                        
        except Exception as e:
            logging.error(f"Fehler bei der Bilderbereinigung: {e}")

    def delete_flashcard(self, flashcard: Flashcard) -> bool:
        """
        Löscht eine Flashcard aus der Liste und speichert die Änderungen.
        """
        with self.flashcards_lock:
            if flashcard in self.flashcards:
                self.flashcards.remove(flashcard)
                logging.info(f"Flashcard gelöscht: {flashcard.question}")
                self.save_flashcards()
                return True
            else:
                logging.warning("Flashcard zum Löschen nicht gefunden.")
                return False

    def get_due_flashcards(self, category: Optional[str] = None, subcategory: Optional[str] = None) -> List[Flashcard]:
        """
        Gibt eine Liste von Flashcards zurück, die fällig für eine Überprüfung sind.
        """
        today = datetime.date.today().strftime("%d.%m.%Y")
        due = []
        with self.flashcards_lock:
            for card in self.flashcards:
                if card.next_review <= today:
                    if category and card.category.lower() != category.lower():
                        continue
                    if subcategory and card.subcategory.lower() != subcategory.lower():
                        continue
                    due.append(card)
        logging.info(f"{len(due)} Flashcards fällig für Überprüfung.")
        return due

    def filter_flashcards_by_tags(self, tags: List[str]) -> List[Flashcard]:
        """
        Filtert Flashcards basierend auf den angegebenen Tags.
        """
        filtered = []
        with self.flashcards_lock:
            for card in self.flashcards:
                if all(tag.lower() in (t.lower() for t in card.tags) for tag in tags):
                    filtered.append(card)
        logging.info(f"{len(filtered)} Flashcards nach Tags {tags} gefiltert.")
        return filtered

    def filter_flashcards(self, category: Optional[str] = None, 
                            subcategory: Optional[str] = None, 
                            progress: Optional[str] = None,
                            difficulty_range: Optional[Tuple[float, float]] = None) -> List[Flashcard]:
        """
        Erweiterte Filterfunktion für Flashcards.
        """
        filtered = []
        with self.flashcards_lock:
            for card in self.flashcards:
                if category and category.lower() != "alle" and card.category.lower() != category.lower():
                    continue
                if subcategory and subcategory.lower() != "alle" and card.subcategory.lower() != subcategory.lower():
                    continue
                    
                if progress:
                    if progress.lower() == "gekonnt" and card.consecutive_correct <= 0:
                        continue
                    elif progress.lower() == "nicht gekonnt" and card.consecutive_correct > 0:
                        continue
                        
                if difficulty_range:
                    min_diff, max_diff = difficulty_range
                    if not (min_diff <= card.difficulty_rating <= max_diff):
                        continue
                        
                filtered.append(card)
                
        logging.info(f"{len(filtered)} Flashcards nach den Kriterien gefiltert.")
        return filtered

    def filter_flashcards_by_category_and_subcategory(self, category: Optional[str], subcategory: Optional[str]) -> List[Flashcard]:
        """
        Filtert Flashcards basierend auf Kategorie und Unterkategorie.
        """
        filtered = []
        with self.flashcards_lock:
            for card in self.flashcards:
                if category and category.lower() != "alle" and card.category.lower() != category.lower():
                    continue
                if subcategory and subcategory.lower() != "alle" and card.subcategory.lower() != subcategory.lower():
                    continue
                filtered.append(card)
        logging.info(f"{len(filtered)} Flashcards nach Kategorie '{category}' und Subkategorie '{subcategory}' gefiltert.")
        return filtered


    def handle_image(self, original_image_path: str) -> str:
        """
        Kopiert ein Bild in das images-Verzeichnis und gibt den relativen Pfad zurück.
        """
        if not original_image_path:
            return ""
            
        try:
            file_extension = os.path.splitext(original_image_path)[1]
            unique_filename = f"img_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{file_extension}"
            new_image_path = os.path.join(self.images_dir, unique_filename)
                
            shutil.copy2(original_image_path, new_image_path)
            logging.info(f"Bild kopiert: {new_image_path}")
            
            return unique_filename
            
        except Exception as e:
            logging.error(f"Fehler beim Kopieren des Bildes: {e}")
            return ""

    # -----------------------------------------------------------------------------
    # KATEGORIEN VERWALTUNG
    # ------------------------------------------------------------------------------

    def load_categories(self):
        """
        Lädt Kategorien aus der Kategorien-Datei.
        """
        if os.path.exists(self.categories_file):
            try:
                with open(self.categories_file, 'r', encoding='utf-8') as f:
                    categories_data = json.load(f)
                    self.categories = defaultdict(dict, {k.lower(): {sk.lower(): sv for sk, sv in v.items()} for k, v in categories_data.items()})
                logging.info(f"{len(self.categories)} Kategorien aus {self.categories_file} geladen.")
            except Exception as e:
                logging.error(f"Fehler beim Laden der Kategorien: {e}")
                self.categories = defaultdict(dict)
        else:
            logging.warning(f"Kategorien-Datei {self.categories_file} existiert nicht. Initialisiere leere Kategorien.")
            self.categories = defaultdict(dict)

    def save_categories(self) -> bool:
        """
        Speichert die aktuellen Kategorien in der Kategorien-Datei.
        """
        try:
            with self.categories_lock:
                categories_data = {k: {sk: sv for sk, sv in v.items()} for k, v in self.categories.items()}
                temp_file_path = self.categories_file + ".tmp"
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    json.dump(categories_data, f, indent=4, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                
                shutil.move(temp_file_path, self.categories_file)
                logging.info(f"Kategorien erfolgreich in {self.categories_file} gespeichert.")
                return True

        except Exception as e:
            logging.error(f"Fehler beim Speichern der Kategorien: {e}")
            raise

    def add_category(self, category: str, subcategories: Optional[List[str]] = None) -> bool:
        """
        Fügt eine neue Kategorie mit optionalen Unterkategorien hinzu.
        """
        with self.categories_lock:
            try:
                if any(existing.lower() == category.strip().lower() for existing in self.categories.keys()):
                    logging.warning(f"Kategorie '{category}' existiert bereits")
                    return False

                category_clean = category.strip().lower()
                if not category_clean:
                    logging.error("Kategoriename darf nicht leer sein")
                    return False

                self.categories[category_clean] = {}

                if subcategories:
                    for subcat in subcategories:
                        subcat_clean = subcat.strip().lower()
                        if subcat_clean:
                            self.categories[category_clean][subcat_clean] = []

                success = self.save_categories()
                if success:
                    logging.info(f"Kategorie '{category_clean}' erfolgreich hinzugefügt mit Subkategorien: {subcategories if subcategories else 'keine'}")
                    return True
                else:
                    logging.error(f"Kategorie '{category_clean}' konnte nicht gespeichert werden")
                    return False

            except Exception as e:
                logging.error(f"Fehler beim Hinzufügen der Kategorie '{category}': {str(e)}")
                return False

    def delete_category(self, category: str) -> bool:
        """
        Löscht eine Kategorie und alle zugehörigen Flashcards.
        """
        with self.categories_lock, self.flashcards_lock:
            category_found = False
            for existing_category in list(self.categories.keys()):
                if existing_category.lower() == category.lower():
                    del self.categories[existing_category]
                    category_found = True
                    
                    self.flashcards = [card for card in self.flashcards 
                                    if card.category.lower() != category.lower()]
                    
                    self.save_categories()
                    self.save_flashcards()
                    
                    logging.info(f"Kategorie '{category}' und zugehörige Flashcards gelöscht.")
                    return True
                    
            if not category_found:
                logging.warning(f"Kategorie '{category}' zum Löschen nicht gefunden.")
            return False

    def add_subcategory(self, category: str, subcategory: str) -> bool:
        """
        Fügt eine neue Subkategorie zu einer bestehenden Kategorie hinzu.
        """
        with self.categories_lock:
            for existing_category in self.categories.keys():
                if existing_category.lower() == category.lower():
                    if subcategory.lower() in (s.lower() for s in self.categories[existing_category]):
                        logging.warning(f"Subkategorie '{subcategory}' in Kategorie '{category}' existiert bereits.")
                        return False
                    self.categories[existing_category][subcategory.lower()] = []
                    logging.info(f"Subkategorie '{subcategory}' zu Kategorie '{category}' hinzugefügt.")
                    self.save_categories()
                    return True
            logging.warning(f"Kategorie '{category}' zum Hinzufügen einer Subkategorie nicht gefunden.")
            return False

    def delete_subcategory(self, category: str, subcategory: str) -> bool:
        """
        Löscht eine Subkategorie und alle zugehörigen Flashcards.
        """
        with self.categories_lock, self.flashcards_lock:
            for existing_category in self.categories.keys():
                if existing_category.lower() == category.lower():
                    for existing_subcat in list(self.categories[existing_category].keys()):
                        if existing_subcat.lower() == subcategory.lower():
                            del self.categories[existing_category][existing_subcat]
                            
                            self.flashcards = [card for card in self.flashcards 
                                            if not (card.category.lower() == category.lower() and 
                                                card.subcategory.lower() == subcategory.lower())]
                            
                            self.save_categories()
                            self.save_flashcards()
                            
                            logging.info(f"Subkategorie '{subcategory}' aus Kategorie '{category}' und zugehörige Flashcards gelöscht.")
                            return True
                            
                    logging.warning(f"Subkategorie '{subcategory}' in Kategorie '{category}' nicht gefunden.")
                    return False
                    
            logging.warning(f"Kategorie '{category}' zum Löschen einer Subkategorie nicht gefunden.")
            return False

    def validate_category_name(self, category_name: str) -> Tuple[bool, str]:
        """
        Validiert einen Kategorienamen.
        """
        category_name = category_name.strip()
        if not category_name:
            return False, "Kategoriename darf nicht leer sein."

        if not all(c.isalnum() or c in ['.', '_', '-', ' '] for c in category_name):
            return False, "Kategoriename darf nur Buchstaben, Zahlen, Punkte, Unterstriche, Leerzeichen und Bindestriche enthalten."

        return True, ""

    # -----------------------------------------------------------------------------
    # STATISTIKEN VERWALTUNG
    # ------------------------------------------------------------------------------

    def load_stats(self):
        """
        Lädt Statistiken aus der Statistiken-Datei.
        """
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
                logging.info(f"{len(self.stats)} Statistiken aus {self.stats_file} geladen.")
            except Exception as e:
                logging.error(f"Fehler beim Laden der Statistiken: {e}")
        else:
            logging.warning(f"Statistik-Datei {self.stats_file} existiert nicht. Initialisiere leere Statistik-Liste.")
            self.stats = []

    def save_stats(self) -> bool:
        """
        Speichert die aktuellen Statistiken in der Statistiken-Datei.
        """
        try:
            with self.stats_lock:
                temp_file_path = self.stats_file + ".tmp"
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.stats, f, indent=4, ensure_ascii=False)

                shutil.move(temp_file_path, self.stats_file)
                logging.info(f"Statistiken in {self.stats_file} gespeichert.")
                return True
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Statistiken: {e}")
            raise

    # =========================================================================
    # NEU: Methode zum Zurücksetzen der Leitner-Statistiken
    # =========================================================================
    def reset_leitner_stats(self, category: Optional[str] = None):
        """
        Setzt die Leitner-spezifischen Statistiken für alle oder eine
        ausgewählte Kategorie von Karten zurück.

        Args:
            category (Optional[str]): Die Kategorie, deren Leitner-Statistiken
                                      zurückgesetzt werden sollen. Wenn None,
                                      werden alle zurückgesetzt.
        """
        logging.info(f"Setze Leitner-Statistiken zurück. Kategorie: {'Alle' if category is None else category}")
        
        with self.flashcards_lock:
            cards_to_reset = self.flashcards
            # Filtere Karten, wenn eine spezifische Kategorie angegeben ist
            if category:
                cards_to_reset = [
                    card for card in self.flashcards if card.category.lower() == category.lower()
                ]

            if not cards_to_reset:
                logging.warning("Keine Karten zum Zurücksetzen der Leitner-Statistiken gefunden.")
                return 0

            reset_count = 0
            for card in cards_to_reset:
                # Setze alle Leitner-Attribute auf ihre Standardwerte zurück
                card.leitner_points = 0
                card.leitner_level = 1
                card.leitner_positive_streak = 0
                card.leitner_negative_streak = 0
                card.leitner_last_reviewed = None
                # Setze das nächste Review-Datum auf jetzt, damit die Karte sofort wieder erscheint
                card.leitner_next_review_date = datetime.datetime.now().isoformat()
                card.leitner_in_recovery_mode = False
                card.leitner_recovery_interval = 1
                
                # Optional: Auch die neue Erfolgshistorie zurücksetzen, falls du sie implementiert hast
                if hasattr(card, 'leitner_success_history'):
                    card.leitner_success_history = []

                reset_count += 1
            
            logging.info(f"{reset_count} Karten wurden im Leitner-System zurückgesetzt.")
            
            # Speichere die Änderungen sofort, um die zurückgesetzten Daten persistent zu machen
            self.save_flashcards()
            
            return reset_count


    def format_learning_time(self, minutes: float) -> str:
        """
        Konvertiert Minuten in ein lesbares Std:Min:Sec Format.
        """
        total_seconds = int(minutes * 60)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    # -----------------------------------------------------------------------------
    # THEMEN VERWALTUNG
    # ------------------------------------------------------------------------------

    def get_theme_manager(self) -> ThemeManager:
        """
        Gibt den ThemeManager zurück.
        """
        return self.theme_manager

    # -----------------------------------------------------------------------------
    # DATEN EXPORT/IMPORT
    # ------------------------------------------------------------------------------

    def export_flashcards_to_csv(self, file_path: str) -> bool:
        """
        Exportiert die Flashcards in eine CSV-Datei.
        """
        import csv
        try:
            with self.flashcards_lock:
                with open(file_path, 'w', encoding='utf-8', newline='') as csvfile:
                    fieldnames = ['question', 'answer', 'category', 'subcategory', 'tags', 'hint', 'source', 'image_path']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for card in self.flashcards:
                        writer.writerow({
                            'question': card.question,
                            'answer': card.answer,
                            'category': card.category,
                            'subcategory': card.subcategory,
                            'tags': ','.join(card.tags),
                            'hint': card.hint,
                            'source': card.source,
                            'image_path': os.path.basename(card.image_path) if card.image_path else ''
                        })
            logging.info(f"{len(self.flashcards)} Flashcards wurden nach {file_path} exportiert.")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Exportieren der Flashcards nach CSV: {e}")
            return False

    def import_flashcards_from_csv(self, file_path: str) -> List[Flashcard]:
        """
        Importiert Flashcards aus einer CSV-Datei.
        """
        import csv
        imported_cards = []
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if not row.get('question') or not row.get('answer'):
                        logging.warning(f"Flashcard mit fehlender Frage oder Antwort übersprungen: {row}")
                        continue

                    flashcard = Flashcard(
                        question=row.get('question', '').strip(),
                        answer=row.get('answer', '').strip(),
                        category=row.get('category', '').strip(),
                        subcategory=row.get('subcategory', '').strip(),
                        tags=[tag.strip() for tag in row.get('tags', '').split(',') if tag.strip()],
                        hint=row.get('hint', '').strip(),
                        source=row.get('source', '').strip(),
                        image_path=row.get('image_path', '').strip() or None
                    )
                    if self.add_flashcard(flashcard):
                        imported_cards.append(flashcard)
            logging.info(f"{len(imported_cards)} Flashcards wurden aus {file_path} importiert.")
            return imported_cards
        except Exception as e:
            logging.error(f"Fehler beim Importieren der Flashcards aus CSV: {e}")
            return imported_cards

    # -----------------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------------------

    def get_all_tags(self) -> List[str]:
        """
        Gibt eine sortierte Liste aller Tags zurück.
        """
        tags = set()
        with self.flashcards_lock:
            for card in self.flashcards:
                for tag in card.tags:
                    tags.add(tag.lower())
        return sorted(tags)

    # -----------------------------------------------------------------------------
    # SM2 ALGORITHMUS
    # ------------------------------------------------------------------------------

    def update_srs_sm2(self, flashcard: Flashcard, quality: int):
        """
        Aktualisiert die SRS-Parameter eines Flashcards basierend auf der Bewertung.
        """
        if quality < 0 or quality > 5:
            logging.warning("Qualitätsbewertung muss zwischen 0 und 5 liegen.")
            return

        if quality >= 3:
            if flashcard.consecutive_correct == 0:
                flashcard.interval = 1
            elif flashcard.consecutive_correct == 1:
                flashcard.interval = 6
            else:
                flashcard.interval = int(flashcard.interval * flashcard.ease_factor)
            flashcard.consecutive_correct += 1
            flashcard.ease_factor += SM2_EASE_FACTOR_INCREMENT
        else:
            flashcard.consecutive_correct = 0
            flashcard.interval = 1
            flashcard.ease_factor -= SM2_EASE_FACTOR_DECREMENT
            if flashcard.ease_factor < SM2_EASE_FACTOR_MIN:
                flashcard.ease_factor = SM2_EASE_FACTOR_MIN

        flashcard.ease_factor = max(flashcard.ease_factor, SM2_EASE_FACTOR_MIN)
        flashcard.last_reviewed = datetime.date.today().strftime("%d.%m.%Y")
        flashcard.next_review = (datetime.date.today() + datetime.timedelta(days=flashcard.interval)).strftime("%d.%m.%Y")
        flashcard.repetitions += 1
        if quality >= 3:
            flashcard.success_count += 1

        logging.info(
            f"Flashcard '{flashcard.question}' aktualisiert: "
            f"Interval={flashcard.interval}, Ease Factor={flashcard.ease_factor}, "
            f"Consecutive Correct={flashcard.consecutive_correct}"
        )

        try:
            self.save_flashcards()
            logging.info(f"Flashcard '{flashcard.question}' erfolgreich gespeichert.")
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Flashcard '{flashcard.question}': {e}")
            messagebox.showerror("Fehler", f"Beim Speichern der Flashcard ist ein Fehler aufgetreten:\n{e}")

    # -----------------------------------------------------------------------------
    # BACKUP MANAGER
    # ------------------------------------------------------------------------------

    def backup_themes(self, reason: str = "update") -> bool:
        """
        Erstellt ein Backup der aktuellen Themes.
        """
        timestamp = datetime.datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
        backup_filename = f"theme_backup_{reason}_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        try:
            self.theme_manager.export_themes(backup_path)
            logging.info(f"Themes-Backup erstellt: {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Theme-Backups: {e}")
            return False

    def backup_flashcards(self, reason: str = "backup") -> bool:
        """
        Erstellt ein Backup der aktuellen Flashcards.
        """
        timestamp = datetime.datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
        backup_filename = f"flashcards_backup_{reason}_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        try:
            with self.flashcards_lock:
                flashcards_data = [card.to_dict() for card in self.flashcards]
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(flashcards_data, f, indent=4, ensure_ascii=False)
            logging.info(f"Flashcards-Backup erstellt: {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Flashcards-Backups: {e}")
            return False

# ------------------------------------------------------------------------------
# INITIALISIERUNG DES LOGGINGS UND BEISPIELFUNKTION
# ------------------------------------------------------------------------------

def main():
    """
    Hauptfunktion zur Initialisierung des DataManagers und Testen der Funktionen.
    """
    initialize_logging()

    data_manager = DataManager()

    flashcard = Flashcard(
        question="Was ist die Hauptstadt von Frankreich?",
        answer="Paris",
        category="Geographie",
        subcategory="Hauptstädte",
        tags=["Europa", "Städte"],
        hint="Bekannt für den Eiffelturm",
        source="Lehrbuch Kapitel 3",
        image_path="path/to/image.jpg"
    )

    if data_manager.add_flashcard(flashcard):
        logging.info("Neue Flashcard erfolgreich hinzugefügt.")
    else:
        logging.info("Flashcard konnte nicht hinzugefügt werden.")

    due_flashcards = data_manager.get_due_flashcards()
    logging.info(f"Anzahl fälliger Flashcards: {len(due_flashcards)}")


if __name__ == "__main__":
    main()
