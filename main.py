__version__ = "0.1.0"

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label


class VaultXApp(App):

    def build(self):
        self.title = "VaultX"

        root = BoxLayout(
            orientation="vertical",
            padding=dp(24),
            spacing=dp(16),
        )

        title = Label(
            text="VAULTX",
            font_size="28sp",
            bold=True,
            size_hint_y=None,
            height=dp(50),
        )

        subtitle = Label(
            text="Secure your accounts. Keep control.",
            font_size="16sp",
            size_hint_y=None,
            height=dp(40),
        )

        button = Button(
            text="GET STARTED",
            font_size="16sp",
            size_hint_y=None,
            height=dp(50),
        )

        root.add_widget(title)
        root.add_widget(subtitle)
        root.add_widget(button)

        return root


if __name__ == "__main__":
    VaultXApp().run()