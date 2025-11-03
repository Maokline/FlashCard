#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kalender-System für FlashCards mit intelligenten Lernempfehlungen.
Implementiert einen KI-gestützten Scoring-Algorithmus basierend auf 4 Faktoren:
1. Dringlichkeit (fällige Karten)
2. Effizienz (Erfolgsquote & Leitner-Level)
3. Lernrhythmus (Zeit seit letzter Session)
4. Ausgeglichenheit (Rotation der Kategorien)
"""

import datetime
import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import uuid


class CategoryScorer:
    """
    Bewertet Kategorien für Lernempfehlungen basierend auf 4 Faktoren.
    """

    def __init__(self, data_manager, leitner_system):
        """
        Initialisiert den CategoryScorer.

        Args:
            data_manager: DataManager-Instanz für Zugriff auf Karten und Statistiken
            leitner_system: LeitnerSystem-Instanz für Zugriff auf Due-Cards
        """
        self.data_manager = data_manager
        self.leitner_system = leitner_system
        logging.info("CategoryScorer initialisiert.")

    def calculate_score(self, category: str, subcategory: str,
                       date: datetime.date, weights: Optional[Dict] = None) -> Dict:
        """
        Berechnet Gesamt-Score für eine Kategorie/Unterkategorie.

        Args:
            category: Die Hauptkategorie
            subcategory: Die Unterkategorie
            date: Das Datum für die Bewertung
            weights: Optionale Gewichtungen (sonst aus algorithm_settings)

        Returns:
            dict: {
                'total_score': float (0-100),
                'breakdown': {
                    'dringlichkeit': float,
                    'effizienz': float,
                    'lernrhythmus': float,
                    'ausgeglichenheit': float
                },
                'details': {
                    'fällige_karten': int,
                    'überfällige_karten': int,
                    'erfolgsquote': float,
                    'tage_seit_letztem_lernen': int,
                    'durchschnittliches_level': float
                }
            }
        """
        # Hole Gewichtungen
        if weights is None:
            weights = self.data_manager.get_algorithm_weights()

        # Berechne die 4 Faktoren
        urgency_score = self.calculate_urgency_score(category, subcategory)
        efficiency_score = self.calculate_efficiency_score(category, subcategory)
        rhythm_score = self.calculate_rhythm_score(category, subcategory)
        balance_score = self.calculate_balance_score(category, date)

        # Gewichtete Gesamt-Score
        total_score = (
            urgency_score * (weights['dringlichkeit'] / 100) +
            efficiency_score * (weights['effizienz'] / 100) +
            rhythm_score * (weights['lernrhythmus'] / 100) +
            balance_score * (weights['ausgeglichenheit'] / 100)
        )

        # Details sammeln
        details = self._get_category_details(category, subcategory)

        return {
            'total_score': round(total_score, 2),
            'breakdown': {
                'dringlichkeit': round(urgency_score, 2),
                'effizienz': round(efficiency_score, 2),
                'lernrhythmus': round(rhythm_score, 2),
                'ausgeglichenheit': round(balance_score, 2)
            },
            'details': details
        }

    def calculate_urgency_score(self, category: str, subcategory: str) -> float:
        """
        Berechnet Dringlichkeits-Score basierend auf fälligen und überfälligen Karten.

        Returns:
            float: Score 0-100
        """
        today = datetime.datetime.now()
        today_due = 0
        overdue = 0
        total_cards = 0

        # Filtere Karten nach Kategorie/Unterkategorie
        for card_id, leitner_card in self.leitner_system.cards.items():
            if leitner_card.category.lower() != category.lower():
                continue
            if leitner_card.subcategory.lower() != subcategory.lower():
                continue

            total_cards += 1

            # Prüfe ob fällig oder überfällig
            if leitner_card.next_review_date <= today:
                days_overdue = (today - leitner_card.next_review_date).days
                if days_overdue > 0:
                    overdue += 1
                else:
                    today_due += 1

        if total_cards == 0:
            return 0.0

        # Gewichtung: Überfällige schwerer (3x), Heute fällige normal (1.5x)
        weighted_score = (overdue * 3 + today_due * 1.5)
        max_possible = total_cards * 3  # Wenn alle überfällig wären

        # Normalisiere auf 0-100
        score = (weighted_score / max_possible * 100) if max_possible > 0 else 0
        return min(score, 100)

    def calculate_efficiency_score(self, category: str, subcategory: str) -> float:
        """
        Berechnet Effizienz-Score basierend auf Erfolgsquote und Leitner-Level.

        Returns:
            float: Score 0-100
        """
        # Hole Statistiken für diese Kategorie/Unterkategorie
        stats_manager = self.data_manager
        if not hasattr(stats_manager, 'stats'):
            return 50.0  # Neutral wenn keine Statistiken

        success_rate = self._get_success_rate(category, subcategory)
        avg_level = self._get_average_level(category, subcategory)

        # Erfolgsquoten-basierter Score (invers: niedrig = mehr Übung nötig)
        if success_rate < 60:
            success_score = 100
        elif success_rate < 70:
            success_score = 80
        elif success_rate < 80:
            success_score = 60
        else:
            success_score = 40

        # Level-basierter Bonus (niedrige Level = mehr Übung nötig)
        if avg_level < 3:
            level_bonus = 20
        elif avg_level < 5:
            level_bonus = 10
        else:
            level_bonus = 0

        final_score = min(success_score + level_bonus, 100)
        return final_score

    def calculate_rhythm_score(self, category: str, subcategory: str) -> float:
        """
        Berechnet Lernrhythmus-Score basierend auf Zeit seit letzter Session.

        Returns:
            float: Score 0-100
        """
        last_session_date = self._get_last_session_date(category, subcategory)

        if last_session_date is None:
            return 100  # Noch nie gelernt = höchste Priorität

        today = datetime.date.today()
        days_since = (today - last_session_date).days

        # Je länger her, desto höher der Score
        if days_since >= 7:
            return 100
        elif days_since >= 5:
            return 80
        elif days_since >= 3:
            return 60
        elif days_since >= 2:
            return 40
        else:
            return 20

    def calculate_balance_score(self, category: str, date: datetime.date) -> float:
        """
        Berechnet Ausgeglichenheits-Score basierend auf Häufigkeit in dieser Woche.

        Args:
            category: Die Hauptkategorie
            date: Das Datum für die Bewertung

        Returns:
            float: Score 0-100
        """
        # Hole Wochenstart (Montag)
        week_start = date - datetime.timedelta(days=date.weekday())

        # Zähle, wie oft diese Kategorie in dieser Woche geplant wurde
        count_this_week = 0
        for i in range(7):
            day = week_start + datetime.timedelta(days=i)
            entries = self.data_manager.get_plan_for_date(day)
            for entry in entries:
                if entry['kategorie'].lower() == category.lower():
                    count_this_week += 1

        # Weniger = höherer Score (Rotation fördern)
        if count_this_week == 0:
            return 100
        elif count_this_week == 1:
            return 70
        elif count_this_week == 2:
            return 40
        else:
            return 10

    def _get_success_rate(self, category: str, subcategory: str) -> float:
        """Berechnet die Erfolgsquote für eine Kategorie/Unterkategorie."""
        stats = self.data_manager.stats
        if not stats:
            return 100.0  # Neutral wenn keine Daten

        total_attempts = 0
        correct_attempts = 0

        for stat in stats:
            if not isinstance(stat, dict) or 'details' not in stat:
                continue

            for detail in stat['details']:
                if not isinstance(detail, dict):
                    continue

                if (detail.get('category', '').lower() == category.lower() and
                    detail.get('subcategory', '').lower() == subcategory.lower()):
                    total_attempts += 1
                    if detail.get('correct', False):
                        correct_attempts += 1

        if total_attempts == 0:
            return 100.0  # Noch keine Versuche

        return (correct_attempts / total_attempts * 100)

    def _get_average_level(self, category: str, subcategory: str) -> float:
        """Berechnet das durchschnittliche Leitner-Level für eine Kategorie/Unterkategorie."""
        levels = []

        for card_id, leitner_card in self.leitner_system.cards.items():
            if (leitner_card.category.lower() == category.lower() and
                leitner_card.subcategory.lower() == subcategory.lower()):
                levels.append(leitner_card.level)

        if not levels:
            return 1.0  # Default Level 1

        return sum(levels) / len(levels)

    def _get_last_session_date(self, category: str, subcategory: str) -> Optional[datetime.date]:
        """Findet das Datum der letzten Lernsession für eine Kategorie/Unterkategorie."""
        stats = self.data_manager.stats
        if not stats:
            return None

        last_date = None

        for stat in stats:
            if not isinstance(stat, dict) or 'details' not in stat or 'date' not in stat:
                continue

            # Prüfe ob diese Session die Kategorie enthält
            has_category = False
            for detail in stat['details']:
                if not isinstance(detail, dict):
                    continue
                if (detail.get('category', '').lower() == category.lower() and
                    detail.get('subcategory', '').lower() == subcategory.lower()):
                    has_category = True
                    break

            if has_category:
                try:
                    # Parse Datum (Format: "DD.MM.YYYY")
                    stat_date = datetime.datetime.strptime(stat['date'], "%d.%m.%Y").date()
                    if last_date is None or stat_date > last_date:
                        last_date = stat_date
                except ValueError:
                    continue

        return last_date

    def _get_category_details(self, category: str, subcategory: str) -> Dict:
        """Sammelt detaillierte Informationen über eine Kategorie/Unterkategorie."""
        today = datetime.datetime.now()
        today_due = 0
        overdue = 0

        for card_id, leitner_card in self.leitner_system.cards.items():
            if (leitner_card.category.lower() != category.lower() or
                leitner_card.subcategory.lower() != subcategory.lower()):
                continue

            if leitner_card.next_review_date <= today:
                days_overdue = (today - leitner_card.next_review_date).days
                if days_overdue > 0:
                    overdue += 1
                else:
                    today_due += 1

        success_rate = self._get_success_rate(category, subcategory)
        avg_level = self._get_average_level(category, subcategory)
        last_session = self._get_last_session_date(category, subcategory)

        days_since = None
        if last_session:
            days_since = (datetime.date.today() - last_session).days

        return {
            'fällige_karten': today_due,
            'überfällige_karten': overdue,
            'erfolgsquote': round(success_rate, 1),
            'tage_seit_letztem_lernen': days_since,
            'durchschnittliches_level': round(avg_level, 1)
        }

    def get_top_recommendations(self, date: datetime.date, n: int = 3,
                               learning_set: Optional[Dict] = None) -> List[Dict]:
        """
        Gibt die Top N Empfehlungen für ein Datum zurück.

        Args:
            date: Das Datum für die Empfehlungen
            n: Anzahl der Empfehlungen
            learning_set: Optionales Lernset zur Filterung

        Returns:
            List[Dict]: Sortierte Liste mit Empfehlungen
        """
        scores = []

        # Bestimme relevante Kategorien
        if learning_set and 'kategorien' in learning_set:
            # Filtere nach Lernset
            categories_to_check = []
            for kat_entry in learning_set['kategorien']:
                cat = kat_entry['kategorie']
                for subcat in kat_entry.get('unterkategorien', []):
                    categories_to_check.append((cat, subcat))
        else:
            # Alle Kategorien aus Flashcards
            categories_to_check = set()
            for card in self.data_manager.flashcards:
                categories_to_check.add((card.category, card.subcategory))

        # Berechne Scores für alle Kategorien
        for category, subcategory in categories_to_check:
            try:
                score_result = self.calculate_score(category, subcategory, date)
                score_result['kategorie'] = category
                score_result['unterkategorie'] = subcategory
                scores.append(score_result)
            except Exception as e:
                logging.error(f"Fehler beim Berechnen des Scores für {category}/{subcategory}: {e}")
                continue

        # Sortiere nach total_score (absteigend)
        scores.sort(key=lambda x: x['total_score'], reverse=True)

        # Gib Top N zurück
        return scores[:n]


class WeeklyPlanner:
    """
    Verwaltet die automatische Wochenplanung.
    """

    def __init__(self, data_manager, leitner_system, category_scorer):
        """
        Initialisiert den WeeklyPlanner.

        Args:
            data_manager: DataManager-Instanz
            leitner_system: LeitnerSystem-Instanz
            category_scorer: CategoryScorer-Instanz
        """
        self.data_manager = data_manager
        self.leitner_system = leitner_system
        self.category_scorer = category_scorer
        logging.info("WeeklyPlanner initialisiert.")

    def auto_plan_week(self, start_date: datetime.date,
                      active_learning_set: Optional[Dict] = None,
                      daily_target: int = 20) -> bool:
        """
        Verteilt Sessions intelligent über 7 Tage.

        Args:
            start_date: Startdatum der Woche (normalerweise Montag)
            active_learning_set: Das aktive Lernset
            daily_target: Ziel-Anzahl Karten pro Tag

        Returns:
            bool: True wenn erfolgreich
        """
        try:
            logging.info(f"Starte Auto-Planung für Woche ab {start_date}")

            # Lösche bestehende Auto-generierte Einträge für diese Woche
            self._clear_auto_generated_entries(start_date)

            # Jeden Tag der Woche planen
            for day_offset in range(7):
                date = start_date + datetime.timedelta(days=day_offset)

                # Hole Top-Empfehlungen für diesen Tag
                recommendations = self.category_scorer.get_top_recommendations(
                    date=date,
                    n=3,  # Top 3 pro Tag
                    learning_set=active_learning_set
                )

                # Füge Empfehlungen als Sessions hinzu
                for i, rec in enumerate(recommendations):
                    # Berechne Priorität basierend auf Score
                    if rec['total_score'] >= 80:
                        prioritaet = 'hoch'
                    elif rec['total_score'] >= 50:
                        prioritaet = 'mittel'
                    else:
                        prioritaet = 'niedrig'

                    # Füge Session hinzu
                    self.data_manager.add_plan_entry(
                        date=date,
                        kategorie=rec['kategorie'],
                        unterkategorie=rec['unterkategorie'],
                        aktion='lernen',
                        erwartete_karten=rec['details']['fällige_karten'] + rec['details']['überfällige_karten'],
                        prioritaet=prioritaet,
                        auto_generiert=True
                    )

                    logging.info(f"Session geplant: {rec['kategorie']}/{rec['unterkategorie']} "
                               f"am {date} (Score: {rec['total_score']})")

            logging.info("Auto-Planung erfolgreich abgeschlossen.")
            return True

        except Exception as e:
            logging.error(f"Fehler bei Auto-Planung: {e}", exc_info=True)
            return False

    def _clear_auto_generated_entries(self, start_date: datetime.date):
        """Löscht alle auto-generierten Einträge für eine Woche."""
        for day_offset in range(7):
            date = start_date + datetime.timedelta(days=day_offset)
            entries = self.data_manager.get_plan_for_date(date)

            for entry in entries:
                if entry.get('auto_generiert', False):
                    self.data_manager.delete_plan_entry(entry['id'])
