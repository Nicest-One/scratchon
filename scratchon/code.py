import json
import websocket
import re
import requests
import colorama
from colorama import Fore
import threading
import time
import asyncio
import inspect
import os


class Client:
    def __init__(self, username, password, source=None):
        """
        Creates a Scratch Client so you can start connecting to your projects.
        *Note: Your Password and Username are not stored both globally and locally!


        :param username: Your Scratch Username
        :param password: Your Scratch Password
        :Param source: Normally set this param to __file__ to allow suggested lines

        :return: None
        :rtype: Undefined
        """
        colorama.init()
        self.sessionID = None
        self.discord_link = "https://discord.gg/tF7j7MswUS"

        self.username = username
        self.password = password
        self.source = source
        self.meta = None

        self.headers = {
            "x-csrftoken": "a",
            "x-requested-with": "XMLHttpRequest",
            "Cookie": "scratchcsrftoken=a;scratchlanguage=en;",
            "referer": "https://scratch.mit.edu",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"
        }
        try:

            self.data = json.dumps({
                "username": self.username,
                "password": self.password
            })

            request = requests.post(
                'https://scratch.mit.edu/login/', data=self.data, headers=self.headers)

            self.sessionId = re.search(
                '\"(.*)\"', request.headers['Set-Cookie']).group()

            self.token = request.json()[0]["token"]

            self.headers = {
                "x-requested-with": "XMLHttpRequest",
                "Cookie": "scratchlanguage=en;permissions=%7B%7D;",
                "referer": "https://scratch.mit.edu",
            }

            self.request = requests.get(
                "https://scratch.mit.edu/csrf_token/", headers=self.headers)

            self.csrftoken = re.search(
                "scratchcsrftoken=(.*?);", request.headers["Set-Cookie"]
            ).group(1)

        except AttributeError as error:
            if source != None:
                self.error_proxy = error

                self.file = open(self.source, "r", encoding='UTF-8')
                self.line = ""
                self.count = 0
                for i in self.file:
                    self.count += 1
                    if 'client' in i.lower():
                        self.line = i
                        break

                self.message = f"{Fore.RED}[scratchon] Invalid Credentials!\n{Fore.YELLOW}  Tip: Double check to make sure your username and password are correct\n {Fore.BLUE} Suggested Line:\n   {Fore.WHITE} Line: {self.count} | {self.line}  {Fore.MAGENTA}Still Having Trouble? Join Our Discord Community: {self.discord_link} {Fore.RESET}"

                print(self.message)
            else:
                self.message = f"{Fore.RED}[scratchon] Invalid Credentials!\n{Fore.YELLOW}  Tip: Double check to make sure your username and password are correct\n {Fore.BLUE} Suggested Line:\n   {Fore.WHITE} Define source in Client() to get suggestions\n    scratchon.Client(source=__file__, ...) {Fore.MAGENTA}Still Having Trouble? Join Our Discord Community: {self.discord_link} {Fore.RESET}"

                print(self.message)

        else:

            self.message = f"{Fore.GREEN}[scratchon] Logged in as: {username}\n{Fore.RESET}  You will be automatically signed out of your scratch account!"
            print(self.message)

            self.headers = {
                "x-csrftoken": self.csrftoken,
                "X-Token": self.token,
                "x-requested-with": "XMLHttpRequest",
                "Cookie": "scratchcsrftoken=" + self.csrftoken + ";scratchlanguage=en;scratchsessionsid=" + self.sessionId + ";",
                "referer": "",

            }

    def manage(self, project_id: int, codec_method=None):
        """
        This is one of the most important methods, as it allows to connect your scratch and python project.

        :param project_id: The id of your scratch project you wish to connect to.
        :return: Project instance
        :rtype: object
        """

        if codec_method != None:
            self.meta = use_file_for_codec(codec_method, self.discord_link)

        try:
            return Manage(project_id, self.sessionId, self.username, self.discord_link, source=self.source, codec_method=self.meta)
        except:
            self.message = f"{Fore.RED}[scratchon] Prior Exception\n{Fore.YELLOW}  Tip: Check to see if any error's occured prior to this message\n {Fore.MAGENTA}Still Having Trouble? Join Our Discord Community: {self.discord_link} {Fore.RESET}"

            print(self.message)


class Variable:
    def __init__(self, last_value, current_value, name, project_owner, project_id, origin):
        """
        A(n) object representing a scratch cloud variable

        :param last_value: Undefined
        :param current_value: Undefined
        :param name: Undefined
        :param project_owner: Undefined
        :param project_id: Undefined
        :param origin: Undefined
        """
        self.last_value = last_value
        self.current_value = current_value
        self.raw_name = name
        self.name = self.raw_name.split('☁ ')[1]
        self.project_owner = project_owner
        self.project_id = project_id
        self.object = origin


def serve_file(path):
    return path


