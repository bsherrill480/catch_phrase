import events as e
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListItemButton, ListView, ListItemLabel
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
import urllib as urllib2
from kivy.uix.scrollview import ScrollView
from kivy.storage.jsonstore import JsonStore
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import Color, Rectangle
from random import random
from kivy.uix.spinner import Spinner
from text_strings import about
import plyer

### TWISTED SETUP
from kivy.support import install_twisted_reactor
install_twisted_reactor()
from twisted_stuff import Uplink, ClientEventManager, reactor, pb
from twisted.internet import protocol
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure
###/TWISTED SETUP
#notes:
#-never name something an empty string, code relies often on emtpy string
#refering to a null value
#-I initially had kv lang initializing all my screens and a lot of stuff
#as a result I have lots of *args, **kwargs for __init__, however
#after refactoring I didn't end up making then in kv, but my methods
#still do *args, **kwargs even though now I know it's unnecesary.
#I should go back and refactor this. TODO: refactor that

VERSION = "1.0"


class MultiLineLabel(Label):
    def __init__(self, **kwargs):
        super(MultiLineLabel, self).__init__( **kwargs)
        self.text_size = self.size
        self.bind(size= self.on_size)
        self.bind(text= self.on_text_changed)
        self.size_hint_y = None # Not needed here

    def on_size(self, widget, size):
        self.text_size = size[0], None
        self.texture_update()
        if self.size_hint_y == None and self.size_hint_x != None:
            self.height = max(self.texture_size[1], self.line_height)
        elif self.size_hint_x == None and self.size_hint_y != None:
            self.width  = self.texture_size[0]

    def on_text_changed(self, widget, text):
        self.on_size(self, self.size)

class FileManager:
    """
    manages files
    """
    MAX_FILE_SIZE_KB = 500
    WORD_LIST_NAMES = "word_list_names" # the list of names for the word lists
    def __init__(self):
        self.store = JsonStore('word_lists.json')
        try:
            self.word_lists_names = self.store.get(self.WORD_LIST_NAMES)["my_list"]
        except KeyError:
            self.word_lists_names = []
            self.store.put(self.WORD_LIST_NAMES, my_list=[])

    def get_word_list(self, name):
        """
        not a url, a wordlist in self.word_list_names
        """
        return self.store.get(name)["my_list"]

    def get_word_list_of_file(self, url):
        """
        returns an empty list if error
        """
        if not (url[0:8] == "https://" or url[0:7] == "http://"):
            url = "http://" + url
        try:
            u = urllib2.urlopen(url)
        except Exception, err:
            return str(err)#for debugging
        meta = u.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        if file_size > self.MAX_FILE_SIZE_KB * 1024:
            return "File To Large"
        l = ""
        block_sz = 4096 # apparently default for sql
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break
            l += buffer
        l = l.split("\n")#split along new lines

        #eliminate blank lines ("  ") and empty lines ("")
        return [value for value in l if value.strip(" ") != ""]

    def store_word_list(self, name, word_list):
        # if name == self.WORD_LIST_NAMES:
        #     return "Invalid Name"
        self.store.put(name, my_list = word_list)
        if name not in self.word_lists_names:
            self.word_lists_names.append(name)
        self._save_word_list_names()
        #return "Successfully Added"

    def delete_word_list(self, name):
        self.word_lists_names.remove(name)
        self.store.delete(name)
        self._save_word_list_names()

    def _save_word_list_names(self):
        self.store.put(self.WORD_LIST_NAMES, my_list=self.word_lists_names)




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
        self.popup = None
        self.lobby = None # will be a root_obj, ie twisted.spread.pb.root
        self.game = None
        self.is_premium = True
        Window.bind(on_keyboard=self.hook_keyboard)#bind back button on anroid
        self.file_manager = FileManager()
        return MyScreenManager()

    def loading_popup(self, instance=None, message = "Loading..."):
        """
        makes a loading popup with no close button. Optional agrument
        to change message
        """
        self.close_popup()
        self.popup = Popup(content=Label(text=message), auto_dismiss=False,
                                                size_hint = (1,.5), title="")
        self.popup.open()

    def close_popup(self, result=None):
        """
        closes popup if open, takes optional argument incase used in twisted
        deferred
        """
        if self.popup:
            self.popup.dismiss()
        return result

    def generic_popup(self, message, popup_size_hint_y = .5, paragraph = False, title = ""):
        """
        closes popup if there is one open. Makes new popup with a close button
        and the passed message.
        """
        self.close_popup()
        box_layout = BoxLayout(orientation="vertical")
        if paragraph:
            scroll_view = ScrollView(size_hint_y = .8)
            scroll_view.add_widget(MultiLineLabel(text=message))
            box_layout.add_widget(scroll_view)
        else:
            box_layout.add_widget(Label(text=message,
                                        size_hint = (1,.8)))
        close_button = Button(text='close', size_hint = (1, .2))
        box_layout.add_widget(close_button)
        self.popup = Popup(content=box_layout, auto_dismiss=False,
                          size_hint = (1, popup_size_hint_y), title=title)
        close_button.bind(on_release=self.popup.dismiss)
        self.popup.open()

    # def generic_popup(self, message, popup_size_hint_y = .5):
    #     """
    #     closes popup if there is one open. Makes new popup with a close button
    #     and the passed message.
    #     """
    #     self.close_popup()
    #     box_layout = BoxLayout(orientation="vertical")
    #     box_layout.add_widget(Label(text=message,
    #                                 size_hint = (1,.8)))
    #     close_button = Button(text='close', size_hint = (1, .2))
    #     box_layout.add_widget(close_button)
    #     self.popup = Popup(content=box_layout, auto_dismiss=False,
    #                       size_hint = (1, popup_size_hint_y), title="")
    #     close_button.bind(on_release=self.popup.dismiss)
    #     self.popup.open()

    def buy_premium_popup(self):
        self.generic_popup("BUY PREMIUM!")


    def hook_keyboard(self, window, key, *args):
        if key == 27:
            self.close_popup()
            return self.root.current_screen.back_to_screen()

