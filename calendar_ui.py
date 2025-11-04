#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kalender-UI für FlashCards mit Wochenansicht und Tagesplanung.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import logging
from typing import Optional, Dict, List
from custom_widgets import ModernButton
from calendar_system import CategoryScorer, WeeklyPlanner
from learning_sets import LearningSetManager


class WeeklyCalendarView(ttk.Frame):
    """
    Hauptansicht des Wochenkalenders mit 7-Tage-Grid und Empfehlungen.
    """

    def __init__(self, master, data_manager, leitner_system, app=None):
        """
        Initialisiert die Wochenkalender-Ansicht.

        Args:
            master: Parent-Widget
            data_manager: DataManager-Instanz
            leitner_system: LeitnerSystem-Instanz
            app: Referenz auf FlashcardApp für Session-Start
        """
        super().__init__(master)
        self.data_manager = data_manager
        self.leitner_system = leitner_system
        self.app = app

        # Initialisiere Systeme
        self.category_scorer = CategoryScorer(data_manager, leitner_system)
        self.weekly_planner = WeeklyPlanner(data_manager, leitner_system, self.category_scorer)
        self.learning_set_manager = LearningSetManager(data_manager)

        # Aktuelles Datum (Start der Woche = Montag)
        self.current_date = datetime.date.today()
        self.week_start = self._get_week_start(self.current_date)

        # UI erstellen
        self._create_ui()
        self._load_week_data()

        # Zeige Benachrichtigung für heute fällige Sessions
        self.after(500, self._check_todays_sessions)

        logging.info("WeeklyCalendarView initialisiert.")

    def _get_week_start(self, date: datetime.date) -> datetime.date:
        """Gibt den Montag der Woche zurück."""
        return date - datetime.timedelta(days=date.weekday())

    def _create_ui(self):
        """Erstellt die Benutzeroberfläche."""
        self.configure(style='Card.TFrame')

        # Header
        self._create_header()

        # Wochenkalender Grid
        self._create_calendar_grid()

        # Wochenstatistik
        self._create_week_statistics()

        # Action-Buttons
        self._create_action_buttons()

    def _create_header(self):
        """Erstellt den Header mit Navigation und Lernset-Auswahl."""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=20, pady=(20, 10))

        # Titel
        title_label = ttk.Label(
            header_frame,
            text="📅 Wochenplaner",
            font=('Segoe UI', 20, 'bold')
        )
        title_label.pack(side='left')

        # Lernset-Dropdown (rechts)
        lernset_frame = ttk.Frame(header_frame)
        lernset_frame.pack(side='right')

        ttk.Label(lernset_frame, text="Lernset:").pack(side='left', padx=(0, 5))

        self.lernset_var = tk.StringVar()
        self.lernset_dropdown = ttk.Combobox(
            lernset_frame,
            textvariable=self.lernset_var,
            state='readonly',
            width=20
        )
        self.lernset_dropdown.pack(side='left')
        self.lernset_dropdown.bind('<<ComboboxSelected>>', self._on_lernset_changed)

        # Lade Lernsets
        self._update_lernset_dropdown()

        # Navigation
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill='x', padx=20, pady=5)

        # Kalenderwoche anzeigen
        self.week_label = ttk.Label(
            nav_frame,
            text="",
            font=('Segoe UI', 12)
        )
        self.week_label.pack(side='left')

        # Navigation-Buttons (rechts)
        nav_buttons_frame = ttk.Frame(nav_frame)
        nav_buttons_frame.pack(side='right')

        ModernButton(
            nav_buttons_frame,
            text="◄ Vorwoche",
            command=self._previous_week,
            style='Secondary.TButton'
        ).pack(side='left', padx=5)

        ModernButton(
            nav_buttons_frame,
            text="Heute",
            command=self._go_to_today,
            style='Secondary.TButton'
        ).pack(side='left', padx=5)

        ModernButton(
            nav_buttons_frame,
            text="Nächste ►",
            command=self._next_week,
            style='Secondary.TButton'
        ).pack(side='left', padx=5)

    def _create_calendar_grid(self):
        """Erstellt das 7-Tage-Grid."""
        # Container für Kalender
        calendar_container = ttk.Frame(self)
        calendar_container.pack(fill='both', expand=True, padx=20, pady=10)

        # Canvas mit Scrollbar
        canvas = tk.Canvas(calendar_container, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(calendar_container, orient='vertical', command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Grid für 7 Tage
        self.day_frames = []
        for i in range(7):
            day_frame = self._create_day_frame(self.scrollable_frame, i)
            day_frame.grid(row=0, column=i, padx=5, pady=5, sticky='nsew')
            self.day_frames.append(day_frame)

        # Grid-Gewichte konfigurieren
        for i in range(7):
            self.scrollable_frame.columnconfigure(i, weight=1, uniform='day')

    def _create_day_frame(self, parent, day_index: int) -> ttk.Frame:
        """Erstellt ein Frame für einen Tag."""
        frame = ttk.Frame(parent, relief='raised', borderwidth=1)

        # Tag-Header (wird später gefüllt)
        header = ttk.Frame(frame, style='DayHeader.TFrame')
        header.pack(fill='x', pady=2, padx=2)

        day_label = ttk.Label(
            header,
            text="",
            font=('Segoe UI', 11, 'bold')
        )
        day_label.pack(pady=5)

        # Badge für fällige Karten (wird später aktualisiert)
        badge_label = ttk.Label(
            header,
            text="",
            font=('Segoe UI', 9)
        )
        badge_label.pack()

        # Session-Container
        sessions_frame = ttk.Frame(frame)
        sessions_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # + Button zum Hinzufügen
        add_button = ModernButton(
            frame,
            text="+ Session hinzufügen",
            command=lambda idx=day_index: self._add_session(idx),
            style='Secondary.TButton'
        )
        add_button.pack(pady=5)

        # Speichere Referenzen
        frame.day_label = day_label
        frame.badge_label = badge_label
        frame.sessions_frame = sessions_frame
        frame.day_index = day_index

        return frame

    def _create_week_statistics(self):
        """Erstellt die Wochenstatistik-Anzeige."""
        stats_frame = ttk.LabelFrame(self, text="📊 Wochenstatistik", padding=10)
        stats_frame.pack(fill='x', padx=20, pady=10)

        self.stats_label = ttk.Label(
            stats_frame,
            text="",
            font=('Segoe UI', 10)
        )
        self.stats_label.pack()

    def _create_action_buttons(self):
        """Erstellt die Action-Buttons am unteren Rand."""
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=20, pady=(10, 20))

        ModernButton(
            button_frame,
            text="🤖 Woche automatisch planen",
            command=self._auto_plan_week,
            style='Primary.TButton',
            width=30
        ).pack(side='left', padx=5)

        ModernButton(
            button_frame,
            text="📁 Lernsets verwalten",
            command=self._manage_learning_sets,
            style='Secondary.TButton',
            width=25
        ).pack(side='left', padx=5)

        ModernButton(
            button_frame,
            text="⚙️ Algorithmus anpassen",
            command=self._configure_algorithm,
            style='Secondary.TButton',
            width=25
        ).pack(side='left', padx=5)

        ModernButton(
            button_frame,
            text="📥 Wochenplan exportieren",
            command=self._export_week_plan,
            style='Secondary.TButton',
            width=25
        ).pack(side='left', padx=5)

        ModernButton(
            button_frame,
            text="📋 Heute-Ansicht",
            command=self._show_today_view,
            style='Primary.TButton',
            width=25
        ).pack(side='left', padx=5)

    def _load_week_data(self):
        """Lädt die Daten für die aktuelle Woche."""
        # Aktualisiere Wochenlabel
        week_num = self.week_start.isocalendar()[1]
        end_date = self.week_start + datetime.timedelta(days=6)
        self.week_label.configure(
            text=f"KW {week_num} | {self.week_start.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
        )

        # Aktualisiere jeden Tag
        for i, day_frame in enumerate(self.day_frames):
            date = self.week_start + datetime.timedelta(days=i)
            self._update_day_frame(day_frame, date)

        # Aktualisiere Statistik
        self._update_week_statistics()

    def _update_day_frame(self, day_frame: ttk.Frame, date: datetime.date):
        """Aktualisiert ein Tag-Frame mit Daten."""
        # Tag-Name und Datum
        day_names = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
        day_name = day_names[date.weekday()]
        date_str = date.strftime('%d.%m.')

        # Markiere heutigen Tag
        is_today = date == datetime.date.today()
        label_text = f"{day_name} {date_str}"
        if is_today:
            label_text = f"🔵 {label_text}"

        day_frame.day_label.configure(text=label_text)

        # Zähle fällige Karten für diesen Tag
        due_count = self._count_due_cards_for_date(date)

        # Badge-Farbe basierend auf Anzahl
        if due_count >= 20:
            badge_color = '🔴'  # Kritisch
        elif due_count >= 10:
            badge_color = '🟡'  # Aufmerksamkeit
        elif due_count > 0:
            badge_color = '🟢'  # OK
        else:
            badge_color = '⚪'  # Keine

        day_frame.badge_label.configure(text=f"{badge_color} {due_count} fällig")

        # Sessions laden
        self._update_day_sessions(day_frame, date)

    def _update_day_sessions(self, day_frame: ttk.Frame, date: datetime.date):
        """Aktualisiert die Sessions für einen Tag."""
        # Lösche alte Session-Widgets
        for widget in day_frame.sessions_frame.winfo_children():
            widget.destroy()

        # Lade Sessions aus DataManager
        entries = self.data_manager.get_plan_for_date(date)

        if not entries:
            ttk.Label(
                day_frame.sessions_frame,
                text="Keine Sessions geplant",
                foreground='gray'
            ).pack(pady=10)
            return

        # Zeige Sessions
        for entry in entries:
            self._create_session_widget(day_frame.sessions_frame, entry, date)

    def _create_session_widget(self, parent, entry: Dict, date: datetime.date):
        """Erstellt ein Widget für eine Session."""
        session_frame = ttk.Frame(parent, relief='solid', borderwidth=1)
        session_frame.pack(fill='x', pady=3)

        # Status-Icon
        status = entry.get('status', 'offen')
        if status == 'erledigt':
            icon = '✓'
            color = 'green'
        elif status == 'übersprungen':
            icon = '✗'
            color = 'orange'
        else:
            icon = '⏳'
            color = 'blue'

        # Kategorie-Label
        kategorie_text = f"{icon} {entry['kategorie']}"
        if entry.get('unterkategorie'):
            kategorie_text += f" - {entry['unterkategorie']}"

        kategorie_label = ttk.Label(
            session_frame,
            text=kategorie_text,
            font=('Segoe UI', 9, 'bold'),
            foreground=color
        )
        kategorie_label.pack(anchor='w', padx=5, pady=2)

        # Karten-Info mit Aktion
        erwartete = entry.get('erwartete_karten', 0)
        aktion = entry.get('aktion', 'lernen')
        aktion_text = "Lernen" if aktion == 'lernen' else "Karten erstellen"
        info_text = f"{aktion_text} • {erwartete} Karten"
        if entry.get('geplante_dauer'):
            info_text += f" • {entry['geplante_dauer']} Min."

        info_label = ttk.Label(
            session_frame,
            text=info_text,
            font=('Segoe UI', 8),
            foreground='gray'
        )
        info_label.pack(anchor='w', padx=5)

        # Button-Frame
        button_frame = ttk.Frame(session_frame)
        button_frame.pack(fill='x', padx=5, pady=3)

        if status == 'offen':
            # Button-Text basierend auf Aktion
            button_text = "Lernen" if aktion == 'lernen' else "Erstellen"
            ModernButton(
                button_frame,
                text=button_text,
                command=lambda: self._start_session(entry),
                style='Primary.TButton'
            ).pack(side='left', padx=2)

            # Erledigt markieren Button
            ModernButton(
                button_frame,
                text="✓",
                command=lambda: self._mark_completed(entry['id']),
                style='Success.TButton',
                width=3
            ).pack(side='left', padx=2)

        # Löschen Button (immer anzeigen)
        ModernButton(
            button_frame,
            text="🗑",
            command=lambda: self._delete_session(entry['id']),
            style='Danger.TButton',
            width=3
        ).pack(side='right', padx=2)

    def _count_due_cards_for_date(self, date: datetime.date) -> int:
        """Zählt fällige Karten für ein bestimmtes Datum."""
        count = 0
        target_datetime = datetime.datetime.combine(date, datetime.time.max)

        for card_id, leitner_card in self.leitner_system.cards.items():
            if leitner_card.next_review_date <= target_datetime:
                count += 1

        return count

    def _update_week_statistics(self):
        """Aktualisiert die Wochenstatistik."""
        week_plan = self.data_manager.get_plan_for_week(self.week_start)

        total_sessions = 0
        completed_sessions = 0
        open_sessions = 0
        total_cards = 0
        completed_cards = 0
        total_correct = 0

        for date_str, entries in week_plan.items():
            for entry in entries:
                total_sessions += 1
                if entry['status'] == 'erledigt':
                    completed_sessions += 1
                    completed_cards += entry.get('tatsaechliche_karten', 0)
                    total_correct += entry.get('karten_korrekt', 0)
                else:
                    open_sessions += 1
                total_cards += entry.get('erwartete_karten', 0)

        # Berechne Fortschritt
        progress = 0
        if total_sessions > 0:
            progress = int(completed_sessions / total_sessions * 100)

        # Berechne Gesamt-Erfolgsquote
        overall_success_rate = 0
        if completed_cards > 0:
            overall_success_rate = int(total_correct / completed_cards * 100)

        # Progress-Bar als Text
        bar_length = 10
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)

        # Hole Wochenziel aus aktivem Lernset
        active_set = self.learning_set_manager.get_active_set()
        weekly_goal = active_set.get('woechentliches_ziel', 100) if active_set else 100

        stats_text = (
            f"Geplant: {total_sessions} Sessions | "
            f"Erledigt: {completed_sessions} ✓ | "
            f"Offen: {open_sessions} ⏳\n"
            f"Fortschritt: {bar} {progress}% | "
            f"Erfolgsquote: {overall_success_rate}% ({total_correct}/{completed_cards} korrekt)\n"
            f"Gelernte Karten: {completed_cards}/{weekly_goal} (Wochenziel)"
        )

        self.stats_label.configure(text=stats_text)

    def _update_lernset_dropdown(self):
        """Aktualisiert das Lernset-Dropdown."""
        all_sets = self.learning_set_manager.get_all_sets()

        # Erstelle Liste mit Namen und IDs
        self.lernset_options = {}
        for set_id, learning_set in all_sets.items():
            name = learning_set['name']
            self.lernset_options[name] = set_id

        # Aktualisiere Dropdown
        names = list(self.lernset_options.keys())
        self.lernset_dropdown['values'] = names

        # Setze aktives Set
        active_set = self.learning_set_manager.get_active_set()
        if active_set:
            self.lernset_var.set(active_set['name'])
        elif names:
            self.lernset_var.set(names[0])

    # Event-Handler
    def _previous_week(self):
        """Navigiert zur vorherigen Woche."""
        self.week_start -= datetime.timedelta(days=7)
        self._load_week_data()

    def _next_week(self):
        """Navigiert zur nächsten Woche."""
        self.week_start += datetime.timedelta(days=7)
        self._load_week_data()

    def _go_to_today(self):
        """Navigiert zur aktuellen Woche."""
        self.current_date = datetime.date.today()
        self.week_start = self._get_week_start(self.current_date)
        self._load_week_data()

    def _on_lernset_changed(self, event=None):
        """Wird aufgerufen wenn Lernset geändert wird."""
        selected_name = self.lernset_var.get()
        if selected_name in self.lernset_options:
            set_id = self.lernset_options[selected_name]
            self.learning_set_manager.activate_set(set_id)
            logging.info(f"Lernset '{selected_name}' aktiviert.")
            # Reload week data to reflect changes
            self._load_week_data()

    def _add_session(self, day_index: int):
        """Öffnet Dialog zum Hinzufügen einer Session."""
        date = self.week_start + datetime.timedelta(days=day_index)
        dialog = DayPlanningDialog(self, self.data_manager, self.leitner_system,
                                   self.category_scorer, date)
        self.wait_window(dialog)
        # Refresh nach Dialog
        self._load_week_data()

    def _start_session(self, entry: Dict):
        """Startet eine Lern-Session."""
        if not self.app:
            messagebox.showerror(
                "Fehler",
                "App-Referenz fehlt. Session kann nicht gestartet werden."
            )
            return

        # Starte Leitner-Session mit vordefinierten Parametern
        try:
            self.app.start_leitner_session_from_plan(
                category=entry['kategorie'],
                subcategory=entry['unterkategorie'],
                plan_id=entry['id'],
                cards_limit=30  # Standard-Limit
            )
        except Exception as e:
            logging.error(f"Fehler beim Starten der Session: {e}", exc_info=True)
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Starten der Session:\n{e}"
            )

    def _mark_completed(self, plan_id: str):
        """Markiert eine Session als erledigt."""
        entry = self.data_manager.get_plan_entry(plan_id)
        if entry:
            updates = {
                'status': 'erledigt',
                'erledigt_am': datetime.datetime.now().isoformat(),
                'tatsaechliche_karten': entry.get('erwartete_karten', 0)
            }
            self.data_manager.update_plan_entry(plan_id, updates)
            self._load_week_data()
            logging.info(f"Session {plan_id} als erledigt markiert.")

    def _delete_session(self, plan_id: str):
        """Löscht eine Session."""
        if messagebox.askyesno("Session löschen", "Möchten Sie diese Session wirklich löschen?"):
            self.data_manager.delete_plan_entry(plan_id)
            self._load_week_data()
            logging.info(f"Session {plan_id} gelöscht.")

    def _auto_plan_week(self):
        """Startet die automatische Wochenplanung."""
        active_set = self.learning_set_manager.get_active_set()

        if not active_set:
            messagebox.showwarning(
                "Kein Lernset",
                "Bitte erstellen und aktivieren Sie zuerst ein Lernset."
            )
            return

        # Bestätige mit User
        if not messagebox.askyesno(
            "Automatische Planung",
            f"Möchten Sie die Woche automatisch planen?\n\n"
            f"Aktives Lernset: {active_set['name']}\n"
            f"Tägliches Ziel: {active_set['taegliches_ziel']} Karten\n\n"
            f"Bestehende automatisch generierte Sessions werden überschrieben."
        ):
            return

        # Starte Auto-Planung
        success = self.weekly_planner.auto_plan_week(
            start_date=self.week_start,
            active_learning_set=active_set,
            daily_target=active_set['taegliches_ziel']
        )

        if success:
            messagebox.showinfo("Erfolg", "Woche wurde automatisch geplant!")
            self._load_week_data()
        else:
            messagebox.showerror("Fehler", "Fehler bei der automatischen Planung.")

    def _manage_learning_sets(self):
        """Öffnet den Lernset-Manager."""
        dialog = LearningSetManagerDialog(self, self.data_manager)
        self.wait_window(dialog)
        # Refresh nach Dialog
        self._update_lernset_dropdown()
        self._load_week_data()

    def _configure_algorithm(self):
        """Öffnet den Algorithmus-Konfigurations-Dialog."""
        dialog = AlgorithmConfigDialog(self, self.data_manager)
        self.wait_window(dialog)

    def _show_today_view(self):
        """Öffnet die dedizierte Heute-Ansicht."""
        dialog = TodayViewDialog(self, self.data_manager, self.leitner_system, self.app)
        self.wait_window(dialog)
        # Refresh nach Dialog
        self._load_week_data()

    def _check_todays_sessions(self):
        """Prüft ob heute Sessions geplant sind und zeigt Benachrichtigung."""
        today = datetime.date.today()
        entries = self.data_manager.get_plan_for_date(today)

        if not entries:
            return  # Keine Sessions heute

        # Zähle offene Sessions
        open_sessions = [e for e in entries if e['status'] == 'offen']

        if not open_sessions:
            return  # Alle bereits erledigt

        # Zähle fällige Karten
        total_due_cards = sum(e.get('erwartete_karten', 0) for e in open_sessions)

        # Erstelle Benachrichtigung
        if len(open_sessions) == 1:
            session = open_sessions[0]
            message = (
                f"📌 Du hast heute 1 geplante Lernsession:\n\n"
                f"• {session['kategorie']} - {session['unterkategorie']}\n"
                f"  {session.get('erwartete_karten', 0)} Karten\n\n"
                f"Möchtest du jetzt starten?"
            )
        else:
            message = (
                f"📌 Du hast heute {len(open_sessions)} geplante Lernsessions:\n\n"
            )
            for session in open_sessions[:3]:  # Zeige max 3
                message += f"• {session['kategorie']} - {session['unterkategorie']}\n"
            if len(open_sessions) > 3:
                message += f"  ... und {len(open_sessions) - 3} weitere\n"
            message += f"\nInsgesamt {total_due_cards} Karten zu lernen."

        # Zeige Benachrichtigung
        result = messagebox.askquestion(
            "Heutige Lernsessions",
            message,
            icon='info'
        )

        # Wenn User "Ja" klickt, starte erste Session
        if result == 'yes' and len(open_sessions) == 1 and self.app:
            self._start_session(open_sessions[0])

    def _export_week_plan(self):
        """Exportiert den aktuellen Wochenplan als CSV."""
        try:
            from tkinter import filedialog
            import csv

            # Hole Wochenplan
            week_plan = self.data_manager.get_plan_for_week(self.week_start)

            # Erstelle CSV-Daten
            csv_data = []
            csv_data.append(['Datum', 'Wochentag', 'Kategorie', 'Unterkategorie', 'Aktion',
                           'Erwartete Karten', 'Geplante Dauer (Min)', 'Priorität', 'Status',
                           'Tatsächliche Karten', 'Erledigt am'])

            # Sortiere nach Datum
            for date_str in sorted(week_plan.keys()):
                date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                weekday_names = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag',
                               'Freitag', 'Samstag', 'Sonntag']
                weekday = weekday_names[date.weekday()]

                entries = week_plan[date_str]
                if not entries:
                    # Leerer Tag
                    csv_data.append([
                        date.strftime('%d.%m.%Y'),
                        weekday,
                        '-', '-', '-', '-', '-', '-', '-', '-', '-'
                    ])
                else:
                    for entry in entries:
                        erledigt_am = ''
                        if entry.get('erledigt_am'):
                            try:
                                dt = datetime.datetime.fromisoformat(entry['erledigt_am'])
                                erledigt_am = dt.strftime('%d.%m.%Y %H:%M')
                            except:
                                erledigt_am = entry['erledigt_am']

                        csv_data.append([
                            date.strftime('%d.%m.%Y'),
                            weekday,
                            entry['kategorie'],
                            entry['unterkategorie'],
                            entry['aktion'].capitalize(),
                            entry.get('erwartete_karten', 0),
                            entry.get('geplante_dauer', '-'),
                            entry.get('prioritaet', 'mittel').capitalize(),
                            entry['status'].capitalize(),
                            entry.get('tatsaechliche_karten', '-'),
                            erledigt_am
                        ])

            # Datei speichern Dialog
            week_num = self.week_start.isocalendar()[1]
            default_filename = f"Wochenplan_KW{week_num}_{self.week_start.strftime('%Y-%m-%d')}.csv"

            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")],
                initialfile=default_filename,
                title="Wochenplan exportieren"
            )

            if not file_path:
                return  # User hat abgebrochen

            # Schreibe CSV
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerows(csv_data)

            messagebox.showinfo(
                "Export erfolgreich",
                f"Wochenplan wurde erfolgreich exportiert:\n{file_path}"
            )
            logging.info(f"Wochenplan exportiert nach: {file_path}")

        except Exception as e:
            logging.error(f"Fehler beim Exportieren des Wochenplans: {e}", exc_info=True)
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Exportieren:\n{e}"
            )


