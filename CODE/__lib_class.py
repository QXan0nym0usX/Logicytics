from __future__ import annotations
import argparse
import json
import os
import subprocess
import ctypes
import os.path
import zipfile
from subprocess import CompletedProcess
from pathlib import Path
from __lib_log import Log


class Actions:
    @staticmethod
    def open_file(file: str, use_full_path=False):
        """
        Opens a specified file using its default application in a cross-platform manner.
        Args:
            file (str): The path to the file to be opened.
            use_full_path (bool): Whether to use the full path of the file or not.
        Returns:
            None
        """
        if not file == "":
            if use_full_path:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(current_dir, file)
            else:
                file_path = os.path.realpath(file)
            try:
                subprocess.call(file_path, shell=False)
            except Exception as e:
                print(f"Error opening file: {e}")

    @staticmethod
    def run_command(command: str) -> str:
        """
        Runs a command in a subprocess and returns the output as a string.

        Parameters:
            command (str): The command to be executed.

        Returns:
            CompletedProcess.stdout: The output of the command as a string.
        """
        process = subprocess.run(command, capture_output=True, text=True)
        return process.stdout

    @staticmethod
    def __parse_arguments() -> tuple[argparse.Namespace, argparse.ArgumentParser]:
        """
        A static method used to parse command-line arguments for the Logicytics application.

        It defines various flags that can be used to customize the behavior of the application,
        including options for running in default or minimal mode, unzipping extra files,
        backing up or restoring data, updating from GitHub, and more.

        The method returns a tuple containing the parsed arguments and the argument parser object.

        Returns:
            tuple[argparse.Namespace, argparse.ArgumentParser]: A tuple containing the parsed arguments and the argument parser object.
        """
        # Define the argument parser
        parser = argparse.ArgumentParser(
            description="Logicytics, The most powerful tool for system data analysis."
        )
        # Define Flags
        parser.add_argument(
            "--default", action="store_true", help="Runs Logicytics default"
        )
        parser.add_argument(
            "--minimal",
            action="store_true",
            help="Run Logicytics in minimal mode. Just bare essential scraping",
        )
        parser.add_argument(
            "--unzip-extra",
            action="store_true",
            help="Unzip the extra directory zip File - Use on your own device only -.",
        )
        parser.add_argument(
            "--backup",
            action="store_true",
            help="Backup Logicytics files to the ACCESS/BACKUPS directory - Use on your own device only -.",
        )
        parser.add_argument(
            "--restore",
            action="store_true",
            help="Restore Logicytics files from the ACCESS/BACKUPS directory - Use on your own device only -.",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update Logicytics from GitHub - Use on your own device only -.",
        )
        parser.add_argument(
            "--extra",
            action="store_true",
            help="Open the extra directory for more tools.",
        )
        parser.add_argument(
            "--dev",
            action="store_true",
            help="Run Logicytics developer mod, this is only for people who want to register their contributions "
            "properly. - Use on your own device only -.",
        )
        parser.add_argument(
            "--exe",
            action="store_true",
            help="Run Logicytics using its precompiled exe's, These may be outdated and not the best, use only if the "
            "device doesnt have python installed.",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Runs the Debugger, Will check for any issues, warning etc, useful for debugging and issue reporting",
        )
        parser.add_argument(
            "--modded",
            action="store_true",
            help="Runs the normal Logicytics, as well as any File in the MODS directory, Useful for custom scripts",
        )
        parser.add_argument(
            "--threaded",
            action="store_true",
            help="Runs Logicytics using threads, where it runs in parallel",
        )
        parser.add_argument(
            "--webhook",
            action="store_true",
            help="Execute Flag that will send zip File via webhook",
        )
        parser.add_argument(
            "--reboot",
            action="store_true",
            help="Execute Flag that will reboot the device afterward",
        )
        parser.add_argument(
            "--shutdown",
            action="store_true",
            help="Execute Flag that will shutdown the device afterward",
        )
        return parser.parse_args(), parser

    @staticmethod
    def __exclusivity(args: argparse.Namespace) -> bool:
        """
        Checks if exclusive flags are used in the provided arguments.

        Args:
            args (argparse.Namespace): The arguments to be checked.

        Returns:
            bool: True if exclusive flags are used, False otherwise.
        """
        special_flag_used = False
        if args.reboot or args.shutdown or args.webhook:
            if not (
                args.default or args.threaded or args.modded or args.minimal or args.exe
            ):
                print("Invalid combination of flags.")
                exit(1)
            special_flag_used = True
        return special_flag_used

    @staticmethod
    def __set_flags(args: argparse.Namespace) -> tuple[str, ...]:
        """
        Sets flags based on the provided arguments.

        Args:
            args (argparse.Namespace): The arguments to be checked for flags.

        Returns:
            tuple[str, ...]: A tuple of flag names that are set to True.
        """
        Flags = {key: getattr(args, key) for key in vars(args)}
        true_keys = []
        for key, value in Flags.items():
            if value:
                true_keys.append(key)
                if len(true_keys) == 2:
                    break
        return tuple(true_keys)

    def flags(self) -> tuple[str, ...] | argparse.ArgumentParser:
        """
        Handles the parsing and validation of command-line flags.

        Returns either a tuple of used flag names or an ArgumentParser instance.
        """
        args, parser = self.__parse_arguments()
        special_flag_used = self.__exclusivity(args)

        if not special_flag_used:
            used_flags = [flag for flag in vars(args) if getattr(args, flag)]
            if len(used_flags) > 1:
                print("Only one flag is allowed.")
                exit(1)

        if special_flag_used:
            used_flags = self.__set_flags(args)
            if len(used_flags) > 2:
                print("Invalid combination of flags.")
                exit(1)

        if not tuple(used_flags):
            return parser
        else:
            return tuple(used_flags)

    @staticmethod
    def read_config() -> tuple[str, bool, str, str, list[str]]:
        """
        Reads the configuration from the config.json file.

        Returns:
            A tuple containing the webhook URL, debug mode, version, API key, and a list of current files.
            The types of the returned values are:
                - webhook_url: str
                - debug: bool
                - version: str
                - api_key: str
                - files: list[str]

        Raises:
            FileNotFoundError: If the config.json file is not found.
            SystemExit: If the config.json file has an invalid format.
        """
        try:
            script_dir = Path(__file__).parent.absolute()
            config_path = script_dir / "config.json"
            with open(config_path, "r") as file:
                data = json.load(file)

                webhook_url = data.get("WEBHOOK_URL", "")
                debug = data.get("DEBUG", False)
                version = data.get("VERSION", "2.0.0")
                api_key = data.get("ipgeolocation.io API KEY", "")
                files = data.get("CURRENT_FILES", [])

                if not (
                    isinstance(webhook_url, str)
                    and isinstance(debug, bool)
                    and isinstance(version, str)
                    and isinstance(api_key, str)
                    and isinstance(files, list)
                ):
                    print("Invalid config.json format.")
                    input("Press Enter to exit...")
                    exit(1)

                return webhook_url, debug, version, api_key, files
        except FileNotFoundError:
            print("The config.json File is not found.")
            input("Press Enter to exit...")
            exit(1)

    @staticmethod
    def check_current_files(directory: str) -> list:
        """
        Retrieves a list of files with specific extensions within a specified directory and its subdirectories.

        Args:
            directory (str): The path to the directory to search for files.

        Returns:
            list: A list of file paths with the following extensions: .py, .exe, .ps1, .bat.
        """
        file = []
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith((".py", ".exe", ".ps1", ".bat")):
                    files_path = os.path.join(root, filename)
                    file.append(files_path.removeprefix(".\\"))
        return file

    @staticmethod
    def mkdir():
        """
        Creates the necessary directories for storing logs, backups, and data.

        Returns:
            None
        """
        os.makedirs("../ACCESS/LOGS/", exist_ok=True)
        os.makedirs("../ACCESS/LOGS/DEBUG", exist_ok=True)
        os.makedirs("../ACCESS/BACKUP/", exist_ok=True)
        os.makedirs("../ACCESS/DATA/Hashes", exist_ok=True)
        os.makedirs("../ACCESS/DATA/Zip", exist_ok=True)

    @staticmethod
    def unzip(zip_path: str):
        """
        Unzips a given zip file to a new directory with the same name.

        Args:
            zip_path (str): The path to the zip file to be unzipped.

        Returns:
            None
        """
        # Get the base name of the zip file
        base_name = os.path.splitext(os.path.basename(zip_path))[0]

        # Create a new directory with the same name as the zip file
        output_dir = os.path.join(os.path.dirname(zip_path), base_name)
        os.makedirs(output_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(path=str(output_dir))


class Check:
    def __init__(self):
        """
        Initializes an instance of the class.

        Sets the Actions attribute to an instance of the Actions class.
        """
        self.Actions = Actions()

    @staticmethod
    def admin() -> bool:
        """
        Check if the current user has administrative privileges.

        Returns:
            bool: True if the user is an admin, False otherwise.
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except AttributeError:
            return False

    def uac(self) -> bool:
        """
        Check if User Account Control (UAC) is enabled on the system.

        This function runs a PowerShell command to retrieve the value of the EnableLUA registry key,
        which indicates whether UAC is enabled. It then returns True if UAC is enabled, False otherwise.

        Returns:
            bool: True if UAC is enabled, False otherwise.
        """
        value = self.Actions.run_command(
            r"powershell (Get-ItemProperty HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System).EnableLUA"
        )
        return int(value.strip("\n")) == 1

    @staticmethod
    def sys_internal_zip():
        """
        Extracts the SysInternal_Suite zip file if it exists and is not ignored.

        This function checks if the SysInternal_Suite zip file exists and if it is not ignored.
         If the zip file exists and is not ignored,
         it extracts its contents to the SysInternal_Suite directory.
         If the zip file is ignored, it prints a message indicating that it is skipping the extraction.

        Raises:
            Exception: If there is an error during the extraction process. The error message is printed to the console and the program exits.
        """
        try:
            ignore_file = os.path.exists("SysInternal_Suite/.sys.ignore")
            zip_file = os.path.exists("SysInternal_Suite/SysInternal_Suite.zip")

            if zip_file and not ignore_file:
                with zipfile.ZipFile(
                    "SysInternal_Suite/SysInternal_Suite.zip"
                ) as zip_ref:
                    zip_ref.extractall("SysInternal_Suite")
                if __name__ == "__main__":
                    Log({"log_level": DEBUG}).debug("SysInternal_Suite zip extracted")

            elif ignore_file:
                if __name__ == "__main__":
                    Log({"log_level": DEBUG}).debug(
                        "Found .sys.ignore file, skipping SysInternal_Suite zip extraction"
                    )

        except Exception as err:
            exit(f"Failed to unzip SysInternal_Suite: {err}")


class Execute:
    @staticmethod
    def get_files(directory: str, file_list: list) -> list:
        """
        Retrieves a list of files in the specified directory that have the specified extensions.
        Parameters:
            directory (str): The path of the directory to search.
            file_list (list): The list to append the filenames to.
        Returns:
            list: The list of filenames with the specified extensions.
        """
        for filename in os.listdir(directory):
            if (
                filename.endswith((".py", ".exe", ".ps1", ".bat"))
                and not filename.startswith("_")
                and filename != "Logicytics.py"
            ):
                file_list.append(filename)
        return file_list

    def file(self, execution_list: list, Index: int):
        # IT IS USED, DO NOT REMOVE
        """
        Executes a file from the execution list at the specified index.
        Parameters:
            Index (int): The index of the file to be executed in the execution list.
            execution_list (list): List to use when indexing
        Returns:
            None
        """
        self.execute_script(execution_list[Index])
        if __name__ == "__main__":
            Log().info(f"{execution_list[Index]} executed")

    def execute_script(self, script: str):
        """
        Executes a script file and handles its output based on the file extension.
        Parameters:
            script (str): The path of the script file to be executed.
        """
        if script.endswith(".ps1"):
            self.__unblock_ps1_script(script)
            self.__run_other_script(script)
        elif script.endswith(".py"):
            self.__run_python_script(script)
        else:
            self.__run_other_script(script)

    @staticmethod
    def __unblock_ps1_script(script: str):
        """
        Unblocks and runs a PowerShell (.ps1) script.
        Parameters:
            script (str): The path of the PowerShell script.
        Returns:
            None
        """
        try:
            unblock_command = f'powershell.exe -Command "Unblock-File -Path {script}"'
            subprocess.run(unblock_command, shell=False, check=True)
            if __name__ == "__main__":
                Log().info("PS1 Script unblocked.")
        except Exception as err:
            exit(f"Failed to unblock script: {err}")

    @staticmethod
    def __run_python_script(script: str):
        """
        Runs a Python (.py) script.
        Parameters:
            script (str): The path of the Python script.
        Returns:
            None
        """
        result = subprocess.Popen(
            ["python", script], stdout=subprocess.PIPE
        ).communicate()[0]
        # LEAVE AS PRINT
        print(result.decode())

    @staticmethod
    def __run_other_script(script: str):
        """
        Runs a script with other extensions and logs output based on its content.
        Parameters:
            script (str): The path of the script.
        Returns:
            None
        """

        result = subprocess.run(
            ["powershell.exe", ".\\" + script], capture_output=True, text=True
        )
        lines = result.stdout.splitlines()
        ID = next((line.split(":")[0].strip() for line in lines if ":" in line), None)
        if ID and __name__ == "__main__":
            Log().string(str(lines), ID)


WEBHOOK, DEBUG, VERSION, API_KEY, CURRENT_FILES = Actions.read_config()