#added so all code should have access to app
app = CatchPhraseApp()


class LoginScreen(Screen):
    MAX_LOGIN_NAME_LENGTH = 12
    IPER_IP = "localhost"
    IPER_PORT = 8000
    class CantFindIperError(Exception):
        pass
    class IncorrectVersionError(Exception):
        pass
    def __init__(self, *args, **kwargs):
        super(LoginScreen, self).__init__(*args, **kwargs)
        self.name = "Login"
        self.factory = pb.PBClientFactory()
        print app.get_application_config()

    def login(self, nickname, password=""):
        """
        attempts to login to server. displays loading popup until
        logged in. Displays failed to connect popup if unable to
        connect
        """
        app.uplink.give_nickname_and_password(nickname, password)
        if len(nickname) > self.MAX_LOGIN_NAME_LENGTH:
            app.generic_popup(
                "nickname must be less than " + str(self.MAX_LOGIN_NAME_LENGTH) + " characters")
            return
        def errback_callback(result):
            error = result.value
            if isinstance(error, self.CantFindIperError):
                app.generic_popup("Failed to find server")
            elif isinstance(error, self.IncorrectVersionError):
                # app.generic_popup("Please update app \n" + "Found version " + self.VERSION  +
                #                   ". Expected version " )#+ result.expected_version)
                app.generic_popup("upgrade version")
            else:
                app.generic_popup("Failed to connect to server")# + str(result))
            return True
        d = self.ask_iper()
        d.addCallbacks(self.server_login, errback_callback)


    def ask_iper(self):
        d = Deferred()
        cant_find_iper = self.CantFindIperError
        wrong_version = self.IncorrectVersionError
        my_version = VERSION
        class IperClient(protocol.Protocol):

            def connectionMade(self):
                self.transport.write(" ")

            def dataReceived(self, recieved_data):
                self.transport.loseConnection()
                ip, port, ver = recieved_data.split()
                if ver != my_version:
                    d.errback(wrong_version())
                else:
                    d.callback((ip, port))

        class IperFactory(protocol.ClientFactory):
            def buildProtocol(self, addr):
                return IperClient()

            def clientConnectionFailed(self, connector, reason):
                d.errback(cant_find_iper())

        reactor.connectTCP(self.IPER_IP, self.IPER_PORT, IperFactory())
        return d

    def server_login(self, ip_port):
        ip, port = ip_port
        print "loggin in to:", ip, port
        app.loading_popup(message="Logging in...")
        reactor.connectTCP(ip, int(port), self.factory)

        d = self.factory.getRootObject()

        def failed_to_connect(result):
            app.generic_popup("can't connect to server")
            return result
        def change_to_gamechooser_screen(result):
            if result:
                app.close_popup()
                app.uplink.evm_registered = True
                app.root.switch_to("game chooser")
                return result
            else:
                app.generic_popup("Empty Username Not Acceptable")

        d.addErrback(failed_to_connect) # change to errback when done debug
        d.addCallback(app.uplink.give_root_obj)
        d.addCallback(app.uplink.register_evm)
        d.addCallback(app.uplink.give_id)
        d.addCallback(change_to_gamechooser_screen)

    def back_to_screen(self):
        return False

class SelectWordsListScreen(Screen):
    """
    Screen for choosing list of words in MakeGameScreen
    """
    LIST_ITEM_BUTTON_HEIGHT = "35dp"
    def __init__(self, word_lists_names = None, switch_to_screen = "make game"):
        super(SelectWordsListScreen, self).__init__()
        self.name = "select words list"
        self.word_lists_names = word_lists_names
        self.switch_to_screen = switch_to_screen
    def back_to_screen(self):
        return False

    def build_screen(self):
        def build_screen(result):
            selected_button = Selected()
            data = [DataItem(selected_obj=selected_button,text=name) for name in result]

            args_converter = lambda row_index, obj: {'text': obj.text,
                                                     'size_hint_y': None,
                                                     'height': self.LIST_ITEM_BUTTON_HEIGHT,
                                                     'deselected_color': [176./255,196./255,222./255, 1],
                                                     'selected_color': [51./255, 164./255, 206./255, 1],
                                                     }

            list_adapter = ListAdapter(data=data,
                                       args_converter=args_converter,
                                       cls=ListItemButton,
                                       propagate_selection_to_data=True,
                                       selection_mode='single',
                                       allow_empty_selection=False)

            list_view = ListView(adapter=list_adapter)
            button = Button(text = "Done", size_hint_y = .2)
            def return_to_screen(instance):
                app.root.switch_to(self.switch_to_screen, direction="right")
                curr_screen = app.root.current_screen
                curr_screen.word_list_name = selected_button.selected.text
                if self.switch_to_screen == "make game": #i.e. we didn't come from somewhere else
                    if self.word_lists_names is None:
                        curr_screen.word_source = curr_screen.SERVER
                    else:
                        curr_screen.word_source = curr_screen.LOCAL_LIST
            button.bind(on_release = return_to_screen)
            box_layout = BoxLayout(orientation="vertical")
            box_layout.add_widget(list_view)
            box_layout.add_widget(button)
            self.add_widget(box_layout)
        if self.word_lists_names is None: #remember, we could get a empty list passed!
            d = app.uplink.root_obj.callRemote("get_word_list_options")
            d.addCallback(build_screen)
            d.addCallback(app.close_popup)
        else:
            build_screen(self.word_lists_names)
            app.close_popup()

    def on_pre_enter(self, *args, **kwargs):
        super(SelectWordsListScreen, self).on_enter(*args, **kwargs)
        app.loading_popup()
        self.build_screen()

    def back_to_screen(self):
        app.root.switch_to("make game", direction="right")
        return True

