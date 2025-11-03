#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lernset-Verwaltung für FlashCards.
Ermöglicht das Erstellen und Verwalten von Lernsets (Ordner von Kategorien).
"""

import logging
from typing import Dict, List, Optional
import datetime


class LearningSetManager:
    """
    Verwaltet Lernsets und deren Kategorien.
    """

    def __init__(self, data_manager):
        """
        Initialisiert den LearningSetManager.

        Args:
            data_manager: DataManager-Instanz
        """
        self.data_manager = data_manager
        logging.info("LearningSetManager initialisiert.")

    def create_set(self, name: str, kategorien: List[Dict],
                  taegliches_ziel: int = 20,
                  woechentliches_ziel: int = 100,
                  farbe: str = '#4a90e2') -> Optional[str]:
        """
        Erstellt ein neues Lernset.

        Args:
            name: Name des Lernsets
            kategorien: Liste von Kategorie-Dicts [{
                'kategorie': 'Mathe',
                'unterkategorien': ['Algebra', 'Geometrie']
            }]
            taegliches_ziel: Anzahl Karten pro Tag
            woechentliches_ziel: Anzahl Karten pro Woche
            farbe: Hex-Farbe für UI

        Returns:
            str: ID des erstellten Sets oder None bei Fehler
        """
        try:
            # Validiere Eingaben
            if not name or not name.strip():
                logging.error("Lernset-Name darf nicht leer sein.")
                return None

            if not kategorien:
                logging.error("Lernset muss mindestens eine Kategorie enthalten.")
                return None

            # Validiere Kategorien
            validated_kategorien = []
            for kat_entry in kategorien:
                if not isinstance(kat_entry, dict):
                    continue
                if 'kategorie' not in kat_entry:
                    continue

                kategorie = kat_entry['kategorie'].strip()
                unterkategorien = [u.strip() for u in kat_entry.get('unterkategorien', [])]

                # Prüfe ob Kategorie existiert
                if kategorie.lower() not in [k.lower() for k in self.data_manager.categories.keys()]:
                    logging.warning(f"Kategorie '{kategorie}' existiert nicht in den Flashcards.")
                    continue

                validated_kategorien.append({
                    'kategorie': kategorie,
                    'unterkategorien': unterkategorien
                })

            if not validated_kategorien:
                logging.error("Keine gültigen Kategorien für Lernset gefunden.")
                return None

            # Erstelle Lernset
            set_id = self.data_manager.create_learning_set(
                name=name.strip(),
                kategorien=validated_kategorien,
                ziele={
                    'täglich': taegliches_ziel,
                    'wöchentlich': woechentliches_ziel
                },
                farbe=farbe
            )

            logging.info(f"Lernset '{name}' erstellt mit ID {set_id}.")
            return set_id

        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Lernsets: {e}", exc_info=True)
            return None

    def update_set(self, set_id: str, **kwargs) -> bool:
        """
        Aktualisiert ein bestehendes Lernset.

        Args:
            set_id: ID des Lernsets
            **kwargs: Zu aktualisierende Felder (name, kategorien, ziele, farbe)

        Returns:
            bool: True wenn erfolgreich
        """
        try:
            learning_set = self.get_set(set_id)
            if not learning_set:
                logging.error(f"Lernset {set_id} nicht gefunden.")
                return False

            # Aktualisiere Felder
            updates = {}
            if 'name' in kwargs and kwargs['name']:
                updates['name'] = kwargs['name'].strip()

            if 'kategorien' in kwargs:
                updates['kategorien'] = kwargs['kategorien']

            if 'taegliches_ziel' in kwargs:
                updates['taegliches_ziel'] = kwargs['taegliches_ziel']

            if 'woechentliches_ziel' in kwargs:
                updates['woechentliches_ziel'] = kwargs['woechentliches_ziel']

            if 'farbe' in kwargs:
                updates['farbe'] = kwargs['farbe']

            return self.data_manager.update_learning_set(set_id, updates)

        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren des Lernsets: {e}", exc_info=True)
            return False

    def delete_set(self, set_id: str) -> bool:
        """
        Löscht ein Lernset.

        Args:
            set_id: ID des zu löschenden Lernsets

        Returns:
            bool: True wenn erfolgreich
        """
        return self.data_manager.delete_learning_set(set_id)

    def get_set(self, set_id: str) -> Optional[Dict]:
        """
        Gibt ein Lernset zurück.

        Args:
            set_id: ID des Lernsets

        Returns:
            Optional[Dict]: Lernset-Daten oder None
        """
        all_sets = self.data_manager.get_all_learning_sets()
        return all_sets.get(set_id)

    def get_all_sets(self) -> Dict[str, Dict]:
        """
        Gibt alle Lernsets zurück.

        Returns:
            Dict[str, Dict]: Dictionary mit set_id: lernset_data
        """
        return self.data_manager.get_all_learning_sets()

    def activate_set(self, set_id: str) -> bool:
        """
        Aktiviert ein Lernset (deaktiviert alle anderen).

        Args:
            set_id: ID des zu aktivierenden Lernsets

        Returns:
            bool: True wenn erfolgreich
        """
        return self.data_manager.activate_learning_set(set_id)

    def get_active_set(self) -> Optional[Dict]:
        """
        Gibt das aktuell aktive Lernset zurück.

        Returns:
            Optional[Dict]: Aktives Lernset oder None
        """
        return self.data_manager.get_active_learning_set()

    def get_categories_from_set(self, set_id: str) -> List[Tuple[str, str]]:
        """
        Gibt alle Kategorie/Unterkategorie-Kombinationen eines Sets zurück.

        Args:
            set_id: ID des Lernsets

        Returns:
            List[Tuple[str, str]]: Liste von (kategorie, unterkategorie) Tupeln
        """
        learning_set = self.get_set(set_id)
        if not learning_set:
            return []

        combinations = []
        for kat_entry in learning_set.get('kategorien', []):
            kategorie = kat_entry['kategorie']
            for unterkategorie in kat_entry.get('unterkategorien', []):
                combinations.append((kategorie, unterkategorie))

        return combinations

    def get_available_categories(self) -> Dict[str, List[str]]:
        """
        Gibt alle verfügbaren Kategorien und Unterkategorien aus dem DataManager zurück.

        Returns:
            Dict[str, List[str]]: Dictionary mit kategorie: [unterkategorien]
        """
        available = {}
        for category_key, subcategories_dict in self.data_manager.categories.items():
            # Konvertiere zu Titelcase für bessere Darstellung
            category_display = category_key.title()
            subcats = [subcat.title() for subcat in subcategories_dict.keys()]
            available[category_display] = subcats

        return available

    def validate_set_name(self, name: str, exclude_set_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validiert einen Lernset-Namen.

        Args:
            name: Zu validierender Name
            exclude_set_id: Optional: Set-ID die ignoriert werden soll (für Updates)

        Returns:
            Tuple[bool, str]: (ist_valide, fehlermeldung)
        """
        if not name or not name.strip():
            return False, "Name darf nicht leer sein."

        # Prüfe auf doppelte Namen
        all_sets = self.get_all_sets()
        for set_id, learning_set in all_sets.items():
            if exclude_set_id and set_id == exclude_set_id:
                continue
            if learning_set['name'].lower() == name.strip().lower():
                return False, f"Ein Lernset mit dem Namen '{name}' existiert bereits."

        return True, ""

    def get_set_statistics(self, set_id: str) -> Dict:
        """
        Gibt Statistiken für ein Lernset zurück.

        Args:
            set_id: ID des Lernsets

        Returns:
            Dict: Statistiken inkl. Anzahl Karten, durchschnittliche Erfolgsquote, etc.
        """
        learning_set = self.get_set(set_id)
        if not learning_set:
            return {}

        total_cards = 0
        due_cards = 0
        total_correct = 0
        total_attempts = 0

        # Sammle Daten aus allen Kategorien des Sets
        combinations = self.get_categories_from_set(set_id)

        for category, subcategory in combinations:
            # Zähle Karten
            cards = [c for c in self.data_manager.flashcards
                    if c.category.lower() == category.lower() and
                       c.subcategory.lower() == subcategory.lower()]
            total_cards += len(cards)

            # Zähle fällige Karten aus Leitner-System
            # (benötigt leitner_system, daher optional)

            # Erfolgsquote aus Statistiken
            for stat in self.data_manager.stats:
                if not isinstance(stat, dict) or 'details' not in stat:
                    continue

                for detail in stat['details']:
                    if not isinstance(detail, dict):
                        continue

                    if (detail.get('category', '').lower() == category.lower() and
                        detail.get('subcategory', '').lower() == subcategory.lower()):
                        total_attempts += 1
                        if detail.get('correct', False):
                            total_correct += 1

        success_rate = (total_correct / total_attempts * 100) if total_attempts > 0 else 0

        return {
            'total_cards': total_cards,
            'due_cards': due_cards,
            'success_rate': round(success_rate, 1),
            'total_attempts': total_attempts,
            'categories_count': len(combinations)
        }


def get_default_colors() -> List[str]:
    """
    Gibt eine Liste von Standard-Farben für Lernsets zurück.

    Returns:
        List[str]: Liste von Hex-Farbcodes
    """
    return [
        '#4a90e2',  # Blau
        '#50c878',  # Grün
        '#ff6b6b',  # Rot
        '#ffd93d',  # Gelb
        '#a855f7',  # Lila
        '#fb923c',  # Orange
        '#38bdf8',  # Hellblau
        '#f472b6',  # Pink
    ]
