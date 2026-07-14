from kivy.app import App
from kivy.uix.label import Label

import arabic_reshaper
from bidi.algorithm import get_display

text = get_display(arabic_reshaper.reshape("سلام دنیا"))

class Test(App):
    def build(self):
        return Label(
            text=text,
            font_name="C:/Windows/Fonts/tahoma.ttf",
            font_size=40
        )

Test().run()