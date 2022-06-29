import pathlib
import threading
import traceback
import json

from colorama import Style, Fore
from cryptography.fernet import InvalidToken, Fernet

from YeetsMenu.menu import Menu
from YeetsMenu.option import Option

from pw_manager.utils import utils, constants, decorators, errors
from pw_manager.db import Database
from pw_manager.utils.legacy_encryption import encryptor
from pw_manager.ui import db_sync_screen


@decorators.catch_ctrl_c
def create_database():
    utils.clear_screen()
    utils.print_noice("Database creation")
    print(f"{Fore.MAGENTA}Where should we create the database? If the folder doesn't exist, it will be created. Press ctrl+c to abort the creation.")
    print()

    try:
        path_str = utils.ask_till_input(f"{Fore.MAGENTA}Please enter a folder to store the database!\n > {Fore.CYAN}")
    except KeyboardInterrupt:
        print(f"{Fore.RED}Creation aborted!{Style.RESET_ALL}")
        return

    try:
        file_name = input(f"{Fore.MAGENTA}Please enter a filename. Leave it empty for the default (database.db)\n > {Fore.CYAN}")
    except KeyboardInterrupt:
        print(f"{Fore.RED}Creation aborted!{Style.RESET_ALL}")
        return

    try:
        while True:
            password = utils.ask_till_input_secret(f"{Fore.MAGENTA}Please enter a password for this database!\n > {Fore.CYAN}")
            confirmation_password = utils.ask_till_input_secret(f"{Fore.MAGENTA}Please confirm the password for this database!\n > {Fore.CYAN}")

            if password != confirmation_password:
                yes_no = utils.ask_till_input(f"{Fore.MAGENTA}Passwords don't match! Do you want to try again? y/N\n > {Fore.CYAN}")

                if yes_no.lower() == "n":
                    return

            else:
                break
    except KeyboardInterrupt:
        print(f"{Fore.RED}Creation aborted!{Style.RESET_ALL}")
        return

    utils.reset_style()

    folder = pathlib.Path(path_str)

    if not folder.exists():
        folder.mkdir(parents=True)

    if not file_name:
        file_name = "database.db"

    full_db_path = pathlib.Path(str(folder.absolute()) + "/" + file_name)

    db: Database = Database(str(full_db_path), password)

    done_event = threading.Event()
    try:
        # threading.Thread(target=utils.run_spinning_animation_till_event, args=["Creating database...", done_event]).start()
        db.create()
        done_event.set()
    except errors.DatabaseAlreadyFoundException:
        done_event.set()
        print(f"{Fore.RED}A database already exists at that path!{Style.RESET_ALL}")
        return

    except Exception:
        done_event.set()
        print(f"{Fore.RED}An error has occurred!{Style.RESET_ALL}")
        traceback.print_exc()
        return

    done_event.set()
    print(f"{Fore.GREEN}Successfully created a database at {Fore.CYAN}{str(full_db_path.absolute())}{Fore.GREEN}!\n\n{Fore.MAGENTA}Note: You still have to select the database in order to use it!{Style.RESET_ALL}")


@decorators.catch_ctrl_c
def select_database():
    utils.clear_screen()

    cache_file_path = pathlib.Path(utils.get_cache_file())

    if not cache_file_path.exists():
        print(f"{Fore.MAGENTA}No previously created databases found! You might want to create one or add an already existing one!")
        return

    with open(str(cache_file_path.absolute())) as f:
        cache_file: dict = json.load(f)

    tmp_dict: dict = dict()

    for key, value in cache_file.items():
        if pathlib.Path(value).exists():
            tmp_dict[len(tmp_dict.keys())] = value

    cache_file = tmp_dict

    with open(str(cache_file_path.absolute()), "w") as f:
        json.dump(cache_file, f, indent=2)

    db_selection_menu = Menu(utils.get_noice_text("Which database do you want to use?"), colors=constants.colors)

    def real_select_database(path: str):
        while True:
            utils.clear_screen()
            utils.print_noice(f"Currently selecting database: {path}")

            password = utils.ask_till_input_secret(f"{Fore.MAGENTA}Password for the database: {Fore.CYAN}")
            utils.reset_style()

            try:
                db: Database = Database(path, password)

                db.read()

                constants.db_file = db
                break
            except InvalidToken:
                print(f"{Fore.RED}Invalid password!{Style.RESET_ALL}")
                try_again = utils.ask_till_input("Do you want to try again? y/n: ")
                if try_again.lower() == "y":
                    continue
                else:
                    return

        print(f"{Fore.GREEN}Successfully selected {Fore.MAGENTA}{constants.db_file.path}{Fore.GREEN} as the database!{Style.RESET_ALL}")

    for i in cache_file.values():
        db_selection_menu.add_selectable(Option(f"- {i}", real_select_database, i, return_after_execution=True, skip_enter_confirmation=True))

    db_selection_menu.run()


