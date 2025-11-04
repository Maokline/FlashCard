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
                      daily_target: int = 20,
                      all_learning_sets: Optional[List[Dict]] = None) -> bool:
        """
        Verteilt Sessions intelligent über 7 Tage mit verbesserter Logik.

        Args:
            start_date: Startdatum der Woche (normalerweise Montag)
            active_learning_set: Das primäre Lernset (deprecated, nutze all_learning_sets)
            daily_target: Ziel-Anzahl Karten pro Tag
            all_learning_sets: Liste aller Lernsets des Planers

        Returns:
            bool: True wenn erfolgreich
        """
        try:
            logging.info(f"Starte intelligente Auto-Planung für Woche ab {start_date}")

            # Lösche bestehende Auto-generierte Einträge für diese Woche
            self._clear_auto_generated_entries(start_date)

            # Verwende all_learning_sets wenn verfügbar, sonst Fallback
            learning_sets = all_learning_sets if all_learning_sets else ([active_learning_set] if active_learning_set else [])

            if not learning_sets:
                logging.warning("Keine Lernsets für Auto-Planung verfügbar")
                return False

            # Sammle alle Kategorien aus allen Lernsets
            all_categories = set()
            for lernset in learning_sets:
                if not lernset or 'kategorien' not in lernset:
                    continue
                for kat_entry in lernset['kategorien']:
                    cat = kat_entry['kategorie']
                    for subcat in kat_entry.get('unterkategorien', []):
                        all_categories.add((cat, subcat))

            if not all_categories:
                logging.warning("Keine Kategorien in Lernsets gefunden")
                return False

            # Berechne Scores für alle Kategorien einmalig
            category_scores = {}
            for cat, subcat in all_categories:
                score_result = self.category_scorer.calculate_score(cat, subcat, start_date)
                category_scores[(cat, subcat)] = score_result

            # Sortiere Kategorien nach Score
            sorted_categories = sorted(
                category_scores.items(),
                key=lambda x: x[1]['total_score'],
                reverse=True
            )

            # Intelligente Verteilung über die Woche
            used_categories_per_day = {i: set() for i in range(7)}
            sessions_per_day = {i: [] for i in range(7)}

            # Berechne optimale Sessions pro Tag basierend auf Lernset-Zielen
            total_daily_goals = sum(ls.get('taegliches_ziel', 20) for ls in learning_sets)
            avg_cards_per_day = total_daily_goals // len(learning_sets) if learning_sets else 20

            # Verteile High-Priority Kategorien zuerst
            for (cat, subcat), score_data in sorted_categories:
                # Finde besten Tag für diese Kategorie
                best_day = self._find_best_day_for_category(
                    cat,
                    used_categories_per_day,
                    sessions_per_day,
                    score_data
                )

                if best_day is not None:
                    used_categories_per_day[best_day].add(cat)

                    # Berechne erwartete Karten intelligent
                    due_cards = score_data['details']['fällige_karten']
                    overdue_cards = score_data['details']['überfällige_karten']
                    expected_cards = min(
                        due_cards + overdue_cards,
                        avg_cards_per_day  # Begrenze auf Tagesziel
                    )

                    # Bestimme Priorität
                    if score_data['total_score'] >= 75:
                        prioritaet = 'hoch'
                    elif score_data['total_score'] >= 50:
                        prioritaet = 'mittel'
                    else:
                        prioritaet = 'niedrig'

                    session = {
                        'kategorie': cat,
                        'unterkategorie': subcat,
                        'erwartete_karten': expected_cards if expected_cards > 0 else 10,
                        'prioritaet': prioritaet,
                        'score': score_data['total_score']
                    }
                    sessions_per_day[best_day].append(session)

            # Erstelle tatsächliche Plan-Einträge
            for day_offset in range(7):
                date = start_date + datetime.timedelta(days=day_offset)

                for session in sessions_per_day[day_offset]:
                    self.data_manager.add_plan_entry(
                        date=date,
                        kategorie=session['kategorie'],
                        unterkategorie=session['unterkategorie'],
                        aktion='lernen',
                        erwartete_karten=session['erwartete_karten'],
                        prioritaet=session['prioritaet'],
                        auto_generiert=True
                    )

                    logging.info(
                        f"Session geplant: {session['kategorie']}/{session['unterkategorie']} "
                        f"am {date} (Score: {session['score']:.1f}, Karten: {session['erwartete_karten']})"
                    )

            logging.info("Intelligente Auto-Planung erfolgreich abgeschlossen.")
            return True

        except Exception as e:
            logging.error(f"Fehler bei Auto-Planung: {e}", exc_info=True)
            return False

    def _find_best_day_for_category(self, category: str, used_categories_per_day: Dict,
                                    sessions_per_day: Dict, score_data: Dict) -> Optional[int]:
        """
        Findet den besten Tag für eine Kategorie basierend auf:
        - Bereits geplante Kategorien (Vermeidung von Duplikaten)
        - Gleichmäßige Verteilung
        - Dringlichkeit

        Returns:
            int: Tag-Index (0-6) oder None wenn Woche voll
        """
        # Berechne "Last" pro Tag
        day_loads = []
        for day in range(7):
            # Bevorzuge Tage ohne diese Kategorie
            if category in used_categories_per_day[day]:
                penalty = 1000  # Sehr hohe Strafe
            else:
                penalty = 0

            # Bevorzuge Tage mit weniger Sessions
            session_count = len(sessions_per_day[day])

            # Gesamt-Last
            load = penalty + session_count * 10
            day_loads.append((day, load))

        # Sortiere nach Last (aufsteigend)
        day_loads.sort(key=lambda x: x[1])

        # Prüfe ob bester Tag akzeptabel ist
        best_day, best_load = day_loads[0]

        # Maximal 4 Sessions pro Tag
        if len(sessions_per_day[best_day]) >= 4:
            return None

        return best_day

    def _clear_auto_generated_entries(self, start_date: datetime.date):
        """Löscht alle auto-generierten Einträge für eine Woche."""
        for day_offset in range(7):
            date = start_date + datetime.timedelta(days=day_offset)
            entries = self.data_manager.get_plan_for_date(date)

            for entry in entries:
                if entry.get('auto_generiert', False):
                    self.data_manager.delete_plan_entry(entry['id'])

    def auto_plan_week_with_preferences(self, start_date: datetime.date,
                                       all_learning_sets: List[Dict],
                                       preferences: Dict,
                                       day_weights: List[float]) -> bool:
        """
        Verteilt Sessions intelligent über 7 Tage mit Berücksichtigung der Nutzerpräferenzen.

        Args:
            start_date: Startdatum der Woche (normalerweise Montag)
            all_learning_sets: Liste aller Lernsets des Planers
            preferences: Dict mit Nutzerpräferenzen:
                - priorities: Dict mit Prioritäten (success_rate, due_date, even_distribution)
                - total_cards: Gewünschte Anzahl Karten für die Woche
                - priority_category: Priorisierte Kategorie (optional)
                - daily_distribution: Dict mit Tagesverteilung
            day_weights: Liste von 7 Gewichten für jeden Tag (Montag-Sonntag)

        Returns:
            bool: True wenn erfolgreich
        """
        try:
            logging.info(f"Starte intelligente Auto-Planung mit Präferenzen für Woche ab {start_date}")
            logging.info(f"Präferenzen: {preferences}")
            logging.info(f"Tagesgewichte: {day_weights}")

            # Lösche bestehende Auto-generierte Einträge für diese Woche
            self._clear_auto_generated_entries(start_date)

            if not all_learning_sets:
                logging.warning("Keine Lernsets für Auto-Planung verfügbar")
                return False

            # Sammle alle Kategorien aus allen Lernsets
            all_categories = set()
            for lernset in all_learning_sets:
                if not lernset or 'kategorien' not in lernset:
                    continue
                for kat_entry in lernset['kategorien']:
                    cat = kat_entry['kategorie']
                    for subcat in kat_entry.get('unterkategorien', []):
                        all_categories.add((cat, subcat))

            if not all_categories:
                logging.warning("Keine Kategorien in Lernsets gefunden")
                return False

            # Berechne Scores für alle Kategorien mit angepassten Gewichten
            category_scores = {}
            for cat, subcat in all_categories:
                score_result = self.category_scorer.calculate_score(cat, subcat, start_date)

                # Prüfe ob dies eine neue Kategorie ist
                is_new_category = self._is_new_category(cat, subcat, start_date)

                # Passe Score basierend auf Prioritäten an
                adjusted_score = self._adjust_score_by_preferences(
                    score_result,
                    cat,
                    preferences
                )

                # Erhöhe Score für neue Kategorien
                if is_new_category:
                    adjusted_score *= 1.3  # 30% Bonus für neue Kategorien
                    logging.info(f"Neue Kategorie erkannt: {cat}/{subcat} - Score erhöht")

                category_scores[(cat, subcat)] = {
                    **score_result,
                    'adjusted_score': adjusted_score,
                    'is_new': is_new_category
                }

            # Sortiere Kategorien nach angepasstem Score
            sorted_categories = sorted(
                category_scores.items(),
                key=lambda x: x[1]['adjusted_score'],
                reverse=True
            )

            # Intelligente Verteilung über die Woche mit Tagesgewichten
            used_categories_per_day = {i: set() for i in range(7)}
            sessions_per_day = {i: [] for i in range(7)}
            cards_per_day = {i: 0 for i in range(7)}

            # Berechne Ziel-Karten pro Tag basierend auf Gewichten
            total_cards = preferences['total_cards']
            target_cards_per_day = [total_cards * (w / 7.0) for w in day_weights]

            # Verteile High-Priority Kategorien zuerst
            for (cat, subcat), score_data in sorted_categories:
                # Finde besten Tag für diese Kategorie basierend auf Gewichten und aktueller Auslastung
                best_day = self._find_best_day_with_weights(
                    cat,
                    used_categories_per_day,
                    cards_per_day,
                    target_cards_per_day,
                    score_data,
                    preferences
                )

                if best_day is not None:
                    used_categories_per_day[best_day].add(cat)

                    # Berechne erwartete Karten intelligent
                    due_cards = score_data['details']['fällige_karten']
                    overdue_cards = score_data['details']['überfällige_karten']

                    # Hole Kartengrenzen aus Präferenzen
                    day_card_limits = preferences.get('day_card_limits', [999] * 7)

                    # Berechne maximale Karten für diesen Tag basierend auf verbleibendem Budget
                    remaining_budget = target_cards_per_day[best_day] - cards_per_day[best_day]
                    day_limit_remaining = day_card_limits[best_day] - cards_per_day[best_day]

                    expected_cards = min(
                        due_cards + overdue_cards,
                        int(remaining_budget),
                        int(day_limit_remaining),  # Berücksichtige Tages-Limit
                        50  # Maximale Session-Größe
                    )

                    if expected_cards < 5:
                        expected_cards = 5  # Mindestens 5 Karten

                    cards_per_day[best_day] += expected_cards

                    # Bestimme Priorität
                    if score_data['adjusted_score'] >= 75:
                        prioritaet = 'hoch'
                    elif score_data['adjusted_score'] >= 50:
                        prioritaet = 'mittel'
                    else:
                        prioritaet = 'niedrig'

                    session = {
                        'kategorie': cat,
                        'unterkategorie': subcat,
                        'erwartete_karten': expected_cards,
                        'prioritaet': prioritaet,
                        'score': score_data['adjusted_score'],
                        'is_new': score_data.get('is_new', False)
                    }

                    sessions_per_day[best_day].append(session)

            # Speichere Sessions
            for day_offset, day_sessions in sessions_per_day.items():
                date = start_date + datetime.timedelta(days=day_offset)

                for session in day_sessions:
                    # Füge Marker für neue Kategorien hinzu
                    notiz = ""
                    if session.get('is_new', False):
                        notiz = "🆕 Neue Kategorie - Optimal zum Einstieg!"

                    self.data_manager.add_plan_entry(
                        date=date,
                        kategorie=session['kategorie'],
                        unterkategorie=session['unterkategorie'],
                        aktion='lernen',
                        erwartete_karten=session['erwartete_karten'],
                        prioritaet=session['prioritaet'],
                        auto_generiert=True,
                        notiz=notiz
                    )

                    new_marker = " [NEU]" if session.get('is_new', False) else ""
                    logging.info(
                        f"Session geplant: {session['kategorie']}/{session['unterkategorie']}{new_marker} "
                        f"am {date} (Score: {session['score']:.1f}, Karten: {session['erwartete_karten']})"
                    )

            logging.info("Intelligente Auto-Planung mit Präferenzen erfolgreich abgeschlossen.")
            return True

        except Exception as e:
            logging.error(f"Fehler bei Auto-Planung mit Präferenzen: {e}", exc_info=True)
            return False

    def _is_new_category(self, category: str, subcategory: str, reference_date: datetime.date) -> bool:
        """
        Prüft ob eine Kategorie/Unterkategorie neu ist.

        Eine Kategorie gilt als neu wenn:
        1. Sie noch nie gelernt wurde (keine Statistiken vorhanden)
        2. Die letzte Lernsession mehr als 7 Tage zurückliegt
        3. Weniger als 10 Karten der Kategorie gelernt wurden

        Args:
            category: Kategorie-Name
            subcategory: Unterkategorie-Name
            reference_date: Referenzdatum für die Prüfung

        Returns:
            bool: True wenn Kategorie als neu gilt
        """
        try:
            # Hole alle Flashcards der Kategorie/Unterkategorie
            flashcards = self.data_manager.flashcards
            matching_cards = [
                card for card in flashcards
                if card.get('kategorie') == category and card.get('unterkategorie') == subcategory
            ]

            if not matching_cards:
                return False  # Keine Karten vorhanden

            # Prüfe wie viele Karten bereits gelernt wurden
            learned_count = 0
            last_review_date = None

            for card in matching_cards:
                review_history = card.get('review_history', [])
                if review_history:
                    learned_count += 1
                    # Finde das neueste Review-Datum
                    for review in review_history:
                        review_date_str = review.get('date')
                        if review_date_str:
                            try:
                                review_date = datetime.datetime.fromisoformat(review_date_str).date()
                                if last_review_date is None or review_date > last_review_date:
                                    last_review_date = review_date
                            except:
                                pass

            # Kriterien für "neue" Kategorie
            total_cards = len(matching_cards)

            # Weniger als 20% der Karten wurden gelernt
            if learned_count < total_cards * 0.2:
                return True

            # Letzte Review ist mehr als 14 Tage her oder nie
            if last_review_date is None:
                return True

            days_since_last_review = (reference_date - last_review_date).days
            if days_since_last_review > 14:
                return True

            return False

        except Exception as e:
            logging.error(f"Fehler bei Prüfung ob Kategorie neu ist: {e}", exc_info=True)
            return False

    def _adjust_score_by_preferences(self, score_result: Dict, category: str, preferences: Dict) -> float:
        """
        Passt den Score einer Kategorie basierend auf Nutzerpräferenzen an.

        Args:
            score_result: Ursprünglicher Score-Result
            category: Kategorie-Name
            preferences: Nutzerpräferenzen

        Returns:
            float: Angepasster Score
        """
        base_score = score_result['total_score']
        priorities = preferences['priorities']
        priority_category = preferences.get('priority_category')

        # Gewichte für verschiedene Komponenten
        weights = {
            'success_rate': 0.3 if priorities.get('success_rate', True) else 0.1,
            'due_date': 0.5 if priorities.get('due_date', True) else 0.2,
            'even_distribution': 0.2 if priorities.get('even_distribution', True) else 0.1
        }

        # Normalisiere Gewichte
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}

        # Berechne gewichteten Score
        # Invertiere Erfolgsquote, um Karten mit geringer Erfolgsquote zu bevorzugen
        # Je niedriger die Erfolgsquote, desto höher der Score
        raw_success_rate = score_result['details'].get('erfolgsquote', 50)
        success_component = 100 - raw_success_rate  # Invertierung

        due_component = min(100, (score_result['details'].get('fällige_karten', 0) +
                                  score_result['details'].get('überfällige_karten', 0)) * 2)

        adjusted_score = (
            success_component * weights['success_rate'] +
            due_component * weights['due_date'] +
            base_score * weights['even_distribution']
        )

        # Bonus für priorisierte Kategorie
        if priority_category and category == priority_category:
            adjusted_score *= 1.5  # 50% Bonus

        return adjusted_score

    def _find_best_day_with_weights(self, category: str, used_categories_per_day: Dict,
                                   cards_per_day: Dict, target_cards_per_day: List[float],
                                   score_data: Dict, preferences: Dict) -> Optional[int]:
        """
        Findet den besten Tag für eine Kategorie basierend auf Tagesgewichten.

        Args:
            category: Kategorie-Name
            used_categories_per_day: Dict mit bereits geplanten Kategorien pro Tag
            cards_per_day: Dict mit bereits geplanten Karten pro Tag
            target_cards_per_day: Liste mit Ziel-Karten pro Tag
            score_data: Score-Daten der Kategorie
            preferences: Nutzerpräferenzen

        Returns:
            int: Tag-Index (0-6) oder None wenn Woche voll
        """
        # Hole Kartengrenzen aus Präferenzen (falls vorhanden)
        day_card_limits = preferences.get('day_card_limits', [999] * 7)

        # Berechne "Last" pro Tag
        day_loads = []
        for day in range(7):
            # Prüfe ob Tag freigegeben ist (Limit = 0)
            if day_card_limits[day] == 0:
                # Sehr hohe Strafe für freie Tage
                day_loads.append((day, 10000))
                continue

            # Prüfe ob Tages-Limit bereits erreicht
            if cards_per_day[day] >= day_card_limits[day]:
                # Sehr hohe Strafe für volle Tage
                day_loads.append((day, 9000))
                continue

            # Bevorzuge Tage ohne diese Kategorie
            if category in used_categories_per_day[day]:
                penalty = 1000  # Sehr hohe Strafe
            else:
                penalty = 0

            # Bevorzuge Tage, die noch unter ihrem Ziel sind
            remaining_capacity = min(target_cards_per_day[day], day_card_limits[day]) - cards_per_day[day]
            if remaining_capacity < 5:
                capacity_penalty = 500  # Hohe Strafe für volle Tage
            else:
                capacity_penalty = 0

            # Bevorzuge gleichmäßige Verteilung
            distribution_score = abs(cards_per_day[day] - target_cards_per_day[day])

            # Gesamt-Last
            load = penalty + capacity_penalty + distribution_score

            day_loads.append((day, load))

        # Sortiere nach Last (aufsteigend)
        day_loads.sort(key=lambda x: x[1])

        # Prüfe ob bester Tag akzeptabel ist
        best_day, best_load = day_loads[0]

        # Maximal 5 Sessions pro Tag
        if len(used_categories_per_day[best_day]) >= 5:
            return None

        # Prüfe ob Tag noch Kapazität hat
        if best_load >= 1000:
            return None

        return best_day
