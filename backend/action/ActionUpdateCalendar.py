# SituationBoard - Alarm Display for Fire Departments
# Copyright (C) 2017-2021 Sebastian Maier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import time

import urllib.request

from backend.action.Action import Action
from backend.util.Settings import Settings
from backend.api.WebSocket import WebSocket

class ActionUpdateCalendar(Action):

    def __init__(self, instanceName: str, settings: Settings, webSocket: WebSocket):
        super().__init__("update_calendar", instanceName, settings)
        self.__webSocket = webSocket
        self.__sourceURL = self.getSettingString("source_url", "")
        self.__destinationURL = self.getSettingFilename("destination_url", "frontend/data/calendar.ics")
        self.__calendarUpdateDuration = self.getSettingInt("calendar_update_duration", 120 * 60) # every 2 hours
        self.__timeout = self.getSettingInt("timeout", 5)

        self.__username = self.getSettingString("username", "")
        self.__password = self.getSettingString("password", "")

        self.__lastUpdateTimestamp = 0.0

        self.print("Updating calendar (initial)")
        self.updateCalendar()

    def handleCyclic(self) -> None:
        if self.__calendarUpdateDuration > 0 and self.__lastUpdateTimestamp > 0:
            nowTimestamp = time.time()
            endTimestamp = self.__lastUpdateTimestamp + self.__calendarUpdateDuration
            if nowTimestamp >= endTimestamp:
                self.print("Updating calendar (periodic)")
                self.updateCalendar()

    def updateCalendar(self) -> None:
        self.__lastUpdateTimestamp = time.time()

        if ActionUpdateCalendar.downloadFile(self.__sourceURL, self.__destinationURL, self.__timeout, self.__username, self.__password):
            self.__webSocket.broadcastCalendarChanged() #TODO: only broadcast change if file (hash) changed
        else:
            self.error("Failed to update calendar")

    @staticmethod
    def downloadFile(fromURL: str, toURL: str, timeout: int, username: str = "", password: str = "") -> bool:
        if not fromURL or not toURL:
            return False

        try:
            if username and password:
                passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                passman.add_password(None, fromURL, username, password)
                authhandler = urllib.request.HTTPBasicAuthHandler(passman)
                opener = urllib.request.build_opener(authhandler)
                urllib.request.install_opener(opener)

            toURLtemp = toURL + ".tmp"
            fIn = urllib.request.urlopen(fromURL, timeout=timeout)
            data = fIn.read()
            with open(toURLtemp, "wb") as fOut:
                fOut.write(data)

            os.rename(toURLtemp, toURL) # atomically overwrite/replace previous file

            return True
        except Exception as e:
            return False
