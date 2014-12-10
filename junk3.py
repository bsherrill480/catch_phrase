# from kivy.base import runTouchApp
# from kivy.uix.spinner import Spinner
# from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.button import Button
# class string_wrapper(str):
#     def __new__(cls, string, hidden):
#         obj = str.__new__(cls, string)
#         obj.hidden = hidden
#         return obj
#
# box_layout = BoxLayout()
# class mySpinner(Spinner):
#     def __init__(self, *args, **kwargs):
#         my_values_strings = []
#         if "values" in kwargs:
#             my_values_objects = kwargs["values"]
#             for value in kwargs["values"]:
#                 my_values_strings.append(value.nickname)
#
#
# spinner = Spinner(
#     # default value shown
#     text='Select One',
#     # available values
#     values=([string_wrapper("cat", "hidden_tiger"),string_wrapper("lizard", "crouching_dragon")]),
#     # just for positioning in our example
#     size_hint=(None, None),
#     size=(100, 44),
#     pos_hint={'center_x': .5, 'center_y': .5})
#
# def show_selected_value(spinner, text):
#     print('The spinner', spinner, 'have text', text)
#     print "hidden value is: ", text.hidden
#
# chng_val_but = Button(text="changes values")
# def changer(instance):
#     spinner.values = ("cat","dog")
# chng_val_but.bind(on_release=changer)
# spinner.bind(text=show_selected_value)
# box_layout.add_widget(chng_val_but)
# box_layout.add_widget(spinner)
# runTouchApp(box_layout)

# from kivy.core.text import Label as CoreLabel
from kivy.base import EventLoop
# EventLoop.ensure_window()
# my_label = CoreLabel()
# my_label.text = 'hello'
# # the label is usually not drawn until needed, so force it to draw.
# my_label.refresh()
# # Now access the texture of the label and use it wherever and
# # however you may please.
# hello_texture = my_label.texture
# print my_label.content_size, my_label.size
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
class B(Widget):
    a = NumericProperty(2)
b = B()
print type(b.a)