from os import getcwd, makedirs, rename, remove
from os.path import splitext, basename, isfile
from datetime import datetime
from zipfile import ZipFile

BASE_DIRECTORY = getcwd() + "/logs/"


class logFile():

    def __init__(self, file_path: str) -> None:
        file_name = splitext(basename(file_path))[0]

        self.__file_path = BASE_DIRECTORY + file_name + ".log"
        self.__zip_path = BASE_DIRECTORY + file_name + ".zip"

        self.store_to_zip()  # Store the last log file to the zip

    def log(self, msg: str) -> None:
        """
        The message is logged whit the following format:
        [DD/MM/YYYY HH:MM:SS.MILIS] MSG
        Logs a message to the log file, also creates the log file if it doesn't exist.
        Logs a message to the console.
        """

        msg = datetime.now().strftime('[%d/%m/%Y %H:%M:%S.%f] ') + msg

        print(msg)

        makedirs(BASE_DIRECTORY, exist_ok=True)

        with open(self.__file_path, "a", encoding='utf-8') as file:
            file.write(msg + "\n")

    def store_to_zip(self) -> bool:
        """
        Move the lastest log file to the zip log and
        removes the old log file, also renames the log file
        to the first and last timestamp.

        Returns True if the log file was stored, False otherwise.
        """

        if isfile(self.__file_path):
            with open(self.__file_path, "r") as file:
                lines = file.readlines()

                if len(lines) == 0:
                    return True  # Empty file

                first_line = lines[0]
                last_line = lines[-1]

            index = first_line.find(']')

            if index == -1:
                return False

            stored_name = first_line[1:index]

            if first_line != last_line:
                index = last_line.find(']')

                if index == -1:
                    return False

                stored_name += " - " + last_line[1:index]

            stored_name = stored_name.replace(
                '/', '-').replace(':', '.') + ".log"

            rename(self.__file_path, stored_name)
            ZipFile(self.__zip_path, "a").write(stored_name)
            remove(stored_name)

            return True

        return False
