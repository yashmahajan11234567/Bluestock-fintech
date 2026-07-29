"""
Dashboard pages package for Nifty 100 Analytics.

Each page module exposes a `render()` function that displays the page content.
"""

from src.dashboard.pages._01_home import render as home_render
from src.dashboard.pages._02_profile import render as profile_render
from src.dashboard.pages._03_screener import render as screener_render
from src.dashboard.pages._04_peers import render as peers_render
from src.dashboard.pages._05_trends import render as trends_render
from src.dashboard.pages._06_sectors import render as sectors_render
from src.dashboard.pages._07_capital import render as capital_render
from src.dashboard.pages._08_reports import render as reports_render

# Create module-like objects with render function
class _Module:
    def __init__(self, render_func):
        self.render = render_func

home = _Module(home_render)
profile = _Module(profile_render)
screener = _Module(screener_render)
peers = _Module(peers_render)
trends = _Module(trends_render)
sectors = _Module(sectors_render)
capital = _Module(capital_render)
reports = _Module(reports_render)

__all__ = [
    "home",
    "profile",
    "screener",
    "peers",
    "trends",
    "sectors",
    "capital",
    "reports",
]