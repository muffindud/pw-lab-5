#!./venv/bin/python3

import bs4
import json
import socket
import sys
import re


DATA_PER_REQUEST = 1024


def print_help():
    print("go2web -u <URL>         # make an HTTP request to the specified URL and print the response")
    print("go2web -s <search-term> # make an HTTP request to search the term using your favorite search engine and print top 10 results")
    print("go2web -h               # show this help")


def make_http_request(url: str) -> dict:
    ...


def google_search(query: str) -> list:
    ...


def main(args: list):
    ...


if __name__ == '__main__':
    main(sys.argv[1:])
