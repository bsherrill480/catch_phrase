from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, ObservableReferenceList
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup


### TWISTED SETUP
from kivy.support import install_twisted_reactor
install_twisted_reactor()
from twisted.internet import reactor
from twisted.spread import pb
from twisted.internet import defer

class Uplink():
    """
    A class which provides access to the server.
    Must call before before register_evm:
    1) give_username_and_pass
    #recomended do first because give_root_object is usally a deffered
    2) give_root_object with a root object
    """
    def __init__(self, evm):
        """
        Must past ClientEventManager
        """
        self.root_obj = None
        self.evm = evm
        self.username = ""
        self.password = ""

    def post(self, event):
        """
        Posts event to server (server will .notify(event)
        to all clients of event)
        """
        if self.root_obj: #insurance post is not called
            return self.root_obj.callRemote("post", event, self.username)

    def register_evm(self, result):
        """
        takes result so it can be used in deffered
        registers the event manager to server (lets server .notify(event)
        from server of events)
        """
        return self.root_obj.callRemote("register_client", self.evm, self.username)

    def give_username_and_password(self, username, password):
        self.username = username
        self.password = password

    def unregister_evm(self):
        #TODO: GET THIS WORKING
        print "attempting unregister"
        if self.root_obj:
            d = self.root_obj.callRemote("unregister_client", self.username)
            def printer(result):
                print "Succesful unregistering"
            d.addCallback(printer)

    def give_root_obj(self, root_obj):
        """
        root_obj is server's root remotley referencable object.
        """
        self.root_obj = root_obj

###TWISTED SETUP DONE

class ClientEventManager(pb.Root):
    """
    Manages events on client side. Is remotley referencable
    """
    def __init__(self):
        self.listeners = []

    def remote_notify(self, event):
        """
        notifies all local listeners of event. Can be called from server.
        """
        for listener in self.listeners:
            listener.notify(event)

    def register_listener(self, listener):
        """
        registers object as a listener for events
        """
        self.listeners.append(listener)

    def unregister_listener(self, listener):
        """
        unregisters object as a listener for events
        """
        self.listeners.remove(listener)

class CatchPhraseApp(App):
    def build(self):
        self.event_manager = ClientEventManager()
        self.uplink = Uplink(self.event_manager)
        return MyScreenManager()

    def on_stop(self, *args, **kwargs):
        #TODO: UNREGISTER EVM
        super(CatchPhraseApp, self).on_stop(*args, **kwargs)

class LoginScreen(Screen):
    def __init__(self, *args, **kwargs):
        super(LoginScreen, self).__init__(*args, **kwargs)
        self.name = "Login"
        self.factory = pb.PBClientFactory()

    def login(self, username, password, app):
        app.uplink.give_username_and_password(username, password)
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
        def is_user_name_in_use(result):
            if result: #username not in use
                popup.dismiss()
                app.root.current = "game chooser"
            else:
                generic_popup("username in use")
        def connected(result):
            print "connected"
            return result

        d.addCallbacks(connected, failed_to_connect) # change to errback when done debug
        d.addCallback(app.uplink.give_root_obj)
        d.addCallback(app.uplink.register_evm)
        d.addCallback(is_user_name_in_use)

    def logging_in_popup(self):
        # create content and add to the popup
        label = Label(text='logging in...')
        popup = Popup(content=label, auto_dismiss=False, size_hint = (1,.5), title="")
        popup.open()
        return popup


class GameChooserScreen(Screen):
    pass

class SetupScreen(Screen):
    pass

class GameScreen(Screen):
    pass

class MyScreenManager(ScreenManager):
    pass


if __name__=="__main__":
    CatchPhraseApp().run()