class DayPlanningDialog(tk.Toplevel):
    """Dialog für Tagesplanung mit KI-Empfehlungen."""

    def __init__(self, parent, data_manager, leitner_system, category_scorer, date: datetime.date):
        super().__init__(parent)
        self.data_manager = data_manager
        self.leitner_system = leitner_system
        self.category_scorer = category_scorer
        self.date = date

        self.title(f"Planung für {date.strftime('%A, %d.%m.%Y')}")
        self.geometry("600x700")
        self.resizable(False, False)

        self._create_ui()

    def _create_ui(self):
        """Erstellt die Dialog-UI."""
        # Header
        header = ttk.Label(
            self,
            text=f"📅 Planung für {self.date.strftime('%A, %d.%m.%Y')}",
            font=('Segoe UI', 14, 'bold')
        )
        header.pack(pady=15)

        # KI-Empfehlungen
        self._create_recommendations_section()

        # Separator
        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=20, pady=15)

        # Manuelle Planung
        self._create_manual_planning_section()

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=15)

        ModernButton(
            button_frame,
            text="Abbrechen",
            command=self.destroy,
            style='Secondary.TButton'
        ).pack(side='left', padx=5)

    def _create_recommendations_section(self):
        """Erstellt den Empfehlungs-Bereich."""
        # Container
        rec_frame = ttk.LabelFrame(
            self,
            text="🎯 KI-Empfehlungen (basierend auf deinem Lernset)",
            padding=10
        )
        rec_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Hole Empfehlungen
        active_set = self.data_manager.get_active_learning_set()
        recommendations = self.category_scorer.get_top_recommendations(
            date=self.date,
            n=3,
            learning_set=active_set
        )

        if not recommendations:
            ttk.Label(
                rec_frame,
                text="Keine Empfehlungen verfügbar.\nBitte Lernset erstellen.",
                foreground='gray'
            ).pack(pady=20)
            return

        # Zeige Top 3
        for i, rec in enumerate(recommendations, 1):
            self._create_recommendation_widget(rec_frame, i, rec)

    def _create_recommendation_widget(self, parent, rank: int, rec: Dict):
        """Erstellt ein Widget für eine Empfehlung."""
        # Frame für Empfehlung
        frame = ttk.Frame(parent, relief='solid', borderwidth=1)
        frame.pack(fill='x', pady=5)

        # Header mit Rang und Score
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill='x', padx=10, pady=5)

        # Prioritäts-Icon
        score = rec['total_score']
        if score >= 80:
            icon = '⚠️'
        elif score >= 50:
            icon = '🔸'
        else:
            icon = '🟢'

        ttk.Label(
            header_frame,
            text=f"{rank}. {icon} {rec['kategorie']} - {rec['unterkategorie']}",
            font=('Segoe UI', 10, 'bold')
        ).pack(side='left')

        ttk.Label(
            header_frame,
            text=f"Score: {score}/100",
            font=('Segoe UI', 9),
            foreground='blue'
        ).pack(side='right')

        # Details
        details = rec['details']
        details_text = (
            f"• {details['fällige_karten'] + details['überfällige_karten']} fällige Karten "
            f"({details['überfällige_karten']} überfällig)\n"
            f"• Erfolgsquote: {details['erfolgsquote']}%\n"
        )
        if details['tage_seit_letztem_lernen'] is not None:
            details_text += f"• Zuletzt gelernt: vor {details['tage_seit_letztem_lernen']} Tagen"
        else:
            details_text += f"• Noch nie gelernt"

        ttk.Label(
            frame,
            text=details_text,
            font=('Segoe UI', 9),
            foreground='gray',
            justify='left'
        ).pack(anchor='w', padx=10, pady=5)

        # Button
        ModernButton(
            frame,
            text="Wählen",
            command=lambda: self._add_recommendation(rec),
            style='Primary.TButton'
        ).pack(anchor='e', padx=10, pady=5)

    def _create_manual_planning_section(self):
        """Erstellt den manuellen Planungsbereich."""
        manual_frame = ttk.LabelFrame(self, text="📝 Manuelle Planung", padding=10)
        manual_frame.pack(fill='x', padx=20, pady=10)

        # Kategorie
        ttk.Label(manual_frame, text="Kategorie:").grid(row=0, column=0, sticky='w', pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            manual_frame,
            textvariable=self.category_var,
            state='readonly',
            width=30
        )
        self.category_combo.grid(row=0, column=1, sticky='ew', pady=5, padx=(5, 0))
        self.category_combo.bind('<<ComboboxSelected>>', self._on_category_changed)

        # Unterkategorie
        ttk.Label(manual_frame, text="Unterkategorie:").grid(row=1, column=0, sticky='w', pady=5)
        self.subcategory_var = tk.StringVar()
        self.subcategory_combo = ttk.Combobox(
            manual_frame,
            textvariable=self.subcategory_var,
            state='readonly',
            width=30
        )
        self.subcategory_combo.grid(row=1, column=1, sticky='ew', pady=5, padx=(5, 0))

        # Aktion
        ttk.Label(manual_frame, text="Aktion:").grid(row=2, column=0, sticky='w', pady=5)
        self.action_var = tk.StringVar(value='lernen')
        action_frame = ttk.Frame(manual_frame)
        action_frame.grid(row=2, column=1, sticky='w', pady=5)

        ttk.Radiobutton(
            action_frame,
            text="Lernen",
            variable=self.action_var,
            value='lernen'
        ).pack(side='left', padx=5)

        ttk.Radiobutton(
            action_frame,
            text="Neue Karten erstellen",
            variable=self.action_var,
            value='erstellen'
        ).pack(side='left', padx=5)

        # Erwartete Dauer (optional)
        ttk.Label(manual_frame, text="Erwartete Dauer (Min):").grid(row=3, column=0, sticky='w', pady=5)
        self.duration_var = tk.StringVar(value='30')
        ttk.Entry(manual_frame, textvariable=self.duration_var, width=10).grid(
            row=3, column=1, sticky='w', pady=5, padx=(5, 0)
        )

        # Grid-Konfiguration
        manual_frame.columnconfigure(1, weight=1)

        # Hinzufügen-Button
        ModernButton(
            manual_frame,
            text="Hinzufügen",
            command=self._add_manual_session,
            style='Primary.TButton'
        ).grid(row=4, column=0, columnspan=2, pady=10)

        # Lade Kategorien
        self._load_categories()

    def _load_categories(self):
        """Lädt verfügbare Kategorien."""
        categories = sorted(set(card.category for card in self.data_manager.flashcards))
        self.category_combo['values'] = categories
        if categories:
            self.category_var.set(categories[0])
            self._on_category_changed()

    def _on_category_changed(self, event=None):
        """Wird aufgerufen wenn Kategorie geändert wird."""
        category = self.category_var.get()
        if not category:
            return

        # Lade Unterkategorien für diese Kategorie
        subcategories = sorted(set(
            card.subcategory
            for card in self.data_manager.flashcards
            if card.category == category
        ))

        self.subcategory_combo['values'] = subcategories
        if subcategories:
            self.subcategory_var.set(subcategories[0])

    def _add_recommendation(self, rec: Dict):
        """Fügt eine Empfehlung als Session hinzu."""
        self.data_manager.add_plan_entry(
            date=self.date,
            kategorie=rec['kategorie'],
            unterkategorie=rec['unterkategorie'],
            aktion='lernen',
            erwartete_karten=rec['details']['fällige_karten'] + rec['details']['überfällige_karten'],
            prioritaet='hoch' if rec['total_score'] >= 80 else 'mittel',
            auto_generiert=False
        )
        messagebox.showinfo("Erfolg", "Session wurde hinzugefügt!")
        self.destroy()

    def _add_manual_session(self):
        """Fügt eine manuelle Session hinzu."""
        category = self.category_var.get()
        subcategory = self.subcategory_var.get()

        if not category or not subcategory:
            messagebox.showwarning("Fehler", "Bitte wählen Sie Kategorie und Unterkategorie.")
            return

        # Zähle fällige Karten
        due_count = sum(
            1 for card_id, leitner_card in self.leitner_system.cards.items()
            if leitner_card.category.lower() == category.lower() and
               leitner_card.subcategory.lower() == subcategory.lower() and
               leitner_card.next_review_date <= datetime.datetime.now()
        )

        # Dauer
        try:
            duration = int(self.duration_var.get()) if self.duration_var.get() else None
        except ValueError:
            duration = None

        self.data_manager.add_plan_entry(
            date=self.date,
            kategorie=category,
            unterkategorie=subcategory,
            aktion=self.action_var.get(),
            erwartete_karten=due_count,
            geplante_dauer=duration,
            prioritaet='mittel',
            auto_generiert=False
        )

        messagebox.showinfo("Erfolg", "Session wurde hinzugefügt!")
        self.destroy()