@decorators.catch_ctrl_c
def add_existing_database():
    utils.print_noice("Add existing database")
    db_path = utils.ask_till_input(f"{Fore.MAGENTA}Please enter the path of the existing database\n > {Fore.CYAN}")
    utils.reset_style()

    db_path = pathlib.Path(db_path)

    if not db_path.exists():
        print(f"{Fore.RED}The directory {Fore.CYAN}{str(db_path.absolute())}{Fore.RED} doesn't exist!")
        return

    if db_path.is_dir() and not db_path.is_file():
        print(f"{Fore.RED}The path has to point to the database file and not a directory!{Style.RESET_ALL}")
        return

    success = utils.add_db_path_to_cache(str(db_path.absolute()))

    if success:
        print(f"{Fore.GREEN}Successfully added path {Fore.CYAN}{str(db_path.absolute())}{Fore.GREEN} to the list of known databases!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to add the path {Fore.CYAN}{str(db_path.absolute())}{Fore.RED} to the list of known databases because it already is an entry!{Style.RESET_ALL}")


@decorators.catch_ctrl_c
@decorators.require_valid_db
def import_v1_database():
    utils.clear_screen()
    utils.print_noice("Import a v1 database")

    print(f"{Fore.MAGENTA}This will import all the entries from the specified database into the currently loaded one!")

    path = utils.ask_till_input(f"{Fore.MAGENTA}Please enter the directory path of the v1 database!\n > {Fore.CYAN}")

    path = pathlib.Path(path)

    if not path.exists():
        print(f"{Fore.RED}That path doesn't exist!{Style.RESET_ALL}")
        return

    if path.is_dir() and not pathlib.Path(str(path.absolute()) + "/database.db").exists():
        print(f"{Fore.RED}That path doesn't have a database.db file!")
        return

    if path.is_file() and path.name == "database.db":
        path = path.parent

    db_password = utils.ask_till_input_secret(f"{Fore.MAGENTA}Enter the password of the v1 database file!\n > {Fore.CYAN}")

    with open(str(path.absolute()) + "/database.db.salt", "rb") as f:
        salt = f.read()

    with open(str(path.absolute()) + "/database.db", "rb") as f:
        data = f.read()

    key, salt = encryptor.generate_key_using_password(db_password, salt)
    fernet = Fernet(key)

    try:
        unencrypted_content = fernet.decrypt(data)
    except InvalidToken:
        print(f"{Fore.RED}Wrong password!{Style.RESET_ALL}")
        return

    event = threading.Event()
    threading.Thread(target=utils.run_spinning_animation_till_event, args=["Importing database...", event]).start()

    json_content: dict = json.loads(unencrypted_content.decode())

    db: Database = constants.db_file

    for key, value in json_content.items():
        website_or_usage = key
        description = value.get("description")
        username = value.get("username")
        password = value.get("password")

        db.add_database_entry(website_or_usage=website_or_usage, description=description, username=username, password=password, should_write=False)

    db.write()

    event.set()


def show():
    utils.clear_screen()

    menu = Menu(utils.get_noice_text("Database menu"), colors=constants.colors)

    menu.add_selectable(Option("Create database", create_database))
    menu.add_selectable(Option("Select database", select_database, return_after_execution=True))
    menu.add_selectable(Option("Add already existing database", add_existing_database))
    menu.add_selectable(Option("Import v1 database", import_v1_database))
    menu.add_selectable(Option("Sync settings", db_sync_screen.show, skip_enter_confirmation=True))

    menu.run()
