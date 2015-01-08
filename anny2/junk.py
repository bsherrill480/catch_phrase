from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.base import runTouchApp
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.app import App
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.base import Builder
from kivy.uix.textinput import TextInput



class MyListView(BoxLayout):
    word_list_name = StringProperty("No List Selected")
    def penis(self):
        self.word_list_name = "PENIS"
        print type(self.word_list_name), self.word_list_name
class MyApp(App):
    def build(self):
        return MyScrollView()

app = MyApp()

class MyScrollView(BoxLayout):
    def __init__(self, *args, **kwargs):
        print "__init__ called"
        super(MyScrollView, self).__init__(*args,**kwargs)
        button = Button(text = "make", state="down")
        button.bind(on_touch_down = self.make_it)
        self.add_widget(button)
    def make_it(self, instance, touch):
        print instance.texture.size
        instance.font_size = instance.font_size + 10

if __name__ == '__main__':
    print "hi"
    app.run()



# #from kivy.uix.boxlayout import BoxLayout
# from kivy.base import runTouchApp
# from kivy.lang import Builder
# from kivy.uix.gridlayout import GridLayout
# from kivy.uix.floatlayout import FloatLayout
# from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.button import Button
# from kivy.uix.label import Label
# from kivy.uix.widget import Widget
# from kivy.uix.scatter import Scatter
# from kivy.uix.scatterlayout import ScatterLayout
# from kivy.graphics import *
# from kivy.properties import ListProperty
# # Note the special nature of indentation in the adapter declaration, where
# # the adapter: is on one line, then the value side must be given at one
# # level of indentation.
#
# Builder.load_string("""
# #:import label kivy.uix.label
# #:import sla kivy.adapters.simplelistadapter
#
# <MyListView>:
#     # canvas.after:
#     #     Color:
#     #         rgba: (0,1,1,.5)
#     #     Rectangle:
#     #         pos: self.pos
#     #         size: self.size
# <MyGrid>:
#     canvas.after:
#         Color:
#             rgba: (0,1,1,.5)
#         Rectangle:
#             pos: self.pos
#             size: self.size
# <MyScat>:
#     canvas.after:
#         Color:
#             rgba: (0,1,1,.5)
#         Rectangle:
#             pos: self.pos
#             size: self.size
#
# <Penis>
#     GridLayout:
#         cols: 1
#         spacing: 0
#         Label:
#             canvas.after:
#                 Color:
#                     rgba: 1,1,1,.5
#                 Rectangle:
#                     size: self.size
#                     pos: self.pos
#             text: 'hi'
#         Button:
#             text: "there"
#             on_release:
#                 print [(child.size,child.pos) for child in root.children[0].children]
#         Label:
#             text: "Joes"
# """)
#
# class MyListView(BoxLayout):
#     def __init__(self, *args, **kwargs):
#         #kwargs["orientation"] = "vertical"
#         #kwargs["orientation"] = "vertical"
#         super(MyListView, self).__init__(*args, **kwargs)
#         # with self.canvas.after:
#         #     Color(rgba=(0,1,0,.5))
#         #     Rectangle(pos=self.pos,size=self.size)
#         float_layout = FloatLayout()
#         grid_layout = MyGrid(cols=4)
#         for i in range(12):
#             grid_layout.add_widget(Label(text=str(i)))
#         # for i in range(2):
#         #     scat = MyScat()
#         #     scat.do_scale = False
#         #     scat.do_rotation = False
#         #     scat.size_hint = (None, None)
#         #     scat.add_widget(Label(text="player"+str(i), size_hint=(None,None)))
#         #     float_layout.add_widget(scat)
#         button = Button(text="DO IT")
#         float_layout.add_widget(grid_layout)
#         self.add_widget(float_layout)
#         self.add_widget(button)
#
# class Penis(Widget):
#     pass
#
# class MyGrid(GridLayout):
#     pass
#
# class MyScat(Scatter):
#     pass
#
# class MyLabel(Label):
#     def __init__(self, **kwargs):
#         super(MyLabel,self).__init__(**kwargs)
#         # with self.canvas.after:
#         #     Color(rgba=(0,1,0,.5))
#         #     Rectangle(pos = self.pos, size=self.size)
#     def on_touch_move(self, touch):
#         print "on touch move", self
#         self.x, self.y = touch.x, touch.y
#         return True
#     # def on_touch_down(self, touch):
#     #     print "on down", self
#     #     return True
#     # def on_touch_up(self, touch):
#     #     print "on up", self
#     #     return True
# if __name__ == '__main__':
#     runTouchApp(Penis())