class LearningSetManagerDialog(tk.Toplevel):
    """Dialog zur Verwaltung von Lernsets."""

    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.learning_set_manager = LearningSetManager(data_manager)

        self.title("Lernsets verwalten")
        self.geometry("700x500")

        self._create_ui()
        self._load_sets()

    def _create_ui(self):
        """Erstellt die Dialog-UI."""
        # Header
        header = ttk.Label(
            self,
            text="📁 Lernsets",
            font=('Segoe UI', 14, 'bold')
        )
        header.pack(pady=15)

        # Button zum Erstellen
        ModernButton(
            self,
            text="+ Neues Lernset",
            command=self._create_new_set,
            style='Primary.TButton'
        ).pack(pady=10)

        # Liste der Sets
        list_frame = ttk.Frame(self)
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        # Canvas für scrollable Content
        self.canvas = tk.Canvas(list_frame, yscrollcommand=scrollbar.set, bg='white')
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.canvas.yview)

        # Frame innerhalb Canvas
        self.sets_container = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.sets_container, anchor='nw')

        self.sets_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Schließen-Button
        ModernButton(
            self,
            text="Schließen",
            command=self.destroy,
            style='Secondary.TButton'
        ).pack(pady=15)

    def _load_sets(self):
        """Lädt und zeigt alle Lernsets."""
        # Lösche bestehende Widgets
        for widget in self.sets_container.winfo_children():
            widget.destroy()

        # Lade Sets
        all_sets = self.learning_set_manager.get_all_sets()
        active_set_id = self.data_manager.learning_sets.get('aktives_set')

        if not all_sets:
            ttk.Label(
                self.sets_container,
                text="Noch keine Lernsets vorhanden.",
                foreground='gray'
            ).pack(pady=20)
            return

        # Zeige jedes Set
        for set_id, learning_set in all_sets.items():
            self._create_set_widget(self.sets_container, set_id, learning_set, set_id == active_set_id)

    def _create_set_widget(self, parent, set_id: str, learning_set: Dict, is_active: bool):
        """Erstellt ein Widget für ein Lernset."""
        frame = ttk.Frame(parent, relief='solid', borderwidth=2 if is_active else 1)
        frame.pack(fill='x', pady=5, padx=5)

        # Header
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill='x', padx=10, pady=5)

        # Status-Icon und Name
        status_icon = '✓' if is_active else '○'
        name_text = f"{status_icon} {learning_set['name']}"

        ttk.Label(
            header_frame,
            text=name_text,
            font=('Segoe UI', 11, 'bold'),
            foreground='green' if is_active else 'black'
        ).pack(side='left')

        # Kategorien
        kategorien_text = "\n".join([
            f"└─ {kat['kategorie']} ({', '.join(kat['unterkategorien'])})"
            for kat in learning_set['kategorien']
        ])

        ttk.Label(
            frame,
            text=kategorien_text,
            font=('Segoe UI', 9),
            foreground='gray',
            justify='left'
        ).pack(anchor='w', padx=20, pady=5)

        # Ziele
        ziele_text = (
            f"Ziel: {learning_set['taegliches_ziel']} Karten/Tag | "
            f"{learning_set['woechentliches_ziel']}/Woche"
        )

        ttk.Label(
            frame,
            text=ziele_text,
            font=('Segoe UI', 9),
            foreground='blue'
        ).pack(anchor='w', padx=20, pady=2)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(anchor='e', padx=10, pady=5)

        if not is_active:
            ModernButton(
                button_frame,
                text="Aktivieren",
                command=lambda: self._activate_set(set_id),
                style='Primary.TButton'
            ).pack(side='left', padx=2)

        ModernButton(
            button_frame,
            text="Bearbeiten",
            command=lambda: self._edit_set(set_id),
            style='Secondary.TButton'
        ).pack(side='left', padx=2)

        ModernButton(
            button_frame,
            text="Löschen",
            command=lambda: self._delete_set(set_id),
            style='Danger.TButton'
        ).pack(side='left', padx=2)

    def _create_new_set(self):
        """Öffnet Dialog zum Erstellen eines neuen Sets."""
        dialog = CreateLearningSetDialog(self, self.data_manager)
        self.wait_window(dialog)
        self._load_sets()

    def _activate_set(self, set_id: str):
        """Aktiviert ein Lernset."""
        self.learning_set_manager.activate_set(set_id)
        self._load_sets()

    def _edit_set(self, set_id: str):
        """Bearbeitet ein Lernset."""
        messagebox.showinfo("Bearbeiten", "Bearbeitungsfunktion wird implementiert.")

    def _delete_set(self, set_id: str):
        """Löscht ein Lernset."""
        if messagebox.askyesno("Löschen", "Möchten Sie dieses Lernset wirklich löschen?"):
            self.learning_set_manager.delete_set(set_id)
            self._load_sets()


