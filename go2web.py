#!./venv/bin/python3

import bs4
import json
import socket
import ssl
import sys
import re


DATA_PER_REQUEST = 1024


def print_help():
    print("go2web -u <URL>         # make an HTTP request to the specified URL and print the response")
    print("go2web -s <search-term> # make an HTTP request to search the term using your favorite search engine and print top 10 results")
    print("go2web -h               # show this help")


def make_http_request(url: str) -> str:
    port = 80
    
    if url.startswith("https://"):
        port = 443
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)

    url = url.replace("http://", "").replace("https://", "")
    recived_charset = "latin-1"
    recived_data = ""

    try:
        host, path = url.split('/', 1)
    except ValueError:
        host, path = url, ""


    if port == 443:
        initial_socc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socc = context.wrap_socket(initial_socc, server_hostname=host)

    else:
        socc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    socc.connect((host, port))
    socc.sendall(f"GET /{path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())

    while True:
        data = socc.recv(DATA_PER_REQUEST)

        if not data:
            break

        recived_data += data.decode(recived_charset)

    socc.close()

    return recived_data


def parse_request(request: str) -> dict:
    head_section = request.split("\r\n\r\n", 1)[0]
    headers = {}

    for header in head_section.split("\r\n")[1:]:
        key, value = header.split(": ", 1)
        headers[key] = value
    
    response = {
        "code": head_section.split("\r\n", 1)[0].split(" ")[1],
        "headers": headers,
    }

    if response["code"][0] == '2':
        if "text/html" in response["headers"]["Content-Type"]:
            body = re.search(r"<!DOCTYPE html.*?</html>", request, re.DOTALL | re.IGNORECASE)
            response["body"] = body.group(0) if body else ""
        elif "text/plain" in response["headers"]["Content-Type"]:
            response["body"] = request.split("\r\n\r\n", 1)[1]
        elif "application/json" in response["headers"]["Content-Type"]:
            response["body"] = json.loads(request.split("\r\n\r\n", 1)[1])

    elif response["code"][0] == '3':
        location = response["headers"]["Location"]
        response = make_http_request(location)
        response = parse_request(response)

    else:
        raise Exception(f"Request failed with status code {response['code']}")

    return response


def keyword_search(query: str) -> list:
    response = make_http_request(f"http://www.duckduckgo.com/html?q={query}")
    response = parse_request(response)
    print(json.dumps(response, indent=4))

    if response["code"] != "200":
        raise Exception("Failed to make the request to the search engine.")

    soup = bs4.BeautifulSoup(response["body"], "html.parser")
    results = soup.find_all("h3")

    return results


def main(args: list):
    if len(args) == 0:
        print_help()
        return
    
    if args[0] == '-h':
        print_help()
        return

    if args[0] == '-u':
        response = make_http_request(args[1])
        response = parse_request(response)
        print(json.dumps(response["header"], indent=4))
        return
    
    if args[0] == '-s':
        search_results = keyword_search(args[1])
        for result in search_results:
            print(result)
        return


if __name__ == '__main__':
    main(sys.argv[1:])