class GameChooserScreen(Screen):
    """
    Join Game or Make Game screen.
    """
    def on_enter(self, *args):
        super(GameChooserScreen, self).on_enter(*args)

    def back_to_screen(self):
        return False

    def download_from_server(self):
        def on_word_list_name_callback(instance, value):
            def switch_screen_callback(result):
                app.root.switch_to(WordListViewerScreen(result, "game chooser"), transition=NoTransition())
            d = app.uplink.root_obj.callRemote("get_word_list", value)
            d.addCallback(switch_screen_callback)
        def back_to_screen_replacement():
            app.root.switch_to("game chooser", direction="right")
            return True
        screen = IntermediateScreen("", on_word_list_name_callback)
        select_words_list_screen = SelectWordsListScreen(switch_to_screen=screen)
        select_words_list_screen.back_to_screen = back_to_screen_replacement
        app.root.switch_to(select_words_list_screen)

class MakeGameScreenContents(GridLayout):
    game_name_text_input = ObjectProperty(None)
    score_system_button = ObjectProperty(None)
    round_length = ObjectProperty(None)
    leeway_time = ObjectProperty(None)

    def check_is_int(self, instance, defualt_val):
        try:
            int(instance.text)
            return True
        except ValueError:
            app.generic_popup("Inappropriate Value in field")
            instance.text = str(defualt_val)
        return False

class MakeGameScreenScoreSystemPopupContent(BoxLayout):
    the_widgets = ObjectProperty(None)
    individuals_button = ObjectProperty(None)
    teams_button = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(MakeGameScreenScoreSystemPopupContent, self).__init__(*args, **kwargs)
        self.score_system = app.root.current_screen.score_system_mode
        self.number_of_teams = app.root.current_screen.number_of_teams
        if app.root.current_screen.score_system_mode == app.root.current_screen.TEAM_SCORE_SYSTEM:
            self.teams_button.state = "down"
        else:
            self.individuals_button.state = "down"

class MakeGameScreen(Screen):
    """
    Screen to select options and make a game
    """
    scroll_layout = ObjectProperty(None)
    unique_game_id = StringProperty("")
    select_word_list_button = ObjectProperty(None)
    word_list_name = StringProperty("No List Selected")
    score_system_mode = StringProperty("teams")
    number_of_teams = NumericProperty(2)
    TEAM_SCORE_SYSTEM = "teams"
    INDIVIDUAL_SCORE_SYSTEM = "individual"
    LOCAL_LIST = "local"
    SERVER = "server"
    def __init__(self):
        super(MakeGameScreen, self).__init__()
        self.word_source = "" #Source is either LOCAL_LIST or SERVER
        grid_layout = MakeGameScreenContents()
        grid_layout.bind(minimum_height=grid_layout.setter('height'))
        self.scroll_layout.add_widget(grid_layout)
        self.contents = grid_layout
        self.popup = None

    def on_number_of_teams(self, instance, value):
        self.on_score_system_mode(None, self.score_system_mode)

    def on_score_system_mode(self, instance, value):
        if value == self.TEAM_SCORE_SYSTEM:
            value = str(self.number_of_teams) + " " + value
        self.contents.score_system_button.text = value

    def on_word_list_name(self, instance, value):
        self.contents.select_word_list_button.text = value

    def on_unique_game_id(self, instance, value):
        self.contents.game_name_text_input.text = value

    def get_unique_game_id(self):
        """
        ask server for a game id. Technically not unique, as a user could choose
        to make a game in the format of the unqiue_game_id". Format is
        "Game" + str(total_number_of_games_ever_made)
        """
        def set_game_id(result):
            self.unique_game_id = result
        d = app.uplink.root_obj.callRemote("get_unique_game_id")
        d.addCallback(set_game_id)

    def check_text_is_int(self, instance, defualt_val):
        try:
            int(instance.text)
            return True
        except ValueError:
            app.generic_popup("Inappropriate Value in field")
            instance.text = str(defualt_val)
        return False


    def score_system(self):
        self.popup = Popup(title = "",
                           content=MakeGameScreenScoreSystemPopupContent(),
                           auto_dismiss=False)
        self.popup.open()

    def local_list(self, instance=None, value=None):
        app.root.switch_to(SelectWordsListScreen(app.file_manager.word_lists_names))
        self.popup.dismiss()
        self.popup = None

    def server_list(self, instance=None, value=None):
        app.root.switch_to(SelectWordsListScreen())
        self.popup.dismiss()
        self.popup = None

    def setup_correct(self):
        message = ""
        if self.word_list_name == "No List Selected":
            message =  "Please Select List"
        elif not self.check_text_is_int(self.contents.round_length, 120):
            message = "Round Length Was Incorrectly Formatted"
        elif not self.check_text_is_int(self.contents.leeway_time, 0):
            message = "Leeway Time Was Incorrectly Formatted"
        if message:
            app.generic_popup(message)
        return not message

    def make_and_join_game(self):
        if self.setup_correct():
            def was_success(result):
                if result[0]:
                    join_screen = app.root.my_get_screen("join game")
                    join_screen.game_name_input.text = self.unique_game_id
                    #app.root.switch_to("game lobby")
                    app.root.switch_to(GameLobbyScreen())
                else:
                    app.generic_popup(result[1])
            d = app.uplink.root_obj.callRemote(
                "make_game_lobby",
                self.unique_game_id,
                self.word_list_name if self.word_source == self.SERVER
                else app.file_manager.get_word_list(self.word_list_name),
                self.score_system_mode,
                self.number_of_teams,
                int(self.contents.round_length.text),
                int(self.contents.leeway_time.text)
            )
            d.addCallback(was_success)


    def back_to_screen(self):
        if self.popup:
            print "closing popup"
            self.popup.dismiss()
            self.popup = None
        else:
            print "switching to game chooser"
            app.root.switch_to("game chooser", direction="right")
        return True

