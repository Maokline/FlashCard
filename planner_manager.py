#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Planer-Verwaltung für FlashCards Wochenplaner.
Ermöglicht das Erstellen und Verwalten von mehreren Planern mit unterschiedlichen Kategorien.
"""

import logging
from typing import Dict, List, Optional
import datetime
import uuid


class PlannerManager:
    """
    Verwaltet mehrere Wochenplaner mit unterschiedlichen Kategorie-Kombinationen.
    """

    def __init__(self, data_manager):
        """
        Initialisiert den PlannerManager.

        Args:
            data_manager: DataManager-Instanz
        """
        self.data_manager = data_manager

        # Initialisiere Planer-Struktur wenn noch nicht vorhanden
        if not hasattr(self.data_manager, 'planners') or self.data_manager.planners is None:
            self.data_manager.planners = {
                'active_planner': None,
                'planners': {}
            }
            self.data_manager.save_data()

        logging.info("PlannerManager initialisiert.")

    def create_planner(self, name: str, lernset_ids: List[str],
                      farbe: str = '#4a90e2', icon: str = '📅') -> Optional[str]:
        """
        Erstellt einen neuen Wochenplaner.

        Args:
            name: Name des Planers
            lernset_ids: Liste von Lernset-IDs die in diesem Planer verwendet werden
            farbe: Hex-Farbe für UI
            icon: Emoji-Icon für den Planer

        Returns:
            str: ID des erstellten Planers oder None bei Fehler
        """
        try:
            # Validiere Eingaben
            if not name or not name.strip():
                logging.error("Planer-Name darf nicht leer sein.")
                return None

            if not lernset_ids:
                logging.error("Planer muss mindestens ein Lernset enthalten.")
                return None

            # Validiere Lernsets
            all_sets = self.data_manager.get_all_learning_sets()
            valid_lernset_ids = []
            for lernset_id in lernset_ids:
                if lernset_id in all_sets:
                    valid_lernset_ids.append(lernset_id)
                else:
                    logging.warning(f"Lernset-ID '{lernset_id}' existiert nicht.")

            if not valid_lernset_ids:
                logging.error("Keine gültigen Lernsets für Planer gefunden.")
                return None

            # Generiere eindeutige ID
            planner_id = str(uuid.uuid4())

            # Erstelle Planer
            planner_data = {
                'id': planner_id,
                'name': name.strip(),
                'lernset_ids': valid_lernset_ids,
                'farbe': farbe,
                'icon': icon,
                'erstellt_am': datetime.datetime.now().isoformat(),
                'zuletzt_verwendet': None
            }

            # Speichere in data_manager
            if not hasattr(self.data_manager, 'planners') or self.data_manager.planners is None:
                self.data_manager.planners = {
                    'active_planner': None,
                    'planners': {}
                }

            self.data_manager.planners['planners'][planner_id] = planner_data

            # Wenn kein aktiver Planer existiert, setze diesen als aktiv
            if not self.data_manager.planners['active_planner']:
                self.data_manager.planners['active_planner'] = planner_id
                planner_data['zuletzt_verwendet'] = datetime.datetime.now().isoformat()

            self.data_manager.save_data()
            logging.info(f"Planer '{name}' erstellt mit ID {planner_id}.")

            return planner_id

        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Planers: {e}", exc_info=True)
            return None

    def update_planner(self, planner_id: str, **kwargs) -> bool:
        """
        Aktualisiert einen bestehenden Planer.

        Args:
            planner_id: ID des Planers
            **kwargs: Zu aktualisierende Felder (name, lernset_ids, farbe, icon)

        Returns:
            bool: True wenn erfolgreich
        """
        try:
            planner = self.get_planner(planner_id)
            if not planner:
                logging.error(f"Planer {planner_id} nicht gefunden.")
                return False

            # Aktualisiere Felder
            if 'name' in kwargs and kwargs['name']:
                planner['name'] = kwargs['name'].strip()

            if 'lernset_ids' in kwargs:
                planner['lernset_ids'] = kwargs['lernset_ids']

            if 'farbe' in kwargs:
                planner['farbe'] = kwargs['farbe']

            if 'icon' in kwargs:
                planner['icon'] = kwargs['icon']

            self.data_manager.save_data()
            logging.info(f"Planer {planner_id} aktualisiert.")
            return True

        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren des Planers: {e}", exc_info=True)
            return False

    def delete_planner(self, planner_id: str) -> bool:
        """
        Löscht einen Planer.

        Args:
            planner_id: ID des zu löschenden Planers

        Returns:
            bool: True wenn erfolgreich
        """
        try:
            if planner_id not in self.data_manager.planners['planners']:
                logging.error(f"Planer {planner_id} nicht gefunden.")
                return False

            # Wenn aktiver Planer gelöscht wird, aktiviere einen anderen
            if self.data_manager.planners['active_planner'] == planner_id:
                remaining = [pid for pid in self.data_manager.planners['planners'].keys()
                           if pid != planner_id]
                self.data_manager.planners['active_planner'] = remaining[0] if remaining else None

            # Lösche Planer
            del self.data_manager.planners['planners'][planner_id]
            self.data_manager.save_data()

            logging.info(f"Planer {planner_id} gelöscht.")
            return True

        except Exception as e:
            logging.error(f"Fehler beim Löschen des Planers: {e}", exc_info=True)
            return False

    def get_planner(self, planner_id: str) -> Optional[Dict]:
        """
        Gibt einen Planer zurück.

        Args:
            planner_id: ID des Planers

        Returns:
            Optional[Dict]: Planer-Daten oder None
        """
        if not hasattr(self.data_manager, 'planners') or self.data_manager.planners is None:
            return None
        return self.data_manager.planners['planners'].get(planner_id)

    def get_all_planners(self) -> Dict[str, Dict]:
        """
        Gibt alle Planer zurück.

        Returns:
            Dict[str, Dict]: Dictionary mit planner_id: planner_data
        """
        if not hasattr(self.data_manager, 'planners') or self.data_manager.planners is None:
            return {}
        return self.data_manager.planners.get('planners', {})

    def activate_planner(self, planner_id: str) -> bool:
        """
        Aktiviert einen Planer (deaktiviert alle anderen).

        Args:
            planner_id: ID des zu aktivierenden Planers

        Returns:
            bool: True wenn erfolgreich
        """
        try:
            planner = self.get_planner(planner_id)
            if not planner:
                logging.error(f"Planer {planner_id} nicht gefunden.")
                return False

            self.data_manager.planners['active_planner'] = planner_id
            planner['zuletzt_verwendet'] = datetime.datetime.now().isoformat()
            self.data_manager.save_data()

            logging.info(f"Planer '{planner['name']}' aktiviert.")
            return True

        except Exception as e:
            logging.error(f"Fehler beim Aktivieren des Planers: {e}", exc_info=True)
            return False

    def get_active_planner(self) -> Optional[Dict]:
        """
        Gibt den aktuell aktiven Planer zurück.

        Returns:
            Optional[Dict]: Aktiver Planer oder None
        """
        if not hasattr(self.data_manager, 'planners') or self.data_manager.planners is None:
            return None

        active_id = self.data_manager.planners.get('active_planner')
        if not active_id:
            return None

        return self.get_planner(active_id)

    def get_planner_lernsets(self, planner_id: str) -> List[Dict]:
        """
        Gibt alle Lernsets eines Planers zurück.

        Args:
            planner_id: ID des Planers

        Returns:
            List[Dict]: Liste von Lernset-Daten
        """
        planner = self.get_planner(planner_id)
        if not planner:
            return []

        all_sets = self.data_manager.get_all_learning_sets()
        lernsets = []

        for lernset_id in planner.get('lernset_ids', []):
            if lernset_id in all_sets:
                lernsets.append(all_sets[lernset_id])

        return lernsets

    def get_planner_categories(self, planner_id: str) -> List[tuple]:
        """
        Gibt alle Kategorie/Unterkategorie-Kombinationen eines Planers zurück.

        Args:
            planner_id: ID des Planers

        Returns:
            List[Tuple[str, str]]: Liste von (kategorie, unterkategorie) Tupeln
        """
        lernsets = self.get_planner_lernsets(planner_id)
        combinations = set()

        for lernset in lernsets:
            for kat_entry in lernset.get('kategorien', []):
                kategorie = kat_entry['kategorie']
                for unterkategorie in kat_entry.get('unterkategorien', []):
                    combinations.add((kategorie, unterkategorie))

        return list(combinations)

    def get_planner_statistics(self, planner_id: str) -> Dict:
        """
        Gibt Statistiken für einen Planer zurück.

        Args:
            planner_id: ID des Planers

        Returns:
            Dict: Statistiken
        """
        planner = self.get_planner(planner_id)
        if not planner:
            return {}

        lernsets = self.get_planner_lernsets(planner_id)

        total_lernsets = len(lernsets)
        total_categories = len(self.get_planner_categories(planner_id))

        # Berechne Gesamtziele
        total_daily_goal = sum(ls.get('taegliches_ziel', 0) for ls in lernsets)
        total_weekly_goal = sum(ls.get('woechentliches_ziel', 0) for ls in lernsets)

        return {
            'total_lernsets': total_lernsets,
            'total_categories': total_categories,
            'total_daily_goal': total_daily_goal,
            'total_weekly_goal': total_weekly_goal,
            'last_used': planner.get('zuletzt_verwendet')
        }


def get_default_planner_icons() -> List[str]:
    """
    Gibt eine Liste von Standard-Icons für Planer zurück.

    Returns:
        List[str]: Liste von Emoji-Icons
    """
    return [
        '📅', '📚', '🎯', '📖', '✏️', '🏆', '💡', '🚀',
        '⭐', '🔥', '💪', '🎓', '📝', '🌟', '🎨', '🔬'
    ]
