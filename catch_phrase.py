import events as e
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListItemButton, ListView, ListItemLabel
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
import urllib2
from kivy.uix.scrollview import ScrollView
from kivy.storage.jsonstore import JsonStore
### TWISTED SETUP
from kivy.support import install_twisted_reactor
install_twisted_reactor()
from twisted_stuff import Uplink, ClientEventManager, reactor, pb
###/TWISTED SETUP

#notes:
#-never name something an empty string, code relies often on emtpy string
#refering to a null value
#-I initially had kv lang initializing all my screens and a lot of stuff
#as a result I have lots of *args, **kwargs for __init__, however
#after refactoring I didn't end up making then in kv, but my methods
#still do *args, **kwargs even though now I know it's unnecesary.
#I should go back and refactor this. TODO: refactor that
class FileManager:
    """
    manages files
    """
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
        if file_size > 100000:
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

    def generic_popup(self, message):
        """
        closes popup if there is one open. Makes new popup with a close button
        and the passed message.
        """
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

    def buy_premium_popup(self):
        self.generic_popup("BUY PREMIUM!")
#added so all code should have access to app
app = CatchPhraseApp()


class LoginScreen(Screen):
    def __init__(self, *args, **kwargs):
        super(LoginScreen, self).__init__(*args, **kwargs)
        self.name = "Login"
        self.factory = pb.PBClientFactory()
        print app.get_application_config()
    def login(self, nickname, password):
        """
        attempts to login to server. displays loading popup until
        logged in. Displays failed to connect popup if unable to
        connect
        """
        app.uplink.give_nickname_and_password(nickname, password)
        app.loading_popup(message="Logging in...")
        reactor.connectTCP("localhost", 8800, self.factory)
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

class SelectWordsListScreen(Screen):
    """
    Screen for choosing list of words in MakeGameScreen
    """

    def __init__(self, *args, **kwargs):
        super(SelectWordsListScreen, self).__init__(*args, **kwargs)
        self.name = "select words list"

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
                app.root.switch_to("make game", direction="right")
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
    """
    Join Game or Make Game screen.
    """
    def on_enter(self, *args):
        super(GameChooserScreen, self).on_enter(*args)
        app.uplink.root_obj.callRemote("give_list", [str(i) for i in xrange(100000)])


class MakeGameScreen(Screen):
    """
    Screen to select options and make a game
    """
    unique_game_id = ObjectProperty(None)
    word_list_name = StringProperty("No List Selected")

    def get_unique_game_id(self):
        """
        ask server for a game id. Technically not unique, as a user could choose
        to make a game in the format of the unqiue_game_id". Format is
        "Game" + str(total_number_of_games_ever_made)
        """
        def set_game_id(result):
            self.unique_game_id.text = result
        d = app.uplink.root_obj.callRemote("get_unique_game_id")
        d.addCallback(set_game_id)

    def make_and_join_game(self):
        if self.word_list_name != "No List Selected":
            def was_success(result):
                if result:
                    join_screen = app.root.my_get_screen("join game")
                    join_screen.game_name_input.text = self.unique_game_id.text
                    app.root.switch_to("game lobby")
                else:
                    app.generic_popup("Game Name Taken")
            d = app.uplink.root_obj.callRemote("make_game_lobby",
                            self.unique_game_id.text, self.word_list_name)
            d.addCallback(was_success)
        else:
            app.generic_popup("Please Select List")

