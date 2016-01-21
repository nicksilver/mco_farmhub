"""
Created by: Nick Silverman
Institute: Montana State Climate Office
Date: 01/18/16
"""

import requests
import json
from datetime import datetime
import pytz
import pandas as pd
import matplotlib.pyplot as plt


class FarmHub(object):
    """Documentation for FarmHub"""

    def __init__(self, email, password):
        self.email = email
        self.password = password
        payload = {"email": self.email, "password": self.password}
        url = "http://api.farmhub.net/v1/session"
        r = requests.post(url, data=payload)
        self.cookie = r.cookies

    def get_cookie(self):
        """
        Gets cookie from initial login POST

        :return: requests cookie
        """
        return self.cookie

    def list_devices(self):
        """
        GET request for list of activated devices

        :return:  list of devices (dictionary)
        """
        url = "http://api.farmhub.net/v1/devices?include_organization=true"
        r = requests.get(url, cookies=self.cookie)
        data = json.loads(r.text)
        devs = {}
        for i in data:
            devs[i['id']] = {'name': i['name'],
                             'lat': i['lat'],
                             'lng': i['lng'],
                             'inserted_at': i['inserted_at']
                             }
        return devs

    def list_sensors(self):
        """
        GET request for a list of sensors for each activated device
        :return:
        """

        # Get devices from FarmHub method list_devices()
        FH = FarmHub(self.email, self.password)
        devs = FH.list_devices()

        sensors = {}
        for dev_id in devs:
            url = "http://api.farmhub.net/v1/devices/" + str(dev_id) + "/sensors"
            r = requests.get(url, cookies=self.cookie)
            data = json.loads(r.text)
            dev_sensors = {}
            for sensor in data:
                dev_sensors[sensor['id']] = {'name': sensor['sensor_definition']['name'],
                                             'units': sensor['sensor_definition']['units']}
            sensors[dev_id] = dev_sensors
        return sensors

    def get_data(self, device_id, sensor_id, start, stop):
        """
        Retrieves data for specified device, sensor, and time.

        :param device_id: device id from list_devices() (int)

        :param sensor_id: sensor_id from list_sensors() (int)

        :param start: start date and time (datetime object)

        :param stop: end date and time (datetime object)

        :return: specified sensor data from specified time interval (pandas dataframe)
        """

        # Timezone information
        mt = pytz.timezone('US/Pacific')
        utc = pytz.timezone('UTC')

        def getEpoch(naiveDatetime, tz):
            """helper function to convert datetime object to epoch"""
            t = tz.localize(naiveDatetime)
            t0 = utc.localize(datetime(1970, 1, 1))
            return int((t-t0).total_seconds())

        # Convert datetime to epoch
        start = getEpoch(start, mt)
        stop = getEpoch(stop, mt)

        # Make request
        url = "http://api.farmhub.net/v1/devices/" + \
              str(device_id) +"/sensors/" + \
              str(sensor_id) + "/data?from=" + \
              str(start) + "&to=" + str(stop)
        r = requests.get(url, cookies=self.cookie)

        # Give it one more try if there was a server hiccup
        if r.status_code != 200:
            r = requests.get(url, cookies=self.cookie)

        # Get data
        data = pd.DataFrame(json.loads(r.text))

        # Convert values for some sensors
        if sensor_id == 2221:  # soil moisture GS1
            # TODO Which Decagon calibration equation is appropriate?
            data['value'] = 4.94e-4 * data['value'] - 0.554
        elif sensor_id == 2213:  # rain bucket (0.4mm/square meter/click)
            data['value'] *= 0.4
        return data

    def plot_data(self, device_id, sensor_id, start, stop):
        """
        Plots data for specified device, sensor, and time.

        :param device_id: device id from list_devices() (int)

        :param sensor_id: sensor_id from list_sensors() (int)

        :param start: start date and time (datetime object)

        :param stop: end date and time (datetime object)

        :return: time series plot of data
        """

        FH = FarmHub(self.email, self.password)
        data = FH.get_data(device_id, sensor_id, start, stop)
        plt.plot(data['created_at'], data['value'])
        plt.show()