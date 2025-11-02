#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Leitner-System mit 10 Levels - Optimierte Version
Mit exponentiellen Multiplikatoren, Streak-System und verbessertem Punktabzug
"""

import datetime
import logging
import math
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple

class LeitnerCard:
    """
    Repräsentiert eine Lernkarte im optimierten 10-Level Leitner-System.
    """

    def __init__(self, card_id, question, answer, category, subcategory, tags=None, image_path=None):
        self.card_id = card_id
        self.question = question
        self.answer = answer
        self.category = category
        self.subcategory = subcategory
        self.tags = tags or []
        self.image_path = image_path
        
        # Leitner-spezifische Eigenschaften
        self.points = 0
        self.positive_streak = 0
        self.negative_streak = 0
        self.total_incorrect_count = 0  # NEU: Zählt alle falschen Antworten gesamt
        self.last_reviewed = datetime.datetime.now()
        self.next_review_date = datetime.datetime.now()
        self.review_history = []
        self.level = 1
        self.consecutive_correct = 0
        
        # Attribute für graduellen Wiederaufbau
        self.in_recovery_mode = False
        self.recovery_interval = 1
        self.success_history = deque(maxlen=10)
        self.success_rate = 0.0
        
        # Kompatibilität mit SRS-System
        self.repetitions = 0
        self.success_count = 0
        self.difficulty_rating = 3.0
        
    def _get_level_interval(self):
        """
        Gibt das Standard-Intervall für das aktuelle Level zurück.
        
        10-Level System:
        1: Täglich (1 Tag)
        2: Alle 2 Tage
        3: Alle 4 Tage
        4: Wöchentlich (7 Tage)
        5: Alle 10 Tage
        6: Alle 12 Tage
        7: Zwei-wöchentlich (14 Tage)
        8: Alle 20 Tage
        9: Alle 25 Tage
        10: Alle 30 Tage
        """
        intervals = {
            1: 1,     # Level 1: täglich
            2: 2,     # Level 2: alle 2 Tage
            3: 4,     # Level 3: alle 4 Tage
            4: 7,     # Level 4: wöchentlich
            5: 10,    # Level 5: alle 10 Tage
            6: 12,    # Level 6: alle 12 Tage
            7: 14,    # Level 7: zwei-wöchentlich
            8: 20,    # Level 8: alle 20 Tage
            9: 25,    # Level 9: alle 25 Tage
            10: 30    # Level 10: alle 30 Tage
        }
        return intervals.get(self.level, 1)
    
    def _update_success_rate(self, was_correct: bool):
        """
        Fügt das letzte Ergebnis zur success_history hinzu und berechnet die success_rate neu.
        """
        self.success_history.append(was_correct)
        if not self.success_history:
            self.success_rate = 0.0
        else:
            self.success_rate = sum(self.success_history) / len(self.success_history)
    
    def _get_exponential_multiplier(self):
        """
        Berechnet den exponentiellen Multiplikator basierend auf der Erfolgsquote.
        
        Piecewise exponentielle Funktion (Option A):
        - 0% -> 0x
        - 50% -> 1x (Referenzpunkt)
        - 85% -> 2x
        - 100% -> 3x (Maximum)
        """
        rate = self.success_rate * 100  # Konvertiere zu Prozent
        
        if rate <= 0:
            return 0.0
        elif rate <= 50:
            # 0-50%: Quadratischer Anstieg von 0 zu 1
            return (rate / 50) ** 2
        elif rate <= 85:
            # 50-85%: Exponentieller Anstieg von 1 zu 2
            normalized = (rate - 50) / 35  # 0 bis 1
            return 1.0 + (normalized ** 1.5)
        else:
            # 85-100%: Beschleunigter Anstieg von 2 zu 3
            normalized = (rate - 85) / 15  # 0 bis 1
            return 2.0 + (normalized ** 1.2)
    
    def _get_streak_bonus(self):
        """
        Gibt den Streak-Bonus für richtige Antworten zurück.
        
        Streak 5:  ×1.5
        Streak 10: ×2.0
        Streak 15: ×2.5
        Streak 20+: ×3.0
        """
        if self.positive_streak >= 20:
            return 3.0
        elif self.positive_streak >= 15:
            return 2.5
        elif self.positive_streak >= 10:
            return 2.0
        elif self.positive_streak >= 5:
            return 1.5
        else:
            return 1.0
    
    def _get_level_penalty_factor(self):
        """
        Gibt den Level-basierten Straf-Faktor für falsche Antworten zurück.
        
        Level 1: 1.0    Level 6: 2.25
        Level 2: 1.25   Level 7: 2.5
        Level 3: 1.5    Level 8: 2.75
        Level 4: 1.75   Level 9: 3.0
        Level 5: 2.0    Level 10: 4.0
        """
        level_factors = {
            1: 1.0,
            2: 1.25,
            3: 1.5,
            4: 1.75,
            5: 2.0,
            6: 2.25,
            7: 2.5,
            8: 2.75,
            9: 3.0,
            10: 4.0
        }
        return level_factors.get(self.level, 1.0)
    
    def _get_total_errors_factor(self):
        """
        Gibt den Faktor basierend auf der Gesamtzahl falscher Antworten zurück.
        
        1-5 falsch:   1
        6-10 falsch:  2
        11-15 falsch: 3
        16-20 falsch: 4
        21+ falsch:   5
        """
        if self.total_incorrect_count <= 5:
            return 1
        elif self.total_incorrect_count <= 10:
            return 2
        elif self.total_incorrect_count <= 15:
            return 3
        elif self.total_incorrect_count <= 20:
            return 4
        else:
            return 5
    
    def _get_streak_loss_penalty(self, broken_streak):
        """
        Gibt den Straf-Faktor für Streak-Verlust zurück.
        
        Streak 5-10:   1.5
        Streak 10-15:  2.0
        Streak 15-20:  3.0
        Streak 20+:    4.0
        """
        if broken_streak < 5:
            return 1.0  # Kein Streak-Verlust
        elif broken_streak < 10:
            return 1.5
        elif broken_streak < 15:
            return 2.0
        elif broken_streak < 20:
            return 3.0
        else:
            return 4.0

    def answer_correct(self, was_wrong_in_session=False):
        """
        Verarbeitet eine richtige Antwort mit exponentiellen Multiplikatoren und Streak-Bonus.
        
        ✓ OPTIMIERT: Session-basierte Punktevergabe
        - Wenn Karte in dieser Session bereits falsch war: +0 Punkte
        - Karte wird für Session abgeschlossen, taucht aber in nächster Session wieder auf
        
        Args:
            was_wrong_in_session (bool): True wenn die Karte bereits in dieser Session falsch war
        
        Returns: 
            tuple: (points_added, base_points, success_multiplier, streak_bonus)
        """
        # ✓ NEU: Session-basierte Logik
        if was_wrong_in_session:
            self.last_reviewed = datetime.datetime.now()
            self._update_success_rate(True)
            self.repetitions += 1
            self.success_count += 1
            
            # Setze nächstes Review-Datum auf HEUTE für erneutes Üben in nächster Session
            self.next_review_date = datetime.datetime.now()
            
            logging.info(f"Card {self.card_id} RICHTIG (nach Fehler in Session). "
                        f"+0 Punkte | Session abgeschlossen | Verfügbar für nächste Session")
            
            return (0, 0, 0.0, 0.0)  # Keine Punkte, Karte für Session abgeschlossen
        
        # ⚡ NORMALE VERARBEITUNG (wie bisher)
        self.positive_streak += 1
        self.negative_streak = 0
        self.consecutive_correct += 1
        self._update_success_rate(True)

        # Basis-Punkte
        base_points = self.positive_streak

        # Exponentieller Erfolgsquoten-Multiplikator
        success_multiplier = self._get_exponential_multiplier()
        
        # Streak-Bonus
        streak_bonus = self._get_streak_bonus()

        # Gesamte Punktberechnung
        points_to_add = max(1, int(base_points * success_multiplier * streak_bonus))
        self.points += points_to_add
        self._update_level()

        # Wenn im Recovery-Modus, graduell das Intervall erhöhen
        if self.in_recovery_mode:
            self.recovery_interval = min(self.recovery_interval * 2, self._get_level_interval())
            if self.recovery_interval >= self._get_level_interval():
                self.in_recovery_mode = False
                logging.info(f"Card {self.card_id} hat Recovery-Modus beendet (Level {self.level})")
            self.next_review_date = datetime.datetime.now() + datetime.timedelta(days=self.recovery_interval)
        else:
            self._set_next_review_date()

        self.last_reviewed = datetime.datetime.now()
        
        # Review History aktualisieren
        self.review_history.append({
            'date': self.last_reviewed,
            'result': True,
            'points_change': points_to_add,
            'new_points': self.points,
            'new_level': self.level,
            'success_rate_after': self.success_rate,
            'positive_streak': self.positive_streak,
            'success_multiplier': success_multiplier,
            'streak_bonus': streak_bonus,
            'in_recovery_mode': self.in_recovery_mode
        })
        
        logging.info(f"Card {self.card_id} CORRECT. "
                    f"Success Rate: {self.success_rate:.2%}, "
                    f"Exp. Multiplier: {success_multiplier:.2f}x, "
                    f"Streak Bonus: {streak_bonus:.1f}x, "
                    f"Points: +{points_to_add} -> {self.points} (Level {self.level})")
        
        return points_to_add, base_points, success_multiplier, streak_bonus


    def answer_incorrect(self):
        """
        Verarbeitet eine falsche Antwort mit optimiertem Punktabzug-System.
        
        ✓ OPTIMIERT: Datum-Reset auf HEUTE
        - Ermöglicht mehrfaches Üben am selben Tag
        - Karte taucht in weiteren Sessions am gleichen Tag wieder auf
        
        Returns: 
            tuple: (points_subtracted, error_factor, level_factor, streak_loss_factor)
        """
        # Speichere den alten Streak für Strafberechnung
        broken_streak = self.positive_streak
        
        # Update Streaks und Zähler
        self.negative_streak += 1
        self.positive_streak = 0
        self.consecutive_correct = 0
        self.total_incorrect_count += 1  # Gesamtzähler erhöhen
        self._update_success_rate(False)

        # Berechne die drei Faktoren
        error_factor = self._get_total_errors_factor()
        level_factor = self._get_level_penalty_factor()
        streak_loss_factor = self._get_streak_loss_penalty(broken_streak)
        
        # Punktabzug = -(Fehler-Faktor × Level-Faktor × Streak-Verlust-Faktor)
        points_to_subtract = int(error_factor * level_factor * streak_loss_factor)
        self.points = max(0, self.points - points_to_subtract)
        
        self._update_level()
        
        # ✓ GEÄNDERT: Setze Datum auf HEUTE (nicht +1 Tag)
        self.in_recovery_mode = True
        self.recovery_interval = 1
        self.next_review_date = datetime.datetime.now()  # ÃÂ¢ÃÂ¬Ã¢â¬Â¦ÃÂ¯ÃÂ¸ÃÂ Entfernt: "+ datetime.timedelta(days=1)"
        self.last_reviewed = datetime.datetime.now()
        
        self.review_history.append({
            'date': self.last_reviewed,
            'result': False,
            'points_change': -points_to_subtract,
            'new_points': self.points,
            'new_level': self.level,
            'success_rate_after': self.success_rate,
            'broken_streak': broken_streak,
            'total_incorrect': self.total_incorrect_count,
            'error_factor': error_factor,
            'level_factor': level_factor,
            'streak_loss_factor': streak_loss_factor,
            'in_recovery_mode': True
        })
        
        logging.info(f"Card {self.card_id} INCORRECT. "
                    f"Success Rate: {self.success_rate:.2%}, "
                    f"Total Errors: {self.total_incorrect_count}, "
                    f"Broken Streak: {broken_streak}, "
                    f"Factors: {error_factor} × {level_factor} × {streak_loss_factor}, "
                    f"Points: -{points_to_subtract} -> {self.points} (Level {self.level}) | "
                    f"✓ Verfügbar für nächste Session HEUTE")

        return points_to_subtract, error_factor, level_factor, streak_loss_factor

    def _update_level(self):
        """
        Aktualisiert das Level basierend auf den Punkten.
        
        10-Level Punktebereiche:
        1: 0-10
        2: 11-25
        3: 26-50
        4: 51-85
        5: 86-120
        6: 121-175
        7: 176-220
        8: 221-285
        9: 286-350
        10: 350+
        """
        if self.points <= 10:
            self.level = 1
        elif self.points <= 25:
            self.level = 2
        elif self.points <= 50:
            self.level = 3
        elif self.points <= 85:
            self.level = 4
        elif self.points <= 120:
            self.level = 5
        elif self.points <= 175:
            self.level = 6
        elif self.points <= 220:
            self.level = 7
        elif self.points <= 285:
            self.level = 8
        elif self.points <= 350:
            self.level = 9
        else:
            self.level = 10

    def _set_next_review_date(self):
        """Setzt das nächste Überprüfungsdatum basierend auf dem Level."""
        interval = self._get_level_interval()
        self.next_review_date = datetime.datetime.now() + datetime.timedelta(days=interval)


class LeitnerSystem:
    """
    Verwaltet das optimierte 10-Level Leitner-System.
    """
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.cards = {}  # Dict mit card_id: LeitnerCard
        self._load_cards()

    def get_level(self, points):
        """
        Gibt das Level basierend auf Punkten zurück.
        """
        if points <= 10:
            return 1
        elif points <= 25:
            return 2
        elif points <= 50:
            return 3
        elif points <= 85:
            return 4
        elif points <= 120:
            return 5
        elif points <= 175:
            return 6
        elif points <= 220:
            return 7
        elif points <= 285:
            return 8
        elif points <= 350:
            return 9
        else:
            return 10

    def get_level_name(self, level):
        """Gibt den Namen eines Levels zurück."""
        level_names = {
            1: "1. Grundlagen",
            2: "2. Basis",
            3: "3. Aufbau",
            4: "4. Kompetent",
            5: "5. Fortgeschritten",
            6: "6. Proficient",
            7: "7. Spezialist",
            8: "8. Experte",
            9: "9. Meister",
            10: "10. Master"
        }
        return level_names.get(level, f"{level}. Unbekannt")

    def get_card_status(self, card):
        """
        Gibt den Status einer Karte zurück.
        """
        if not isinstance(card, LeitnerCard):
            return None
        
        # Berechne days_overdue und days_until_review
        today = datetime.datetime.now().date()
        next_review_date = card.next_review_date.date()
        days_difference = (next_review_date - today).days
        
        days_overdue = max(0, -days_difference)
        days_until_review = max(0, days_difference)
            
        return {
            'points': card.points,
            'level': card.level,
            'level_name': self.get_level_name(card.level),
            'positive_streak': card.positive_streak,
            'negative_streak': card.negative_streak,
            'total_incorrect_count': card.total_incorrect_count,  # NEU
            'success_rate': card.success_rate,
            'in_recovery_mode': card.in_recovery_mode,
            'recovery_interval': card.recovery_interval,
            'next_review': card.next_review_date.strftime("%d.%m.%Y %H:%M"),
            'next_review_date': card.next_review_date,
            'last_reviewed': card.last_reviewed.strftime("%d.%m.%Y %H:%M"),
            'last_reviewed_date': card.last_reviewed,
            'interval_days': card._get_level_interval(),
            'days_overdue': days_overdue,
            'days_until_review': days_until_review,
            'exponential_multiplier': card._get_exponential_multiplier(),  # NEU
            'streak_bonus': card._get_streak_bonus()  # NEU
        }

    def reschedule_due_dates_evenly(self):
        """
        Plant die Fälligkeitstermine aller Karten einmalig neu,
        basierend auf ihrem aktuellen Leitner-Level.
        """
        logging.info("Starte einmalige Neuplanung der Fälligkeitstermine für 10-Level System...")
        all_flashcards = self.data_manager.flashcards

        if not all_flashcards:
            logging.warning("Keine Karten zur Neuplanung gefunden.")
            return False

        now = datetime.datetime.now()
        today_date = now.date()

        # Intervalle für alle 10 Level
        level_max_intervals = {
            1: 1,
            2: 2,
            3: 4,
            4: 7,
            5: 10,
            6: 12,
            7: 14,
            8: 20,
            9: 25,
            10: 30
        }

        # Gruppiere Karten nach Level
        cards_by_level = defaultdict(list)
        for fc in all_flashcards:
            if not hasattr(fc, 'leitner_points'):
                continue
            points = fc.leitner_points
            level = self.get_level(points)
            cards_by_level[level].append(fc)

        # Verteile Karten gleichmäßig über erlaubtes Intervall
        for level, cards_in_level in cards_by_level.items():
            if not cards_in_level:
                continue
                
            max_days = level_max_intervals.get(level, 1)
            num_cards = len(cards_in_level)
            
            logging.info(f"Level {level}: {num_cards} Karten, max {max_days} Tage")
            
            # Verteile gleichmäßig
            for i, card in enumerate(cards_in_level):
                if num_cards == 1:
                    offset_days = max_days
                else:
                    offset_days = int((i / (num_cards - 1)) * max_days)
                
                new_due = today_date + datetime.timedelta(days=offset_days)
                new_due_dt = datetime.datetime.combine(new_due, datetime.time(12, 0))
                
                card.leitner_next_review_date = new_due_dt.isoformat()
                
                if hasattr(card, 'id') and card.id in self.cards:
                    self.cards[card.id].next_review_date = new_due_dt

        # Speichern
        try:
            self.save_cards()
            self.data_manager.save_flashcards()
            logging.info("Neuplanung erfolgreich abgeschlossen und gespeichert.")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Speichern nach Neuplanung: {e}")
            return False

    def _load_cards(self):
        """Lädt Karten aus dem DataManager und konvertiert sie zu LeitnerCards."""
        self.cards.clear()
        if not self.data_manager or not hasattr(self.data_manager, 'flashcards'):
            logging.error("DataManager oder DataManager.flashcards nicht initialisiert.")
            return

        for card_data in self.data_manager.flashcards:
            if not hasattr(card_data, 'id') or not card_data.id:
                continue
            
            leitner_card = LeitnerCard(
                card_id=card_data.id,
                question=card_data.question,
                answer=card_data.answer,
                category=card_data.category,
                subcategory=card_data.subcategory,
                tags=card_data.tags,
                image_path=getattr(card_data, 'image_path', None)
            )

            # Bestehende Daten laden
            leitner_card.points = getattr(card_data, 'leitner_points', 0)
            leitner_card.positive_streak = getattr(card_data, 'leitner_positive_streak', 0)
            leitner_card.negative_streak = getattr(card_data, 'leitner_negative_streak', 0)
            leitner_card.total_incorrect_count = getattr(card_data, 'leitner_total_incorrect_count', 0)  # NEU
            leitner_card.in_recovery_mode = getattr(card_data, 'leitner_in_recovery_mode', False)
            leitner_card.recovery_interval = getattr(card_data, 'leitner_recovery_interval', 1)
            leitner_card.last_reviewed = self._parse_datetime(
                getattr(card_data, 'leitner_last_reviewed', None)
            )
            leitner_card.next_review_date = self._parse_datetime(
                getattr(card_data, 'leitner_next_review_date', datetime.datetime.now())
            )
            leitner_card._update_level()
            
            # Lade Erfolgshistorie
            success_history_data = getattr(card_data, 'leitner_success_history', [])
            if success_history_data:
                leitner_card.success_history.extend(success_history_data)
                leitner_card.success_rate = (
                    sum(leitner_card.success_history) / len(leitner_card.success_history)
                    if leitner_card.success_history else 0.0
                )

            self.cards[card_data.id] = leitner_card
            
        logging.info(f"{len(self.cards)} Karten in das optimierte 10-Level Leitner-System geladen.")

    def save_cards(self):
        """Speichert alle Leitner-Karten zurück in den DataManager."""
        if not self.data_manager or not hasattr(self.data_manager, 'flashcards'):
            logging.error("DataManager nicht verfügbar zum Speichern.")
            return

        for card_id, leitner_card in self.cards.items():
            matching_cards = [fc for fc in self.data_manager.flashcards if fc.id == card_id]
            if not matching_cards:
                continue
                
            card_data = matching_cards[0]
            card_data.leitner_points = leitner_card.points
            card_data.leitner_positive_streak = leitner_card.positive_streak
            card_data.leitner_negative_streak = leitner_card.negative_streak
            card_data.leitner_total_incorrect_count = leitner_card.total_incorrect_count  # NEU
            card_data.leitner_in_recovery_mode = leitner_card.in_recovery_mode
            card_data.leitner_recovery_interval = leitner_card.recovery_interval
            card_data.leitner_last_reviewed = leitner_card.last_reviewed.isoformat()
            card_data.leitner_next_review_date = leitner_card.next_review_date.isoformat()
            card_data.leitner_success_history = list(leitner_card.success_history)
            
        self.data_manager.save_flashcards()
        logging.info("Optimierte Leitner-Karten gespeichert.")

    def _parse_datetime(self, date_value):
        """Hilfsmethode zum Parsen von Datetime-Werten."""
        if isinstance(date_value, datetime.datetime):
            return date_value
        elif isinstance(date_value, str):
            try:
                return datetime.datetime.fromisoformat(date_value)
            except:
                return datetime.datetime.now()
        else:
            return datetime.datetime.now()

    def get_due_cards(self, category=None, subcategory=None, level=None):
        """
        Gibt eine Liste der fälligen Karten zurück, optional gefiltert.
        """
        now = datetime.datetime.now()
        due_cards = []
        
        for card in self.cards.values():
            if card.next_review_date <= now:
                if category and card.category != category:
                    continue
                if subcategory and card.subcategory != subcategory:
                    continue
                if level and card.level != level:
                    continue
                due_cards.append(card)
        
        return due_cards

    def get_statistics(self):
        """Gibt Statistiken über alle Karten zurück."""
        total_cards = len(self.cards)
        if total_cards == 0:
            return {}
        
        level_distribution = defaultdict(int)
        total_points = 0
        in_recovery = 0
        total_errors = 0
        
        for card in self.cards.values():
            level_distribution[card.level] += 1
            total_points += card.points
            total_errors += card.total_incorrect_count
            if card.in_recovery_mode:
                in_recovery += 1
        
        return {
            'total_cards': total_cards,
            'level_distribution': dict(level_distribution),
            'average_points': total_points / total_cards if total_cards > 0 else 0,
            'cards_in_recovery': in_recovery,
            'recovery_percentage': (in_recovery / total_cards * 100) if total_cards > 0 else 0,
            'total_errors': total_errors,
            'average_errors_per_card': total_errors / total_cards if total_cards > 0 else 0
        }
    
    def reload_cards(self):
        """Lädt die Karten neu aus dem DataManager."""
        logging.info("Lade Leitner-Karten neu...")
        old_card_ids = set(self.cards.keys())
        self.cards.clear()
        self._load_cards()
        new_card_ids = set(self.cards.keys())
        
        added = new_card_ids - old_card_ids
        removed = old_card_ids - new_card_ids
        
        if added:
            logging.info(f"{len(added)} neue Leitner-Karten hinzugefügt")
        if removed:
            logging.info(f"{len(removed)} Leitner-Karten entfernt")
        
        logging.info(f"Neuladen abgeschlossen. Gesamt: {len(self.cards)} Karten.")