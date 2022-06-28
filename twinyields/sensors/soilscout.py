import json
import requests
import pandas as pd
import datetime
from ..import Config

class SoilScoutAPI(object):

    base_url = "https://soilscouts.fi/api/v1"

    def __init__(self, user=None, password=None):
        self.session = requests.Session()
        if user is None:
            self.user = Config.SoilScout.user
            self.password = Config.SoilScout.password
        else:
            self.user = user
            self.password = password
        self.token = None

    def login(self):
        r = self.session.post(self.base_url + "/auth/login/",
            json = {"username" : self.user, "password" : self.password})
        response = r.json()
        if r.status_code != 200:
            raise Exception("Login error!")
        self.token = "Bearer {0}".format(response["access"])

    def devices(self):
        self.login()
        r = self.session.get(self.base_url + "/devices/", headers={'Authorization' : self.token})
        return r.json()

    def measurements(self, since, until, device=None):
        self.login()
        response_data = []
        url = self.base_url + "/measurements/"
        next = url
        params = {'since' : since, 'until' : until}
        if device is not None:
            params['device'] = device
        while next is not None:
            r = self.session.get(next, headers={'Authorization' : self.token},
                params =  params)
            #print(r.status_code)
            #response = r.json()
            try:
                response = json.loads(r.content.decode("utf-8"), object_hook=self.date_hook)
            except:
                print("Exception")
                print(r.content.decode("utf-8"))
                break
            response_data.append(response["results"])
            #rtext = r.content.decode("utf-8")
            #response_data.append(rtext)
            print(".", end = "")
            next = response["next"]
        print()
        return response_data

    def date_hook(self, json_dict):
        for (key, value) in json_dict.items():
            if key == "timestamp":
                try:
                    json_dict[key] = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
                except:
                    try:
                        json_dict[key] = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
                    except:
                        print("Failed to parse both date formats")
                        pass
            return json_dict