class CreateLearningSetDialog(tk.Toplevel):
    """Dialog zum Erstellen eines neuen Lernsets."""

    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.learning_set_manager = LearningSetManager(data_manager)

        self.title("Neues Lernset erstellen")
        self.geometry("500x600")

        self.selected_categories = []  # Liste von (kategorie, [unterkategorien])

        self._create_ui()

    def _create_ui(self):
        """Erstellt die Dialog-UI."""
        # Name
        ttk.Label(self, text="Name des Lernsets:").pack(pady=(20, 5))
        self.name_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.name_var, width=40).pack()

        # Ziele
        goals_frame = ttk.Frame(self)
        goals_frame.pack(pady=15)

        ttk.Label(goals_frame, text="Tägliches Ziel:").grid(row=0, column=0, sticky='w', padx=5)
        self.daily_goal_var = tk.StringVar(value='20')
        ttk.Entry(goals_frame, textvariable=self.daily_goal_var, width=10).grid(row=0, column=1, padx=5)

        ttk.Label(goals_frame, text="Wöchentliches Ziel:").grid(row=1, column=0, sticky='w', padx=5)
        self.weekly_goal_var = tk.StringVar(value='100')
        ttk.Entry(goals_frame, textvariable=self.weekly_goal_var, width=10).grid(row=1, column=1, padx=5)

        # Kategorien auswählen
        ttk.Label(self, text="Kategorien auswählen:").pack(pady=(15, 5))

        # Liste zum Anzeigen ausgewählter Kategorien
        self.selected_listbox = tk.Listbox(self, height=10, width=60)
        self.selected_listbox.pack(padx=20, pady=5)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        ModernButton(
            button_frame,
            text="+ Kategorie hinzufügen",
            command=self._add_category,
            style='Secondary.TButton'
        ).pack(side='left', padx=5)

        ModernButton(
            button_frame,
            text="- Entfernen",
            command=self._remove_category,
            style='Secondary.TButton'
        ).pack(side='left', padx=5)

        # Erstellen/Abbrechen
        action_frame = ttk.Frame(self)
        action_frame.pack(pady=20)

        ModernButton(
            action_frame,
            text="Erstellen",
            command=self._create_set,
            style='Primary.TButton'
        ).pack(side='left', padx=5)

        ModernButton(
            action_frame,
            text="Abbrechen",
            command=self.destroy,
            style='Secondary.TButton'
        ).pack(side='left', padx=5)

    def _add_category(self):
        """Öffnet Dialog zum Hinzufügen einer Kategorie."""
        # Hole verfügbare Kategorien
        available = self.learning_set_manager.get_available_categories()

        if not available:
            messagebox.showinfo("Keine Kategorien", "Bitte erstellen Sie zuerst Kategorien und Karten.")
            return

        # Einfacher Auswahl-Dialog
        dialog = tk.Toplevel(self)
        dialog.title("Kategorie auswählen")
        dialog.geometry("400x300")

        ttk.Label(dialog, text="Kategorie:").pack(pady=10)
        category_var = tk.StringVar()
        category_combo = ttk.Combobox(
            dialog,
            textvariable=category_var,
            values=list(available.keys()),
            state='readonly',
            width=30
        )
        category_combo.pack(pady=5)

        if available:
            category_combo.current(0)

        ttk.Label(dialog, text="Unterkategorien (mehrfach auswählbar):").pack(pady=10)

        # Listbox für Unterkategorien
        subcat_listbox = tk.Listbox(dialog, selectmode='multiple', height=8, width=30)
        subcat_listbox.pack(pady=5)

        def update_subcategories(event=None):
            subcat_listbox.delete(0, tk.END)
            cat = category_var.get()
            if cat in available:
                for subcat in available[cat]:
                    subcat_listbox.insert(tk.END, subcat)

        category_combo.bind('<<ComboboxSelected>>', update_subcategories)
        update_subcategories()

        def add():
            cat = category_var.get()
            selected_indices = subcat_listbox.curselection()
            if not cat or not selected_indices:
                messagebox.showwarning("Fehler", "Bitte wählen Sie Kategorie und Unterkategorien.")
                return

            subcats = [subcat_listbox.get(i) for i in selected_indices]
            self.selected_categories.append({
                'kategorie': cat,
                'unterkategorien': subcats
            })
            self._update_selected_listbox()
            dialog.destroy()

        ModernButton(dialog, text="Hinzufügen", command=add, style='Primary.TButton').pack(pady=10)

    def _remove_category(self):
        """Entfernt ausgewählte Kategorie."""
        selection = self.selected_listbox.curselection()
        if selection:
            index = selection[0]
            del self.selected_categories[index]
            self._update_selected_listbox()

    def _update_selected_listbox(self):
        """Aktualisiert die Listbox mit ausgewählten Kategorien."""
        self.selected_listbox.delete(0, tk.END)
        for cat_entry in self.selected_categories:
            text = f"{cat_entry['kategorie']}: {', '.join(cat_entry['unterkategorien'])}"
            self.selected_listbox.insert(tk.END, text)

    def _create_set(self):
        """Erstellt das Lernset."""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Fehler", "Bitte geben Sie einen Namen ein.")
            return

        if not self.selected_categories:
            messagebox.showwarning("Fehler", "Bitte wählen Sie mindestens eine Kategorie.")
            return

        try:
            daily_goal = int(self.daily_goal_var.get())
            weekly_goal = int(self.weekly_goal_var.get())
        except ValueError:
            messagebox.showwarning("Fehler", "Ungültige Ziele.")
            return

        # Erstelle Set
        set_id = self.learning_set_manager.create_set(
            name=name,
            kategorien=self.selected_categories,
            taegliches_ziel=daily_goal,
            woechentliches_ziel=weekly_goal
        )

        if set_id:
            messagebox.showinfo("Erfolg", f"Lernset '{name}' erstellt!")
            self.destroy()
        else:
            messagebox.showerror("Fehler", "Fehler beim Erstellen des Lernsets.")


