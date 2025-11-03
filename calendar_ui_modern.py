#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modernisierte Kalender-UI für FlashCards mit Multi-Planer-System.
Nutzt CustomTkinter für ein modernes, ansprechendes Design.
"""

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
import datetime
import logging
from typing import Optional, Dict, List
from calendar_system import CategoryScorer, WeeklyPlanner
from learning_sets import LearningSetManager
from planner_manager import PlannerManager, get_default_planner_icons


# Helles, modernes Farbschema für bessere Lesbarkeit
COLORS = {
    'primary': '#3b82f6',      # Kräftiges Blau
    'primary_hover': '#2563eb',
    'secondary': '#8b5cf6',    # Lila
    'success': '#10b981',      # Grün
    'warning': '#f59e0b',      # Orange
    'danger': '#ef4444',       # Rot
    'background': '#f8fafc',   # Sehr heller Hintergrund
    'surface': '#ffffff',      # Weiße Surface
    'card': '#f1f5f9',         # Sehr helle Card Background
    'text': '#1e293b',         # Dunkler Text
    'text_secondary': '#64748b', # Grauer Text
    'border': '#e2e8f0',       # Heller Border
    'accent': '#0ea5e9',       # Sky Blue Akzent
    'card_hover': '#e2e8f0',   # Hover-State für Cards
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
        """Erstellt eine moderne Card für einen Planer mit verbessertem Design."""
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=COLORS['surface'],
            corner_radius=18,
            border_width=3 if is_active else 2,
            border_color=COLORS['primary'] if is_active else COLORS['border']
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
            font=ctk.CTkFont(size=44)
        )
        icon_label.pack(side='left', padx=(0, 15))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side='left', fill='x', expand=True)

        name = ctk.CTkLabel(
            title_frame,
            text=planner['name'],
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS['text'],
            anchor='w'
        )
        name.pack(fill='x')

        # Active Badge mit Animation-Effekt
        if is_active:
            badge_frame = ctk.CTkFrame(title_frame, fg_color=COLORS['primary'], corner_radius=6)
            badge_frame.pack(fill='x', pady=(5, 0))

            badge = ctk.CTkLabel(
                badge_frame,
                text="✓ AKTIV",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLORS['text']
            )
            badge.pack(padx=8, pady=3)

        # Statistiken mit modernem Design
        stats = self.planner_manager.get_planner_statistics(planner['id'])

        stats_frame = ctk.CTkFrame(content_frame, fg_color=COLORS['card'], corner_radius=12, border_width=1, border_color=COLORS['border'])
        stats_frame.pack(fill='x', pady=(0, 15))

        # Grid für Statistiken
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill='x', padx=15, pady=12)
        stats_grid.grid_columnconfigure((0, 1), weight=1)

        # Lernsets
        lernsets_frame = ctk.CTkFrame(stats_grid, fg_color="transparent")
        lernsets_frame.grid(row=0, column=0, sticky='w', padx=(0, 10))

        ctk.CTkLabel(
            lernsets_frame,
            text="📚",
            font=ctk.CTkFont(size=16)
        ).pack(side='left', padx=(0, 5))

        ctk.CTkLabel(
            lernsets_frame,
            text=f"{stats['total_lernsets']} Lernsets",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text']
        ).pack(side='left')

        # Kategorien
        cats_frame = ctk.CTkFrame(stats_grid, fg_color="transparent")
        cats_frame.grid(row=0, column=1, sticky='e', padx=(10, 0))

        ctk.CTkLabel(
            cats_frame,
            text="🎯",
            font=ctk.CTkFont(size=16)
        ).pack(side='left', padx=(0, 5))

        ctk.CTkLabel(
            cats_frame,
            text=f"{stats['total_categories']} Kategorien",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text']
        ).pack(side='left')

        # Ziel-Badge
        goal_frame = ctk.CTkFrame(content_frame, fg_color=COLORS['success'], corner_radius=10)
        goal_frame.pack(fill='x', pady=(0, 15))

        ctk.CTkLabel(
            goal_frame,
            text=f"🎯 Tägliches Ziel: {stats['total_daily_goal']} Karten",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['text']
        ).pack(padx=15, pady=10)

        # Buttons mit verbessertem Layout
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill='x')

        if not is_active:
            activate_btn = ctk.CTkButton(
                button_frame,
                text="▶ Auswählen",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=COLORS['primary'],
                hover_color=COLORS['primary_hover'],
                command=lambda: self._select_planner(planner['id']),
                height=38,
                corner_radius=10
            )
            activate_btn.pack(side='left', fill='x', expand=True, padx=(0, 8))
        else:
            open_btn = ctk.CTkButton(
                button_frame,
                text="▶ Öffnen",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=COLORS['accent'],
                hover_color=COLORS['primary'],
                command=lambda: self._open_planner(planner['id']),
                height=38,
                corner_radius=10
            )
            open_btn.pack(side='left', fill='x', expand=True, padx=(0, 8))

        edit_btn = ctk.CTkButton(
            button_frame,
            text="⚙",
            font=ctk.CTkFont(size=16),
            fg_color=COLORS['card'],
            hover_color=COLORS['card_hover'],
            command=lambda: self._edit_planner(planner['id']),
            width=38,
            height=38,
            corner_radius=10
        )
        edit_btn.pack(side='left', padx=(0, 8))

        delete_btn = ctk.CTkButton(
            button_frame,
            text="🗑",
            font=ctk.CTkFont(size=16),
            fg_color=COLORS['danger'],
            hover_color='#dc2626',
            command=lambda: self._delete_planner(planner['id']),
            width=38,
            height=38,
            corner_radius=10
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
        """Zeigt Planer-Erstellungsformular inline."""
        self._show_planner_form(planner_id=None)

    def _edit_planner(self, planner_id: str):
        """Zeigt Planer-Bearbeitungsformular inline."""
        self._show_planner_form(planner_id=planner_id)

    def _show_planner_form(self, planner_id: Optional[str] = None):
        """Zeigt das Planer-Formular inline."""
        # Lösche aktuelle Ansicht
        for widget in self.winfo_children():
            widget.destroy()

        # Zeige CreatePlannerFrame
        planner_frame = CreatePlannerFrame(
            self,
            self.data_manager,
            planner_id=planner_id,
            on_close_callback=self._on_planner_form_closed
        )
        planner_frame.pack(fill='both', expand=True)

    def _on_planner_form_closed(self, created: bool):
        """Callback wenn Planer-Formular geschlossen wird."""
        # Baue normale Ansicht wieder auf
        for widget in self.winfo_children():
            widget.destroy()
        self._create_ui()

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
        self.month_start = datetime.date(self.current_date.year, self.current_date.month, 1)

        # Aktuelle Ansicht
        self.current_view = 'week'  # 'day', 'week', 'month'

        # UI erstellen
        self._create_ui()
        self._load_data()

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

        # View Toggle (Mitte-Rechts)
        view_frame = ctk.CTkFrame(header_frame, fg_color=COLORS['card'], corner_radius=8)
        view_frame.pack(side='right', padx=(0, 20))

        # View Buttons
        self.day_view_btn = ctk.CTkButton(
            view_frame,
            text="Tag",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS['surface'] if self.current_view != 'day' else COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            command=lambda: self._switch_view('day'),
            width=70,
            height=35,
            corner_radius=6
        )
        self.day_view_btn.pack(side='left', padx=3, pady=3)

        self.week_view_btn = ctk.CTkButton(
            view_frame,
            text="Woche",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS['surface'] if self.current_view != 'week' else COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            command=lambda: self._switch_view('week'),
            width=70,
            height=35,
            corner_radius=6
        )
        self.week_view_btn.pack(side='left', padx=3, pady=3)

        self.month_view_btn = ctk.CTkButton(
            view_frame,
            text="Monat",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS['surface'] if self.current_view != 'month' else COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            command=lambda: self._switch_view('month'),
            width=70,
            height=35,
            corner_radius=6
        )
        self.month_view_btn.pack(side='left', padx=3, pady=3)

        # Navigation (rechts)
        nav_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        nav_frame.pack(side='right')

        self.prev_btn = ctk.CTkButton(
            nav_frame,
            text="◄",
            font=ctk.CTkFont(size=16),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=self._previous_period,
            width=40,
            height=40,
            corner_radius=8
        )
        self.prev_btn.pack(side='left', padx=5)

        self.today_btn = ctk.CTkButton(
            nav_frame,
            text="Heute",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            command=self._go_to_today,
            height=40,
            corner_radius=8
        )
        self.today_btn.pack(side='left', padx=5)

        self.next_btn = ctk.CTkButton(
            nav_frame,
            text="►",
            font=ctk.CTkFont(size=16),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=self._next_period,
            width=40,
            height=40,
            corner_radius=8
        )
        self.next_btn.pack(side='left', padx=5)

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
        """Erstellt ein modernes Frame für einen Tag mit verbessertem Design."""
        frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS['surface'],
            corner_radius=15,
            border_width=2,
            border_color=COLORS['border']
        )

        # Header mit Gradient-Look
        header = ctk.CTkFrame(frame, fg_color=COLORS['background'], corner_radius=12)
        header.pack(fill='x', padx=10, pady=10)

        day_label = ctk.CTkLabel(
            header,
            text=day_name,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS['text']
        )
        day_label.pack(pady=(10, 5))

        date_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary']
        )
        date_label.pack(pady=(0, 10))

        # Badge für fällige Karten mit modernem Design
        badge_frame = ctk.CTkFrame(
            frame,
            fg_color=COLORS['card'],
            corner_radius=8
        )
        badge_frame.pack(fill='x', padx=10, pady=(0, 10))

        badge_label = ctk.CTkLabel(
            badge_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text']
        )
        badge_label.pack(pady=8)

        # Sessions Container
        sessions_frame = ctk.CTkFrame(frame, fg_color="transparent")
        sessions_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Add Button mit modernem Design
        add_btn = ctk.CTkButton(
            frame,
            text="➕ Session hinzufügen",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['primary'],
            command=lambda idx=day_index: self._add_session(idx),
            height=36,
            corner_radius=10
        )
        add_btn.pack(padx=10, pady=(0, 10), fill='x')

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
        """Erstellt ein Widget für eine Session mit verbessertem Design."""
        # Session Frame mit Gradient-Effekt
        session_frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS['surface'],
            corner_radius=10,
            border_width=2,
            border_color=COLORS['border']
        )
        session_frame.pack(fill='x', pady=6)

        # Status Icon
        status = entry.get('status', 'offen')
        if status == 'erledigt':
            icon = '✓'
            color = COLORS['success']
            border_color = COLORS['success']
        elif status == 'übersprungen':
            icon = '✗'
            color = COLORS['warning']
            border_color = COLORS['warning']
        else:
            icon = '⏳'
            color = COLORS['accent']
            border_color = COLORS['accent']

        session_frame.configure(border_color=border_color)

        # Header mit Icon und Kategorie
        header_frame = ctk.CTkFrame(session_frame, fg_color="transparent")
        header_frame.pack(fill='x', padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header_frame,
            text=icon,
            font=ctk.CTkFont(size=16),
            text_color=color
        ).pack(side='left', padx=(0, 8))

        # Kategorie
        kategorie_text = f"{entry['kategorie']}"
        if entry.get('unterkategorie'):
            kategorie_text += f" • {entry['unterkategorie']}"

        kategorie_label = ctk.CTkLabel(
            header_frame,
            text=kategorie_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['text'],
            anchor='w'
        )
        kategorie_label.pack(side='left', fill='x', expand=True)

        # Karten-Info mit Icon
        info_frame = ctk.CTkFrame(session_frame, fg_color="transparent")
        info_frame.pack(fill='x', padx=10, pady=5)

        info_text = f"🎴 {entry.get('erwartete_karten', 0)} Karten"
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary'],
            anchor='w'
        ).pack(side='left')

        # Buttons Frame
        buttons_frame = ctk.CTkFrame(session_frame, fg_color="transparent")
        buttons_frame.pack(fill='x', padx=10, pady=(5, 10))

        # Bearbeiten Button (immer sichtbar)
        edit_btn = ctk.CTkButton(
            buttons_frame,
            text="✏️",
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['card'],
            hover_color=COLORS['card_hover'],
            command=lambda: self._edit_session(entry, date),
            width=40,
            height=32,
            corner_radius=8
        )
        edit_btn.pack(side='right', padx=(5, 0))

        if status == 'offen':
            # Lernen Button mit modernem Design
            learn_btn = ctk.CTkButton(
                buttons_frame,
                text="▶ Lernen starten",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=COLORS['primary'],
                hover_color=COLORS['primary_hover'],
                command=lambda: self._start_session(entry),
                height=32,
                corner_radius=8
            )
            learn_btn.pack(side='left', fill='x', expand=True, padx=(0, 5))

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
        """Erstellt eine moderne Statistik-Card mit verbessertem Design."""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS['surface'],
            corner_radius=12,
            border_width=2,
            border_color=COLORS['border']
        )
        card.grid(row=0, column=column, padx=8, sticky='ew')

        # Icon mit Hintergrund
        icon_frame = ctk.CTkFrame(card, fg_color=COLORS['card'], corner_radius=10)
        icon_frame.pack(pady=(15, 10))

        ctk.CTkLabel(
            icon_frame,
            text=icon,
            font=ctk.CTkFont(size=28)
        ).pack(padx=15, pady=10)

        ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS['text']
        ).pack(pady=(0, 15))

    # Event Handler
    def _previous_period(self):
        """Navigiert zur vorherigen Periode (Tag/Woche/Monat)."""
        if self.current_view == 'day':
            self.current_date -= datetime.timedelta(days=1)
        elif self.current_view == 'week':
            self.week_start -= datetime.timedelta(days=7)
        else:  # month
            # Vorheriger Monat
            if self.month_start.month == 1:
                self.month_start = datetime.date(self.month_start.year - 1, 12, 1)
            else:
                self.month_start = datetime.date(self.month_start.year, self.month_start.month - 1, 1)
        self._load_data()

    def _next_period(self):
        """Navigiert zur nächsten Periode (Tag/Woche/Monat)."""
        if self.current_view == 'day':
            self.current_date += datetime.timedelta(days=1)
        elif self.current_view == 'week':
            self.week_start += datetime.timedelta(days=7)
        else:  # month
            # Nächster Monat
            if self.month_start.month == 12:
                self.month_start = datetime.date(self.month_start.year + 1, 1, 1)
            else:
                self.month_start = datetime.date(self.month_start.year, self.month_start.month + 1, 1)
        self._load_data()

    def _go_to_today(self):
        """Navigiert zu heute."""
        self.current_date = datetime.date.today()
        self.week_start = self._get_week_start(self.current_date)
        self.month_start = datetime.date(self.current_date.year, self.current_date.month, 1)
        self._load_data()

    def _switch_view(self, view: str):
        """Wechselt die Ansicht."""
        if view == self.current_view:
            return

        self.current_view = view

        # Update Button-Farben
        self.day_view_btn.configure(fg_color=COLORS['primary'] if view == 'day' else COLORS['surface'])
        self.week_view_btn.configure(fg_color=COLORS['primary'] if view == 'week' else COLORS['surface'])
        self.month_view_btn.configure(fg_color=COLORS['primary'] if view == 'month' else COLORS['surface'])

        # Neu laden
        self._load_data()

    def _load_data(self):
        """Lädt Daten basierend auf aktueller Ansicht."""
        if self.current_view == 'day':
            self._load_day_data()
        elif self.current_view == 'week':
            self._load_week_data()
        else:  # month
            self._load_month_data()

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
        """Öffnet Inline-Editor zum Hinzufügen einer Session."""
        date = self.week_start + datetime.timedelta(days=day_index)
        self._show_session_editor(date, entry=None)

    def _edit_session(self, entry: Dict, date: datetime.date):
        """Öffnet Inline-Editor zum Bearbeiten einer Session."""
        self._show_session_editor(date, entry=entry)

    def _show_session_editor(self, date: datetime.date, entry: Optional[Dict] = None):
        """Zeigt Inline-Editor zum Erstellen/Bearbeiten einer Session."""
        # Verstecke Kalenderansicht
        for widget in self.winfo_children():
            widget.pack_forget()

        # Erstelle Session-Editor Frame
        editor_frame = SessionEditorFrame(
            self,
            self.data_manager,
            self.planner_manager,
            self.planner_id,
            date,
            entry,
            on_close_callback=self._on_session_editor_closed
        )
        editor_frame.pack(fill='both', expand=True)

    def _on_session_editor_closed(self):
        """Callback wenn Session-Editor geschlossen wird."""
        # Stelle Kalenderansicht wieder her
        for widget in self.winfo_children():
            widget.destroy()
        self._create_ui()
        self._load_week_data()

    def _show_session_dialog(self, date: datetime.date, entry: Optional[Dict] = None):
        """Zeigt Dialog zum Erstellen/Bearbeiten einer Session."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Session bearbeiten" if entry else "Session hinzufügen")
        dialog.geometry("600x700")
        dialog.transient(self)
        dialog.grab_set()

        # Hole Planer-Kategorien
        planner_categories = self.planner_manager.get_planner_categories(self.planner_id)
        category_dict = {}
        for cat, subcat in planner_categories:
            if cat not in category_dict:
                category_dict[cat] = []
            category_dict[cat].append(subcat)

        # Header
        header = ctk.CTkLabel(
            dialog,
            text="✏️ Session bearbeiten" if entry else "➕ Neue Session",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS['text']
        )
        header.pack(pady=(30, 20))

        # Content Frame
        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill='both', expand=True, padx=30, pady=(0, 20))

        # Datum
        ctk.CTkLabel(
            content,
            text=f"📅 Datum: {date.strftime('%d.%m.%Y')}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        ).pack(anchor='w', pady=(0, 15))

        # Kategorie
        ctk.CTkLabel(
            content,
            text="Kategorie:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w', pady=(10, 5))

        category_var = ctk.StringVar(value=entry['kategorie'] if entry else list(category_dict.keys())[0] if category_dict else "")
        category_combo = ctk.CTkComboBox(
            content,
            values=list(category_dict.keys()) if category_dict else ["Keine Kategorien"],
            variable=category_var,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['surface'],
            border_color=COLORS['border']
        )
        category_combo.pack(fill='x', pady=(0, 15))

        # Unterkategorie
        ctk.CTkLabel(
            content,
            text="Unterkategorie:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w', pady=(10, 5))

        def update_subcategories(*args):
            cat = category_var.get()
            subcats = category_dict.get(cat, [])
            subcategory_combo.configure(values=subcats if subcats else ["Keine"])
            if subcats and not entry:
                subcategory_var.set(subcats[0])

        subcategory_var = ctk.StringVar(value=entry['unterkategorie'] if entry else "")
        subcategory_combo = ctk.CTkComboBox(
            content,
            variable=subcategory_var,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['surface'],
            border_color=COLORS['border']
        )
        subcategory_combo.pack(fill='x', pady=(0, 15))

        # Update Subcategories bei Kategorie-Wechsel
        category_var.trace_add('write', update_subcategories)
        update_subcategories()

        # Erwartete Karten
        ctk.CTkLabel(
            content,
            text="Erwartete Karten:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w', pady=(10, 5))

        cards_entry = ctk.CTkEntry(
            content,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['surface'],
            border_color=COLORS['border']
        )
        cards_entry.insert(0, str(entry.get('erwartete_karten', 20)) if entry else "20")
        cards_entry.pack(fill='x', pady=(0, 15))

        # Priorität
        ctk.CTkLabel(
            content,
            text="Priorität:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w', pady=(10, 5))

        priority_var = ctk.StringVar(value=entry.get('prioritaet', 'mittel') if entry else 'mittel')
        priority_frame = ctk.CTkFrame(content, fg_color="transparent")
        priority_frame.pack(fill='x', pady=(0, 15))

        for prio in ['niedrig', 'mittel', 'hoch']:
            ctk.CTkRadioButton(
                priority_frame,
                text=prio.capitalize(),
                variable=priority_var,
                value=prio,
                font=ctk.CTkFont(size=13)
            ).pack(side='left', padx=10)

        # Notizen
        ctk.CTkLabel(
            content,
            text="Notizen (optional):",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w', pady=(10, 5))

        notes_textbox = ctk.CTkTextbox(
            content,
            height=100,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['surface'],
            border_color=COLORS['border']
        )
        if entry and entry.get('notizen'):
            notes_textbox.insert('1.0', entry['notizen'])
        notes_textbox.pack(fill='x', pady=(0, 20))

        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=(0, 30))

        def save_session():
            try:
                kategorie = category_var.get()
                unterkategorie = subcategory_var.get()
                erwartete_karten = int(cards_entry.get().strip())
                prioritaet = priority_var.get()
                notizen = notes_textbox.get('1.0', 'end').strip()

                if not kategorie or not unterkategorie:
                    messagebox.showwarning("Fehler", "Bitte wähle Kategorie und Unterkategorie.")
                    return

                if erwartete_karten <= 0:
                    messagebox.showwarning("Fehler", "Erwartete Karten muss größer als 0 sein.")
                    return

                if entry:
                    # Bearbeite bestehende Session
                    self.data_manager.update_plan_entry(
                        entry['id'],
                        kategorie=kategorie,
                        unterkategorie=unterkategorie,
                        erwartete_karten=erwartete_karten,
                        prioritaet=prioritaet,
                        notizen=notizen
                    )
                else:
                    # Neue Session
                    self.data_manager.add_plan_entry(
                        date=date,
                        kategorie=kategorie,
                        unterkategorie=unterkategorie,
                        aktion='lernen',
                        erwartete_karten=erwartete_karten,
                        prioritaet=prioritaet,
                        notizen=notizen,
                        auto_generiert=False
                    )

                dialog.destroy()
                self._load_week_data()

            except ValueError:
                messagebox.showwarning("Fehler", "Erwartete Karten muss eine Zahl sein.")

        def delete_session():
            if entry and messagebox.askyesno("Löschen", "Session wirklich löschen?"):
                self.data_manager.delete_plan_entry(entry['id'])
                dialog.destroy()
                self._load_week_data()

        ctk.CTkButton(
            button_frame,
            text="✓ Speichern",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['success'],
            hover_color='#059669',
            command=save_session,
            width=140,
            height=40,
            corner_radius=10
        ).pack(side='left', padx=5)

        if entry:
            ctk.CTkButton(
                button_frame,
                text="🗑 Löschen",
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=COLORS['danger'],
                hover_color='#dc2626',
                command=delete_session,
                width=140,
                height=40,
                corner_radius=10
            ).pack(side='left', padx=5)

        ctk.CTkButton(
            button_frame,
            text="✗ Abbrechen",
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=dialog.destroy,
            width=140,
            height=40,
            corner_radius=10
        ).pack(side='left', padx=5)

    def _start_session(self, entry: Dict):
        """Startet eine Lern-Session - Navigiert zur Leitner-Kartenauswahl mit voreingestellten Filtern."""
        if not self.app:
            messagebox.showerror("Fehler", "App-Referenz fehlt.")
            return

        try:
            # Navigiere zur Leitner-Kartenauswahl-Seite
            self.app.show_leitner_options()

            # Setze die Filter entsprechend der geplanten Session
            kategorie = entry.get('kategorie', 'Alle')
            unterkategorie = entry.get('unterkategorie', 'Alle')
            erwartete_karten = entry.get('erwartete_karten', 20)

            # Setze Kategorie
            if kategorie and kategorie != 'Alle':
                self.app.category_var.set(kategorie)
                self.app.update_leitner_subcategories()

            # Setze Unterkategorie
            if unterkategorie and unterkategorie != 'Alle':
                self.app.subcategory_var.set(unterkategorie)

            # Setze Session-Größe
            cards_str = str(erwartete_karten)
            available_cards = ["10", "20", "30", "40", "50", "100"]
            if cards_str in available_cards:
                self.app.cards_per_session_var.set(cards_str)
            else:
                # Finde den nächstgelegenen Wert
                cards_int = int(erwartete_karten)
                closest = min(available_cards, key=lambda x: abs(int(x) - cards_int))
                self.app.cards_per_session_var.set(closest)

            # Aktualisiere die Kartenvorschau mit den neuen Filtern
            self.app.preview_leitner_cards()

            logging.info(f"Navigiert zur Leitner-Kartenauswahl mit Filtern: {kategorie}/{unterkategorie}, {erwartete_karten} Karten")

        except Exception as e:
            logging.error(f"Fehler beim Navigieren zur Leitner-Auswahl: {e}", exc_info=True)
            messagebox.showerror("Fehler", f"Fehler beim Öffnen der Kartenauswahl:\n{e}")

    def _auto_plan_week(self):
        """Startet die intelligente automatische Wochenplanung mit individuellen Präferenzen."""
        # Hole alle Lernsets des Planers
        lernsets = self.planner_manager.get_planner_lernsets(self.planner_id)

        if not lernsets:
            messagebox.showwarning("Keine Lernsets", "Dieser Planer hat keine Lernsets.")
            return

        # Berechne Statistiken
        total_daily_goal = sum(ls.get('taegliches_ziel', 0) for ls in lernsets)

        # Sammle alle Kategorien aus den Lernsets
        all_categories = set()
        for lernset in lernsets:
            if 'kategorien' in lernset:
                for kat_entry in lernset['kategorien']:
                    all_categories.add(kat_entry['kategorie'])

        # Öffne Präferenzen-Dialog
        dialog = PlannerPreferencesDialog(
            self.root,
            categories=sorted(list(all_categories)),
            total_daily_goal=total_daily_goal if total_daily_goal > 0 else 20
        )
        preferences = dialog.get_result()

        if not preferences:
            # Nutzer hat abgebrochen
            return

        # Berechne Tagesgewichte basierend auf der Verteilung
        day_weights = self._calculate_day_weights(preferences['daily_distribution'])

        # Rufe die erweiterte auto_plan_week Methode mit Präferenzen auf
        success = self.weekly_planner.auto_plan_week_with_preferences(
            start_date=self.week_start,
            all_learning_sets=lernsets,
            preferences=preferences,
            day_weights=day_weights
        )

        if success:
            messagebox.showinfo(
                "✓ Erfolg",
                "Woche wurde intelligent geplant!\n\n"
                "Du kannst die Sessions jetzt individuell anpassen."
            )
            self._load_week_data()
        else:
            messagebox.showerror("Fehler", "Fehler bei der automatischen Planung.")

    def _calculate_day_weights(self, daily_distribution: Dict[str, str]) -> List[float]:
        """
        Berechnet Gewichte für jeden Tag basierend auf der gewählten Belastung.

        Args:
            daily_distribution: Dict mit Tag-Namen und Belastung (Hoch/Mittel/Gering)

        Returns:
            Liste von 7 Gewichten (Montag-Sonntag), normalisiert auf Summe 7.0
        """
        # Mapping von Belastung zu Gewicht
        weight_map = {
            "Hoch": 1.5,
            "Mittel": 1.0,
            "Gering": 0.5
        }

        days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        weights = [weight_map.get(daily_distribution.get(day, "Mittel"), 1.0) for day in days]

        # Normalisiere, damit die Summe 7.0 ist (durchschnittlich 1.0 pro Tag)
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w * 7.0 / total_weight for w in weights]

        return weights

    def _load_day_data(self):
        """Lädt Daten für die Tagesansicht."""
        # Aktualisiere Label
        self.week_label.configure(
            text=f"📅 {self.current_date.strftime('%A, %d. %B %Y')}"
        )

        # Lösche Grid und zeige Tagesdetails
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Detaillierte Tagesansicht
        day_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        day_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Fällige Karten Header
        due_count = self._count_due_cards_for_date(self.current_date)
        due_frame = ctk.CTkFrame(day_container, fg_color=COLORS['card'], corner_radius=15)
        due_frame.pack(fill='x', pady=(0, 20))

        ctk.CTkLabel(
            due_frame,
            text=f"📊 {due_count} Karten fällig heute",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text']
        ).pack(pady=20)

        # Sessions
        sessions_header = ctk.CTkFrame(day_container, fg_color="transparent")
        sessions_header.pack(fill='x', pady=(10, 15))

        ctk.CTkLabel(
            sessions_header,
            text="📝 Geplante Sessions",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text']
        ).pack(side='left')

        add_btn = ctk.CTkButton(
            sessions_header,
            text="➕ Session hinzufügen",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            command=lambda: self._add_session(0),
            height=35,
            corner_radius=8
        )
        add_btn.pack(side='right')

        # Sessions Liste
        entries = self.data_manager.get_plan_for_date(self.current_date)
        if not entries:
            ctk.CTkLabel(
                day_container,
                text="Noch keine Sessions für heute geplant.\nKlicke auf 'Session hinzufügen' um zu starten!",
                font=ctk.CTkFont(size=14),
                text_color=COLORS['text_secondary'],
                justify='center'
            ).pack(pady=40)
        else:
            for entry in entries:
                session_card = ctk.CTkFrame(day_container, fg_color=COLORS['surface'], corner_radius=15, border_width=2, border_color=COLORS['border'])
                session_card.pack(fill='x', pady=10)

                # Header
                header = ctk.CTkFrame(session_card, fg_color="transparent")
                header.pack(fill='x', padx=20, pady=(15, 10))

                status = entry.get('status', 'offen')
                status_icons = {'offen': '⏳', 'erledigt': '✓', 'übersprungen': '✗'}
                status_colors = {'offen': COLORS['accent'], 'erledigt': COLORS['success'], 'übersprungen': COLORS['warning']}

                ctk.CTkLabel(
                    header,
                    text=status_icons.get(status, '⏳'),
                    font=ctk.CTkFont(size=24),
                    text_color=status_colors.get(status, COLORS['accent'])
                ).pack(side='left', padx=(0, 15))

                info_frame = ctk.CTkFrame(header, fg_color="transparent")
                info_frame.pack(side='left', fill='x', expand=True)

                ctk.CTkLabel(
                    info_frame,
                    text=f"{entry['kategorie']} • {entry['unterkategorie']}",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=COLORS['text'],
                    anchor='w'
                ).pack(fill='x')

                ctk.CTkLabel(
                    info_frame,
                    text=f"🎴 {entry.get('erwartete_karten', 0)} Karten • Priorität: {entry.get('prioritaet', 'mittel').capitalize()}",
                    font=ctk.CTkFont(size=13),
                    text_color=COLORS['text_secondary'],
                    anchor='w'
                ).pack(fill='x')

                # Notizen
                if entry.get('notizen'):
                    notes_frame = ctk.CTkFrame(session_card, fg_color=COLORS['card'], corner_radius=10)
                    notes_frame.pack(fill='x', padx=20, pady=(0, 10))
                    ctk.CTkLabel(
                        notes_frame,
                        text=f"📌 {entry['notizen']}",
                        font=ctk.CTkFont(size=12),
                        text_color=COLORS['text_secondary'],
                        wraplength=600,
                        justify='left'
                    ).pack(padx=15, pady=10, anchor='w')

                # Buttons
                btn_frame = ctk.CTkFrame(session_card, fg_color="transparent")
                btn_frame.pack(fill='x', padx=20, pady=(0, 15))

                if status == 'offen':
                    ctk.CTkButton(
                        btn_frame,
                        text="▶ Lernen starten",
                        font=ctk.CTkFont(size=13, weight="bold"),
                        fg_color=COLORS['primary'],
                        hover_color=COLORS['primary_hover'],
                        command=lambda e=entry: self._start_session(e),
                        height=40,
                        corner_radius=10
                    ).pack(side='left', fill='x', expand=True, padx=(0, 10))

                ctk.CTkButton(
                    btn_frame,
                    text="✏️ Bearbeiten",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    fg_color=COLORS['surface'],
                    hover_color=COLORS['border'],
                    command=lambda e=entry: self._edit_session(e, self.current_date),
                    height=40,
                    corner_radius=10
                ).pack(side='left', padx=(0, 10))

        # Update Statistik
        self._update_week_statistics()

    def _load_month_data(self):
        """Lädt Daten für die Monatsansicht."""
        # Aktualisiere Label
        month_name = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
                     'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'][self.month_start.month - 1]
        self.week_label.configure(
            text=f"📅 {month_name} {self.month_start.year}"
        )

        # Lösche Grid
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Monats-Grid
        month_grid = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        month_grid.pack(fill='both', expand=True, padx=20, pady=20)

        # Wochentag-Header
        day_names = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
        for i, day_name in enumerate(day_names):
            header = ctk.CTkLabel(
                month_grid,
                text=day_name,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLORS['text']
            )
            header.grid(row=0, column=i, padx=5, pady=10, sticky='ew')
            month_grid.grid_columnconfigure(i, weight=1, minsize=150)

        # Berechne Tage im Monat
        import calendar
        cal = calendar.monthcalendar(self.month_start.year, self.month_start.month)

        row = 1
        for week in cal:
            for col, day in enumerate(week):
                if day == 0:
                    # Leerer Tag
                    empty_frame = ctk.CTkFrame(month_grid, fg_color="transparent")
                    empty_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
                else:
                    # Tag mit Daten
                    date = datetime.date(self.month_start.year, self.month_start.month, day)
                    day_frame = self._create_month_day_cell(month_grid, date)
                    day_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            row += 1

        # Update Statistik (für den ganzen Monat)
        self._update_month_statistics()

    def _create_month_day_cell(self, parent, date: datetime.date) -> ctk.CTkFrame:
        """Erstellt eine Zelle für einen Tag in der Monatsansicht."""
        is_today = date == datetime.date.today()

        cell = ctk.CTkFrame(
            parent,
            fg_color=COLORS['surface'],
            corner_radius=10,
            border_width=2 if is_today else 1,
            border_color=COLORS['primary'] if is_today else COLORS['border']
        )

        # Datum
        date_label = ctk.CTkLabel(
            cell,
            text=str(date.day),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['primary'] if is_today else COLORS['text']
        )
        date_label.pack(pady=(10, 5))

        # Sessions Count
        entries = self.data_manager.get_plan_for_date(date)
        if entries:
            count_label = ctk.CTkLabel(
                cell,
                text=f"📝 {len(entries)} Session(s)",
                font=ctk.CTkFont(size=10),
                text_color=COLORS['text_secondary']
            )
            count_label.pack(pady=2)

            # Status Summary
            completed = sum(1 for e in entries if e.get('status') == 'erledigt')
            if completed > 0:
                status_label = ctk.CTkLabel(
                    cell,
                    text=f"✓ {completed}",
                    font=ctk.CTkFont(size=10),
                    text_color=COLORS['success']
                )
                status_label.pack(pady=2)

        # Fällige Karten
        due_count = self._count_due_cards_for_date(date)
        if due_count > 0:
            due_label = ctk.CTkLabel(
                cell,
                text=f"🔔 {due_count}",
                font=ctk.CTkFont(size=10),
                text_color=COLORS['warning'] if due_count >= 20 else COLORS['text_secondary']
            )
            due_label.pack(pady=(2, 10))
        else:
            # Spacer
            ctk.CTkLabel(cell, text="", height=15).pack()

        # Click handler um zum Tag zu springen
        def goto_day():
            self.current_date = date
            self._switch_view('day')

        cell.bind("<Button-1>", lambda e: goto_day())
        date_label.bind("<Button-1>", lambda e: goto_day())

        return cell

    def _update_month_statistics(self):
        """Aktualisiert Statistiken für Monatsansicht."""
        # Lösche alte Widgets
        for widget in self.stats_container.winfo_children():
            widget.destroy()

        # Berechne Monatsstatistiken
        import calendar
        days_in_month = calendar.monthrange(self.month_start.year, self.month_start.month)[1]

        total_sessions = 0
        completed_sessions = 0
        total_cards = 0

        for day in range(1, days_in_month + 1):
            date = datetime.date(self.month_start.year, self.month_start.month, day)
            entries = self.data_manager.get_plan_for_date(date)
            for entry in entries:
                total_sessions += 1
                if entry['status'] == 'erledigt':
                    completed_sessions += 1
                    total_cards += entry.get('tatsaechliche_karten', 0)

        # Stats-Grid
        stats_grid = ctk.CTkFrame(self.stats_container, fg_color="transparent")
        stats_grid.pack(fill='x')
        stats_grid.grid_columnconfigure((0, 1, 2), weight=1)

        # Sessions
        self._create_stat_card(stats_grid, 0, "📋", "Sessions", f"{completed_sessions}/{total_sessions}")

        # Karten
        self._create_stat_card(stats_grid, 1, "🎴", "Gelernte Karten", f"{total_cards}")

        # Fortschritt
        progress = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        self._create_stat_card(stats_grid, 2, "📈", "Fortschritt", f"{int(progress)}%")

    def _export_week_plan(self):
        """Exportiert den Wochenplan."""
        messagebox.showinfo("Info", "Export wird implementiert...")


class SessionEditorFrame(ctk.CTkFrame):
    """Inline Frame zum Erstellen/Bearbeiten einer Session."""

    def __init__(self, parent, data_manager, planner_manager, planner_id, date, entry=None, on_close_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.data_manager = data_manager
        self.planner_manager = planner_manager
        self.planner_id = planner_id
        self.date = date
        self.entry = entry
        self.on_close_callback = on_close_callback
        self._create_ui()

    def _create_ui(self):
        """Erstellt die UI."""
        # Container
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill='both', expand=True, padx=40, pady=30)

        # Header mit Zurück-Button
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill='x', pady=(0, 20))

        back_btn = ctk.CTkButton(
            header_frame,
            text="← Zurück",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=self._cancel,
            width=100,
            height=35,
            corner_radius=8
        )
        back_btn.pack(side='left')

        # Titel
        title_text = "✏️ Session bearbeiten" if self.entry else "➕ Neue Session"
        header = ctk.CTkLabel(
            main_container,
            text=title_text,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS['text']
        )
        header.pack(pady=(20, 30))

        # Hole Planer-Kategorien
        planner_categories = self.planner_manager.get_planner_categories(self.planner_id)
        category_dict = {}
        for cat, subcat in planner_categories:
            if cat not in category_dict:
                category_dict[cat] = []
            category_dict[cat].append(subcat)

        # Content Frame (scrollbar)
        content = ctk.CTkScrollableFrame(main_container, fg_color=COLORS['surface'], corner_radius=12)
        content.pack(fill='both', expand=True, pady=(0, 20))

        # Innerer Content mit Padding
        inner_content = ctk.CTkFrame(content, fg_color="transparent")
        inner_content.pack(fill='both', expand=True, padx=20, pady=20)

        # Datum
        ctk.CTkLabel(
            inner_content,
            text=f"📅 Datum: {self.date.strftime('%d.%m.%Y')}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        ).pack(anchor='w', pady=(0, 15))

        # Kategorie
        ctk.CTkLabel(
            inner_content,
            text="Kategorie:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w', pady=(10, 5))

        self.category_var = ctk.StringVar(
            value=self.entry['kategorie'] if self.entry else (list(category_dict.keys())[0] if category_dict else "")
        )
        category_combo = ctk.CTkComboBox(
            inner_content,
            values=list(category_dict.keys()) if category_dict else ["Keine Kategorien"],
            variable=self.category_var,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['card'],
            border_color=COLORS['border']
        )
        category_combo.pack(fill='x', pady=(0, 15))

        # Unterkategorie
        ctk.CTkLabel(
            inner_content,
            text="Unterkategorie:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w', pady=(10, 5))

        def update_subcategories(*args):
            cat = self.category_var.get()
            subcats = category_dict.get(cat, [])
            self.subcategory_combo.configure(values=subcats if subcats else ["Keine"])
            if subcats and not self.entry:
                self.subcategory_var.set(subcats[0])

        self.subcategory_var = ctk.StringVar(value=self.entry['unterkategorie'] if self.entry else "")
        self.subcategory_combo = ctk.CTkComboBox(
            inner_content,
            variable=self.subcategory_var,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['card'],
            border_color=COLORS['border']
        )
        self.subcategory_combo.pack(fill='x', pady=(0, 15))

        # Update Subcategories bei Kategorie-Wechsel
        self.category_var.trace_add('write', update_subcategories)
        update_subcategories()

        # Erwartete Karten
        ctk.CTkLabel(
            inner_content,
            text="Erwartete Karten:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w', pady=(10, 5))

        self.cards_entry = ctk.CTkEntry(
            inner_content,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['card'],
            border_color=COLORS['border']
        )
        self.cards_entry.insert(0, str(self.entry.get('erwartete_karten', 20)) if self.entry else "20")
        self.cards_entry.pack(fill='x', pady=(0, 15))

        # Priorität
        ctk.CTkLabel(
            inner_content,
            text="Priorität:",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w', pady=(10, 5))

        self.priority_var = ctk.StringVar(value=self.entry.get('prioritaet', 'mittel') if self.entry else 'mittel')
        priority_frame = ctk.CTkFrame(inner_content, fg_color="transparent")
        priority_frame.pack(fill='x', pady=(0, 15))

        for prio in ['niedrig', 'mittel', 'hoch']:
            ctk.CTkRadioButton(
                priority_frame,
                text=prio.capitalize(),
                variable=self.priority_var,
                value=prio,
                font=ctk.CTkFont(size=13)
            ).pack(side='left', padx=10)

        # Notizen
        ctk.CTkLabel(
            inner_content,
            text="Notizen (optional):",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w', pady=(10, 5))

        self.notes_textbox = ctk.CTkTextbox(
            inner_content,
            height=100,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['card'],
            border_color=COLORS['border']
        )
        if self.entry and self.entry.get('notizen'):
            self.notes_textbox.insert('1.0', self.entry['notizen'])
        self.notes_textbox.pack(fill='x', pady=(0, 20))

        # Buttons (fixiert unten)
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(pady=(0, 10))

        ctk.CTkButton(
            button_frame,
            text="✓ Speichern",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['success'],
            hover_color='#059669',
            command=self._save_session,
            width=140,
            height=40,
            corner_radius=10
        ).pack(side='left', padx=5)

        if self.entry:
            ctk.CTkButton(
                button_frame,
                text="🗑 Löschen",
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=COLORS['danger'],
                hover_color='#dc2626',
                command=self._delete_session,
                width=140,
                height=40,
                corner_radius=10
            ).pack(side='left', padx=5)

        ctk.CTkButton(
            button_frame,
            text="✗ Abbrechen",
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=self._cancel,
            width=140,
            height=40,
            corner_radius=10
        ).pack(side='left', padx=5)

    def _save_session(self):
        """Speichert die Session."""
        try:
            kategorie = self.category_var.get()
            unterkategorie = self.subcategory_var.get()
            erwartete_karten = int(self.cards_entry.get().strip())
            prioritaet = self.priority_var.get()
            notizen = self.notes_textbox.get('1.0', 'end').strip()

            if not kategorie or not unterkategorie:
                messagebox.showwarning("Fehler", "Bitte wähle Kategorie und Unterkategorie.")
                return

            if erwartete_karten <= 0:
                messagebox.showwarning("Fehler", "Erwartete Karten muss größer als 0 sein.")
                return

            if self.entry:
                # Bearbeite bestehende Session
                self.data_manager.update_plan_entry(
                    self.entry['id'],
                    {
                        'kategorie': kategorie,
                        'unterkategorie': unterkategorie,
                        'erwartete_karten': erwartete_karten,
                        'prioritaet': prioritaet,
                        'notizen': notizen
                    }
                )
            else:
                # Neue Session
                self.data_manager.add_plan_entry(
                    date=self.date,
                    kategorie=kategorie,
                    unterkategorie=unterkategorie,
                    aktion='lernen',
                    erwartete_karten=erwartete_karten,
                    prioritaet=prioritaet,
                    notizen=notizen,
                    auto_generiert=False
                )

            if self.on_close_callback:
                self.on_close_callback()

        except ValueError:
            messagebox.showwarning("Fehler", "Erwartete Karten muss eine Zahl sein.")

    def _delete_session(self):
        """Löscht die Session."""
        if self.entry and messagebox.askyesno("Löschen", "Session wirklich löschen?"):
            self.data_manager.delete_plan_entry(self.entry['id'])
            if self.on_close_callback:
                self.on_close_callback()

    def _cancel(self):
        """Bricht ab."""
        if self.on_close_callback:
            self.on_close_callback()


class CreateLearningSetFrame(ctk.CTkFrame):
    """Inline Frame zum Erstellen/Bearbeiten eines Lernsets mit modernem Dropdown-Design."""

    def __init__(self, parent, data_manager, set_id=None, on_close_callback=None):
        super().__init__(parent, fg_color=COLORS['background'], corner_radius=20, border_width=2, border_color=COLORS['border'])
        self.data_manager = data_manager
        self.learning_set_manager = LearningSetManager(data_manager)
        self.set_id = set_id
        self.on_close_callback = on_close_callback

        self.selected_categories = {}  # Dict: {category: [subcategories]}
        self.category_widgets = {}  # Speichert Referenzen zu Widgets

        # Lade bestehende Daten wenn wir bearbeiten
        self.existing_set = None
        if set_id:
            all_sets = self.learning_set_manager.get_all_sets()
            self.existing_set = all_sets.get(set_id)
            if self.existing_set:
                # Konvertiere Kategorien in das richtige Format
                for kat_entry in self.existing_set.get('kategorien', []):
                    cat = kat_entry['kategorie']
                    subcats = kat_entry.get('unterkategorien', [])
                    self.selected_categories[cat] = subcats

        self._create_ui()

    def _create_ui(self):
        """Erstellt die UI mit modernem Design."""
        # Header mit Gradient-Effekt (nicht scrollbar)
        header_frame = ctk.CTkFrame(self, fg_color=COLORS['surface'], corner_radius=15)
        header_frame.pack(fill='x', padx=20, pady=20)

        # Zurück-Button (nur wenn Callback vorhanden)
        if self.on_close_callback:
            back_btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            back_btn_frame.pack(fill='x', padx=20, pady=(15, 0))

            back_btn = ctk.CTkButton(
                back_btn_frame,
                text="← Zurück",
                font=ctk.CTkFont(size=13),
                fg_color=COLORS['card'],
                hover_color=COLORS['card_hover'],
                command=self._cancel,
                width=100,
                height=35,
                corner_radius=8
            )
            back_btn.pack(side='left')

        title_text = "✏️  Lernset bearbeiten" if self.set_id else "📚  Neues Lernset erstellen"
        header = ctk.CTkLabel(
            header_frame,
            text=title_text,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['text']
        )
        header.pack(pady=20)

        # Beschreibung
        desc_text = "Bearbeite dein Lernset und passe Ziele an" if self.set_id else "Wähle Kategorien aus, die du in diesem Lernset lernen möchtest\nBeim Auswählen einer Kategorie werden automatisch alle Unterkategorien hinzugefügt"
        desc = ctk.CTkLabel(
            header_frame,
            text=desc_text,
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary'],
            justify='center'
        )
        desc.pack(pady=(0, 20))

        # Scrollable Content Frame für den gesamten Inhalt
        content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))

        # Name
        name_frame = ctk.CTkFrame(content_frame, fg_color=COLORS['surface'], corner_radius=12)
        name_frame.pack(fill='x', pady=(0, 15))

        ctk.CTkLabel(
            name_frame,
            text="📝 Name des Lernsets:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        ).pack(pady=(15, 5), padx=15, anchor='w')

        self.name_entry = ctk.CTkEntry(
            name_frame,
            height=40,
            font=ctk.CTkFont(size=14),
            placeholder_text="z.B. Mathematik Grundlagen",
            fg_color=COLORS['card'],
            border_color=COLORS['border']
        )
        if self.existing_set:
            self.name_entry.insert(0, self.existing_set['name'])
        self.name_entry.pack(fill='x', pady=(0, 15), padx=15)

        # Ziel-Einstellungen
        goals_frame = ctk.CTkFrame(content_frame, fg_color=COLORS['surface'], corner_radius=12)
        goals_frame.pack(fill='x', pady=(0, 15))

        ctk.CTkLabel(
            goals_frame,
            text="🎯 Lernziele festlegen:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        ).pack(pady=(15, 10), padx=15, anchor='w')

        # Grid für Ziele
        goals_grid = ctk.CTkFrame(goals_frame, fg_color="transparent")
        goals_grid.pack(fill='x', padx=15, pady=(0, 15))
        goals_grid.grid_columnconfigure((0, 1), weight=1)

        # Tägliches Ziel
        daily_frame = ctk.CTkFrame(goals_grid, fg_color="transparent")
        daily_frame.grid(row=0, column=0, padx=(0, 10), sticky='ew')

        ctk.CTkLabel(
            daily_frame,
            text="Tägliches Ziel (Karten):",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w', pady=(0, 5))

        self.daily_goal_entry = ctk.CTkEntry(
            daily_frame,
            height=40,
            font=ctk.CTkFont(size=14),
            placeholder_text="z.B. 20",
            fg_color=COLORS['card'],
            border_color=COLORS['border']
        )
        daily_default = str(self.existing_set.get('taegliches_ziel', 20)) if self.existing_set else "20"
        self.daily_goal_entry.insert(0, daily_default)
        self.daily_goal_entry.pack(fill='x')

        # Wöchentliches Ziel
        weekly_frame = ctk.CTkFrame(goals_grid, fg_color="transparent")
        weekly_frame.grid(row=0, column=1, padx=(10, 0), sticky='ew')

        ctk.CTkLabel(
            weekly_frame,
            text="Wöchentliches Ziel (Karten):",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w', pady=(0, 5))

        self.weekly_goal_entry = ctk.CTkEntry(
            weekly_frame,
            height=40,
            font=ctk.CTkFont(size=14),
            placeholder_text="z.B. 100",
            fg_color=COLORS['card'],
            border_color=COLORS['border']
        )
        weekly_default = str(self.existing_set.get('woechentliches_ziel', 100)) if self.existing_set else "100"
        self.weekly_goal_entry.insert(0, weekly_default)
        self.weekly_goal_entry.pack(fill='x')

        # Kategorien-Auswahl mit Dropdown
        cat_header = ctk.CTkFrame(content_frame, fg_color="transparent")
        cat_header.pack(fill='x', pady=(10, 10))

        ctk.CTkLabel(
            cat_header,
            text="🏷️ Kategorien auswählen:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        ).pack(side='left')

        # Dropdown für Kategorie-Auswahl
        dropdown_frame = ctk.CTkFrame(content_frame, fg_color=COLORS['surface'], corner_radius=12)
        dropdown_frame.pack(fill='x', pady=(0, 15))

        ctk.CTkLabel(
            dropdown_frame,
            text="Kategorie hinzufügen:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        ).pack(pady=(15, 5), padx=15, anchor='w')

        # Hole verfügbare Kategorien
        self.available_categories = self.learning_set_manager.get_available_categories()
        category_names = list(self.available_categories.keys())

        # Dropdown
        self.category_dropdown = ctk.CTkComboBox(
            dropdown_frame,
            values=category_names if category_names else ["Keine Kategorien verfügbar"],
            command=self._on_category_selected,
            height=40,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12),
            fg_color=COLORS['card'],
            border_color=COLORS['border'],
            button_color=COLORS['primary'],
            button_hover_color=COLORS['primary_hover']
        )
        self.category_dropdown.pack(fill='x', pady=(0, 15), padx=15)
        if category_names:
            self.category_dropdown.set("Kategorie auswählen...")

        # Ausgewählte Kategorien Anzeige
        ctk.CTkLabel(
            content_frame,
            text="✓ Ausgewählte Kategorien:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        ).pack(pady=(10, 10), anchor='w')

        # Frame für ausgewählte Kategorien (jetzt innerhalb des scrollbaren Bereichs)
        self.selected_frame = ctk.CTkFrame(
            content_frame,
            fg_color=COLORS['surface'],
            corner_radius=12
        )
        self.selected_frame.pack(fill='x', pady=(0, 15))

        self._update_selected_display()

        # Buttons bleiben unten fixiert (außerhalb des Scrollbereichs)
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(10, 20))

        button_text = "✓ Speichern" if self.set_id else "✓ Erstellen"
        ctk.CTkButton(
            button_frame,
            text=button_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['success'],
            hover_color='#22c55e',
            command=self._create,
            width=160,
            height=45,
            corner_radius=10
        ).pack(side='left', padx=10)

        ctk.CTkButton(
            button_frame,
            text="✗ Abbrechen",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['danger'],
            hover_color='#dc2626',
            command=self._cancel,
            width=160,
            height=45,
            corner_radius=10
        ).pack(side='left', padx=10)

    def _on_category_selected(self, selected_category: str):
        """Wird aufgerufen wenn eine Kategorie aus dem Dropdown ausgewählt wird.
        Fügt automatisch alle Unterkategorien hinzu."""
        if selected_category == "Kategorie auswählen..." or selected_category == "Keine Kategorien verfügbar":
            return

        # Prüfe ob Kategorie bereits ausgewählt ist
        if selected_category in self.selected_categories:
            messagebox.showinfo("Info", f"'{selected_category}' ist bereits ausgewählt.")
            self.category_dropdown.set("Kategorie auswählen...")
            return

        # Hole alle Unterkategorien
        subcategories = self.available_categories.get(selected_category, [])

        # Füge Kategorie mit allen Unterkategorien hinzu
        self.selected_categories[selected_category] = subcategories.copy()

        # Aktualisiere Anzeige
        self._update_selected_display()

        # Zeige Bestätigung
        messagebox.showinfo(
            "Kategorie hinzugefügt",
            f"✓ '{selected_category}' wurde hinzugefügt\n"
            f"Alle {len(subcategories)} Unterkategorien wurden automatisch ausgewählt."
        )

        # Reset Dropdown
        self.category_dropdown.set("Kategorie auswählen...")

    def _update_selected_display(self):
        """Aktualisiert die Anzeige der ausgewählten Kategorien."""
        # Lösche alte Widgets
        for widget in self.selected_frame.winfo_children():
            widget.destroy()

        if not self.selected_categories:
            ctk.CTkLabel(
                self.selected_frame,
                text="Noch keine Kategorien ausgewählt.\nWähle Kategorien aus dem Dropdown oben.",
                font=ctk.CTkFont(size=12),
                text_color=COLORS['text_secondary'],
                justify='center'
            ).pack(expand=True, pady=40)
            return

        # Zeige ausgewählte Kategorien
        for category, subcategories in self.selected_categories.items():
            # Category Card
            cat_card = ctk.CTkFrame(
                self.selected_frame,
                fg_color=COLORS['card'],
                corner_radius=12,
                border_width=2,
                border_color=COLORS['primary']
            )
            cat_card.pack(fill='x', pady=8, padx=10)

            # Header
            header_frame = ctk.CTkFrame(cat_card, fg_color="transparent")
            header_frame.pack(fill='x', padx=15, pady=(15, 10))

            # Icon und Name
            icon_label = ctk.CTkLabel(
                header_frame,
                text="📁",
                font=ctk.CTkFont(size=20)
            )
            icon_label.pack(side='left', padx=(0, 10))

            title_label = ctk.CTkLabel(
                header_frame,
                text=category,
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=COLORS['text']
            )
            title_label.pack(side='left')

            # Entfernen-Button
            remove_btn = ctk.CTkButton(
                header_frame,
                text="✗",
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=COLORS['danger'],
                hover_color='#dc2626',
                command=lambda c=category: self._remove_category(c),
                width=32,
                height=32,
                corner_radius=8
            )
            remove_btn.pack(side='right')

            # Unterkategorien
            if subcategories:
                subcat_frame = ctk.CTkFrame(cat_card, fg_color=COLORS['background'], corner_radius=8)
                subcat_frame.pack(fill='x', padx=15, pady=(0, 15))

                ctk.CTkLabel(
                    subcat_frame,
                    text=f"✓ {len(subcategories)} Unterkategorien automatisch ausgewählt:",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=COLORS['success']
                ).pack(anchor='w', padx=10, pady=(10, 5))

                # Zeige Unterkategorien in kompakter Form
                subcat_text = " • ".join(subcategories)
                ctk.CTkLabel(
                    subcat_frame,
                    text=subcat_text,
                    font=ctk.CTkFont(size=10),
                    text_color=COLORS['text_secondary'],
                    anchor='w',
                    wraplength=450
                ).pack(anchor='w', padx=10, pady=(0, 10))

    def _remove_category(self, category: str):
        """Entfernt eine Kategorie und alle ihre Unterkategorien."""
        if category in self.selected_categories:
            del self.selected_categories[category]
            self._update_selected_display()

    def _create(self):
        """Erstellt oder aktualisiert das Lernset mit automatisch ausgewählten Unterkategorien."""
        name = self.name_entry.get().strip()

        if not name:
            messagebox.showwarning("Fehler", "Bitte gib einen Namen ein.")
            return

        if not self.selected_categories:
            messagebox.showwarning("Fehler", "Bitte wähle mindestens eine Kategorie aus.")
            return

        # Hole Ziele
        try:
            daily_goal = int(self.daily_goal_entry.get().strip())
            if daily_goal <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Fehler", "Tägliches Ziel muss eine positive Zahl sein.")
            return

        try:
            weekly_goal = int(self.weekly_goal_entry.get().strip())
            if weekly_goal <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Fehler", "Wöchentliches Ziel muss eine positive Zahl sein.")
            return

        # Konvertiere selected_categories (Dict) in das richtige Format
        kategorien_list = [
            {'kategorie': cat, 'unterkategorien': subcats}
            for cat, subcats in self.selected_categories.items()
        ]

        # Zähle Gesamtzahl der Unterkategorien
        total_subcats = sum(len(subcats) for subcats in self.selected_categories.values())

        if self.set_id:
            # Aktualisiere bestehendes Set
            success = self.learning_set_manager.update_set(
                self.set_id,
                name=name,
                kategorien=kategorien_list,
                taegliches_ziel=daily_goal,
                woechentliches_ziel=weekly_goal
            )

            if success:
                messagebox.showinfo(
                    "✓ Erfolg",
                    f"Lernset '{name}' wurde aktualisiert!\n\n"
                    f"📁 {len(self.selected_categories)} Kategorien\n"
                    f"📂 {total_subcats} Unterkategorien\n"
                    f"🎯 Tägliches Ziel: {daily_goal} Karten\n"
                    f"📅 Wöchentliches Ziel: {weekly_goal} Karten"
                )
                if self.on_close_callback:
                    self.on_close_callback(self.set_id)
            else:
                messagebox.showerror("Fehler", "Fehler beim Aktualisieren des Lernsets.")
        else:
            # Erstelle neues Set
            set_id = self.learning_set_manager.create_set(
                name=name,
                kategorien=kategorien_list,
                taegliches_ziel=daily_goal,
                woechentliches_ziel=weekly_goal
            )

            if set_id:
                messagebox.showinfo(
                    "✓ Erfolg",
                    f"Lernset '{name}' wurde erstellt!\n\n"
                    f"📁 {len(self.selected_categories)} Kategorien\n"
                    f"📂 {total_subcats} Unterkategorien (automatisch ausgewählt)\n"
                    f"🎯 Tägliches Ziel: {daily_goal} Karten\n"
                    f"📅 Wöchentliches Ziel: {weekly_goal} Karten"
                )
                if self.on_close_callback:
                    self.on_close_callback(set_id)
            else:
                messagebox.showerror("Fehler", "Fehler beim Erstellen des Lernsets.")

    def _cancel(self):
        """Bricht ab."""
        if self.on_close_callback:
            self.on_close_callback(None)


class CreatePlannerFrame(ctk.CTkFrame):
    """Inline Frame zum Erstellen/Bearbeiten eines Planers."""

    def __init__(self, parent, data_manager, planner_id: Optional[str] = None, on_close_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.data_manager = data_manager
        self.planner_manager = PlannerManager(data_manager)
        self.learning_set_manager = LearningSetManager(data_manager)
        self.planner_id = planner_id
        self.on_close_callback = on_close_callback

        self.selected_lernsets = []
        self.showing_lernset_creator = False

        # Wenn wir einen Planer bearbeiten, lade dessen Daten
        if planner_id:
            planner = self.planner_manager.get_planner(planner_id)
            if planner:
                self.selected_lernsets = planner.get('lernset_ids', []).copy()

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

        # Header mit Zurück-Button
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill='x', padx=40, pady=(30, 0))

        back_btn = ctk.CTkButton(
            header_frame,
            text="← Zurück",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=lambda: self._cancel_planner(),
            width=100,
            height=35,
            corner_radius=8
        )
        back_btn.pack(side='left')

        # Header
        title_text = "Planer bearbeiten" if self.planner_id else "Neuer Wochenplaner"
        header = ctk.CTkLabel(
            self.main_container,
            text=title_text,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=(20, 30))

        # Lade Planer-Daten wenn wir bearbeiten
        planner = None
        if self.planner_id:
            planner = self.planner_manager.get_planner(self.planner_id)

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

        button_text = "Speichern" if self.planner_id else "Erstellen"
        ctk.CTkButton(
            button_frame,
            text=button_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            command=self._create_planner,
            width=150,
            height=40
        ).pack(side='left', padx=10)

        ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['surface'],
            hover_color=COLORS['border'],
            command=self._cancel_planner,
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

    def _edit_lernset(self, set_id: str):
        """Zeigt den Lernset-Editor inline."""
        # Lösche bestehenden Inhalt
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Zeige CreateLearningSetFrame im Edit-Modus
        editor = CreateLearningSetFrame(
            self.main_container,
            self.data_manager,
            set_id=set_id,
            on_close_callback=self._on_lernset_edited
        )
        editor.pack(fill='both', expand=True, padx=20, pady=20)

    def _on_lernset_edited(self, set_id):
        """Callback wenn Lernset bearbeitet wurde."""
        # Zurück zum Planer-Formular
        self._show_planner_form()

    def _on_lernset_created(self, set_id):
        """Callback wenn Lernset erstellt oder abgebrochen wurde."""
        if set_id:
            # Füge das neue Set zur Auswahl hinzu
            if set_id not in self.selected_lernsets:
                self.selected_lernsets.append(set_id)

        # Zurück zum Planer-Formular
        self._show_planner_form()

    def _load_lernsets(self):
        """Lädt alle verfügbaren Lernsets mit Edit-Buttons."""
        all_sets = self.learning_set_manager.get_all_sets()

        if not all_sets:
            ctk.CTkLabel(
                self.lernsets_scroll,
                text="Keine Lernsets vorhanden.\nKlicke auf '+ Neues Lernset' um eines zu erstellen.",
                text_color=COLORS['text_secondary']
            ).pack(pady=20)
            return

        for set_id, lernset in all_sets.items():
            # Frame für jedes Lernset (Checkbox + Edit Button)
            set_frame = ctk.CTkFrame(self.lernsets_scroll, fg_color="transparent")
            set_frame.pack(fill='x', pady=5)

            var = ctk.IntVar()
            # Setze Checkbox wenn bereits ausgewählt
            if set_id in self.selected_lernsets:
                var.set(1)

            cb = ctk.CTkCheckBox(
                set_frame,
                text=f"{lernset['name']} ({len(lernset['kategorien'])} Kategorien, Ziel: {lernset.get('taegliches_ziel', 20)}/Tag)",
                variable=var,
                font=ctk.CTkFont(size=13),
                command=lambda sid=set_id, v=var: self._toggle_lernset(sid, v)
            )
            cb.pack(side='left', fill='x', expand=True)

            # Edit-Button
            edit_btn = ctk.CTkButton(
                set_frame,
                text="✏️",
                font=ctk.CTkFont(size=14),
                fg_color=COLORS['primary'],
                hover_color=COLORS['primary_hover'],
                command=lambda sid=set_id: self._edit_lernset(sid),
                width=40,
                height=28
            )
            edit_btn.pack(side='right', padx=(10, 0))

    def _toggle_lernset(self, set_id: str, var: ctk.IntVar):
        """Fügt/Entfernt Lernset aus Auswahl."""
        if var.get():
            if set_id not in self.selected_lernsets:
                self.selected_lernsets.append(set_id)
        else:
            if set_id in self.selected_lernsets:
                self.selected_lernsets.remove(set_id)

    def _create_planner(self):
        """Erstellt oder aktualisiert den Planer."""
        name = self.name_entry.get().strip()

        if not name:
            messagebox.showwarning("Fehler", "Bitte gib einen Namen ein.")
            return

        if not self.selected_lernsets:
            messagebox.showwarning("Fehler", "Bitte wähle mindestens ein Lernset aus.")
            return

        if self.planner_id:
            # Planer aktualisieren
            success = self.planner_manager.update_planner(
                self.planner_id,
                name=name,
                lernset_ids=self.selected_lernsets,
                icon=self.icon_var.get()
            )

            if success:
                messagebox.showinfo("✓ Erfolg", f"Planer '{name}' wurde aktualisiert!")
                if self.on_close_callback:
                    self.on_close_callback(True)
            else:
                messagebox.showerror("Fehler", "Fehler beim Aktualisieren des Planers.")
        else:
            # Neuen Planer erstellen
            planner_id = self.planner_manager.create_planner(
                name=name,
                lernset_ids=self.selected_lernsets,
                icon=self.icon_var.get()
            )

            if planner_id:
                messagebox.showinfo("✓ Erfolg", f"Planer '{name}' wurde erstellt!")
                if self.on_close_callback:
                    self.on_close_callback(True)
            else:
                messagebox.showerror("Fehler", "Fehler beim Erstellen des Planers.")

    def _cancel_planner(self):
        """Bricht die Planer-Erstellung/-Bearbeitung ab."""
        if self.on_close_callback:
            self.on_close_callback(False)


class PlannerPreferencesDialog(ctk.CTkToplevel):
    """Dialog für individuelle Präferenzen beim intelligenten Planner."""

    def __init__(self, parent, categories: List[str], total_daily_goal: int):
        super().__init__(parent)

        self.title("Intelligente Wochenplanung - Präferenzen")
        self.geometry("700x800")
        self.resizable(False, False)

        # Zentriere das Fenster
        self.transient(parent)
        self.grab_set()

        self.result = None
        self.categories = categories
        self.total_daily_goal = total_daily_goal

        self._create_ui()

    def _create_ui(self):
        """Erstellt das UI für die Präferenzen-Eingabe."""
        # Haupt-Container mit Scrollbar
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Titel
        ctk.CTkLabel(
            main_frame,
            text="Intelligente Wochenplanung",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            main_frame,
            text="Passe die automatische Planung an deine individuellen Bedürfnisse an.",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(pady=(0, 20))

        # Sektion 1: Priorisierung
        self._create_priority_section(main_frame)

        # Sektion 2: Anzahl Karten
        self._create_cards_section(main_frame)

        # Sektion 3: Priorisierte Kategorie
        self._create_category_section(main_frame)

        # Sektion 4: Tagesverteilung
        self._create_daily_distribution_section(main_frame)

        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=20, fill='x')

        ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            command=self._cancel,
            fg_color="gray",
            hover_color="darkgray",
            width=150,
            height=40
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            button_frame,
            text="Woche planen",
            command=self._confirm,
            width=150,
            height=40
        ).pack(side='right', padx=5)

    def _create_priority_section(self, parent):
        """Erstellt die Sektion für die Priorisierung."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill='x', pady=10)

        ctk.CTkLabel(
            frame,
            text="Was soll priorisiert werden?",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor='w', padx=10, pady=(10, 5))

        self.priority_vars = {}
        priorities = [
            ("success_rate", "Erfolgsquote (bevorzuge gut gelernte Kategorien)"),
            ("due_date", "Fälligkeit (bevorzuge überfällige Karten)"),
            ("even_distribution", "Gleichmäßige Verteilung (verteile Sessions gleichmäßig)")
        ]

        for key, label in priorities:
            var = tk.BooleanVar(value=True)
            self.priority_vars[key] = var
            ctk.CTkCheckBox(
                frame,
                text=label,
                variable=var,
                font=ctk.CTkFont(size=13)
            ).pack(anchor='w', padx=20, pady=5)

    def _create_cards_section(self, parent):
        """Erstellt die Sektion für die Anzahl der Karten."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill='x', pady=10)

        ctk.CTkLabel(
            frame,
            text="Wie viele Karten möchtest du insgesamt lernen?",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor='w', padx=10, pady=(10, 5))

        ctk.CTkLabel(
            frame,
            text=f"(Empfohlen basierend auf täglichem Ziel: {self.total_daily_goal * 7} Karten/Woche)",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor='w', padx=10, pady=(0, 10))

        cards_input_frame = ctk.CTkFrame(frame)
        cards_input_frame.pack(fill='x', padx=10, pady=5)

        ctk.CTkLabel(
            cards_input_frame,
            text="Gesamt-Karten:",
            font=ctk.CTkFont(size=13)
        ).pack(side='left', padx=5)

        self.total_cards_var = tk.StringVar(value=str(self.total_daily_goal * 7))
        ctk.CTkEntry(
            cards_input_frame,
            textvariable=self.total_cards_var,
            width=100,
            font=ctk.CTkFont(size=13)
        ).pack(side='left', padx=5)

    def _create_category_section(self, parent):
        """Erstellt die Sektion für die priorisierte Kategorie."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill='x', pady=10)

        ctk.CTkLabel(
            frame,
            text="Gibt es eine priorisierte Kategorie?",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor='w', padx=10, pady=(10, 5))

        cat_frame = ctk.CTkFrame(frame)
        cat_frame.pack(fill='x', padx=10, pady=5)

        self.priority_category_var = tk.StringVar(value="Keine")
        category_options = ["Keine"] + self.categories

        ctk.CTkOptionMenu(
            cat_frame,
            variable=self.priority_category_var,
            values=category_options,
            width=300,
            font=ctk.CTkFont(size=13)
        ).pack(side='left', padx=5)

    def _create_daily_distribution_section(self, parent):
        """Erstellt die Sektion für die Tagesverteilung."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill='x', pady=10)

        ctk.CTkLabel(
            frame,
            text="Tagesverteilung (Belastung pro Tag)",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor='w', padx=10, pady=(10, 5))

        ctk.CTkLabel(
            frame,
            text="Hoch = viele Karten, Mittel = durchschnittlich, Gering = wenige Karten",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor='w', padx=10, pady=(0, 10))

        days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        self.day_distribution = {}

        for day in days:
            day_frame = ctk.CTkFrame(frame)
            day_frame.pack(fill='x', padx=10, pady=3)

            ctk.CTkLabel(
                day_frame,
                text=f"{day}:",
                font=ctk.CTkFont(size=13),
                width=100
            ).pack(side='left', padx=5)

            var = tk.StringVar(value="Mittel")
            self.day_distribution[day] = var

            ctk.CTkOptionMenu(
                day_frame,
                variable=var,
                values=["Hoch", "Mittel", "Gering"],
                width=120,
                font=ctk.CTkFont(size=13)
            ).pack(side='left', padx=5)

    def _confirm(self):
        """Bestätigt die Eingaben und schließt den Dialog."""
        try:
            total_cards = int(self.total_cards_var.get())
            if total_cards <= 0:
                messagebox.showwarning("Fehler", "Anzahl der Karten muss größer als 0 sein.")
                return
        except ValueError:
            messagebox.showwarning("Fehler", "Bitte gib eine gültige Zahl für die Karten ein.")
            return

        self.result = {
            'priorities': {
                key: var.get() for key, var in self.priority_vars.items()
            },
            'total_cards': total_cards,
            'priority_category': self.priority_category_var.get() if self.priority_category_var.get() != "Keine" else None,
            'daily_distribution': {
                day: var.get() for day, var in self.day_distribution.items()
            }
        }

        self.destroy()

    def _cancel(self):
        """Bricht den Dialog ab."""
        self.result = None
        self.destroy()

    def get_result(self):
        """Wartet auf die Eingabe und gibt das Ergebnis zurück."""
        self.wait_window()
        return self.result
