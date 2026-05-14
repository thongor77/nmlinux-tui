from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.binding import Binding


class WifiScreen(Screen):
    BINDINGS = [Binding("escape", "app.switch_screen('dashboard')", "Retour")]

    def compose(self):
        yield Static("[b]WI-FI[/b] — loading...")
        yield Footer()
