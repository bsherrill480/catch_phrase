from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.base import runTouchApp
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
Builder.load_string("""
<Penis>
    GridLayout:
        cols: 1
        spacing: 0
        Button:
            text: "there"
            on_release: root.make_popup()
""")


class Penis(Widget):
    def __init__(self):
        super(Penis, self).__init__()
        self.popup = Popup(title='Test popup', content=Label(text='Hello world'), auto_dismiss=False)
    def make_popup(self):
        self.popup.dismiss()
        self.popup.dismiss()

if __name__ == '__main__':
    runTouchApp(Penis())