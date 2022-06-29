import os
import sys
import time
import pathlib
import json
import threading
import random

from YeetsMenu.menu import Menu
from YeetsMenu.option import Option
from colorama import Style, Fore
from stdiomask import getpass

from pw_manager.utils import constants


def clear_screen():
    if sys.platform.startswith("win"):
        os.system("cls")

    elif sys.platform.startswith("linux"):
        os.system("clear")


def run_spinning_animation_till_event(message: str, event: threading.Event, sleep_delay: float = 0.2):
    characters = ["-", "\\", "|", "/"]
    current_index = 0
    while not event.is_set():
        clear_screen()
        print(f"{Fore.CYAN}{message} {Fore.MAGENTA}{characters[current_index]}{Style.RESET_ALL}")
        time.sleep(sleep_delay)
        current_index += 1

        if current_index == len(characters):
            current_index = 0


def exit_pw_manager():
    finished_cleanup_event = threading.Event()
    threading.Thread(target=run_spinning_animation_till_event, args=["Shutting down...", finished_cleanup_event]).start()
    # do any cleanup work here
    finished_cleanup_event.set()
    exit(0)


def get_root_folder() -> str:
    return str(pathlib.Path(__file__).parent.parent.parent.absolute())


def get_data_folder():
    return get_root_folder() + "/data"


def get_cache_file():
    return get_data_folder() + "/cache.json"


def get_sync_file():
    return get_data_folder() + "/sync.json"


def ask_till_input(string_to_ask) -> str:
    _input = ""

    while not _input:
        _input = input(string_to_ask)

    return _input.strip()


def ask_till_input_secret(string_to_ask) -> str:
    _input = ""

    while not _input:
        _input = getpass(string_to_ask)

    return _input.strip()


def print_noice(message: str, box_color=Fore.CYAN, text_color=Fore.RED) -> None:
    """
    Prints the supplied string in a box
    :param message: The message to show
    :param box_color: The box color
    :param text_color: The text color
    """

    print(get_noice_text(message, box_color, text_color))


def get_noice_text(message, box_color=Fore.CYAN, text_color=Fore.RED):
    """
    Returns the supplied string in a box
    :param message: The message to show
    :param box_color: The box color
    :param text_color: The text color
    """
    top_len = len(message) + (3 * 2)

    space_before = int(top_len / 2 - len(message) - 2)

    space_after = int(top_len - space_before - len(message) - 4)

    while (space_after + space_before) > top_len:
        if space_after > 0:
            space_after -= 1

        elif space_before > 0:
            space_before -= 1

        else:
            break

    while space_after > space_before:
        space_after -= 1
        space_before += 1

    while space_before > space_after:
        space_before -= 1
        space_after += 1

    string = ""
    string += f"{box_color}{top_len * '-'}{Style.RESET_ALL}" + "\n"
    string += f"{box_color}| {space_before * ' '}{text_color}{message}{space_after * ' '} {box_color}|" + "\n"
    string += f"{box_color}{top_len * '-'}{Style.RESET_ALL}"

    return string


def add_db_path_to_cache(path: str) -> bool:
    """
    Adds a path to the cache file
    :param path: Path to add
    :return: If the adding was successful or not
    """
    data_folder = get_data_folder()

    if not os.path.exists(data_folder):
        os.mkdir(data_folder)

    if not os.path.exists(get_cache_file()):
        with open(get_cache_file(), "w+") as f:
            f.write("{}")

    with open(get_cache_file()) as f:
        content: dict = json.load(f)

    for value in content.values():
        if value == path:
            return False

    content[len(content.keys()) + 1] = path

    with open(get_cache_file(), "w") as f:
        json.dump(content, f, indent=2)

    return True


def reset_style():
    print(Style.RESET_ALL, end='')


def enter_confirmation():
    input(f"{Fore.CYAN}Press enter to continue...{Style.RESET_ALL}")


def generate_password(length: int, chars_to_use: list[str]) -> str:
    password = ""
    for i in range(length):
        password += random.choice(random.choice(chars_to_use))

    return password


def get_entry(title: str, func_to_run, skip_enter_confirmation: bool = True):
    while True:
        clear_screen()
        print_noice(title)

        db = constants.db_file

        entries: list = db.get_all_entries()

        entries.sort()

        i: int = 1

        print(f"{constants.colors[0]}0{constants.colors[1]}) {Fore.CYAN}Exit this menu{Style.RESET_ALL}")

        for entry in entries:
            print(f"{constants.colors[0]}{i}{constants.colors[1]}) {constants.colors[0] if i % 2 == 0 else constants.colors[1]}{entry.website_or_usage}{Style.RESET_ALL}")
            i += 1

        print()
        user_input = ask_till_input(f"{Fore.MAGENTA}Enter a number or a term to search for\n > {Fore.CYAN}")
        reset_style()

        is_number: bool = False

        try:
            user_input = int(user_input)
            is_number = True
        except ValueError:
            pass

        if is_number:
            if user_input == 0:
                return

            if user_input > len(entries):
                print(f"{Fore.RED}The number is greater than the number of entries!{Style.RESET_ALL}")
                continue

            selected_entry = entries[user_input - 1]

            func_to_run(selected_entry)

        else:
            result_list = []

            for entry in entries:

                if user_input.lower() in entry.website_or_usage.lower():
                    result_list.append(entry)

                elif user_input.lower() in entry.username.lower():
                    result_list.append(entry)

                elif user_input.lower() in entry.description.lower():
                    result_list.append(entry)

                elif user_input.lower() in entry.password.lower():
                    result_list.append(entry)

            menu = Menu(get_noice_text(f"Search result for \"{user_input}\""), colors=constants.colors)

            for entry in result_list:
                menu.add_selectable(Option(entry.website_or_usage, func_to_run, entry, skip_enter_confirmation=skip_enter_confirmation))

            menu.run()
