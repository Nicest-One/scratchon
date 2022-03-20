import json
import websocket
import re
import requests
import colorama
from colorama import Fore
import threading
import time
import asyncio
import os


class Client:
    def __init__(self, username, password):
        """
        Creates a Scratch Client so you can start connecting to your projects.
        *Note: Your Password and Username are not stored both globally and locally!


        :param username: Your Scratch Username
        :param password: Your Scratch Password

        :return: None
        :rtype: Undefined
        """
        colorama.init()
        self.sessionID = None
        self.discord_link = "https://discord.gg/tF7j7MswUS"

        self.chars = """
            AabBCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789 -_`~!@#$%^&*()+=[];:'"|,.<>/?}{\
        """

        self.username = username
        self.password = password

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
            self.error_proxy = error
            self.file = open(__file__, "r", encoding='UTF-8')
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

            self.message = f"{Fore.GREEN}[scratchon] Logged in as: {username}\n{Fore.RESET}  You will be automatically signed out of your scratch account!"
            print(self.message)

            self.headers = {
                "x-csrftoken": self.csrftoken,
                "X-Token": self.token,
                "x-requested-with": "XMLHttpRequest",
                "Cookie": "scratchcsrftoken=" + self.csrftoken + ";scratchlanguage=en;scratchsessionsid=" + self.sessionId + ";",
                "referer": "",

            }

    def manage(self, project_id: int):
        """
        This is one of the most important methods, as it allows to connect your scratch and python project.

        :param project_id: The id of your scratch project you wish to connect to.
        :return: Project instance
        :rtype: object
        """
        return Manage(project_id, self.sessionId, self.username, self.discord_link)


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



class Manage:
    def __init__(self, project_id, session_id, username, discord_link):
        """
        A(n) object that represents your scratch project


        :param project_id: Undefined
        :param session_id: Undefined
        :param username: Undefined
        :param discord_link: https://discord.gg/tF7j7MswUS
        """

        self.ws = websocket.WebSocket()
        self.project_id, self.session_id, self.username = project_id, session_id, username
        self.proxy_response = None
        self.websocket_connected = True
        self.proxy_calls = 0
        self.discord_link = discord_link
        self.var_object = None
        self.stats, self.message, self.counter = None, None, 0

        self.callback_directory = {}
        self.event_dictionary = ['cloud_update', 'connected']
        self.responses = []
        self.cloud_last_values = {}

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
                    self.response = requests.get("https://clouddata.scratch.mit.edu/logs?projectid=" + str(self.project_id) + "&limit=1" + "&offset=0").json()
                    self.response = self.response[0]
                    self.var_name = self.response['name']
                    self.var_value = self.response['value']
                    self.proxy_calls += 1
                    if self.var_name not in self.cloud_last_values:
                        self.cloud_last_values[self.var_name] = self.var_value

                    if self.cloud_last_values[self.var_name] != self.var_value:
                        if 'cloud_update' in self.callback_directory.keys():
                            self.var_object = Variable(self.cloud_last_values[self.var_name], self.var_value, self.var_name, self.username, self.project_id, self)
                            threading.Thread(target=asyncio.run, args=(
                            self.callback_directory['cloud_update'](variable=self.var_object),)).start()
                        self.cloud_last_values[self.var_name] = self.var_value

                    self.responses.append(self.response)
                    time.sleep(0.25)

                    if int(self.proxy_response) == 82:
                        if 'connected' in self.callback_directory.keys() and self.proxy_calls < 2:
                            threading.Thread(target=asyncio.run, args=(
                                 self.callback_directory['connected'](),)).start()
                    else:
                        self.file = open(__file__, "r", encoding='UTF-8')
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
                    self.message = f"{Fore.RED}[scratchon] [502] To Much Gateway Traffic for Project: ID: {self.project_id}\n{Fore.YELLOW}  We have slowed down requests for 5 seconds to help.\n{Fore.RESET}  Full Traceback: {error}"
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


class Project:
    def __init__(self, data):
        for key in data:
            setattr(self, key, data[key])
        self.raw = data

class ExtensionManager:
    def __init__(self):
        self.extension_manual = None

class Encode:
    def __init__(self, encode_method=None):
        if encode_method == None:
            pass
        else:
            pass

class CodecMethod:
    @staticmethod
    def default():
        char_dict = {
            'a': 10,
            'b': 11,
            'c': 12,
            'd': 13,
            'e': 14,
            'f': 15,
            'g': 16,
            'h': 17,
            'i': 18,
            'j': 19,
            'k': 20,
            'l': 21,
            'm': 22,
            'n': 23,
            'o': 24,
            'p': 25,
            'q': 26,
            'r': 27,
            's': 28,
            't': 29,
            'u': 30,
            'v': 31,
            'w': 32,
            'x': 33,
            'y': 34,
            'z': 35,
            '1': 36,
            '2': 37,
            '3': 38,
            '4': 39,
            '5': 40,
            '6': 41,
            '7': 42,
            '8': 43,
            '9': 44,
            '0': 45,
            '!': 46,
            '@': 47,
            '#': 48,
            '$': 49,
            '%': 50,
            '^': 51,
            '&': 52,
            '*': 53,
            '(': 54,
            ')': 55,
            '{': 56,
            '}': 57,
            '[': 58,
            ']': 59,
            '|': 60,
            ':': 61,
            ';': 62,
            '"': 63,
            '\'': 64,
            '<': 65,
            ',': 66,
            '>': 67,
            '.': 68,
            '?': 69,
            '\\': 70,
            '/': 71,
            '`': 72,
            '~': 73,
            '☁': 74,
            ' ': 75,
            '-': 76,
            '_': 77,
            '+': 78,
            '=': 79,
        }
        return char_dict

    @staticmethod
    def from_file(file_path):
        if os.path.isfile(file_path):
            print(f'using {file_path} as the encoding method!')
        else:
            print('make sure the file path is correct!')
