"""
⣞⢽⢪⢣⢣⢣⢫⡺⡵⣝⡮⣗⢷⢽⢽⢽⣮⡷⡽⣜⣜⢮⢺⣜⢷⢽⢝⡽⣝
⠸⡸⠜⠕⠕⠁⢁⢇⢏⢽⢺⣪⡳⡝⣎⣏⢯⢞⡿⣟⣷⣳⢯⡷⣽⢽⢯⣳⣫⠇
⠀⠀⢀⢀⢄⢬⢪⡪⡎⣆⡈⠚⠜⠕⠇⠗⠝⢕⢯⢫⣞⣯⣿⣻⡽⣏⢗⣗⠏⠀
⠀⠪⡪⡪⣪⢪⢺⢸⢢⢓⢆⢤⢀⠀⠀⠀⠀⠈⢊⢞⡾⣿⡯⣏⢮⠷⠁⠀⠀
⠀⠀⠀⠈⠊⠆⡃⠕⢕⢇⢇⢇⢇⢇⢏⢎⢎⢆⢄⠀⢑⣽⣿⢝⠲⠉⠀⠀⠀⠀
⠀⠀⠀⠀⠀⡿⠂⠠⠀⡇⢇⠕⢈⣀⠀⠁⠡⠣⡣⡫⣂⣿⠯⢪⠰⠂⠀⠀⠀⠀
⠀⠀⠀⠀⡦⡙⡂⢀⢤⢣⠣⡈⣾⡃⠠⠄⠀⡄⢱⣌⣶⢏⢊⠂⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢝⡲⣜⡮⡏⢎⢌⢂⠙⠢⠐⢀⢘⢵⣽⣿⡿⠁⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠨⣺⡺⡕⡕⡱⡑⡆⡕⡅⡕⡜⡼⢽⡻⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣼⣳⣫⣾⣵⣗⡵⡱⡡⢣⢑⢕⢜⢕⡝⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣴⣿⣾⣿⣿⣿⡿⡽⡑⢌⠪⡢⡣⣣⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⡟⡾⣿⢿⢿⢵⣽⣾⣼⣘⢸⢸⣞⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠁⠇⠡⠩⡫⢿⣝⡻⡮⣒⢽⠋⠀⠀⠀
    
     NO COVERS?
"""


import re
from time import sleep
from urllib.error import HTTPError
from termcolor import colored
from colorama import init
import urllib.request
import os, sys, ssl
import platform

ssl._create_default_https_context = ssl._create_unverified_context
COVERS_URL = "https://raw.githubusercontent.com/xlenore/psx-covers/main/covers/"
VERSION_URL = "https://raw.githubusercontent.com/xlenore/psx-covers/main/DuckStation-cover-downloader/version"
VERSION = 1.1


def path():
    if getattr(sys, "frozen", False):
        path = os.path.dirname(os.path.realpath(sys.executable))
    elif __file__:
        path = os.path.dirname(__file__)
    return path


def check_version():
    try:
        version = urllib.request.urlopen(VERSION_URL)
        if float(version.read().decode("utf-8").replace("\n", "")) != VERSION:
            print("[LOG]:", colored(f"New update available!\n", "green"))
    except:
        pass


def serial_list():  # Get game serial
    with open(
        f'{os.path.join(path(), "cache", "gamelist.cache")}', errors="ignore"
    ) as file:
        regex = re.compile("(\w{4}-\d{5})").findall(file.read())
        serial_list = list(dict.fromkeys(regex))
        print("[LOG]:", colored(f"Found {len(serial_list)} games", "green"))
        if len(serial_list) == 0:
            print("[ERROR]:", colored(f"You have 0 games installed", "red"))
            input()
            quit()
        return serial_list


def existing_covers():
    covers = [
        w.replace(".jpg", "") for w in os.listdir(f'{os.path.join(path(), "covers")}')
    ]

    return covers


def download_covers(serial_list: list):  # Download Covers
    existing_cover = existing_covers()
    for i in range(len(serial_list)):
        game_serial = serial_list[i]
        if game_serial not in existing_cover:
            print("[LOG]:", colored(f"Downloading {game_serial} cover...", "green"))
            try:
                urllib.request.urlretrieve(
                    f"{COVERS_URL}{game_serial}.jpg",
                    f'{os.path.join("covers", "{game_serial}.jpg")}',
                )
                sleep(0.1)
            except HTTPError:
                print(
                    "[WARNING]",
                    colored(f"{game_serial} Not found. Skipping...", "yellow"),
                )
        else:
            print(
                "[WARNING]:",
                colored(
                    f"{game_serial} already exist in \covers. Skipping...", "yellow"
                ),
            )


def set_terminal_title(title):
    if platform.system() == "Windows":
        os.system(f"title {title}")


def run():
    set_terminal_title(f"DuckStation Cover Downloader {VERSION}")
    # check_version()
    download_covers(serial_list())
    print(
        "[LOG]:",
        colored(
            f"Done!, please report Not found | Low quality | Wrong covers in GitHub.",
            "green",
        ),
    )
    input()


init()
run()
