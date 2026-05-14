from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.binding import Binding


class InterfacesScreen(Screen):
    BINDINGS = [Binding("escape", "app.switch_screen('dashboard')", "Retour")]

    def compose(self):
        yield Static("[b]INTERFACES[/b] — loading...")
        yield Footer()
