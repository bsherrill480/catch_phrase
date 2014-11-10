import events as e
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, ObservableReferenceList, StringProperty, ListProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.adapters.models import SelectableDataItem
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListItemButton, ListView, ListItemLabel
from kivy.uix.scatter import Scatter

### TWISTED SETUP
from kivy.support import install_twisted_reactor
install_twisted_reactor()
from twisted_stuff import Uplink, ClientEventManager, reactor, pb
###/TWISTED SETUP

class DataItem(object):
    """
    used in buttons
    """
    def __init__(self, selected_obj, text):
        """
        selected_obj is the object passed to DataItem, which
        is used to house which button is selected in list
        """
        self.text = text
        self.selected_obj = selected_obj
        self._is_selected = False

    @property
    def is_selected(self):
        return self._is_selected

    @is_selected.setter
    def is_selected(self, value):
        if value:
            #self.selected_obj.selected = self.text
            self.selected_obj.selected = self
        self._is_selected = value

class Selected():
    """
    used in buttons. Basically just using as a reference/pointer
    Is there a better way?
    """
    def __init__(self):
        self.selected = None


class CatchPhraseApp(App):
    def build(self):
        self.event_manager = ClientEventManager()
        self.uplink = Uplink(self.event_manager)
        self.popup  = None
        self.lobby = None
        self.game = None
        return MyScreenManager()

    def loading_popup(self, message = "Loading..."):
        if self.popup:
            self.close_popup()
        self.popup = Popup(content=Label(text=message), auto_dismiss=False,
                                                size_hint = (1,.5), title="")
        self.popup.open()

    def close_popup(self, result=None):
        if self.popup:
            self.popup.dismiss()
            self.popup = None
        return result

    def generic_popup(self, message):
        if self.popup:
            self.close_popup()
        box_layout = BoxLayout(orientation="vertical")
        box_layout.add_widget(Label(text=message,
                                    size_hint = (1,.8)))
        close_button = Button(text='close', size_hint = (1, .2))
        box_layout.add_widget(close_button)
        self.popup = Popup(content=box_layout, auto_dismiss=False,
                          size_hint = (1, .5), title="")
        close_button.bind(on_release=self.popup.dismiss)
        self.popup.open()

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
        app.loading_popup(message="Logging in...")
        reactor.connectTCP("localhost", 8800, self.factory)
        d = self.factory.getRootObject()

        def failed_to_connect(result):
            app.generic_popup("can't connect to server")
            return result
        def change_to_gamechooser_screen(result):
            app.close_popup()
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
        popup = Popup(content=label, auto_dismiss=False, size_hint = (1, .5), title="")
        popup.open()
        return popup


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

    def __init__(self, *args, **kwargs):
        super(SelectWordsListScreen, self).__init__(*args, **kwargs)
        self.name = "select word list"

    def on_pre_enter(self, *args, **kwargs):
        super(SelectWordsListScreen, self).on_enter(*args, **kwargs)
        app.loading_popup()
        def build_screen(result):
            selected_button = Selected()
            data = [DataItem(selected_obj=selected_button,text=name) for name in result]

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
            def return_to_make_game(instance):
                app.root.change_right("make game")
                app.root.current_screen.word_list_name = selected_button.selected.text
            button.bind(on_release = return_to_make_game)
            box_layout = BoxLayout(orientation="vertical")
            box_layout.add_widget(list_view)
            box_layout.add_widget(button)
            self.add_widget(box_layout)


        d = app.uplink.root_obj.callRemote("get_word_list_options")
        d.addCallback(build_screen)
        d.addCallback(app.close_popup)


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

    def make_and_join_game(self):
        if self.word_list_name != "No List Selected":
            def was_success(result):
                if result:
                    join_screen = app.root.get_screen("join game")
                    join_screen.game_name_input.text = self.unique_game_id.text
                    app.root.current = "game lobby"
                else:
                    app.generic_popup("Game Name Taken")
            d = app.uplink.root_obj.callRemote("make_game_lobby",
                            self.unique_game_id.text, self.word_list_name)
            d.addCallback(was_success)
        else:
            app.generic_popup("Please Select List")
