from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.binding import Binding


class DashboardScreen(Screen):
    def compose(self):
        yield Static("[b]DASHBOARD[/b] — loading...")
        yield Footer()