class AlgorithmConfigDialog(tk.Toplevel):
    """Dialog zum Anpassen der Algorithmus-Gewichtungen."""

    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager

        self.title("Algorithmus anpassen")
        self.geometry("500x400")

        self.sliders = {}
        self._create_ui()

    def _create_ui(self):
        """Erstellt die Dialog-UI."""
        # Header
        ttk.Label(
            self,
            text="⚙️ Empfehlungs-Algorithmus anpassen",
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=15)

        ttk.Label(
            self,
            text="Gewichtung der Faktoren (Summe muss 100% sein):",
            font=('Segoe UI', 10)
        ).pack(pady=5)

        # Hole aktuelle Gewichtungen
        weights = self.data_manager.get_algorithm_weights()

        # Slider-Frame
        slider_frame = ttk.Frame(self)
        slider_frame.pack(fill='both', expand=True, padx=40, pady=20)

        # Erstelle Slider für jeden Faktor
        factors = {
            'dringlichkeit': 'Dringlichkeit (fällige Karten):',
            'effizienz': 'Effizienz (Erfolgsquote & Level):',
            'lernrhythmus': 'Lernrhythmus (letzte Session):',
            'ausgeglichenheit': 'Ausgeglichenheit (Rotation):'
        }

        for i, (key, label) in enumerate(factors.items()):
            ttk.Label(slider_frame, text=label).grid(row=i*2, column=0, sticky='w', pady=(10, 0))

            var = tk.IntVar(value=weights[key])
            self.sliders[key] = var

            slider = ttk.Scale(
                slider_frame,
                from_=0,
                to=100,
                orient='horizontal',
                variable=var,
                command=lambda v, k=key: self._on_slider_change(k)
            )
            slider.grid(row=i*2+1, column=0, sticky='ew', pady=5)

            # Value-Label
            value_label = ttk.Label(slider_frame, text=f"{weights[key]}%")
            value_label.grid(row=i*2+1, column=1, padx=10)
            slider.value_label = value_label

        slider_frame.columnconfigure(0, weight=1)

        # Summen-Label
        self.sum_label = ttk.Label(
            self,
            text="",
            font=('Segoe UI', 11, 'bold')
        )
        self.sum_label.pack(pady=10)

        self._update_sum()

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=15)

        ModernButton(
            button_frame,
            text="Zurücksetzen auf Standard",
            command=self._reset_to_default,
            style='Secondary.TButton'
        ).pack(side='left', padx=5)

        ModernButton(
            button_frame,
            text="Speichern",
            command=self._save,
            style='Primary.TButton'
        ).pack(side='left', padx=5)

        ModernButton(
            button_frame,
            text="Abbrechen",
            command=self.destroy,
            style='Secondary.TButton'
        ).pack(side='left', padx=5)

    def _on_slider_change(self, key):
        """Wird aufgerufen wenn ein Slider bewegt wird."""
        self._update_sum()

    def _update_sum(self):
        """Aktualisiert die Summen-Anzeige."""
        total = sum(var.get() for var in self.sliders.values())

        # Update value labels
        for key, var in self.sliders.items():
            # Finde den Slider
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Scale) and child.cget('variable') == str(var):
                            child.value_label.configure(text=f"{var.get()}%")

        # Summen-Label
        if total == 100:
            self.sum_label.configure(text=f"Summe: {total}% ✓", foreground='green')
        else:
            self.sum_label.configure(text=f"Summe: {total}% (muss 100 sein)", foreground='red')

    def _reset_to_default(self):
        """Setzt auf Standardwerte zurück."""
        defaults = {
            'dringlichkeit': 40,
            'effizienz': 30,
            'lernrhythmus': 20,
            'ausgeglichenheit': 10
        }
        for key, value in defaults.items():
            self.sliders[key].set(value)
        self._update_sum()

    def _save(self):
        """Speichert die Gewichtungen."""
        total = sum(var.get() for var in self.sliders.values())

        if total != 100:
            messagebox.showwarning("Fehler", "Die Summe der Gewichtungen muss 100% sein.")
            return

        weights = {key: var.get() for key, var in self.sliders.items()}

        if self.data_manager.update_algorithm_weights(weights):
            messagebox.showinfo("Erfolg", "Gewichtungen wurden gespeichert!")
            self.destroy()
        else:
            messagebox.showerror("Fehler", "Fehler beim Speichern der Gewichtungen.")