class GameLobbyScreen(Screen):
    """
    screen before game starts. Users need to input who they will pass the device
    to.
    """
    SPINNER_HEIGHT = "50dp"
    view_label = ObjectProperty(None)
    view_list = ObjectProperty(None)
    pointing_to_spinner = ObjectProperty(None)#List of buttons of players who can be point to
    number_sharing_device_spinner = ObjectProperty(None)
    waiting_is_empty = BooleanProperty(False)
    interactive_half = ObjectProperty(None)
    # class MyDataItem(DataItem):
    #     def __init__(self, selected_obj, text, client_id):
    #         super(GameLobbyScreen.MyDataItem, self).__init__(selected_obj,text)
    #         self.client_id = client_id
    #
    # class MyListItemButton(ListItemButton):
    #     def __init__(self, **kwargs):
    #         super(GameLobbyScreen.MyListItemButton,self).__init__(**kwargs)
    #         if "is_selected" in kwargs and kwargs["is_selected"]:
    #             self.select()

    class StringHider(str):
        def __new__(cls, string, dict_values):
            obj = str.__new__(cls, string)
            if isinstance(dict_values, dict):
                for key, value in dict_values.iteritems():
                    setattr(obj, key, value)
            else:
                raise TypeError("StringHider: dict_values must be a dict")
            return obj

    def __init__(self, observer=False, *args, **kwargs):
        super(GameLobbyScreen, self).__init__(*args, **kwargs)
        self.pointing_at = self.StringHider("", {"client_id": ""}) # who user is pointing to
        #self.waiting_label = Label(text="Waiting On:")
        self.selected_client = Selected()
        #self.waiting_is_empty = False
        self.player_lineup = [] #list formated [...(client_id, name)...]
        self.is_observer = observer

    def submit_start_game_request(self):
        if self.waiting_is_empty:
            app.lobby.callRemote("notify", e.StartGameRequestEvent())

    def on_pre_enter(self, *args, **kwargs):
        join_screen = app.root.my_get_screen("join game")
        game_name = join_screen.game_name_input.text
        super(GameLobbyScreen, self).on_enter(*args, **kwargs)
        app.event_manager.register_listener(self)
        app.loading_popup()
        join_lobby = "join_lobby_score" if self.is_observer else "join_lobby"
        d = app.uplink.root_obj.callRemote(join_lobby, app.uplink.id, game_name)
        def was_success(result):
            if result:
                app.close_popup()
                app.lobby = result
            else:
                app.generic_popup(message="Unable To Join Game")
                app.root.switch_to("join game", direction="right")
            return result
        d.addCallback(was_success)

        #setup spinner
        self.pointing_to_spinner.bind(text=self.submit_point_at)
        self.number_sharing_device_spinner.bind(text=self.submit_number_sharing_device)


    def on_enter(self, *args):
        super(GameLobbyScreen, self).on_enter(*args)
        if self.is_observer:
            self.interactive_half.clear_widgets()
    def submit_number_sharing_device(self, spinner, text):
        print "sending event"
        app.lobby.callRemote("notify", e.NumberSharingDeviceEvent(app.uplink.id, int(text)))

    def submit_point_at(self, spinner, text):
        if text: #i.e. not a blank string, which I plan to be a defalt back to if
                #person i'm pointing at leaves
            print text, text.client_id
            self.pointing_at = text
            to_hand_off_to = e.ToHandoffToEvent(app.uplink.id, text.client_id)
            app.lobby.callRemote("notify", to_hand_off_to)

    def update_spinner(self):
        values = []
        seen_pointing_at = False
        for client_id, name in self.player_lineup:
            values.append(self.StringHider(name, {"client_id" : client_id}))
            if self.pointing_at.client_id == client_id:
                seen_pointing_at = True
        if not seen_pointing_at:
            self.pointing_to_spinner.text = ""
        self.pointing_to_spinner.values = values

    def notify(self, event):
        print event
        if isinstance(event, e.NewPlayerLineupEvent):
            self.player_lineup = event.id_nickname_list
            self.update_spinner()
            if event.waiting_list != []:
                #event.waiting_list = ["waiting on:"] + event.waiting_list
                self.waiting_is_empty = False
            else:
                self.waiting_is_empty = True
            self.view_list.adapter = ListAdapter(data=event.waiting_list,
                                       cls=ListItemLabel)
        elif isinstance(event, e.WrongOrderingEvent):
            self.view_list.adapter = ListAdapter(
                data = ["Error In Ordering", "Current Cycles:"] + event.print_out_list,
                cls = ListItemLabel)
        elif isinstance(event, e.GameStartEvent):
            app.root.switch_to(GameScreen(event.team_scores))

    def back_to_screen(self):
        app.lobby.callRemote("notify", e.QuitEvent(app.uplink.id))
        app.root.switch_to("game chooser", direction="right")
        return True

    def on_leave(self, *args, **kwargs):
        super(GameLobbyScreen, self).on_leave(*args, **kwargs)
        app.event_manager.unregister_listener(self)

class ScoreLabel(BoxLayout):
    score = NumericProperty(0)
    score_label = ObjectProperty(None)
    team_label = ObjectProperty(None)
    def __init__(self, team_name, team_id, **kwargs):
        super(ScoreLabel, self).__init__(**kwargs)
        self.e = e #give kv access to events
        self.team_id = team_id
        self.team_label.text = team_name
        self.score_label.text = "0"
    def on_score(self, instance, value):
        self.score_label.text = str(value)

# class ScoreLabel(Label):
#     score = NumericProperty(0)
#     def __init__(self, team_name, team_id, **kwargs):
#         super(ScoreLabel, self).__init__(**kwargs)
#         self.team_id = team_id
#         self.team_name = team_name
#         self.text = team_name + "\n" + "0"
#     def on_touch_down(self, touch):
#         if self.collide_point(*touch.pos):
#             if touch.is_double_tap:
#                 event = e.ScoreDecreaseRequestEvent(self.team_id)
#                 print "doubletap"
#             elif touch.is_triple_tap:
#                 event = e.ScoreIncreaseRequestEvent(self.team_id)
#                 print "tripletap"
#             #app.lobby.callRemote("notify", event)
#     def on_score(self, instance, value):
#         self.text = self.team_name + "\n" + str(value)

