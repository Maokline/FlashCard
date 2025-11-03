#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modernisierte Kalender-UI für FlashCards mit Multi-Planer-System.
Nutzt CustomTkinter für ein modernes, ansprechendes Design.
"""

import customtkinter as ctk
from tkinter import messagebox
import datetime
import logging
from typing import Optional, Dict, List
from calendar_system import CategoryScorer, WeeklyPlanner
from learning_sets import LearningSetManager
from planner_manager import PlannerManager, get_default_planner_icons


# Moderne Farbpalette
COLORS = {
    'primary': '#3b82f6',      # Modernes Blau
    'primary_hover': '#2563eb',
    'secondary': '#8b5cf6',    # Lila
    'success': '#10b981',      # Grün
    'warning': '#f59e0b',      # Orange
    'danger': '#ef4444',       # Rot
    'background': '#0f172a',   # Dunkelblau
    'surface': '#1e293b',      # Mittel-Dunkel
    'card': '#1e293b',         # Card Background
    'text': '#f1f5f9',         # Heller Text
    'text_secondary': '#94a3b8', # Sekundärer Text
    'border': '#334155',       # Border
}


class PlannerSelectionView(ctk.CTkFrame):
    """
    Moderne Planer-Auswahl-Ansicht.
    Zeigt alle verfügbaren Planer in einem ansprechenden Grid-Layout.
    """

    def __init__(self, master, data_manager, leitner_system, app=None):
        super().__init__(master, fg_color="transparent")
        self.data_manager = data_manager
        self.leitner_system = leitner_system
        self.app = app

        self.planner_manager = PlannerManager(data_manager)
        self.learning_set_manager = LearningSetManager(data_manager)

        self._create_ui()
        logging.info("PlannerSelectionView initialisiert.")

    def _create_ui(self):
        """Erstellt die Benutzeroberfläche."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill='x', padx=40, pady=(40, 20))

        title = ctk.CTkLabel(
            header_frame,
            text="📅  Wochenplaner auswählen",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS['text']
        )
        title.pack(side='left')

        # Neuer Planer Button
        new_btn = ctk.CTkButton(
            header_frame,
            text="+ Neuer Planer",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            command=self._create_new_planner,
            height=40,
            corner_radius=10
        )
        new_btn.pack(side='right')

        # Subtitle
        subtitle = ctk.CTkLabel(
            self,
            text="Wähle einen Planer um deine Woche zu organisieren",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text_secondary']
        )
        subtitle.pack(padx=40, pady=(0, 30))

        # Scrollable Frame für Planer
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['surface'],
            scrollbar_button_hover_color=COLORS['border']
        )
        self.scroll_frame.pack(fill='both', expand=True, padx=40, pady=(0, 40))

        # Lade Planer
        self._load_planners()

    def _load_planners(self):
        """Lädt und zeigt alle Planer."""
        # Lösche bestehende Widgets
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        all_planners = self.planner_manager.get_all_planners()
        active_planner_id = self.planner_manager.get_active_planner()
        active_id = active_planner_id['id'] if active_planner_id else None

        if not all_planners:
            # Keine Planer vorhanden
            empty_frame = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=COLORS['surface'],
                corner_radius=15
            )
            empty_frame.pack(fill='both', expand=True, pady=20)

            ctk.CTkLabel(
                empty_frame,
                text="📭",
                font=ctk.CTkFont(size=60)
            ).pack(pady=(40, 10))

            ctk.CTkLabel(
                empty_frame,
                text="Noch keine Planer vorhanden",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=COLORS['text']
            ).pack(pady=5)

            ctk.CTkLabel(
                empty_frame,
                text="Erstelle deinen ersten Planer um zu starten",
                font=ctk.CTkFont(size=14),
                text_color=COLORS['text_secondary']
            ).pack(pady=(0, 40))

            return

        # Grid-Layout für Planer (2 Spalten)
        col = 0
        row = 0
        for planner_id, planner in all_planners.items():
            is_active = (planner_id == active_id)
            card = self._create_planner_card(planner, is_active)
            card.grid(row=row, column=col, padx=15, pady=15, sticky='nsew')

            col += 1
            if col >= 2:
                col = 0
                row += 1

        # Grid-Gewichte
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(1, weight=1)

    def _create_planner_card(self, planner: Dict, is_active: bool) -> ctk.CTkFrame:
        """Erstellt eine moderne Card für einen Planer."""
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=COLORS['card'],
            corner_radius=15,
            border_width=3 if is_active else 0,
            border_color=COLORS['primary'] if is_active else None
        )

        # Card-Content
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill='both', expand=True, padx=25, pady=25)

        # Header mit Icon und Name
        header = ctk.CTkFrame(content_frame, fg_color="transparent")
        header.pack(fill='x', pady=(0, 15))

        icon_label = ctk.CTkLabel(
            header,
            text=planner.get('icon', '📅'),
            font=ctk.CTkFont(size=40)
        )
        icon_label.pack(side='left', padx=(0, 15))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side='left', fill='x', expand=True)

        name = ctk.CTkLabel(
            title_frame,
            text=planner['name'],
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS['text'],
            anchor='w'
        )
        name.pack(fill='x')

        # Active Badge
        if is_active:
            badge = ctk.CTkLabel(
                title_frame,
                text="✓ AKTIV",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLORS['primary'],
                anchor='w'
            )
            badge.pack(fill='x')

        # Statistiken
        stats = self.planner_manager.get_planner_statistics(planner['id'])

        stats_frame = ctk.CTkFrame(content_frame, fg_color=COLORS['background'], corner_radius=10)
        stats_frame.pack(fill='x', pady=(0, 15))

        # Lernsets
        lernsets_label = ctk.CTkLabel(
            stats_frame,
            text=f"📚 {stats['total_lernsets']} Lernsets  •  🎯 {stats['total_categories']} Kategorien",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        )
        lernsets_label.pack(padx=15, pady=10)

        # Ziele
        goals_label = ctk.CTkLabel(
            stats_frame,
            text=f"Ziel: {stats['total_daily_goal']} Karten/Tag",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['success']
        )
        goals_label.pack(padx=15, pady=(0, 10))

        # Buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill='x')

        if not is_active:
            activate_btn = ctk.CTkButton(
                button_frame,
                text="Auswählen",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=COLORS['primary'],
                hover_color=COLORS['primary_hover'],
                command=lambda: self._select_planner(planner['id']),
                height=35,
                corner_radius=8
            )
            activate_btn.pack(side='left', padx=(0, 8))
        else:
            open_btn = ctk.CTkButton(
                button_frame,
                text="Öffnen",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=COLORS['success'],
                hover_color='#059669',
                command=lambda: self._open_planner(planner['id']),
                height=35,
                corner_radius=8
            )
            open_btn.pack(side='left', padx=(0, 8))

        edit_btn = ctk.CTkButton(
            button_frame,
            text="⚙️",
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=lambda: self._edit_planner(planner['id']),
            width=35,
            height=35,
            corner_radius=8
        )
        edit_btn.pack(side='left', padx=(0, 8))

        delete_btn = ctk.CTkButton(
            button_frame,
            text="🗑",
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['danger'],
            hover_color='#dc2626',
            command=lambda: self._delete_planner(planner['id']),
            width=35,
            height=35,
            corner_radius=8
        )
        delete_btn.pack(side='left')

        return card

    def _select_planner(self, planner_id: str):
        """Wählt einen Planer aus und öffnet ihn."""
        if self.planner_manager.activate_planner(planner_id):
            self._open_planner(planner_id)

    def _open_planner(self, planner_id: str):
        """Öffnet den Wochenplaner für einen Planer."""
        planner = self.planner_manager.get_planner(planner_id)
        if not planner:
            messagebox.showerror("Fehler", "Planer nicht gefunden.")
            return

        # Wechsel zur Wochenplaner-Ansicht
        if hasattr(self.master, 'show_weekly_calendar'):
            self.master.show_weekly_calendar(planner_id)
        else:
            # Fallback: Zeige in neuem Fenster
            calendar_window = ctk.CTkToplevel(self)
            calendar_window.title(f"Wochenplaner - {planner['name']}")
            calendar_window.geometry("1400x900")

            calendar_view = ModernWeeklyCalendarView(
                calendar_window,
                self.data_manager,
                self.leitner_system,
                planner_id,
                self.app
            )
            calendar_view.pack(fill='both', expand=True)

    def _create_new_planner(self):
        """Öffnet Dialog zum Erstellen eines neuen Planers."""
        dialog = CreatePlannerDialog(self, self.data_manager)
        dialog.wait_window()
        self._load_planners()

    def _edit_planner(self, planner_id: str):
        """Öffnet Dialog zum Bearbeiten eines Planers."""
        dialog = EditPlannerDialog(self, self.data_manager, planner_id)
        dialog.wait_window()
        self._load_planners()

    def _delete_planner(self, planner_id: str):
        """Löscht einen Planer nach Bestätigung."""
        planner = self.planner_manager.get_planner(planner_id)
        if not planner:
            return

        if messagebox.askyesno(
            "Planer löschen",
            f"Möchtest du '{planner['name']}' wirklich löschen?\n\nDie zugeordneten Lernsets bleiben erhalten."
        ):
            if self.planner_manager.delete_planner(planner_id):
                messagebox.showinfo("Erfolg", "Planer wurde gelöscht!")
                self._load_planners()


