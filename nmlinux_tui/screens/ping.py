from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.binding import Binding


class PingScreen(Screen):
    BINDINGS = [Binding("escape", "app.switch_screen('dashboard')", "Retour")]

    def compose(self):
        yield Static("[b]PING MONITOR[/b] — loading...")
        yield Footer()