class GameScreen(Screen):
    players_turn_label = ObjectProperty(None)
    word_label = ObjectProperty(None)
    bottom_buttons = ObjectProperty(None)
    time_label = ObjectProperty(None)
    scores_label = ObjectProperty(None)
    scores_scroll_view = ObjectProperty(None)
    NOT_YOUR_TURN = "Not Your Turn"
    def __init__(self, team_scores, *args, **kwargs):
        super(GameScreen, self).__init__(*args, **kwargs)
        self.start_round_button = Button(text="Start Round")
        self.start_round_button.bind(on_release=self.post_round_start_event)
        self.word_guessed_button = Button(text="Next")
        self.word_guessed_button.bind(on_release = self.post_end_turn)
        self.start_time = 0
        self.turn_time = 0
        self.count_downer = None
        self.team_scores = team_scores #setup [...[score, team_name, team_id]...]
        self.team_scores_label_dict = {}
        #setup scroll view
        grid_layout_scores = GridLayout(rows=1, size_hint_x=None)
        grid_layout_scores.bind(minimum_width=grid_layout_scores.setter('width'))
        for score, team_name, team_id in self.team_scores:
            label = ScoreLabel(team_name, team_id)
            grid_layout_scores.add_widget(label)
            self.team_scores_label_dict[team_id] = label
        self.scores_scroll_view.add_widget(grid_layout_scores)

    def make_text_big(self, instance, value):
        instance.font_size = 12 #default font size
        if value != self.NOT_YOUR_TURN:
            print "resziing ", value
            label_width, label_height = instance.size
            texture_width, texture_height = instance.texture.size
            while texture_width < label_width and texture_height < label_height:
                instance.font_size += 1
                instance.texture_update()
                texture_width, texture_height = instance.texture.size


    def quit(self, instance = None):
        """
        used in button
        """
        app.root.switch_to("game chooser", direction="right")
        app.lobby.callRemote("notify", e.QuitEvent(app.uplink.id))
        app.lobby = None

    def post_round_start_event(self, instance):
        """
        used in button
        """
        app.lobby.callRemote("notify", e.StartRoundEvent())

    def time_remaining(self):
        time_elapsed = Clock.get_time() - self.start_time
        time_remaining = self.turn_time - time_elapsed
        return time_remaining

    def post_end_turn(self, instance):
        """
        used in button
        """
        Clock.unschedule(self.count_downer)
        self.bottom_buttons.clear_widgets()
        app.lobby.callRemote("notify", e.EndTurnEvent(app.uplink.id,
                                                      self.time_remaining()))
        self.word_label.text = self.NOT_YOUR_TURN

    def on_enter(self, *args, **kwargs):
        super(GameScreen, self).on_enter(*args, **kwargs)
        self.bottom_buttons.clear_widgets()#playing another game
        self.bottom_buttons.add_widget(self.start_round_button)
        app.event_manager.register_listener(self)

        #make big letters
        self.word_label.bind(text = self.make_text_big)

        #setup scores
    def notify(self, event):
        # if hasattr(event, "lobby_id"):
        #     print "event recieved", event, event.lobby_id
        # else:
        #     print "event", event
        if isinstance(event, e.StartRoundEvent):
            self.bottom_buttons.clear_widgets()
        elif isinstance(event, e.EndRoundEvent):
            self.bottom_buttons.clear_widgets()
            #self.scores_label.text = event.scores
            self.bottom_buttons.add_widget(self.start_round_button)
        elif isinstance(event, e.BeginTurnEvent):
            self.players_turn_label.text = "Current Turn: " + event.nickname
            if event.client_id == app.uplink.id:
                self.my_turn(event.time_left, event.word)
        elif isinstance(event, e.ScoreDecreaseRequestEvent):
            self.team_scores_label_dict[event.team_id].score -= 1
        elif isinstance(event, e.ScoreIncreaseRequestEvent):
            self.team_scores_label_dict[event.team_id].score += 1

    def my_turn(self, time_left, word):
        try:
            plyer.vibrator.vibrate(.1)
        except Exception as e:
            pass
        self.bottom_buttons.clear_widgets()
        self.bottom_buttons.add_widget(self.word_guessed_button)
        self.start_time = Clock.get_time()
        self.turn_time = time_left
        self.word_label.text = word
        def count_downer(interval):
            time_remaining  = self.time_remaining()
            if time_remaining <= 0.0:
                time_remaining = 0
                self.post_end_turn(0)#forced to pass some argument
            self.time_label.text = str(int(round(time_remaining)))
        count_downer(0)#forced to pass some argument
        self.count_downer = count_downer
        Clock.schedule_interval(self.count_downer, 1.0)

    def on_leave(self, *args, **kwargs):
        super(GameScreen, self).on_leave(*args, **kwargs)
        app.event_manager.unregister_listener(self)

    def back_to_screen(self):
        Clock.unschedule(self.count_downer)
        self.quit()
        return True