def use_file_for_codec(path, discord_link):
    if os.path.isfile(path):
        file = open(path)
        root = {}
        counter = 0
        for lines in file:
            counter += 1
            if lines != '\n':
                root[lines.replace('\n', '')] = counter
        file.close()
        return CreateCodecClass(root)
    else:
        print(f"{Fore.RED}[scratchon] File Not Served\n{Fore.YELLOW}  Tip: Check to see if the file path is correct\n {Fore.MAGENTA}Still Having Trouble? Join Our Discord Community: {discord_link} {Fore.RESET}")


class CreateCodecClass:
    def __init__(self, root):
        self.root = root
        self.temp = None
        self.letter = None
        self.data = None

    def _encode(self, data):

        self.temp = ""
        for letter in data:
            self.temp += str(self.root[letter])
        return self.temp

    def _decode(self, data):
        self.data = str(data)
        self.temp = ""
        for times in range(0, len(self.data), 2):
            self.letter = self.data[times] + self.data[times + 1]
            self.temp += self.get_key(int(self.letter))
        return self.temp

    def get_key(self, val):
        for key, value in self.root.items():
            if val == value:
                return key


class Manage:
    def __init__(self, project_id, session_id, username, discord_link, source, codec_method):
        """
        A(n) object that represents your scratch project, not meant to be used by the user.


        :param project_id: Undefined
        :param session_id: Undefined
        :param username: Undefined
        :param discord_link: https://discord.gg/tF7j7MswUS
        :param codec_method: Undefined
        """

        self.ws = websocket.WebSocket()
        self.project_id, self.session_id, self.username = project_id, session_id, username
        self.proxy_response = None
        self.websocket_connected = True
        self.proxy_calls = 0
        self.discord_link = discord_link
        self.var_object = None
        self.stats, self.message, self.counter = None, None, 0
        self.source = source
        self.codec_method = codec_method
        self.is_using_codec = codec_method

        self.callback_directory = {}
        self.event_dictionary = ['cloud_update', 'connected', 'tick']
        self.responses = []
        self.cloud_last_values = {}

        self.receive_type = None

        self.ws.connect('wss://clouddata.scratch.mit.edu', cookie='scratchsessionsid=' + self.session_id + ';',
                        origin='https://scratch.mit.edu', enable_multithread=True)

        self.proxy_response = self.ws.send(json.dumps({
            'method': 'handshake',
            'user': self.username,
            'project_id': str(self.project_id)
        }) + '\n')

        def call_scratch_api():
            while self.websocket_connected:
                try:
                    self.response = requests.get("https://clouddata.scratch.mit.edu/logs?projectid=" + str(
                        self.project_id) + "&limit=1" + "&offset=0").json()
                    self.response = self.response[0]
                    self.var_name = self.response['name']
                    self.var_value = self.response['value']
                    self.proxy_calls += 1
                    if self.var_name not in self.cloud_last_values:
                        self.cloud_last_values[self.var_name] = self.var_value

                    if self.cloud_last_values[self.var_name] != self.var_value:
                        if 'cloud_update' in self.callback_directory.keys():
                            self.var_object = Variable(self.cloud_last_values[self.var_name], self.var_value,
                                                       self.var_name, self.username, self.project_id, self)
                            threading.Thread(target=asyncio.run, args=(
                                self.callback_directory['cloud_update'](variable=self.var_object),)).start()
                        self.cloud_last_values[self.var_name] = self.var_value

                    self.responses.append(self.response)
                    time.sleep(0.25)

                    if 'tick' in self.callback_directory.keys():
                        threading.Thread(target=asyncio.run, args=(
                            self.callback_directory['tick'](),)).start()

                    if int(self.proxy_response) == 82:
                        if 'connected' in self.callback_directory.keys() and self.proxy_calls < 2:
                            threading.Thread(target=asyncio.run, args=(
                                self.callback_directory['connected'](),)).start()

                    else:
                        self.file = open(self.source, "r", encoding='UTF-8')
                        self.line = ""
                        self.count = 0
                        for i in self.file:
                            self.count += 1
                            if str(self.project_id) in i.lower():
                                self.line = i
                                break

                        self.message = f"{Fore.RED}[scratchon] Could Not Connect To Project: ID: {self.project_id}\n{Fore.YELLOW}  Tip: Double check to make sure your this project has atleast 1 cloud variable and/or the project id is correct!\n {Fore.BLUE} Suggested Line:\n   {Fore.WHITE} Line: {self.count} | {self.line}  {Fore.MAGENTA}Still Having Trouble? Join Our Discord Community: {self.discord_link} {Fore.RESET}"
                        print(self.message)
                except Exception as error:
                    print(error)
                    self.message = f"{Fore.RED}[scratchon] [502] Too Much Gateway Traffic for Project: ID: {self.project_id}\n{Fore.YELLOW}  We have slowed down requests for 5 seconds to help.\n{Fore.RESET}  Full Traceback: {error}"
                    print(self.message)
                    time.sleep(5)

        self.main_loop = threading.Thread(target=call_scratch_api)
        self.main_loop.start()

    async def stop(self):
        """
        Stops the connection to your scratch project.

        :return: None
        """
        self.websocket_connected = False
        self.ws.close()
        self.stats = await self.get_stats()

        if self.counter < 1:
            self.message = f"{Fore.GREEN}[scratchon] Closed Connection To: {self.stats.title}\n{Fore.RESET}  You will no longer be able to use methods with this project, unless reconnected!"
            print(self.message)
            self.counter += 1
        del self

    def on(self, event):
        """
        This decorator decorates your function so it is called when a event happens within your scratch project.

        :param event: The type of event
        :return: Wrapper
        """

        def wrapper(function):
            if str(event.lower()) in self.event_dictionary:
                self.callback_directory[event.lower()] = function
                if event.lower() == 'cloud_update':
                    funonstring = str(inspect.signature(function))
                    funonstring = funonstring.replace('(', '')
                    funonstring = funonstring.replace(')', '')
                    funonstring = funonstring.replace(' ', '')
                    funonstring = funonstring.split(",")[0]
                    funonstring = funonstring.split(':')
                    self.receive_type = None
                    if len(funonstring) == 1:
                        self.receive_type = object
                    else:
                        if funonstring[1] == 'list':
                            self.receive_type = list
                        elif funonstring[1] == 'object':
                            self.receive_type = object
                        else:
                            print("Wrong Data Format Type!")

            else:
                print('event not found!')

        return wrapper

    async def get_stats(self):
        """
        Gets the stats of your scratch project.

        :return: Project instance
        :rtype: object
        """
        self.proxy_response = requests.get('https://api.scratch.mit.edu/projects/' + str(self.project_id)).json()
        return Project(self.proxy_response)

    async def set_variable(self, variable, value):
        try:
            self.ws.send(json.dumps({
                'method': 'set',
                'name': '☁ ' + variable,
                'value': str(value),
                'user': self.username,
                'project_id': self.project_id
            }) + '\n')
        except BrokenPipeError:
            print('Broken Pipe Error. Connection Lost.')
            self.ws.connect('wss://clouddata.scratch.mit.edu', cookie='scratchsessionsid=' + self.session_id + ';',
                            origin='https://scratch.mit.edu', enable_multithread=True)
            self.ws.send(json.dumps({
                'method': 'handshake',
                'user': self.username,
                'project_id': str(self.project_id)
            }) + '\n')
            print('Re-connected to wss://clouddata.scratch.mit.edu')
            print('Re-sending the data')
            self.ws.send(json.dumps({
                'method': 'set',
                'name': '☁ ' + variable,
                'value': str(value),
                'user': self.username,
                'project_id': self.project_id
            }) + '\n')

    async def get_variable(self, name: str, limit: str = "1000") -> str:
        try:
            resp = requests.get("https://clouddata.scratch.mit.edu/logs?projectid=" +
                                str(self.project_id) + "&limit=" + str(limit) + "&offset=0").json()
            for i in resp:
                x = i['name']
                if x == ('☁ ' + str(name)):
                    return i['value']
        except Exception:
            raise Exception('Cloud variable could not be read.')

    def encode(self, value):
        if self.is_using_codec == None:
            self.message = f"{Fore.RED}[scratchon] No codec_method has been set for Project: ID: {self.project_id}\n{Fore.YELLOW}  Tip: Make sure to serve a file in scratchon.Client().manage()\n{Fore.MAGENTA}  Still Having Trouble? Join Our Discord Community: {self.discord_link} {Fore.RESET}"
            print(self.message)
        else:
            return self.codec_method._encode(value)

    def decode(self, value):
        if self.is_using_codec == None:
            self.message = f"{Fore.RED}[scratchon] No codec_method has been set for Project: ID: {self.project_id}\n{Fore.YELLOW}  Tip: Make sure to serve a file in scratchon.Client().manage()\n{Fore.MAGENTA}  Still Having Trouble? Join Our Discord Community: {self.discord_link} {Fore.RESET}"
            print(self.message)
        else:
            return self.codec_method._decode(value)


class Project:
    def __init__(self, data):
        for key in data:
            setattr(self, key, data[key])
        self.raw = data


def main(myself):
    discord_link = "https://discord.gg/tF7j7MswUS"
    if not isinstance(myself, Client):
        print(f"{Fore.RED}[scratchon] Must run scratchon.main() on scratchon.Client()\n{Fore.YELLOW}  Tip: Check to see if scratchon.Client() is a argument in scratchon.main()\n {Fore.MAGENTA}Still Having Trouble? Join Our Discord Community: {discord_link} {Fore.RESET}")
    else:
        while True:
            pass


# In the works
class ExtensionManager:
    def __init__(self):
        self.extension_manual = None