class GameLobbyScreen(Screen):
    """
    screen before game starts. Users need to input who they will pass the device
    to.
    """
    view_label = ObjectProperty(None)
    view_list = ObjectProperty(None)
    pointing_to = ObjectProperty(None)#List of buttons of players who can be point to
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
        self.pointing_at = None # who user is pointing to
        self.waiting_label = Label(text="Waiting On:")
        self.selected_client = Selected()
        self.waiting_is_empty = False

    def submit_start_game_request(self):
        if self.waiting_is_empty:
            app.lobby.callRemote("notify", e.StartGameRequestEvent())

    def on_pre_enter(self, *args, **kwargs):
        join_screen = app.root.my_get_screen("join game")
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
                app.root.switch_to("join game", direction="right")
            return result
        d.addCallback(was_success)

    def submit_point_at(self):
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
            self.view_list.adapter = ListAdapter(
                data = ["Error In Ordering", "Current Cycles:"] + event.print_out_list,
                cls = ListItemLabel)
        elif isinstance(event, e.GameStartEvent):
            app.root.switch_to("game")

    def on_leave(self, *args, **kwargs):
        super(GameLobbyScreen, self).on_leave(*args, **kwargs)
        app.event_manager.unregister_listener(self)

#for some reason it does not allow "GameScreen" somehow conficts with MakeGameScreen?
class GameScreen(Screen):
    players_turn_label = ObjectProperty(None)
    word_label = ObjectProperty(None)
    bottom_buttons = ObjectProperty(None)
    time_label = ObjectProperty(None)
    scores_label = ObjectProperty(None)
    def __init__(self, *args, **kwargs):
        super(GameScreen, self).__init__(*args, **kwargs)
        self.start_round_button = Button(text="Start Round")
        self.start_round_button.bind(on_release=self.post_round_start_event)
        self.word_guessed_button = Button(text="Someone Guess Right")
        self.word_guessed_button.bind(on_release = self.post_end_turn)
        self.quit_button = Button(text="quit")
        self.quit_button.bind(on_release = self.quit)
        self.start_time = 0
        self.turn_time = 0
        self.count_downer = None

    def quit(self, instance):
        """
        used in button
        """
        app.root.switch_to("game chooser")
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
        self.word_label.text = "Not Your Turn"

    def on_enter(self, *args, **kwargs):
        super(GameScreen, self).on_enter(*args, **kwargs)
        self.bottom_buttons.clear_widgets()#playing another game
        self.bottom_buttons.add_widget(self.start_round_button)
        app.event_manager.register_listener(self)


    def notify(self, event):
        if isinstance(event, e.StartRoundEvent):
            self.bottom_buttons.clear_widgets()
        elif isinstance(event, e.EndRoundEvent):
            self.bottom_buttons.clear_widgets()
            self.scores_label.text = event.scores
            self.bottom_buttons.add_widget(self.quit_button)
            self.bottom_buttons.add_widget(self.start_round_button)
        elif isinstance(event, e.BeginTurnEvent):
            self.players_turn_label.text = "Current Turn: " + event.nickname
            if event.client_id == app.uplink.id:
                self.my_turn(event.time_left, event.word)

    def my_turn(self, time_left, word):
        self.bottom_buttons.clear_widgets()
        self.bottom_buttons.add_widget(self.word_guessed_button)
        self.start_time = Clock.get_time()
        self.turn_time = time_left
        self.word_label.text = word
        def count_downer(interval):
            time_remaining  = self.time_remaining()
            self.time_label.text = str(round(time_remaining))
            if time_remaining < 0.0:
                self.post_end_turn(0)#forced to pass some argument
        count_downer(0)#forced to pass some argument
        self.count_downer = count_downer
        Clock.schedule_interval(self.count_downer, 1.0)

    def on_leave(self, *args, **kwargs):
        super(GameScreen, self).on_leave(*args, **kwargs)
        app.event_manager.unregister_listener(self)