class ManageWordListsScreen(Screen):
    list_label = ObjectProperty(None)
    new_list_okay = ObjectProperty(None)
    new_list_not_okay = ObjectProperty(None)
    scroll_view = ObjectProperty(None)
    new_list_box = ObjectProperty(None)
    SCROLL_BUTTON_SIZES = "40dp"
    VIEW_WORDS_LABEL_HEIGHT = "25dp"
    def __init__(self, *args, **kwargs):
        super(ManageWordListsScreen, self).__init__(*args, **kwargs)

    def on_pre_enter(self, *args, **kwargs):
        super(ManageWordListsScreen, self).on_pre_enter(*args, **kwargs)
        app.loading_popup()

    def get_word_list_from_row_button(self, instance):
        """
        instance is either a view_button or a edit_button in a row (see on_enter).
        """
        label = instance.parent.get_named_child("label")
        list_name = label.text
        word_list = app.file_manager.get_word_list(list_name)
        word_list.sort()
        return list_name, word_list

    def view_button_callback(self, instance):
        #note: parents of this will be a ChildWatchingBoxLayout
        list_name, words_list = self.get_word_list_from_row_button(instance)
        # args_converter = lambda row_index, word: {"text": word,
        #                                           "size_hint_y" : None,
        #                                           "height" : self.VIEW_WORDS_LABEL_HEIGHT}
        # list_adapter = ListAdapter(data=words_list,
        #                            args_converter=args_converter,
        #                            cls=ListItemLabel)
        list_view_screen = WordListViewerScreen(words_list)

        #list_view = app.root.my_get_screen('word list viewer').words_list_view
        #list_view.adapter = list_adapter
        # list_view_screen.words_list_view.adapter = list_adapter
        app.root.switch_to(list_view_screen)
        #app.root.switch_to("word list viewer")
    def edit_button_callback(self, instance):
        list_name, words_list = self.get_word_list_from_row_button(instance)
        word_list_editor = WordListEditor(list_name, words_list)
        app.loading_popup()
        app.root.switch_to(word_list_editor)

    def delete_buton_callback(self, instance):
        list_name, words_list = self.get_word_list_from_row_button(instance)
        app.file_manager.delete_word_list(list_name)
        self.build_screen()

    def build_screen(self):
        self.scroll_view.clear_widgets()#because I rebuild everytime
        word_list_names = app.file_manager.word_lists_names

        #can not add a widget that has a parent. Made them in kv file
        #so they have a parent.

        #make rows for the scroll view
        if word_list_names == []:
            self.scroll_view.add_widget(Label(text="filler"))
        else:
            layout = GridLayout(cols=1, spacing=0, size_hint_y=None)
            layout.bind(minimum_height=layout.setter('height'))
            for list_name in word_list_names:
                #setup
                row = ChildWatchingBoxLayout(size_hint_y = None, height = self.SCROLL_BUTTON_SIZES)
                label = Label(text=list_name, size_hint_x=(1.0-3*.125), size_hint_y = None,
                              height = self.SCROLL_BUTTON_SIZES)
                # with label.canvas.after:
                #     color = Color()
                #     color.rgba = [random() for x in range(3)] +[.1]
                #     rec = Rectangle()
                #     rec.size = self.size
                #     rec.pos = self.pos

                delete_button = Button(text="delete", background_color=(1,0,0,1),
                                       size_hint_y = None, size_hint_x = .125,
                                       height = self.SCROLL_BUTTON_SIZES)
                delete_button.bind(on_release = self.delete_buton_callback)
                view_button = Button(text="view", size_hint_x = .125, size_hint_y = None,
                              height = self.SCROLL_BUTTON_SIZES)
                view_button.bind(on_release = self.view_button_callback)
                edit_button = Button(text="edit", size_hint_x = .125, size_hint_y = None,
                              height = self.SCROLL_BUTTON_SIZES)
                edit_button.bind(on_release = self.edit_button_callback)

                #add to row
                row.add_widget(label, name="label")
                row.add_widget(delete_button)
                row.add_widget(view_button)
                row.add_widget(edit_button)
                #add to self.box_layout
                layout.add_widget(row)
            self.scroll_view.add_widget(layout)
            self.help_layout = layout
            # for child in layout.children:
            #     if isinstance(child, ChildWatchingBoxLayout):
            #         label = child.get_named_child('label')
            #         print label.text, label.size, label.pos, label.canvas.after.color
        #add make new_list_button

        self.new_list_box.clear_widgets()
        if (not app.is_premium) and len(app.file_manager.word_lists_names) >= 1:
            self.new_list_box.add_widget(self.new_list_not_okay)
        else:
            self.new_list_box.add_widget(self.new_list_okay)
        app.close_popup()#close loading popup
    def help(self):
        for child in self.help_layout.children:
            print (child.size, child.pos)
            print "===================="
        # self.help_layout.cols = 1
        # print "sceeen",app.root.current_screen.size, app.root.current_screen.pos
        # print "scroll", self.scroll_view.size, self.scroll_view.pos
        # print self.help_layout, self.help_layout.size, self.help_layout.pos, self.help_layout.spacing
        # for child in self.help_layout.children:
        #         print child.get_named_child('label').text
        #         print [ (child2.text,child2.size, child2.pos) for child2 in child.children]
        #         print "===================="
    def on_enter(self, *args, **kwargs):
        #TODO: refactor so that all I am doing is the rows and col. Put rest in kv lang
        #TODO: like word_list_editor
        super(ManageWordListsScreen, self).on_enter(*args,**kwargs)
        self.build_screen()

    def back_to_screen(self):
        app.root.switch_to("game chooser", direction="right")
        return True

