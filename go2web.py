#!./venv/bin/python3

import bs4
import json
import socket
import ssl
import sys
import os
import re

from time import time


DATA_PER_REQUEST = 1024
MAX_CACHE_SECONDS = 60 * 60 * 24

def print_help():
    print("go2web -u <URL>         # make an HTTP request to the specified URL and print the response")
    print("go2web -s <search-term> # make an HTTP request to search the term using your favorite search engine and print top 10 results")
    print("go2web -h               # show this help")


def make_http_request(url: str) -> str:
    current_time = time()

    if not os.path.exists(f"cache/cache_manager.json"):
        with open(f"cache/cache_manager.json", "w") as file:
            file.write("{}")

    with open(f"cache/cache_manager.json", "r") as file:
        cache_manager = json.loads(file.read())

    if url in cache_manager.keys():
        file_time = cache_manager[url]

        if current_time - file_time < MAX_CACHE_SECONDS:
            with open(f"cache/{file_time}.txt", "r") as file:
                return file.read()
        else:
            os.remove(f"cache/{file_time}.txt")
            del cache_manager[url]

    port = 80

    if url.startswith("https://"):
        port = 443
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)

    recived_charset = "latin-1"
    recived_data = ""

    try:
        host, path = url.replace("http://", "").replace("https://", "").split('/', 1)
    except ValueError:
        host, path = url.replace("http://", "").replace("https://", ""), ""


    if port == 443:
        initial_socc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socc = context.wrap_socket(initial_socc, server_hostname=host)

    else:
        socc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    socc.connect((host, port))
    socc.sendall(f"GET /{path} HTTP/1.1\nHost: {host}\nConnection: close\n\n".encode())

    while True:
        data = socc.recv(DATA_PER_REQUEST)

        if not data:
            break

        recived_data += data.decode(recived_charset)

    recived_data = recived_data.replace("\r\n", "\n")

    socc.close()

    with open(f"cache/{current_time}.txt", "w") as file:
        file.write(recived_data)

    with open(f"cache/cache_manager.json", "w") as file:
        cache_manager[url] = current_time
        file.write(json.dumps(cache_manager, indent=4))

    return recived_data


def parse_request(request: str) -> dict:
    head_section = request.split("\n\n", 1)[0]
    headers = {}

    for header in head_section.split("\n")[1:]:
        key, value = header.split(": ", 1)
        headers[key] = value
    
    response = {
        "code": head_section.split("\n", 1)[0].split(" ")[1],
        "headers": headers,
    }

    if response["code"][0] == '2':
        if "text/html" in response["headers"]["Content-Type"]:
            body = re.search(r"<!DOCTYPE html.*?</html>", request, re.DOTALL | re.IGNORECASE)
            response["body"] = body.group(0) if body else ""
        elif "text/plain" in response["headers"]["Content-Type"]:
            response["body"] = request.split("\n\n", 1)[1]
        elif "application/json" in response["headers"]["Content-Type"]:
            response["body"] = json.loads(request.split("\n\n", 1)[1])

    elif response["code"][0] == '3':
        location = response["headers"]["Location"]
        response = make_http_request(location)
        response = parse_request(response)

    else:
        raise Exception(f"Request failed with status code {response['code']}")

    return response


def parse_body(response: dict) -> str:
    body = response["body"]
    soup = bs4.BeautifulSoup(body, "html.parser")
    text = soup.get_text()

    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n")

    links = soup.find_all("a")
    for link in links:
        text += f"\n{link['href']}"

    # images = soup.find_all("img")

    # for image in images:
    #     if url[-1] == "/":
    #         url = url[:-1]
    #     text += f"\n{url}{image['src']}"

    return text


def keyword_search(query: str) -> list:
    query = query.replace(" ", "+")
    url = f"http://www.duckduckgo.com/html?q={query}&kp=1"
    response = make_http_request(url)
    response = parse_request(response)

    if response["code"][0] != "2":
        raise Exception("Failed to make the request to the search engine.")

    soup = bs4.BeautifulSoup(response["body"], "html.parser")
    html_results = soup.find_all("h2")

    results = []
    for result in html_results:
        title = result.get_text().replace("\n", "").strip()
        search_url = re.search(r"//duckduckgo.com/l/\?uddg=(.*?)&rut=", result.a["href"], re.DOTALL).group(1)
        #parse the % encoded url
        search_url = search_url.replace("%3A", ":").replace("%2F", "/").replace("%3F", "?").replace("%3D", "=").replace("%26", "&")

        results.append({"title": title, "url": search_url})

    return results


def main(args: list):
    if len(args) == 0:
        print_help()

        return

    if args[0] == '-h':
        print_help()

        return

    if args[0] == '-u':
        url = args[1]
        response = make_http_request(url)
        response = parse_request(response)
        # print(json.dumps(response, indent=4))
        print(parse_body(response))

        return

    if args[0] == '-s':
        search_results = keyword_search(" ".join(args[1:]).replace(" ", "+"))

        for result in search_results:
            print(result["title"])
            print(result["url"])
            print()

        return


if __name__ == '__main__':
    main(sys.argv[1:])
