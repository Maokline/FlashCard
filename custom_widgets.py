import tkinter as tk
from tkinter import ttk
import logging
import re  # Für reguläre Ausdrücke bei der RGB-Farbverarbeitung


class ModernButton(ttk.Button):
    """Ein moderner Button mit vordefinierten ttk-Styles und Hover-Effekten."""

    def __init__(self, master=None, style='Primary.TButton', command=None, **kwargs):
        super().__init__(master, style=style, command=self._on_click, **kwargs)
        self.original_style = style
        self._command = command
        self._configure_hover_effects()

    def _on_click(self):
        """Ruft die hinterlegte command Funktion auf (falls vorhanden)"""
        if self._command:
            self._command()

    def _configure_hover_effects(self):
        """Konfiguriert einen minimalen Hover-Effekt, der nur die Farbe ändert."""
        style = ttk.Style()
        style_name = self.original_style.replace('.TButton', '')
        hover_style = f"{style_name}.Hover.TButton"

        # Hole die ursprüngliche Hintergrundfarbe
        base_bg = style.lookup(self.original_style, 'background')
        if not base_bg:
            base_bg = '#ffffff'  # Fallback

        # Berechne die dunklere Farbe für den Hover-Effekt
        hover_bg = self._get_hover_background(base_bg)

        # Kopiere alle bestehenden Style-Eigenschaften
        original_settings = {}
        for option in ['relief', 'borderwidth', 'padding', 'font', 'anchor', 'foreground']:
            try:
                value = style.lookup(self.original_style, option)
                if value:
                    original_settings[option] = value
            except:
                pass

        # Konfiguriere den Hover-Style als exakte Kopie des Originals
        style.configure(hover_style, background=hover_bg, **original_settings)

        # Verwende map nur für die Hintergrundfarbe
        # Entferne alle anderen Mappings, um unerwünschte Änderungen zu verhindern
        style.map(hover_style, 
                background=[('active', hover_bg)],
                relief=[],  # Leere Mappings verhindern Änderungen
                borderwidth=[],
                padding=[])

        # Bindet die Events für minimale Änderungen
        self.bind("<Enter>", lambda e: self.configure(style=hover_style))
        self.bind("<Leave>", lambda e: self.configure(style=self.original_style))
    def _get_hover_background(self, color: str, factor: float = 0.75) -> str:
        """
        Berechnet eine dunklere Farbe (mit RGB- und Hex-Unterstützung).
        Der Faktor 0.75 entspricht einer 25% Abdunklung.
        """
        try:
            if color.startswith('#'):
                if len(color) == 7:
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                elif len(color) == 4:  # Kurzform #RGB
                    r = int(color[1] * 2, 16)
                    g = int(color[2] * 2, 16)
                    b = int(color[3] * 2, 16)
                else:
                    logging.error(f"Ungültiges Hex-Farbformat: {color}")
                    return '#cccccc'
            elif color.startswith('rgb'):
                match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
                if match:
                    r, g, b = map(int, match.groups())
                else:
                    logging.error(f"Ungültiges RGB-Format: {color}")
                    return '#cccccc'
            else:
                logging.error(f"Unbekanntes Farbformat: {color}")
                return '#cccccc'

            r = max(0, min(255, int(r * factor)))
            g = max(0, min(255, int(g * factor)))
            b = max(0, min(255, int(b * factor)))
            return f'#{r:02x}{g:02x}{b:02x}'
        except (ValueError, AttributeError) as e:
            logging.error(f"Fehler bei der Farbberechnung: {e}")
            return '#cccccc'
    def set_style(self, new_style: str):
        """Ändert den Stil und konfiguriert die Hover-Effekte neu."""
        self.original_style = new_style
        self.configure(style=new_style)
        self._configure_hover_effects()

    @property
    def style(self):
        return self.cget('style')


class ModernCombobox(ttk.Combobox):
    """Ein modernes Dropdown-Menü."""

    def __init__(self, master=None, textvariable=None, values=None, **kwargs):
        super().__init__(master, textvariable=textvariable, values=values, **kwargs)
        self._linked_combobox = None
        self._dropdown_open = False
        self.configure_style()
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Up>", self._handle_key_up)
        self.bind("<Down>", self._handle_key_down)
        self.bind("<Return>", self._handle_return)

    def configure_style(self):
        """Konfiguriert den Stil des Combobox."""
        style = ttk.Style()
        style_name = 'ModernCombobox.TCombobox'
        style.configure(style_name, fieldbackground='#ffffff', background='#ffffff', foreground='#000000', borderwidth=1)
        style.map(style_name, fieldbackground=[('readonly', '#ffffff')], background=[('readonly', '#ffffff')], foreground=[('readonly', '#000000')])
        self.configure(style=style_name)

    def _on_focus_out(self, event):
        """Schließt das Dropdown beim Fokusverlust (mit kurzer Verzögerung)."""
        self.after(50, self._check_and_close_dropdown)

    def _check_and_close_dropdown(self):
        if self.focus_get() is None:
            self.close_dropdown()

    def _on_click(self, event):
        if not self._dropdown_open:
            self._show_dropdown()

    def _handle_key_up(self, event):
        current = self.current()
        if current > 0:
            self.current(current - 1)
        return "break"

    def _handle_key_down(self, event):
        current = self.current()
        if current < len(self['values']) - 1:
            self.current(current + 1)
        return "break"

    def _handle_return(self, event):
        if self["state"] == "readonly" and not self._dropdown_open:
            self._show_dropdown()
        return "break"

    def _show_dropdown(self):
        if not self._dropdown_open:
            self._dropdown_open = True
            self.event_generate('<Down>')
            self.after(100, lambda: self.config(postcommand=self._reset_dropdown_flag))  # Nutze postcommand, um das Flag zurückzusetzen

    def _reset_dropdown_flag(self):
        self._dropdown_open = False
        self.config(postcommand=None)  # postcommand wieder entfernen

    def close_dropdown(self):
        if self._dropdown_open:
            self.event_generate('<Escape>')
            self._dropdown_open = False

    def close_linked_dropdown(self):
        if self._linked_combobox and isinstance(self._linked_combobox, ModernCombobox):
            self._linked_combobox.close_dropdown()

    def link_combobox(self, combobox):
        """Verlinkt diesen Combobox mit einem anderen, sodass sich deren Dropdowns gemeinsam schließen."""
        if isinstance(combobox, ModernCombobox):
            self._linked_combobox = combobox
            combobox._linked_combobox = self

    def add_values(self, new_values: list):
        current_values = list(self['values'])
        for value in new_values:
            if value not in current_values:
                current_values.append(value)
        self.configure(values=current_values)

    def remove_value(self, value: str):
        current_values = list(self['values'])
        if value in current_values:
            current_values.remove(value)
        self.configure(values=current_values)