class TodayViewDialog(tk.Toplevel):
    """Dialog für die Heute-Ansicht mit Quick Access zu heutigen Sessions."""

    def __init__(self, parent, data_manager, leitner_system, app):
        super().__init__(parent)
        self.data_manager = data_manager
        self.leitner_system = leitner_system
        self.app = app

        self.title(f"Heute: {datetime.date.today().strftime('%A, %d.%m.%Y')}")
        self.geometry("700x600")

        self._create_ui()

    def _create_ui(self):
        """Erstellt die Dialog-UI."""
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill='x', padx=20, pady=15)

        ttk.Label(
            header_frame,
            text=f"📅 Heute: {datetime.date.today().strftime('%A, %d.%m.%Y')}",
            font=('Segoe UI', 16, 'bold')
        ).pack()

        # Statistik-Frame
        stats_frame = ttk.LabelFrame(self, text="📊 Tagesübersicht", padding=10)
        stats_frame.pack(fill='x', padx=20, pady=10)

        # Berechne Statistiken
        today = datetime.date.today()
        entries = self.data_manager.get_plan_for_date(today)

        total_sessions = len(entries)
        open_sessions = [e for e in entries if e['status'] == 'offen']
        completed_sessions = [e for e in entries if e['status'] == 'erledigt']

        total_cards = sum(e.get('erwartete_karten', 0) for e in entries)
        completed_cards = sum(e.get('tatsaechliche_karten', 0) for e in completed_sessions)

        # Fällige Karten insgesamt (aus Leitner-System)
        due_cards_total = sum(
            1 for card in self.leitner_system.cards.values()
            if card.next_review_date <= datetime.datetime.now()
        )

        # Statistik-Grid
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill='x')
        stats_grid.columnconfigure((0, 1, 2), weight=1)

        # Stat 1: Sessions
        self._create_stat_widget(
            stats_grid, 0,
            "Geplante Sessions",
            f"{len(completed_sessions)}/{total_sessions}",
            "green" if len(completed_sessions) == total_sessions else "blue"
        )

        # Stat 2: Karten
        self._create_stat_widget(
            stats_grid, 1,
            "Karten",
            f"{completed_cards}/{total_cards}",
            "green" if completed_cards >= total_cards else "orange"
        )

        # Stat 3: Fällig insgesamt
        self._create_stat_widget(
            stats_grid, 2,
            "Insgesamt fällig",
            str(due_cards_total),
            "red" if due_cards_total > 50 else ("orange" if due_cards_total > 20 else "green")
        )

        # Fortschrittsbalken
        if total_sessions > 0:
            progress = len(completed_sessions) / total_sessions
            progress_frame = ttk.Frame(stats_frame)
            progress_frame.pack(fill='x', pady=10)

            ttk.Label(progress_frame, text="Fortschritt:").pack(anchor='w')

            bar_length = 40
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)

            ttk.Label(
                progress_frame,
                text=f"{bar} {int(progress * 100)}%",
                font=('Courier', 10)
            ).pack(anchor='w')

        # Sessions-Liste
        sessions_frame = ttk.LabelFrame(self, text="🎯 Geplante Sessions", padding=10)
        sessions_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Scrollable Container
        canvas = tk.Canvas(sessions_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(sessions_frame, orient='vertical', command=canvas.yview)
        scrollable_container = ttk.Frame(canvas)

        scrollable_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Zeige Sessions
        if not entries:
            ttk.Label(
                scrollable_container,
                text="Keine Sessions für heute geplant.",
                foreground='gray'
            ).pack(pady=20)
        else:
            for entry in entries:
                self._create_session_widget(scrollable_container, entry)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=15)

        ModernButton(
            button_frame,
            text="+ Neue Session hinzufügen",
            command=self._add_new_session,
            style='Primary.TButton'
        ).pack(side='left', padx=5)

        ModernButton(
            button_frame,
            text="Schließen",
            command=self.destroy,
            style='Secondary.TButton'
        ).pack(side='left', padx=5)

    def _create_stat_widget(self, parent, column: int, label: str, value: str, color: str):
        """Erstellt ein Statistik-Widget."""
        frame = ttk.Frame(parent, relief='solid', borderwidth=1)
        frame.grid(row=0, column=column, padx=5, pady=5, sticky='nsew')

        ttk.Label(
            frame,
            text=label,
            font=('Segoe UI', 9),
            foreground='gray'
        ).pack(pady=(5, 0))

        ttk.Label(
            frame,
            text=value,
            font=('Segoe UI', 18, 'bold'),
            foreground=color
        ).pack(pady=(0, 5))

    def _create_session_widget(self, parent, entry: Dict):
        """Erstellt ein Widget für eine Session."""
        frame = ttk.Frame(parent, relief='solid', borderwidth=1)
        frame.pack(fill='x', pady=5, padx=5)

        # Status-Icon
        status = entry['status']
        if status == 'erledigt':
            icon = '✓'
            color = 'green'
        else:
            icon = '⏳'
            color = 'blue'

        # Info-Frame
        info_frame = ttk.Frame(frame)
        info_frame.pack(side='left', fill='x', expand=True, padx=10, pady=8)

        # Kategorie
        kategorie_text = f"{icon} {entry['kategorie']} - {entry['unterkategorie']}"
        ttk.Label(
            info_frame,
            text=kategorie_text,
            font=('Segoe UI', 11, 'bold'),
            foreground=color
        ).pack(anchor='w')

        # Details
        details_text = f"{entry.get('erwartete_karten', 0)} Karten"
        if entry.get('geplante_dauer'):
            details_text += f" • {entry['geplante_dauer']} Min."
        if entry.get('prioritaet'):
            prioritaet_map = {'hoch': '🔴', 'mittel': '🟡', 'niedrig': '🟢'}
            details_text += f" • {prioritaet_map.get(entry['prioritaet'], '')} {entry['prioritaet'].capitalize()}"

        ttk.Label(
            info_frame,
            text=details_text,
            font=('Segoe UI', 9),
            foreground='gray'
        ).pack(anchor='w')

        # Button-Frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(side='right', padx=10, pady=8)

        if status == 'offen':
            ModernButton(
                button_frame,
                text="Jetzt lernen",
                command=lambda: self._start_session(entry),
                style='Primary.TButton'
            ).pack(side='left', padx=2)

            ModernButton(
                button_frame,
                text="✓ Erledigt",
                command=lambda: self._mark_completed(entry['id']),
                style='Success.TButton'
            ).pack(side='left', padx=2)
        else:
            # Zeige Statistik für erledigte Session
            if entry.get('tatsaechliche_karten'):
                ttk.Label(
                    button_frame,
                    text=f"✓ {entry['tatsaechliche_karten']} Karten",
                    font=('Segoe UI', 10, 'bold'),
                    foreground='green'
                ).pack()

    def _start_session(self, entry: Dict):
        """Startet eine Session."""
        if not self.app:
            messagebox.showerror("Fehler", "App-Referenz fehlt.")
            return

        try:
            self.app.start_leitner_session_from_plan(
                category=entry['kategorie'],
                subcategory=entry['unterkategorie'],
                plan_id=entry['id'],
                cards_limit=30
            )
            self.destroy()
        except Exception as e:
            logging.error(f"Fehler beim Starten der Session: {e}", exc_info=True)
            messagebox.showerror("Fehler", f"Fehler beim Starten:\n{e}")

    def _mark_completed(self, plan_id: str):
        """Markiert Session als erledigt."""
        entry = self.data_manager.get_plan_entry(plan_id)
        if entry:
            updates = {
                'status': 'erledigt',
                'erledigt_am': datetime.datetime.now().isoformat(),
                'tatsaechliche_karten': entry.get('erwartete_karten', 0)
            }
            self.data_manager.update_plan_entry(plan_id, updates)
            # Refresh UI
            self.destroy()
            self.__init__(self.master, self.data_manager, self.leitner_system, self.app)

    def _add_new_session(self):
        """Öffnet Dialog zum Hinzufügen einer neuen Session."""
        from calendar_ui import DayPlanningDialog
        today = datetime.date.today()
        dialog = DayPlanningDialog(self, self.data_manager, self.leitner_system,
                                   CategoryScorer(self.data_manager, self.leitner_system),
                                   today)
        self.wait_window(dialog)
        # Refresh
        self.destroy()
        self.__init__(self.master, self.data_manager, self.leitner_system, self.app)
