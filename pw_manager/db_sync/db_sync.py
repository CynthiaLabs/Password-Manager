import pathlib

from pw_manager.db import Database
from pw_manager.utils import utils, errors

import paramiko


class Options:
    UPLOAD = 1
    DOWNLOAD = 2


def check_credentials(server: str, username: str, password: str) -> bool:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname=server, username=username, password=password, port=22)
        return True
    except paramiko.ssh_exception.AuthenticationException:
        return False


def sync(db: Database, action: Options, server: str, username: str, password: str, path: str):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(hostname=server, username=username, password=password, port=22)

    sftp = ssh.open_sftp()

    if action == Options.UPLOAD:
        try:
            sftp.stat(path)
        except FileNotFoundError:
            sftp.mkdir(path.rsplit("/", maxsplit=1)[0])

        sftp.put(db.path, path)

    elif action == Options.DOWNLOAD:
        pathlib.Path(db.path + ".old").unlink(missing_ok=True)

        pathlib.Path(db.path).rename(db.path + ".old")
        sftp.get(path, db.path)

    sftp.close()
    ssh.close()

