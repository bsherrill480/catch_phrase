from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, ObservableReferenceList, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout

from kivy.adapters.models import SelectableDataItem
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListItemButton, ListView

### TWISTED SETUP
from kivy.support import install_twisted_reactor
install_twisted_reactor()
from twisted_stuff import Uplink, ClientEventManager, reactor, pb
###/TWISTED SETUP

class CatchPhraseApp(App):
    def build(self):
        self.event_manager = ClientEventManager()
        self.uplink = Uplink(self.event_manager)
        return MyScreenManager()

#    def on_stop(self, *args, **kwargs):

        # sup = super(CatchPhraseApp, self)
        # def container(result):
        #     print "IN CONTAINER"
        #     sup.on_stop(*args, **kwargs)
        # d = self.uplink.unregister_evm()
        # if d:#if we got a deferred
        #     print "adding callback"
        #     d.addCallback(container)
        # else:
        #     sup.on_stop(*args, **kwargs)

#HOLY SHIT DON'T OVERLOOK THIS
app = CatchPhraseApp()


class LoginScreen(Screen):
    def __init__(self, *args, **kwargs):
        super(LoginScreen, self).__init__(*args, **kwargs)
        self.name = "Login"
        self.factory = pb.PBClientFactory()

    def login(self, nickname, password):
        app.uplink.give_nickname_and_password(nickname, password)
        popup = self.logging_in_popup()
        reactor.connectTCP("localhost", 8800, self.factory)
        d = self.factory.getRootObject()

        def generic_popup(message):
            popup.dismiss()
            box_layout = BoxLayout(orientation="vertical")
            box_layout.add_widget(Label(text=message,
                                        size_hint = (1,.8)))
            close_button = Button(text='close', size_hint = (1,.2))
            box_layout.add_widget(close_button)
            new_popup = Popup(content=box_layout, auto_dismiss=False,
                              size_hint = (1,.5), title="")
            close_button.bind(on_release=new_popup.dismiss)
            new_popup.open()
        def failed_to_connect(result):
            generic_popup("can't connect to server")
            return result
        def change_to_gamechooser_screen(result):
            popup.dismiss()
            app.uplink.evm_registered = True
            app.root.current = "game chooser"
            return result

        d.addErrback(failed_to_connect) # change to errback when done debug
        d.addCallback(app.uplink.give_root_obj)
        d.addCallback(app.uplink.register_evm)
        d.addCallback(app.uplink.give_id)
        d.addCallback(change_to_gamechooser_screen)

    def logging_in_popup(self):
        # create content and add to the popup
        label = Label(text='logging in...')
        popup = Popup(content=label, auto_dismiss=False, size_hint = (1,.5), title="")
        popup.open()
        return popup

class penis:
    pass

class MainView(GridLayout):
    '''
    Implementation of a simple list view with 100 items.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 1
        super(MainView, self).__init__(**kwargs)
        list_view = ListView(item_strings=[str(index) for index in range(100)])
        self.add_widget(list_view)

class SelectWordsListScreen(Screen):
    """
    Note: get data from server when chaning to this screen
    """
    #Done in python and not kv lang. Ran into trouble with kv lang
    class DataItem(object):
        def __init__(self, selected_obj, text):
            self.text = text
            self.selected_obj = selected_obj
            self._is_selected = False

        @property
        def is_selected(self):
            return self._is_selected

        @is_selected.setter
        def is_selected(self, value):
            if value:
                self.selected_obj.selected = self.text
            self._is_selected = value

    class Selected(object):
        def __init__(self):
            self.selected = ""
    def __init__(self, *args, **kwargs):
        super(SelectWordsListScreen, self).__init__(*args, **kwargs)
        self.name = "select word list"
    def setup(self):
        """
        Should change this to on_switch kind of thing
        """
        self.popup = Popup(content=Label(text="Loading List..."), auto_dismiss=False,
                                                size_hint = (1,.5), title="")
        self.popup.open()

        def build_screen(result):
            selected_button = self.Selected()
            data = [self.DataItem(selected_obj=selected_button,text=name) for name in result]

            args_converter = lambda row_index, obj: {'text': obj.text,
                                                     'size_hint_y': None,
                                                     'height': 25}

            list_adapter = ListAdapter(data=data,
                                       args_converter=args_converter,
                                       cls=ListItemButton,
                                       propagate_selection_to_data=True,
                                       selection_mode='single',
                                       allow_empty_selection=False)

            list_view = ListView(adapter=list_adapter)
            button = Button(text = "Done", size_hint_y = .2)
            def callback(instance):
                app.root.transition.direction = "right"
                app.root.current = "make game"
                #app.root.transition.direction = "left"#didn't work
                                                # schedule callback?
                def change_left():
                    app.root.transition.direction = "left"
                reactor.callLater(.5, change_left)
                app.root.current_screen.word_list_name = selected_button.selected
            button.bind(on_release = callback)
            box_layout = BoxLayout(orientation="vertical")
            box_layout.add_widget(list_view)
            box_layout.add_widget(button)
            self.add_widget(box_layout)

        def close_popup(result):
            self.popup.dismiss()
        d = app.uplink.root_obj.callRemote("get_word_list_options")
        d.addCallback(build_screen)
        d.addCallback(close_popup)


class GameChooserScreen(Screen):
    pass

class MakeGameScreen(Screen):
    unique_game_id = ObjectProperty(None)
    word_list_name = StringProperty("No List Selected")
    def get_unique_game_id(self):
        print "changing id"
        def set_game_id(result):
            self.unique_game_id.text = result
        d = app.uplink.root_obj.callRemote("get_unique_game_id")
        d.addCallback(set_game_id)



class GameLobbyScreen(Screen):
    pass

class JoinGameScreen(Screen):
    pass

class SetupScreen(Screen):
    pass

class GameScreen(Screen):
    pass

class MyScreenManager(ScreenManager):
    pass


if __name__=="__main__":
    app.run()