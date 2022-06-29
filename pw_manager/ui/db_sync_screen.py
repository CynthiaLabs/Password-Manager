import pathlib
import threading
import subprocess
import json

from pw_manager.utils import utils, decorators, constants
from pw_manager.db_sync import db_sync
from pw_manager.db import Database

from YeetsMenu.menu import Menu, Option
from colorama import Style, Fore
from cryptography.fernet import InvalidToken


@decorators.require_valid_db()
@decorators.require_valid_sync_config()
def upload_current_db():
    event = threading.Event()
    try:
        with open(utils.get_sync_file()) as f:
            data: dict = json.load(f)

        threading.Thread(target=utils.run_spinning_animation_till_event, args=["Uploading file...", event]).start()

        db_sync.sync(db=constants.db_file,
                     action=db_sync.Options.UPLOAD,
                     server=data.get("server"),
                     username=data.get("username"),
                     password=data.get("password"),
                     path=data.get("path"))

    finally:
        event.set()

    utils.clear_screen()
    print(f"{Fore.GREEN}Successfully uploaded the database file!{Style.RESET_ALL}")


@decorators.require_valid_db()
@decorators.require_valid_sync_config()
def download_and_replace_current_db():
    event = threading.Event()
    try:
        with open(utils.get_sync_file()) as f:
            data: dict = json.load(f)

        threading.Thread(target=utils.run_spinning_animation_till_event, args=["Downloading file...", event]).start()

        db_sync.sync(db=constants.db_file,
                     action=db_sync.Options.DOWNLOAD,
                     server=data.get("server"),
                     username=data.get("username"),
                     password=data.get("password"),
                     path=data.get("path"))

    finally:
        event.set()

    utils.clear_screen()
    print(f"{Fore.GREEN}Successfully downloaded the database file!{Style.RESET_ALL}")

    while True:
        password = utils.ask_till_input_secret(f"{Fore.MAGENTA}Password for the database!\n > {Fore.CYAN}")
        utils.reset_style()

        try:
            db: Database = Database(constants.db_file.path, password)

            db.read()

            constants.db_file = db
            break
        except InvalidToken:
            print(f"{Fore.RED}Invalid password!{Style.RESET_ALL}")
            try_again = utils.ask_till_input("Do you want to try again? y/n: ")
            if try_again.lower() == "y":
                continue
            else:
                break

    print(f"{Fore.GREEN}Successfully selected the downloaded database!{Style.RESET_ALL}")


@decorators.catch_ctrl_c
def setup_sync():
    utils.clear_screen()
    utils.print_noice("Setup sync")
    sync_file = pathlib.Path(utils.get_sync_file())

    if sync_file.exists():
        should_overwrite = utils.ask_till_input(f"{Fore.MAGENTA}Are you sure you want to overwrite and re-setup your sync settings? y/N\n > {Fore.CYAN}")
        utils.reset_style()

        if not should_overwrite.lower().strip() == "y":
            print(f"{Fore.RED}Aborting overwrite!{Style.RESET_ALL}")
            return

        print(f"{Fore.GREEN}Overwriting...")

    server = utils.ask_till_input(f"{Fore.MAGENTA}Please enter a server to sync your database with!\n > {Fore.CYAN}").strip()

    event = threading.Event()
    threading.Thread(target=utils.run_spinning_animation_till_event, args=["Running a quick ping to see if the server is reachable!", event]).start()
    process = subprocess.Popen(f"ping -c 2 {server}".split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    exit_code = process.wait(timeout=30)
    event.set()
    utils.clear_screen()

    if exit_code != 0:
        print(f"{Fore.RED}The server \"{server}\" could not be reached!{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}Server could be reached!{Style.RESET_ALL}")
    username = utils.ask_till_input(f"{Fore.MAGENTA}Please enter a username to that server!\n > {Fore.CYAN}").strip()
    password = utils.ask_till_input_secret(f"{Fore.MAGENTA}Please enter the password to that username!\n > {Fore.CYAN}").strip()

    event = threading.Event()
    threading.Thread(target=utils.run_spinning_animation_till_event, args=["Checking if the credentials are working!", event]).start()

    valid = db_sync.check_credentials(server, username, password)

    event.set()
    utils.clear_screen()

    if not valid:
        print(f"{Fore.RED}Credentials are not working!{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}Credentials are working!{Style.RESET_ALL}")

    path = utils.ask_till_input(f"{Fore.MAGENTA}Please enter the path of where the database should be stored on the server! (with the .db ending)\n > {Fore.CYAN}")

    with open(utils.get_sync_file(), "w+") as f:
        data = {
            "server": server,
            "username": username,
            "password": password,
            "path": path
        }

        json.dump(data, f, indent=2)

    print(f"{Fore.GREEN}Configuration successfully saved!{Style.RESET_ALL}")


def show():
    utils.clear_screen()
    menu = Menu(utils.get_noice_text("Database sync"), colors=constants.colors)

    menu.add_selectable(Option("Setup sync", setup_sync))
    menu.add_selectable(Option("Upload current db", upload_current_db))
    menu.add_selectable(Option("Download and replace current db", download_and_replace_current_db))

    menu.run()
