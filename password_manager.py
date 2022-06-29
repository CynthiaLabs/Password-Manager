import colorama

from pw_manager.ui import main_screen
from pw_manager.utils import utils


def main():
    colorama.init()
    main_screen.show()
    utils.exit_pw_manager()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        utils.exit_pw_manager()
