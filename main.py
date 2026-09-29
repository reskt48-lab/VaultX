__version__ = "0.2.0"

from kivy.app import App
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class VaultXApp(App):

    def build(self):
        self.title = "VaultX"

        root = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(24)],
            spacing=dp(16),
        )

        # Spacer atas
        root.add_widget(Widget(size_hint_y=0.5))

        title = Label(
            text="VAULTX",
            font_size=sp(30),
            bold=True,
            size_hint_y=None,
            height=dp(50),
            halign="center",
            valign="middle",
        )
        title.bind(size=lambda instance, value: setattr(
            instance, "text_size", value
        ))

        subtitle = Label(
            text="Secure your accounts.\nKeep control.",
            font_size=sp(16),
            size_hint_y=None,
            height=dp(60),
            halign="center",
            valign="middle",
        )
        subtitle.bind(size=lambda instance, value: setattr(
            instance, "text_size", value
        ))

        root.add_widget(title)
        root.add_widget(subtitle)

        # Area tombol agar tidak memenuhi layar
        button_container = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(55),
            padding=[dp(10), 0],
        )

        get_started = Button(
            text="GET STARTED",
            font_size=sp(16),
            size_hint=(1, 1),
        )

        button_container.add_widget(get_started)
        root.add_widget(button_container)

        # Spacer bawah
        root.add_widget(Widget(size_hint_y=0.5))

        return root


if __name__ == "__main__":
    VaultXApp().run()