# components/enhanced_cards.py
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivy.properties import StringProperty, NumericProperty

class StatsCard(MDCard):
    title = StringProperty("")
    value = StringProperty("")
    icon = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = "16dp"
        self.size_hint = (None, None)
        self.size = (120, 100)
        self.radius = [15,]
        self.elevation = 2
        
        # This will be built in KV