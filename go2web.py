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
    url = url.replace("http://", "").replace("https://", "")
    recived_charset = "latin-1"
    recived_data = ""

    try:
        host, path = url.split('/', 1)
    except ValueError:
        host, path = url, ""
    
    socc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socc.connect((host, 80))
    socc.send(f"GET /{path} HTTP/1.1\r\nHost: {host}\r\n\r\n".encode("utf-8"))

    while True:
        data = socc.recv(DATA_PER_REQUEST)
        recived_data += data.decode(recived_charset)

        if len(data) < DATA_PER_REQUEST:
            break
    
    socc.close()

    head_section = recived_data.split("\r\n\r\n", 1)[0]
    headers = {}

    for header in head_section.split("\r\n")[1:]:
        key, value = header.split(": ", 1)
        headers[key] = value
    
    response = {
        "code": recived_data.split("\r\n", 1)[0].split(" ")[1],
        "headers": headers,
    }

    if response["code"] == "200":
        if "text/html" in response["headers"]["Content-Type"]:
            response["body"] = re.search(r"<!DOCTYPE html>.*?</html>", recived_data, re.DOTALL | re.IGNORECASE).group(0)
        elif "text/plain" in response["headers"]["Content-Type"]:
            response["body"] = recived_data.split("\r\n\r\n", 1)[1]
        elif "application/json" in response["headers"]["Content-Type"]:
            response["body"] = json.loads(recived_data.split("\r\n\r\n", 1)[1])

    return response


def google_search(query: str) -> list:
    ...


def main(args: list):
    if len(args) == 0:
        print_help()
        return
    
    if args[0] == '-h':
        print_help()
        return

    if args[0] == '-u':
        print(json.dumps(make_http_request(args[1]), indent=4))
        return
    
    if args[0] == '-s':
        print(json.dumps(google_search(args[1]), indent=4))
        return


if __name__ == '__main__':
    main(sys.argv[1:])