class GameLobbyScreen(Screen):
    view_label = ObjectProperty(None)
    view_list = ObjectProperty(None)
    pointing_to = ObjectProperty(None)
    class MyDataItem(DataItem):
        def __init__(self, selected_obj, text, client_id):
            super(GameLobbyScreen.MyDataItem, self).__init__(selected_obj,text)
            self.client_id = client_id
    class MyListItemButton(ListItemButton):
        def __init__(self, **kwargs):
            super(GameLobbyScreen.MyListItemButton,self).__init__(**kwargs)
            if "is_selected" in kwargs and kwargs["is_selected"]:
                self.select()

    def __init__(self, *args, **kwargs):
        super(GameLobbyScreen, self).__init__(*args, **kwargs)
        self.pointing_at = None
        self.waiting_label = Label(text="Waiting On:")
        self.bad_setup_label = Label(text="Bad Setup:")
        self.ready_label = Label(text="ready")
        self.selected_client = Selected()
        self.waiting_is_empty = False

    def submit_start_game_request(self):
        if self.waiting_is_empty:
            start_request = e.StartGameRequestEvent()
            app.lobby.callRemote("notify", start_request)

    def on_pre_enter(self, *args, **kwargs):
        join_screen = app.root.get_screen("join game")
        game_name = join_screen.game_name_input.text
        super(GameLobbyScreen, self).on_enter(*args, **kwargs)
        app.event_manager.register_listener(self)
        app.loading_popup()
        d = app.uplink.root_obj.callRemote("join_lobby", app.uplink.id, game_name)
        def was_success(result):
            if result:
                app.close_popup()
                app.lobby = result
            else:
                app.generic_popup(message="Unable To Join Game")
                app.root.change_right("join game")
            return result
        d.addCallback(was_success)

    def submit_point_at(self):
        selection = self.pointing_to.adapter.selection
        print ""
        if self.selected_client.selected:
            to_hand_off_to = e.ToHandoffToEvent(app.uplink.id,
                                                self.selected_client.selected.client_id)
            app.lobby.callRemote("notify", to_hand_off_to)


    def notify(self, event):
        if isinstance(event, e.NewPlayerLineupEvent):
            #player point_at setup
            data = [self.MyDataItem(self.selected_client, name, client_id)
                    for client_id, name in event.id_nickname_list]
            def args_converter(row_index, obj):
                return_dict = {'text': obj.text, 'size_hint_y': .1}
                #if we have a button, and if that button has same client_id
                if (self.selected_client.selected) and \
                        (obj.client_id == self.selected_client.selected.client_id):
                    return_dict["is_selected"] = True
                return return_dict

            list_adapter = ListAdapter(data=data,
                                       args_converter=args_converter,
                                       cls=self.MyListItemButton,
                                       propagate_selection_to_data=True,
                                       selection_mode='single',
                                       allow_empty_selection=True)
            self.pointing_to.adapter = list_adapter

            #player_view setup
            if event.waiting_list != []:
                event.waiting_list = ["waiting on:"] + event.waiting_list
                self.waiting_is_empty = False
            else:
                self.waiting_is_empty = True
            self.view_list.adapter = ListAdapter(data=event.waiting_list,
                                       cls=ListItemLabel)
        elif isinstance(event, e.WrongOrderingEvent):
            print event.print_out_list
            self.view_list.adapter = ListAdapter(
                data = ["Error In Ordering", "Current Cycles:"] + event.print_out_list,
                cls = ListItemLabel)
        elif isinstance(event, e.GameStartEvent):
            print "GO TO START GAME"


    def on_leave(self, *args, **kwargs):
        super(GameLobbyScreen, self).on_leave(*args, **kwargs)
        app.event_manager.unregister_listener(self)


class MyLabel(Label):
    pass

class MyScat(Scatter):
    pass


class MyListView(Widget):
    pass


class JoinGameScreen(Screen):
    game_name_input = ObjectProperty(None)
    def join_game(self):
        print "JOINING GAME"


class SetupScreen(Screen):
    pass


class GameScreen(Screen):
    pass


class MyScreenManager(ScreenManager):
    def change_right(self, screen):
        app.root.transition.direction = "right"
        app.root.current = screen
        def change_left():
            app.root.transition.direction = "left"
        reactor.callLater(.5, change_left)



if __name__=="__main__":
    app.run()