class WordListEditor(Screen):
    #needs view of words, add word, save name and note that if save_name =
    scroll_view = ObjectProperty(None)
    save_name_input = ObjectProperty(None)
    new_word_input = ObjectProperty(None)
    ROW_BUTTON_SIZES = "25dp"
    def __init__(self,list_name, word_list):
        super(WordListEditor, self).__init__()
        self.word_list = list(word_list) # don't want to change list unless we save!
        self.list_name = list_name
        self.save_name_input_text = ""
        self.popup = None
    def add_word(self, word):
        if not word:
            app.generic_popup("No empty words")
        elif word in self.word_list:
            app.generic_popup("word already in list")
        else:
            self.word_list.append(word)
            self.new_word_input.text = ""
            app.loading_popup()
            self.focus_text = True
            self.build_scroll_word_list()
    def remove_word_callback(self, instance):
        #hacky workaround for my loading popup not displaying before
        #(time intensive) remove operation.
        def callback(junk):
            label = instance.parent.get_named_child("label")
            word = label.text
            self.word_list.remove(word)#O(n) when we could have O(log(n)) w/ lazy deletes
            self.scroll_view.clear_widgets()
            self.build_scroll_word_list()
        Clock.schedule_once(callback, 0.01)

    def build_scroll_word_list(self):
        self.scroll_view.clear_widgets()
        layout = GridLayout(cols=1, spacing="10dp", size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        for word in self.word_list:
            row = ChildWatchingBoxLayout(size_hint_y = None, height=self.ROW_BUTTON_SIZES)
            label = Label(text=word, size_hint_x=.8, size_hint_y = None,
                          height = self.ROW_BUTTON_SIZES,)
            remove_button = Button(text="REMOVE", size_hint_x = .2, size_hint_y = None,
                          height = self.ROW_BUTTON_SIZES, background_color = [1,0,0,1])
            remove_button.bind(on_press = app.loading_popup)
            remove_button.bind(on_release = self.remove_word_callback)

            #add to row
            row.add_widget(label, name="label")
            row.add_widget(remove_button)
            #add to self.box_layout
            layout.add_widget(row)
        self.scroll_view.add_widget(layout)
        self.new_word_input.focus = True
        app.close_popup()

    def save_popup(self):
        """
        a popup made to save list
        """
        class PopupHelper:
            def __init__(self, err_label, text_input, popup, word_list, close_popup):
                self.err_label = err_label
                self.text_input = text_input
                self.popup = popup
                self.word_list = word_list
                self.close_popup = close_popup
            def __call__(self, instance):
                name = self.text_input.text
                word_list_names = app.file_manager.word_lists_names
                if not name:
                    self.err_label.text = ("ERROR: can not have empty name")
                elif name in word_list_names:
                    app.file_manager.store_word_list(name, self.word_list)
                    self.close_popup()
                    app.root.switch_to("manage word lists", direction="right")
                elif app.is_premium or len(word_list_names) < 1:
                    app.file_manager.word_lists_names.append(name)
                    app.file_manager.store_word_list(name, self.word_list)
                    self.close_popup()
                    app.root.switch_to("manage word lists", direction="right")
                else:
                    self.err_label.text = ("ERROR: You must upgrade to Premium to have more "
                                      "than 1 personal list")

        content = BoxLayout(orientation = "vertical")
        question_label = Label(text="Please input save name")
        err_label = Label(text="")
        buttons = BoxLayout()
        save_name_input = TextInput(text=self.save_name_input_text, multiline = False)
        # close_button = Button(text="cancel")
        save_button = Button(text="save") #CHANGED TO "save 1" for debugging
        # buttons.add_widget(close_button)
        buttons.add_widget(save_button)
        for widget in [question_label,err_label,save_name_input,buttons]:
            content.add_widget(widget)
        popup = Popup(title="save popup", auto_dismiss = False, content=content)
        def close_popup():
            popup.dismiss()
            self.popup = None #needs to be set back to None, so I can check if a popup is open
        # close_button.bind(on_release = popup.dismiss)
        save_button.bind(on_release = PopupHelper(err_label, save_name_input, popup, self.word_list, close_popup))
        popup.open()
        self.popup = popup
    def popup_save(self, instance):
        """
        popup's save method
        """
        name = None #debug
        err_label = None #debug
        word_list_names = app.file_manager.word_lists_names
        box_layout_of_popup = instance.parent.parent
        for child in box_layout_of_popup.children:
            if isinstance(child, TextInput):
                name = child.text
            if isinstance(child, Label) and child.text == "":#e.g. err_label
                err_label = child
        if not name:
            err_label.text = ("ERROR: can not have empty name")
        elif name in word_list_names:
            app.file_manager.store_word_list(name, self.word_list)
            app.root.switch_to("manage word lists", direction="right")
        elif app.is_premium or len(word_list_names) < 1:
            app.file_manager.word_lists_names.append(name)
            app.file_manager.store_word_list(name, self.word_list)
            app.root.switch_to("manage word lists", direction="right")
        else:
            err_label.text = ("ERROR: You must upgrade to Premium to have more "
                              "than 1 personal list")


    def save(self):
        self.save_popup()

    def on_enter(self, *args, **kwargs):
        super(WordListEditor, self).on_enter(*args, **kwargs)
        self.save_name_input_text = self.list_name #make the default.
        self.build_scroll_word_list()

    def back_to_screen(self):
        if self.popup:
            self.popup.dismiss()
            self.popup = None
        else:
            app.root.switch_to("manage word lists", direction="right")
        return True

class WordListViewerScreen(Screen):
    words_list_view = ObjectProperty(None)
    VIEW_WORDS_LABEL_HEIGHT = "25dp"

    def __init__(self, words_list, switch_to_screen = "manage word lists"):
        super(WordListViewerScreen, self).__init__()
        args_converter = lambda row_index, word: {"text": word,
                                                  "size_hint_y" : None,
                                                  "height" : self.VIEW_WORDS_LABEL_HEIGHT}
        self.list_adapter = ListAdapter(data=words_list,
                                   args_converter=args_converter,
                                   cls=ListItemLabel)
        self.words_list_view.adapter = self.list_adapter
        self.switch_to_screen = switch_to_screen
    def on_enter(self, *args):
        super(WordListViewerScreen, self).on_enter(*args)
        # self.words_list_view.adapter = self.list_adapter

    def back_to_screen(self):
        app.root.switch_to(self.switch_to_screen, direction="right")
        return True

class ChildWatchingBoxLayout(BoxLayout):
    """
    BoxLayout that lets you get a child by a name, if you gave one
    """
    def __init__(self, *args, **kwargs):
        super(ChildWatchingBoxLayout, self).__init__(*args, **kwargs)
        self.child_dic = {}

    #format stolen from pycharm's autofill in feature.
    def add_widget(self, widget, index=0, name=""):
        """
        can pass a name kw, as long as name is not an empty string
        """
        if name:
            self.child_dic[name] = widget
        super(ChildWatchingBoxLayout, self).add_widget(widget, index)

    def get_named_child(self, name):
        return self.child_dic[name]


# class BackButton(Button):
#     def __init__(self, *args, **kwargs):
#         screen = None #switch_to will either be a string or screen
#         if "switch_to" in kwargs:
#             screen = kwargs["switch_to"]
#             del kwargs["switch_to"]
#         super(BackButton, self).__init__(*args, **kwargs)
#         if screen:
#             def switch_to_callback(instance):
#                 app.root.switch_to(screen, direction="right")
#             self.bind(on_release = switch_to_callback)
class BackButton(Button): #EventDispatcher is already subclassed by Button it appears
    """
    switches to another screen that is in screenamangers dict of screens
    """
    switch_to = StringProperty("")
    def __init__(self, *args, **kwargs):
        """
        switch_to is a string that is the screen name you wish to switch to.
        can be initialized with switch_to as a keyword. or can set switch_to
        after initalization. Can not do both.
        """
        self.screen = None
        super(BackButton, self).__init__(*args, text="back", **kwargs)

    def on_switch_to(self, instance, value):
        self.screen = value
        def switch_to_callback(instance):
            app.root.switch_to(self.screen, direction="right")
        self.bind(on_release = switch_to_callback)

class JoinGameScreen(Screen):
    def join_observer(self):
        app.root.switch_to(GameLobbyScreen(observer=True))
    def join(self):
        app.root.switch_to(GameLobbyScreen())
    def back_to_screen(self):
        app.root.switch_to("game chooser", direction="right")
        return True

class MakeWordListFromUrlScreen(Screen):
    pass

class IntermediateScreen(Screen):
    """
    for use with WordListEditor
    """
    word_list_name = StringProperty("None")
    def __init__(self, list_name, on_word_list_name_callback):
        super(IntermediateScreen, self).__init__()
        self.list_name = list_name
        self.on_word_list_name_callback = on_word_list_name_callback
    def on_word_list_name(self, instance, value):
        # def switch_screen_callback(result):
        #     app.root.switch_to(WordListEditor(self.list_name, result), transition=NoTransition())
        # d = app.uplink.root_obj.callRemote("get_word_list", value)
        # d.addCallback(switch_screen_callback)
        self.on_word_list_name_callback(instance, value)
    def on_pre_enter(self, *args):
        super(IntermediateScreen, self).on_pre_enter(*args)
        app.loading_popup()

    def on_leave(self, *args):
        super(IntermediateScreen, self).on_leave(*args)
        app.close_popup()
        #app.root.switch_to(WordListEditor(self.list_name, self.word_list_name))


class MakeWordListScreen(Screen):
    name_text_input = ObjectProperty(None)
    def __init__(self):
        super(MakeWordListScreen, self).__init__()
        self.select_words_list_screen = SelectWordsListScreen
    def make_list_locally(self, list_name, word_list):
        app.root.switch_to(WordListEditor(list_name, word_list))

    def download_from_server(self):
        def on_word_list_name_callback(instance, value):
            print instance, value
            def switch_screen_callback(result):
                app.root.switch_to(WordListEditor("", result), transition=NoTransition())
            d = app.uplink.root_obj.callRemote("get_word_list", value)
            d.addCallback(switch_screen_callback)
        screen = IntermediateScreen(self.name_text_input.text, on_word_list_name_callback)
        select_words_list_screen = SelectWordsListScreen(switch_to_screen=screen)
        select_words_list_screen.back_to_screen = self.back_to_screen
        app.root.switch_to(select_words_list_screen)


    def add_word_list(self, name, url):
        if name == "" and url == "":
            name = "test"
            url = "https://www.dropbox.com/s/jvvh5a3wdwe7k3o/test?dl=1"
        if name == app.file_manager.WORD_LIST_NAMES:
            app.generic_popup("Invalid Name")
        else:
            app.loading_popup()#filemanger is a blocking call.
            word_list = app.file_manager.get_word_list_of_file(url)
            app.close_popup()
            if isinstance(word_list, str):#we had an error
                app.generic_popup(word_list)
            else: #is the words list
                app.file_manager.store_word_list(name, word_list)
                app.root.switch_to("manage word lists", direction="right")

    def back_to_screen(self):
        app.root.switch_to("manage word lists", direction="right")
        return True

class MyScreenManager(ScreenManager):
    def __init__(self, *args, **kwargs):
        super(MyScreenManager, self).__init__(*args, **kwargs)
        #    LoginScreen:
        #    GameChooserScreen:
        #    MakeGameScreen:
        #    SelectWordsListScreen:
        #    JoinGameScreen:
        #    GameLobbyScreen:
        #    GameScreen:
        #    ManageWordListsScreen:
        self.screen_stack = []
        #login_screen = LoginScreen()
        self.switch_to(LoginScreen())
        self.my_screens = {
            #"login": 1,
            "game chooser" : GameChooserScreen(),
            "make game" : MakeGameScreen(),
            "select words list" : SelectWordsListScreen(),
            "join game" : JoinGameScreen(),
            #"game lobby" : GameLobbyScreen(),
            #"game" : GameScreen(),
            "manage word lists" : ManageWordListsScreen(),
            "make word list": MakeWordListScreen(),
            #"word list viewer" : WordListViewerScreen()
            }

    def my_get_screen(self, name):
        return self.my_screens[name]

    def switch_to(self, screen, **options):
        """
        overwriting so I can pass screen name or a screen.
        Set defualt direction to left
        """
        if "direction" not in options:
            options["direction"] = "left"
        if isinstance(screen, str):
            screen = self.my_screens[screen]
        #print "switching to: ",screen, type(screen)
        super(MyScreenManager, self).switch_to(screen, **options)

class PremiumLabel(Label):
    """
    class to be used in kv. If clicked shows
    popup for buying premium
    """
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            app.buy_premium_popup()



if __name__=="__main__":
    app.run()