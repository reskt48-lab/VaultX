__version__ = "0.3.0"

from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager

from screens import LoginScreen, RegisterScreen


class LoginPage(Screen):

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(LoginScreen(app))


class RegisterPage(Screen):

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(RegisterScreen(app))


class VaultXApp(App):

    def build(self):
        self.title = "VaultX"

        self.screen_manager = ScreenManager()

        self.login_page = LoginPage(self, name="login")
        self.register_page = RegisterPage(self, name="register")

        self.screen_manager.add_widget(self.login_page)
        self.screen_manager.add_widget(self.register_page)

        return self.screen_manager

    def show_login(self):
        self.screen_manager.current = "login"

    def show_register(self):
        self.screen_manager.current = "register"


if __name__ == "__main__":
    VaultXApp().run()