#!./venv/bin/python3

import bs4
import json
import socket
import sys
import re


DATA_PER_REQUEST = 1024


def print_help():
    ...


def make_http_request(url: str) -> dict:
    ...


def google_search(query: str) -> list:
    ...


def main(args: list):
    ...


if __name__ == '__main__':
    main(sys.argv[1:])
