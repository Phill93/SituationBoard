import urllib.error

from backend.action.Action import Action
from backend.util.Settings import Settings
from backend.event.SourceEvent import SourceEvent
from backend.event.AlarmEvent import AlarmEvent

from urllib import request, parse
import json


class ActionWebRequest(Action):

    def __init__(self, instanceName: str, settings: Settings):
        super().__init__("web_request", instanceName, settings)
        self.__url = self.getSettingString('url', default='')
        self.__username = self.getSettingString('username', default='')
        self.__password = self.getSettingString('password', default='')
        self.print("Web request action activated!")

    def handleEvent(self, sourceEvent: SourceEvent) -> None:
        if isinstance(sourceEvent, AlarmEvent):
            if self.__url:
                try:
                    if self.__username and self.__password:
                        passman = request.HTTPPasswordMgrWithDefaultRealm()
                        passman.add_password(None, self.__url, self.__username, self.__password)
                        authhandler = request.HTTPBasicAuthHandler(passman)
                        opener = request.build_opener(authhandler)
                        request.install_opener(opener)

                    data = {
                        "alarmTimestamp": sourceEvent.alarmTimestamp,
                        "event": sourceEvent.event
                    }
                    req = request.Request(self.__url, data=parse.urlencode(data).encode())
                    request.urlopen(req)
                    self.print("Web request send to {}!".format(self.__url))
                except urllib.error.URLError:
                    self.print("Url not reachable")
