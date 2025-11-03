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


# Moderne Farbpalette mit verbesserter Lesbarkeit
COLORS = {
    'primary': '#60a5fa',      # Helleres Blau für bessere Lesbarkeit
    'primary_hover': '#3b82f6',
    'secondary': '#a78bfa',    # Helleres Lila
    'success': '#34d399',      # Helleres Grün
    'warning': '#fbbf24',      # Helleres Orange
    'danger': '#f87171',       # Helleres Rot
    'background': '#1e293b',   # Aufgehelltes Dunkelblau
    'surface': '#334155',      # Hellere Surface
    'card': '#475569',         # Hellere Card Background für besseren Kontrast
    'text': '#f8fafc',         # Sehr heller Text
    'text_secondary': '#cbd5e1', # Hellerer sekundärer Text
    'border': '#475569',       # Hellerer Border
    'accent': '#38bdf8',       # Akzentfarbe
    'card_hover': '#64748b',   # Hover-State für Cards
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

        if status == 'offen':
            # Lernen Button mit modernem Design
            learn_btn = ctk.CTkButton(
                session_frame,
                text="▶ Lernen starten",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=COLORS['primary'],
                hover_color=COLORS['primary_hover'],
                command=lambda: self._start_session(entry),
                height=32,
                corner_radius=8
            )
            learn_btn.pack(padx=10, pady=(5, 10), fill='x')

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
    """Inline Frame zum Erstellen eines neuen Lernsets mit modernem Dropdown-Design."""

    def __init__(self, parent, data_manager, on_close_callback=None):
        super().__init__(parent, fg_color=COLORS['background'], corner_radius=20, border_width=2, border_color=COLORS['border'])
        self.data_manager = data_manager
        self.learning_set_manager = LearningSetManager(data_manager)
        self.on_close_callback = on_close_callback

        self.selected_categories = {}  # Dict: {category: [subcategories]}
        self.category_widgets = {}  # Speichert Referenzen zu Widgets
        self._create_ui()

    def _create_ui(self):
        """Erstellt die UI mit modernem Design."""
        # Header mit Gradient-Effekt
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

        header = ctk.CTkLabel(
            header_frame,
            text="📚  Neues Lernset erstellen",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['text']
        )
        header.pack(pady=20)

        # Beschreibung
        desc = ctk.CTkLabel(
            header_frame,
            text="Wähle Kategorien aus, die du in diesem Lernset lernen möchtest\nBeim Auswählen einer Kategorie werden automatisch alle Unterkategorien hinzugefügt",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_secondary'],
            justify='center'
        )
        desc.pack(pady=(0, 20))

        # Content Frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill='both', expand=True, padx=20)

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
        self.name_entry.pack(fill='x', pady=(0, 15), padx=15)

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

        # Scrollable Frame für ausgewählte Kategorien
        self.selected_frame = ctk.CTkScrollableFrame(
            content_frame,
            fg_color=COLORS['surface'],
            height=200,
            corner_radius=12
        )
        self.selected_frame.pack(fill='both', expand=True, pady=(0, 15))

        self._update_selected_display()

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        ctk.CTkButton(
            button_frame,
            text="✓ Erstellen",
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
        """Erstellt das Lernset mit automatisch ausgewählten Unterkategorien."""
        name = self.name_entry.get().strip()

        if not name:
            messagebox.showwarning("Fehler", "Bitte gib einen Namen ein.")
            return

        if not self.selected_categories:
            messagebox.showwarning("Fehler", "Bitte wähle mindestens eine Kategorie aus.")
            return

        # Konvertiere selected_categories (Dict) in das richtige Format
        kategorien_list = [
            {'kategorie': cat, 'unterkategorien': subcats}
            for cat, subcats in self.selected_categories.items()
        ]

        # Zähle Gesamtzahl der Unterkategorien
        total_subcats = sum(len(subcats) for subcats in self.selected_categories.values())

        # Erstelle Set mit Standardzielen
        set_id = self.learning_set_manager.create_set(
            name=name,
            kategorien=kategorien_list,
            taegliches_ziel=20,
            woechentliches_ziel=100
        )

        if set_id:
            messagebox.showinfo(
                "✓ Erfolg",
                f"Lernset '{name}' wurde erstellt!\n\n"
                f"📁 {len(self.selected_categories)} Kategorien\n"
                f"📂 {total_subcats} Unterkategorien (automatisch ausgewählt)\n"
                f"🎯 Tägliches Ziel: 20 Karten"
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