class ManageWordListsScreen(Screen):
    list_label = ObjectProperty(None)
    new_list_okay = ObjectProperty(None)
    new_list_not_okay = ObjectProperty(None)
    scroll_view = ObjectProperty(None)
    back_or_new_list = ObjectProperty(None)
    SCROLL_BUTTON_SIZES = 40
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
        args_converter = lambda row_index, word: {"text": word,
                                                  "size_hint_y" : None,
                                                  "height" : 25}
        print words_list
        list_adapter = ListAdapter(data=words_list,
                                   args_converter=args_converter,
                                   cls=ListItemLabel)
        list_view = app.root.my_get_screen('word list viewer').words_list_view
        list_view.adapter = list_adapter
        app.root.switch_to("word list viewer")

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
            layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
            layout.bind(minimum_height=layout.setter('height'))
            for list_name in word_list_names:
                #setup
                row = ChildWatchingBoxLayout(size_hint_y = None)
                label = Label(text=list_name, size_hint_x=(1.0-3*.125), size_hint_y = None,
                              height = self.SCROLL_BUTTON_SIZES)
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

        #add make new_list_button

        self.back_or_new_list.clear_widgets()
        self.back_or_new_list.add_widget(BackButton(switch_to="game chooser"))
        if (not app.is_premium) and len(app.file_manager.word_lists_names) >= 1:
            self.back_or_new_list.add_widget(self.new_list_not_okay)
        else:
            self.back_or_new_list.add_widget(self.new_list_okay)
        app.close_popup()#close loading popup


    def on_enter(self, *args, **kwargs):
        #TODO: refactor so that all I am doing is the rows and col. Put rest in kv lang
        #TODO: like word_list_editor
        super(ManageWordListsScreen, self).on_enter(*args,**kwargs)
        self.build_screen()
class WordListEditor(Screen):
    #needs view of words, add word, save name and note that if save_name =
    scroll_view = ObjectProperty(None)
    save_name_input = ObjectProperty(None)
    new_word_input = ObjectProperty(None)
    ROW_BUTTON_SIZES = 25
    def __init__(self,list_name, word_list):
        super(WordListEditor, self).__init__()
        self.word_list = list(word_list) # don't want to change list unless we save!
        self.list_name = list_name

    def add_word(self, word):
        if not word:
            app.generic_popup("No empty words")
        elif word in self.word_list:
            app.generic_popup("word already in list")
        else:
            self.word_list.append(word)
            self.new_word_input.text = ""
            app.loading_popup()
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
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        for word in self.word_list:
            row = ChildWatchingBoxLayout(size_hint_y = None)
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
        app.close_popup()

    def save(self):
        name = self.save_name_input.text
        word_list_names = app.file_manager.word_lists_names
        print name
        print word_list_names
        print name in word_list_names
        if not name:
            app.generic_popup("can not have empty name")
        elif name in word_list_names:
            app.file_manager.store_word_list(name, self.word_list)
            app.root.switch_to("manage word lists", direction="right")
        elif app.is_premium or len(word_list_names) < 1:
            app.file_manager.word_lists_names.append(name)
            app.file_manager.store_word_list(name, self.word_list)
            app.root.switch_to("manage word lists", direction="right")
        else:
            app.generic_popup("You must upgrade to Premium to have more "
                              "than 1 personal list")

    def on_enter(self, *args, **kwargs):
        super(WordListEditor, self).on_enter(*args, **kwargs)
        self.save_name_input.text = self.list_name #make the default.
        self.build_scroll_word_list()

class WordListViewerScreen(Screen):
    words_list_view = ObjectProperty(None)

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
    pass

class MakeWordListScreen(Screen):
    def make_list_locally(self, list_name, word_list):
        app.root.switch_to(WordListEditor(list_name, word_list))
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
        login_screen = LoginScreen()
        self.switch_to(login_screen)
        self.my_screens = {
            "login": 1,
            "game chooser" : GameChooserScreen(),
            "make game" : MakeGameScreen(),
            "select words list" : SelectWordsListScreen(),
            "join game" : JoinGameScreen(),
            "game lobby" : GameLobbyScreen(),
            "game" : GameScreen(),
            "manage word lists" : ManageWordListsScreen(),
            "make word list": MakeWordListScreen(),
            "word list viewer" : WordListViewerScreen()
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