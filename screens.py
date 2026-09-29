from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget


class LoginScreen(BoxLayout):

    def __init__(self, app, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=[dp(24), dp(30)],
            spacing=dp(14),
            **kwargs,
        )

        self.app = app

        self.add_widget(Widget(size_hint_y=0.3))

        title = Label(
            text="WELCOME TO VAULTX",
            font_size=sp(25),
            bold=True,
            size_hint_y=None,
            height=dp(50),
        )

        subtitle = Label(
            text="Login to access your vault",
            font_size=sp(15),
            size_hint_y=None,
            height=dp(35),
        )

        self.email = TextInput(
            hint_text="Email",
            multiline=False,
            size_hint_y=None,
            height=dp(50),
        )

        self.password = TextInput(
            hint_text="Password",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(50),
        )

        login_button = Button(
            text="LOGIN",
            size_hint_y=None,
            height=dp(50),
        )
        login_button.bind(on_press=self.login)

        register_button = Button(
            text="CREATE ACCOUNT",
            size_hint_y=None,
            height=dp(45),
        )
        register_button.bind(on_press=self.register)

        self.message = Label(
            text="",
            font_size=sp(14),
            size_hint_y=None,
            height=dp(35),
        )

        self.add_widget(title)
        self.add_widget(subtitle)
        self.add_widget(self.email)
        self.add_widget(self.password)
        self.add_widget(login_button)
        self.add_widget(register_button)
        self.add_widget(self.message)

        self.add_widget(Widget(size_hint_y=0.5))

    def login(self, instance):
        email = self.email.text.strip()
        password = self.password.text

        if not email or not password:
            self.message.text = "Email dan password wajib diisi."
            return

        self.message.text = "Login lokal berhasil (sementara)."

    def register(self, instance):
        self.app.show_register()


class RegisterScreen(BoxLayout):

    def __init__(self, app, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=[dp(24), dp(30)],
            spacing=dp(14),
            **kwargs,
        )

        self.app = app

        self.add_widget(Widget(size_hint_y=0.2))

        title = Label(
            text="CREATE ACCOUNT",
            font_size=sp(25),
            bold=True,
            size_hint_y=None,
            height=dp(50),
        )

        self.name = TextInput(
            hint_text="Name",
            multiline=False,
            size_hint_y=None,
            height=dp(50),
        )

        self.email = TextInput(
            hint_text="Email",
            multiline=False,
            size_hint_y=None,
            height=dp(50),
        )

        self.password = TextInput(
            hint_text="Password",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(50),
        )

        register_button = Button(
            text="REGISTER",
            size_hint_y=None,
            height=dp(50),
        )
        register_button.bind(on_press=self.create_account)

        back_button = Button(
            text="BACK TO LOGIN",
            size_hint_y=None,
            height=dp(45),
        )
        back_button.bind(on_press=self.back_to_login)

        self.message = Label(
            text="",
            size_hint_y=None,
            height=dp(35),
        )

        self.add_widget(title)
        self.add_widget(self.name)
        self.add_widget(self.email)
        self.add_widget(self.password)
        self.add_widget(register_button)
        self.add_widget(back_button)
        self.add_widget(self.message)

        self.add_widget(Widget(size_hint_y=0.4))

    def create_account(self, instance):
        name = self.name.text.strip()
        email = self.email.text.strip()
        password = self.password.text

        if not name or not email or not password:
            self.message.text = "Semua data wajib diisi."
            return

        self.message.text = "Registrasi lokal berhasil (sementara)."

    def back_to_login(self, instance):
        self.app.show_login()