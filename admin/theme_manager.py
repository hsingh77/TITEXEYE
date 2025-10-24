# theme_manager.py
from kivy.properties import DictProperty, ListProperty
from kivy.core.window import Window
from kivymd.app import MDApp

class ThemeManager:
    def __init__(self):
        self.current_theme = "default"
        self.themes = {
            "default": {
                "primary": "Teal",
                "accent": "Amber", 
                "bg_color": [0.95, 0.95, 0.95, 1],
                "card_color": [1, 1, 1, 1],
                "text_primary": [0, 0, 0, 1],
                "text_secondary": [0.2, 0.2, 0.2, 1]
            },
            "dark": {
                "primary": "DeepOrange",
                "accent": "BlueGray",
                "bg_color": [0.1, 0.1, 0.1, 1],
                "card_color": [0.2, 0.2, 0.2, 1],
                "text_primary": [1, 1, 1, 1],
                "text_secondary": [0.8, 0.8, 0.8, 1]
            },
            "professional": {
                "primary": "BlueGray", 
                "accent": "Cyan",
                "bg_color": [0.96, 0.96, 0.98, 1],
                "card_color": [1, 1, 1, 1],
                "text_primary": [0.1, 0.1, 0.1, 1],
                "text_secondary": [0.4, 0.4, 0.4, 1]
            }
        }
    
    def set_theme(self, theme_name):
        if theme_name in self.themes:
            self.current_theme = theme_name
            return True
        return False
    
    def get_color(self, color_name):
        return self.themes[self.current_theme].get(color_name, [1, 1, 1, 1])
    
    def toggle_dark_mode(self):
        if self.current_theme == "dark":
            self.set_theme("default")
        else:
            self.set_theme("dark")
        return self.current_theme