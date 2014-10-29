from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, ObservableReferenceList, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup


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


class GameChooserScreen(Screen):
    pass

class MakeGameScreen(Screen):
    unique_game_id = ObjectProperty(None)

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