class ModernWeeklyCalendarView(ctk.CTkFrame):
    """
    Moderne Wochenkalender-Ansicht mit CustomTkinter.
    """

    def __init__(self, master, data_manager, leitner_system, planner_id, app=None):
        super().__init__(master, fg_color="transparent")
        self.data_manager = data_manager
        self.leitner_system = leitner_system
        self.planner_id = planner_id
        self.app = app

        # Initialisiere Systeme
        self.planner_manager = PlannerManager(data_manager)
        self.category_scorer = CategoryScorer(data_manager, leitner_system)
        self.weekly_planner = WeeklyPlanner(data_manager, leitner_system, self.category_scorer)
        self.learning_set_manager = LearningSetManager(data_manager)

        # Hole Planer-Info
        self.planner = self.planner_manager.get_planner(planner_id)

        # Aktuelles Datum
        self.current_date = datetime.date.today()
        self.week_start = self._get_week_start(self.current_date)

        # UI erstellen
        self._create_ui()
        self._load_week_data()

        logging.info(f"ModernWeeklyCalendarView für Planer '{self.planner['name']}' initialisiert.")

    def _get_week_start(self, date: datetime.date) -> datetime.date:
        """Gibt den Montag der Woche zurück."""
        return date - datetime.timedelta(days=date.weekday())

    def _create_ui(self):
        """Erstellt die Benutzeroberfläche."""
        # Header
        self._create_header()

        # Wochenstatistik
        self._create_week_statistics()

        # Wochenkalender Grid
        self._create_calendar_grid()

        # Action-Buttons
        self._create_action_buttons()

    def _create_header(self):
        """Erstellt den Header mit Navigation."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill='x', padx=40, pady=(30, 20))

        # Zurück-Button
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Zurück",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=self._go_back,
            width=100,
            height=35,
            corner_radius=8
        )
        back_btn.pack(side='left', padx=(0, 20))

        # Titel mit Icon
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side='left')

        icon = ctk.CTkLabel(
            title_frame,
            text=self.planner.get('icon', '📅'),
            font=ctk.CTkFont(size=28)
        )
        icon.pack(side='left', padx=(0, 10))

        title = ctk.CTkLabel(
            title_frame,
            text=self.planner['name'],
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['text']
        )
        title.pack(side='left')

        # Navigation (rechts)
        nav_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        nav_frame.pack(side='right')

        prev_btn = ctk.CTkButton(
            nav_frame,
            text="◄",
            font=ctk.CTkFont(size=16),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=self._previous_week,
            width=40,
            height=40,
            corner_radius=8
        )
        prev_btn.pack(side='left', padx=5)

        today_btn = ctk.CTkButton(
            nav_frame,
            text="Heute",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            command=self._go_to_today,
            height=40,
            corner_radius=8
        )
        today_btn.pack(side='left', padx=5)

        next_btn = ctk.CTkButton(
            nav_frame,
            text="►",
            font=ctk.CTkFont(size=16),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=self._next_week,
            width=40,
            height=40,
            corner_radius=8
        )
        next_btn.pack(side='left', padx=5)

        # Kalenderwoche
        week_frame = ctk.CTkFrame(self, fg_color="transparent")
        week_frame.pack(fill='x', padx=40, pady=(0, 20))

        self.week_label = ctk.CTkLabel(
            week_frame,
            text="",
            font=ctk.CTkFont(size=16),
            text_color=COLORS['text_secondary']
        )
        self.week_label.pack()

    def _create_week_statistics(self):
        """Erstellt die Wochenstatistik."""
        stats_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS['card'],
            corner_radius=15
        )
        stats_frame.pack(fill='x', padx=40, pady=(0, 20))

        self.stats_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        self.stats_container.pack(fill='x', padx=25, pady=20)

    def _create_calendar_grid(self):
        """Erstellt das 7-Tage-Grid."""
        # Scrollable Frame
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS['surface'],
            scrollbar_button_hover_color=COLORS['border']
        )
        self.scroll_frame.pack(fill='both', expand=True, padx=40, pady=(0, 20))

        # Grid für 7 Tage
        self.day_frames = []
        day_names = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']

        for i in range(7):
            day_frame = self._create_day_frame(self.scroll_frame, i, day_names[i])
            day_frame.grid(row=0, column=i, padx=10, pady=10, sticky='nsew')
            self.day_frames.append(day_frame)
            self.scroll_frame.grid_columnconfigure(i, weight=1, minsize=200)

    def _create_day_frame(self, parent, day_index: int, day_name: str) -> ctk.CTkFrame:
        """Erstellt ein modernes Frame für einen Tag."""
        frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS['card'],
            corner_radius=12
        )

        # Header
        header = ctk.CTkFrame(frame, fg_color=COLORS['background'], corner_radius=10)
        header.pack(fill='x', padx=8, pady=8)

        day_label = ctk.CTkLabel(
            header,
            text=day_name,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        )
        day_label.pack(pady=8)

        date_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        )
        date_label.pack(pady=(0, 8))

        # Badge für fällige Karten
        badge_frame = ctk.CTkFrame(frame, fg_color="transparent")
        badge_frame.pack(fill='x', padx=8, pady=8)

        badge_label = ctk.CTkLabel(
            badge_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        )
        badge_label.pack()

        # Sessions Container
        sessions_frame = ctk.CTkFrame(frame, fg_color="transparent")
        sessions_frame.pack(fill='both', expand=True, padx=8, pady=8)

        # Add Button
        add_btn = ctk.CTkButton(
            frame,
            text="+ Session",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=lambda idx=day_index: self._add_session(idx),
            height=32,
            corner_radius=8
        )
        add_btn.pack(padx=8, pady=8)

        # Speichere Referenzen
        frame.day_label = day_label
        frame.date_label = date_label
        frame.badge_label = badge_label
        frame.sessions_frame = sessions_frame
        frame.day_index = day_index

        return frame

    def _create_action_buttons(self):
        """Erstellt die Action-Buttons."""
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill='x', padx=40, pady=(0, 30))

        auto_plan_btn = ctk.CTkButton(
            button_frame,
            text="🤖 Automatisch planen",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            command=self._auto_plan_week,
            height=45,
            corner_radius=10
        )
        auto_plan_btn.pack(side='left', padx=(0, 10))

        export_btn = ctk.CTkButton(
            button_frame,
            text="📥 Exportieren",
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=self._export_week_plan,
            height=45,
            corner_radius=10
        )
        export_btn.pack(side='left')

    def _load_week_data(self):
        """Lädt die Daten für die aktuelle Woche."""
        # Aktualisiere Wochenlabel
        week_num = self.week_start.isocalendar()[1]
        end_date = self.week_start + datetime.timedelta(days=6)
        self.week_label.configure(
            text=f"KW {week_num}  •  {self.week_start.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
        )

        # Aktualisiere jeden Tag
        for i, day_frame in enumerate(self.day_frames):
            date = self.week_start + datetime.timedelta(days=i)
            self._update_day_frame(day_frame, date)

        # Aktualisiere Statistik
        self._update_week_statistics()

    def _update_day_frame(self, day_frame: ctk.CTkFrame, date: datetime.date):
        """Aktualisiert ein Tag-Frame."""
        # Datum
        date_str = date.strftime('%d.%m.')
        is_today = date == datetime.date.today()

        if is_today:
            day_frame.configure(border_width=2, border_color=COLORS['primary'])
            day_frame.date_label.configure(text=f"🔵 {date_str}", text_color=COLORS['primary'])
        else:
            day_frame.configure(border_width=0)
            day_frame.date_label.configure(text=date_str, text_color=COLORS['text_secondary'])

        # Fällige Karten
        due_count = self._count_due_cards_for_date(date)

        if due_count >= 20:
            badge_text = f"🔴 {due_count} fällig"
            badge_color = COLORS['danger']
        elif due_count >= 10:
            badge_text = f"🟡 {due_count} fällig"
            badge_color = COLORS['warning']
        elif due_count > 0:
            badge_text = f"🟢 {due_count} fällig"
            badge_color = COLORS['success']
        else:
            badge_text = "⚪ Keine fällig"
            badge_color = COLORS['text_secondary']

        day_frame.badge_label.configure(text=badge_text, text_color=badge_color)

        # Sessions
        self._update_day_sessions(day_frame, date)

    def _update_day_sessions(self, day_frame: ctk.CTkFrame, date: datetime.date):
        """Aktualisiert die Sessions für einen Tag."""
        # Lösche alte Widgets
        for widget in day_frame.sessions_frame.winfo_children():
            widget.destroy()

        entries = self.data_manager.get_plan_for_date(date)

        if not entries:
            ctk.CTkLabel(
                day_frame.sessions_frame,
                text="Keine Sessions",
                font=ctk.CTkFont(size=11),
                text_color=COLORS['text_secondary']
            ).pack(pady=10)
            return

        for entry in entries:
            self._create_session_widget(day_frame.sessions_frame, entry, date)

    def _create_session_widget(self, parent, entry: Dict, date: datetime.date):
        """Erstellt ein Widget für eine Session."""
        session_frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS['background'],
            corner_radius=8
        )
        session_frame.pack(fill='x', pady=4)

        # Status Icon
        status = entry.get('status', 'offen')
        if status == 'erledigt':
            icon = '✓'
            color = COLORS['success']
        elif status == 'übersprungen':
            icon = '✗'
            color = COLORS['warning']
        else:
            icon = '⏳'
            color = COLORS['text_secondary']

        # Kategorie
        kategorie_text = f"{entry['kategorie']}"
        if entry.get('unterkategorie'):
            kategorie_text += f"\n{entry['unterkategorie']}"

        kategorie_label = ctk.CTkLabel(
            session_frame,
            text=kategorie_text,
            font=ctk.CTkFont(size=11),
            text_color=color,
            anchor='w'
        )
        kategorie_label.pack(anchor='w', padx=8, pady=(8, 4))

        # Karten
        info_text = f"{entry.get('erwartete_karten', 0)} Karten"
        ctk.CTkLabel(
            session_frame,
            text=info_text,
            font=ctk.CTkFont(size=10),
            text_color=COLORS['text_secondary'],
            anchor='w'
        ).pack(anchor='w', padx=8, pady=(0, 8))

        if status == 'offen':
            # Lernen Button
            learn_btn = ctk.CTkButton(
                session_frame,
                text="Lernen",
                font=ctk.CTkFont(size=10),
                fg_color=COLORS['primary'],
                hover_color=COLORS['primary_hover'],
                command=lambda: self._start_session(entry),
                height=28,
                corner_radius=6
            )
            learn_btn.pack(padx=8, pady=(0, 8))

    def _count_due_cards_for_date(self, date: datetime.date) -> int:
        """Zählt fällige Karten für ein Datum."""
        count = 0
        target_datetime = datetime.datetime.combine(date, datetime.time.max)

        # Filtere nach Planer-Kategorien
        planner_categories = set(self.planner_manager.get_planner_categories(self.planner_id))

        for card_id, leitner_card in self.leitner_system.cards.items():
            # Prüfe ob Karte im Planer ist
            if (leitner_card.category, leitner_card.subcategory) not in planner_categories:
                continue

            if leitner_card.next_review_date <= target_datetime:
                count += 1

        return count

    def _update_week_statistics(self):
        """Aktualisiert die Wochenstatistik."""
        # Lösche alte Widgets
        for widget in self.stats_container.winfo_children():
            widget.destroy()

        week_plan = self.data_manager.get_plan_for_week(self.week_start)

        total_sessions = 0
        completed_sessions = 0
        total_cards = 0
        completed_cards = 0

        for date_str, entries in week_plan.items():
            for entry in entries:
                total_sessions += 1
                if entry['status'] == 'erledigt':
                    completed_sessions += 1
                    completed_cards += entry.get('tatsaechliche_karten', 0)
                total_cards += entry.get('erwartete_karten', 0)

        # Fortschritt
        progress = 0
        if total_sessions > 0:
            progress = completed_sessions / total_sessions

        # Stats-Grid
        stats_grid = ctk.CTkFrame(self.stats_container, fg_color="transparent")
        stats_grid.pack(fill='x')
        stats_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Sessions
        self._create_stat_card(stats_grid, 0, "📋", "Sessions", f"{completed_sessions}/{total_sessions}")

        # Karten
        self._create_stat_card(stats_grid, 1, "🎴", "Karten", f"{completed_cards}/{total_cards}")

        # Fortschritt
        progress_text = f"{int(progress * 100)}%"
        self._create_stat_card(stats_grid, 2, "📈", "Fortschritt", progress_text)

        # Wochenziel
        planner_stats = self.planner_manager.get_planner_statistics(self.planner_id)
        goal_text = f"{planner_stats['total_weekly_goal']}"
        self._create_stat_card(stats_grid, 3, "🎯", "Wochenziel", goal_text)

    def _create_stat_card(self, parent, column: int, icon: str, label: str, value: str):
        """Erstellt eine Statistik-Card."""
        card = ctk.CTkFrame(parent, fg_color=COLORS['background'], corner_radius=10)
        card.grid(row=0, column=column, padx=8, sticky='ew')

        ctk.CTkLabel(
            card,
            text=icon,
            font=ctk.CTkFont(size=24)
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        ).pack()

        ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text']
        ).pack(pady=(0, 10))

    # Event Handler
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

    def _go_back(self):
        """Geht zurück zur Planer-Auswahl."""
        # Gehe durch die Widget-Hierarchie um zur FlashcardApp zu gelangen
        if self.app and hasattr(self.app, 'show_weekly_calendar'):
            self.app.show_weekly_calendar()  # Zeigt Planer-Auswahl
        elif hasattr(self.master, 'show_planner_selection'):
            self.master.show_planner_selection()
        else:
            # Fallback: Schließe Fenster wenn Toplevel
            if isinstance(self.master, ctk.CTkToplevel):
                self.master.destroy()

    def _add_session(self, day_index: int):
        """Öffnet Dialog zum Hinzufügen einer Session."""
        messagebox.showinfo("Info", "Session hinzufügen wird implementiert...")

    def _start_session(self, entry: Dict):
        """Startet eine Lern-Session."""
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
        except Exception as e:
            logging.error(f"Fehler beim Starten der Session: {e}", exc_info=True)
            messagebox.showerror("Fehler", f"Fehler beim Starten:\n{e}")

    def _auto_plan_week(self):
        """Startet die automatische Wochenplanung."""
        # Hole alle Lernsets des Planers
        lernsets = self.planner_manager.get_planner_lernsets(self.planner_id)

        if not lernsets:
            messagebox.showwarning("Keine Lernsets", "Dieser Planer hat keine Lernsets.")
            return

        # Kombiniere Ziele aller Lernsets
        total_daily_goal = sum(ls.get('taegliches_ziel', 0) for ls in lernsets)

        if messagebox.askyesno(
            "Automatische Planung",
            f"Möchtest du die Woche automatisch planen?\n\n"
            f"Planer: {self.planner['name']}\n"
            f"Tägliches Ziel: {total_daily_goal} Karten\n\n"
            f"Bestehende automatisch generierte Sessions werden überschrieben."
        ):
            # Verwende erstes Lernset als Basis (kann erweitert werden)
            active_set = lernsets[0] if lernsets else None

            success = self.weekly_planner.auto_plan_week(
                start_date=self.week_start,
                active_learning_set=active_set,
                daily_target=total_daily_goal // 7  # Verteile auf Woche
            )

            if success:
                messagebox.showinfo("Erfolg", "Woche wurde automatisch geplant!")
                self._load_week_data()
            else:
                messagebox.showerror("Fehler", "Fehler bei der automatischen Planung.")

    def _export_week_plan(self):
        """Exportiert den Wochenplan."""
        messagebox.showinfo("Info", "Export wird implementiert...")


class CreateLearningSetFrame(ctk.CTkFrame):
    """Inline Frame zum Erstellen eines neuen Lernsets."""

    def __init__(self, parent, data_manager, on_close_callback=None):
        super().__init__(parent, fg_color=COLORS['surface'], corner_radius=15)
        self.data_manager = data_manager
        self.learning_set_manager = LearningSetManager(data_manager)
        self.on_close_callback = on_close_callback

        self.selected_categories = []
        self._create_ui()

    def _create_ui(self):
        """Erstellt die UI."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="📚  Neues Lernset erstellen",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS['text']
        )
        header.pack(pady=20)

        # Beschreibung
        desc = ctk.CTkLabel(
            self,
            text="Wähle Kategorien aus, die du in diesem Lernset lernen möchtest",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        )
        desc.pack(pady=(0, 20))

        # Name
        ctk.CTkLabel(
            self,
            text="Name des Lernsets:",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text']
        ).pack(pady=(10, 5))

        self.name_entry = ctk.CTkEntry(
            self,
            width=400,
            height=40,
            font=ctk.CTkFont(size=14),
            placeholder_text="z.B. Mathematik Grundlagen"
        )
        self.name_entry.pack(pady=(0, 20))

        # Kategorien-Auswahl
        ctk.CTkLabel(
            self,
            text="Kategorien auswählen:",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text']
        ).pack(pady=(10, 5))

        # Scrollable Frame für Kategorien
        self.categories_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS['background'],
            height=250,
            width=400
        )
        self.categories_frame.pack(pady=(0, 20), padx=20)

        self._load_available_categories()

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        ctk.CTkButton(
            button_frame,
            text="Erstellen",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['success'],
            hover_color='#059669',
            command=self._create,
            width=150,
            height=40
        ).pack(side='left', padx=10)

        ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=self._cancel,
            width=150,
            height=40
        ).pack(side='left', padx=10)

    def _load_available_categories(self):
        """Lädt alle verfügbaren Kategorien."""
        available = self.learning_set_manager.get_available_categories()

        if not available:
            ctk.CTkLabel(
                self.categories_frame,
                text="Keine Kategorien vorhanden.\nErstelle zuerst Flashcards mit Kategorien.",
                text_color=COLORS['text_secondary']
            ).pack(pady=20)
            return

        for category, subcategories in available.items():
            # Category Header
            cat_frame = ctk.CTkFrame(self.categories_frame, fg_color=COLORS['card'], corner_radius=8)
            cat_frame.pack(fill='x', pady=5, padx=5)

            # Category Checkbox
            cat_var = ctk.IntVar()
            cat_checkbox = ctk.CTkCheckBox(
                cat_frame,
                text=f"📁 {category}",
                variable=cat_var,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda c=category, v=cat_var, subs=subcategories: self._toggle_category(c, v, subs)
            )
            cat_checkbox.pack(anchor='w', padx=10, pady=10)

            # Subcategories
            if subcategories:
                subcat_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
                subcat_frame.pack(fill='x', padx=30, pady=(0, 10))

                for subcat in subcategories:
                    sub_var = ctk.IntVar()
                    sub_cb = ctk.CTkCheckBox(
                        subcat_frame,
                        text=subcat,
                        variable=sub_var,
                        font=ctk.CTkFont(size=12),
                        command=lambda c=category, s=subcat, v=sub_var: self._toggle_subcategory(c, s, v)
                    )
                    sub_cb.pack(anchor='w', pady=2)

    def _toggle_category(self, category: str, var: ctk.IntVar, subcategories: List[str]):
        """Wählt alle Unterkategorien einer Kategorie aus/ab."""
        # Diese Funktion wird aufgerufen wenn die Hauptkategorie angeklickt wird
        # Wir müssen alle Unterkategorien entsprechend setzen
        pass

    def _toggle_subcategory(self, category: str, subcategory: str, var: ctk.IntVar):
        """Fügt/Entfernt eine Unterkategorie."""
        cat_subcat = (category, subcategory)
        if var.get():
            if cat_subcat not in self.selected_categories:
                self.selected_categories.append(cat_subcat)
        else:
            if cat_subcat in self.selected_categories:
                self.selected_categories.remove(cat_subcat)

    def _create(self):
        """Erstellt das Lernset."""
        name = self.name_entry.get().strip()

        if not name:
            messagebox.showwarning("Fehler", "Bitte gib einen Namen ein.")
            return

        if not self.selected_categories:
            messagebox.showwarning("Fehler", "Bitte wähle mindestens eine Kategorie/Unterkategorie aus.")
            return

        # Konvertiere selected_categories in das richtige Format
        kategorien_dict = {}
        for cat, subcat in self.selected_categories:
            if cat not in kategorien_dict:
                kategorien_dict[cat] = []
            kategorien_dict[cat].append(subcat)

        kategorien_list = [
            {'kategorie': cat, 'unterkategorien': subcats}
            for cat, subcats in kategorien_dict.items()
        ]

        # Erstelle Set mit Standardzielen
        set_id = self.learning_set_manager.create_set(
            name=name,
            kategorien=kategorien_list,
            taegliches_ziel=20,
            woechentliches_ziel=100
        )

        if set_id:
            messagebox.showinfo("Erfolg", f"Lernset '{name}' wurde erstellt!")
            if self.on_close_callback:
                self.on_close_callback(set_id)
        else:
            messagebox.showerror("Fehler", "Fehler beim Erstellen des Lernsets.")

    def _cancel(self):
        """Bricht ab."""
        if self.on_close_callback:
            self.on_close_callback(None)


