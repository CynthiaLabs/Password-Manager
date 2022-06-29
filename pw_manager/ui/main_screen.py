from YeetsMenu.menu import Menu
from YeetsMenu.option import Option

from pw_manager.ui import database_screen, password_screen
from pw_manager.utils import utils, constants


def show():
    menu = Menu(utils.get_noice_text("Password manager V2"), colors=constants.colors)

    menu.add_selectable(Option("Database menu", database_screen.show, skip_enter_confirmation=True))
    menu.add_selectable(Option("Password menu", password_screen.show, skip_enter_confirmation=True))

    menu.run()
