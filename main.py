__version__ = "0.4.0"

from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.popup import Popup
from kivy.uix.label import Label

from screens import LoginScreen, RegisterScreen
from dashboard import DashboardScreen


class LoginPage(Screen):
    pass


class RegisterPage(Screen):
    pass


class DashboardPage(Screen):
    pass


class VaultXApp(App):

    def build(self):
        self.title = "VaultX"

        manager = ScreenManager()

        manager.add_widget(LoginPage(name="login"))
        manager.add_widget(RegisterPage(name="register"))
        manager.add_widget(DashboardPage(name="dashboard"))

        return manager

    def show_login(self):
        self.root.current = "login"

    def show_register(self):
        self.root.current = "register"

    def show_dashboard(self):
        self.root.current = "dashboard"

    def show_message(self, message):
        Popup(
            title="VaultX",
            content=Label(text=message),
            size_hint=(0.8, 0.3),
        ).open()


if __name__ == "__main__":
    VaultXApp().run()