class CreatePlannerDialog(ctk.CTkToplevel):
    """Dialog zum Erstellen eines neuen Planers."""

    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.planner_manager = PlannerManager(data_manager)
        self.learning_set_manager = LearningSetManager(data_manager)

        self.title("Neuer Planer")
        self.geometry("600x750")
        self.resizable(False, False)

        # Zentriere Fenster
        self.transient(parent)
        self.grab_set()

        self.selected_lernsets = []
        self.showing_lernset_creator = False
        self._create_ui()

    def _create_ui(self):
        """Erstellt die UI."""
        # Container für den Hauptinhalt
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill='both', expand=True)

        self._show_planner_form()

    def _show_planner_form(self):
        """Zeigt das Planer-Erstellungsformular."""
        # Lösche bestehenden Inhalt
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Header
        header = ctk.CTkLabel(
            self.main_container,
            text="Neuer Wochenplaner",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=30)

        # Name
        ctk.CTkLabel(self.main_container, text="Name:", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))
        self.name_entry = ctk.CTkEntry(self.main_container, width=400, height=40, font=ctk.CTkFont(size=14))
        self.name_entry.pack(pady=(0, 20))

        # Icon
        ctk.CTkLabel(self.main_container, text="Icon:", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))

        icon_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        icon_frame.pack()

        self.icon_var = ctk.StringVar(value="📅")
        icons = get_default_planner_icons()

        for i, icon in enumerate(icons[:8]):
            btn = ctk.CTkRadioButton(
                icon_frame,
                text=icon,
                variable=self.icon_var,
                value=icon,
                font=ctk.CTkFont(size=20),
                radiobutton_width=15,
                radiobutton_height=15
            )
            btn.grid(row=0, column=i, padx=5, pady=10)

        # Lernsets Header mit Button
        lernset_header = ctk.CTkFrame(self.main_container, fg_color="transparent")
        lernset_header.pack(fill='x', padx=40, pady=(20, 10))

        ctk.CTkLabel(
            lernset_header,
            text="Lernsets auswählen:",
            font=ctk.CTkFont(size=14)
        ).pack(side='left')

        ctk.CTkButton(
            lernset_header,
            text="+ Neues Lernset",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['secondary'],
            hover_color='#7c3aed',
            command=self._show_lernset_creator,
            width=130,
            height=30
        ).pack(side='right')

        # Liste
        list_frame = ctk.CTkFrame(self.main_container, fg_color=COLORS['surface'])
        list_frame.pack(fill='both', expand=True, padx=40, pady=(0, 20))

        self.lernsets_scroll = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.lernsets_scroll.pack(fill='both', expand=True, padx=10, pady=10)

        self._load_lernsets()

        # Buttons
        button_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        button_frame.pack(pady=20)

        ctk.CTkButton(
            button_frame,
            text="Erstellen",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            command=self._create,
            width=150,
            height=40
        ).pack(side='left', padx=10)

        ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=self.destroy,
            width=150,
            height=40
        ).pack(side='left', padx=10)

    def _show_lernset_creator(self):
        """Zeigt den Lernset-Ersteller inline."""
        # Lösche bestehenden Inhalt
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Zeige CreateLearningSetFrame
        creator = CreateLearningSetFrame(
            self.main_container,
            self.data_manager,
            on_close_callback=self._on_lernset_created
        )
        creator.pack(fill='both', expand=True, padx=20, pady=20)

    def _on_lernset_created(self, set_id):
        """Callback wenn Lernset erstellt oder abgebrochen wurde."""
        if set_id:
            # Füge das neue Set zur Auswahl hinzu
            if set_id not in self.selected_lernsets:
                self.selected_lernsets.append(set_id)

        # Zurück zum Planer-Formular
        self._show_planner_form()

    def _load_lernsets(self):
        """Lädt alle verfügbaren Lernsets."""
        all_sets = self.learning_set_manager.get_all_sets()

        if not all_sets:
            ctk.CTkLabel(
                self.lernsets_scroll,
                text="Keine Lernsets vorhanden.\nKlicke auf '+ Neues Lernset' um eines zu erstellen.",
                text_color=COLORS['text_secondary']
            ).pack(pady=20)
            return

        for set_id, lernset in all_sets.items():
            var = ctk.IntVar()
            # Setze Checkbox wenn bereits ausgewählt
            if set_id in self.selected_lernsets:
                var.set(1)

            cb = ctk.CTkCheckBox(
                self.lernsets_scroll,
                text=f"{lernset['name']} ({len(lernset['kategorien'])} Kategorien)",
                variable=var,
                font=ctk.CTkFont(size=13),
                command=lambda sid=set_id, v=var: self._toggle_lernset(sid, v)
            )
            cb.pack(anchor='w', pady=5)

    def _toggle_lernset(self, set_id: str, var: ctk.IntVar):
        """Fügt/Entfernt Lernset aus Auswahl."""
        if var.get():
            if set_id not in self.selected_lernsets:
                self.selected_lernsets.append(set_id)
        else:
            if set_id in self.selected_lernsets:
                self.selected_lernsets.remove(set_id)

    def _create(self):
        """Erstellt den Planer."""
        name = self.name_entry.get().strip()

        if not name:
            messagebox.showwarning("Fehler", "Bitte gib einen Namen ein.")
            return

        if not self.selected_lernsets:
            messagebox.showwarning("Fehler", "Bitte wähle mindestens ein Lernset aus.")
            return

        planner_id = self.planner_manager.create_planner(
            name=name,
            lernset_ids=self.selected_lernsets,
            icon=self.icon_var.get()
        )

        if planner_id:
            messagebox.showinfo("Erfolg", f"Planer '{name}' wurde erstellt!")
            self.destroy()
        else:
            messagebox.showerror("Fehler", "Fehler beim Erstellen des Planers.")


class EditPlannerDialog(CreatePlannerDialog):
    """Dialog zum Bearbeiten eines Planers."""

    def __init__(self, parent, data_manager, planner_id: str):
        self.planner_id = planner_id
        super().__init__(parent, data_manager)
        self.title("Planer bearbeiten")

    def _show_planner_form(self):
        """Überschreibt um den Titel anzupassen."""
        # Lösche bestehenden Inhalt
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Lade Planer-Daten
        planner = self.planner_manager.get_planner(self.planner_id)

        # Header
        header = ctk.CTkLabel(
            self.main_container,
            text="Planer bearbeiten",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=30)

        # Name
        ctk.CTkLabel(self.main_container, text="Name:", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))
        self.name_entry = ctk.CTkEntry(self.main_container, width=400, height=40, font=ctk.CTkFont(size=14))
        self.name_entry.pack(pady=(0, 20))
        if planner:
            self.name_entry.insert(0, planner['name'])

        # Icon
        ctk.CTkLabel(self.main_container, text="Icon:", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))

        icon_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        icon_frame.pack()

        self.icon_var = ctk.StringVar(value=planner.get('icon', '📅') if planner else "📅")
        icons = get_default_planner_icons()

        for i, icon in enumerate(icons[:8]):
            btn = ctk.CTkRadioButton(
                icon_frame,
                text=icon,
                variable=self.icon_var,
                value=icon,
                font=ctk.CTkFont(size=20),
                radiobutton_width=15,
                radiobutton_height=15
            )
            btn.grid(row=0, column=i, padx=5, pady=10)

        # Lernsets Header mit Button
        lernset_header = ctk.CTkFrame(self.main_container, fg_color="transparent")
        lernset_header.pack(fill='x', padx=40, pady=(20, 10))

        ctk.CTkLabel(
            lernset_header,
            text="Lernsets auswählen:",
            font=ctk.CTkFont(size=14)
        ).pack(side='left')

        ctk.CTkButton(
            lernset_header,
            text="+ Neues Lernset",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['secondary'],
            hover_color='#7c3aed',
            command=self._show_lernset_creator,
            width=130,
            height=30
        ).pack(side='right')

        # Liste
        list_frame = ctk.CTkFrame(self.main_container, fg_color=COLORS['surface'])
        list_frame.pack(fill='both', expand=True, padx=40, pady=(0, 20))

        self.lernsets_scroll = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.lernsets_scroll.pack(fill='both', expand=True, padx=10, pady=10)

        self._load_lernsets()

        # Buttons
        button_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        button_frame.pack(pady=20)

        ctk.CTkButton(
            button_frame,
            text="Speichern",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            command=self._create,
            width=150,
            height=40
        ).pack(side='left', padx=10)

        ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=self.destroy,
            width=150,
            height=40
        ).pack(side='left', padx=10)

    def _create_ui(self):
        """Überschreibt _create_ui um Daten zu laden."""
        # Lade Planer-Daten ZUERST
        planner = self.planner_manager.get_planner(self.planner_id)
        if planner:
            self.selected_lernsets = planner.get('lernset_ids', []).copy()

        # Erstelle UI
        super()._create_ui()

    def _create(self):
        """Aktualisiert den Planer statt neu zu erstellen."""
        name = self.name_entry.get().strip()

        if not name:
            messagebox.showwarning("Fehler", "Bitte gib einen Namen ein.")
            return

        if not self.selected_lernsets:
            messagebox.showwarning("Fehler", "Bitte wähle mindestens ein Lernset aus.")
            return

        success = self.planner_manager.update_planner(
            self.planner_id,
            name=name,
            lernset_ids=self.selected_lernsets,
            icon=self.icon_var.get()
        )

        if success:
            messagebox.showinfo("Erfolg", f"Planer '{name}' wurde aktualisiert!")
            self.destroy()
        else:
            messagebox.showerror("Fehler", "Fehler beim Aktualisieren des Planers.")
