"""
A Python script to monitor statuscake ip change and notify to slack
"""
import json
import os
import sys
import time
from distutils.util import strtobool

import requests

# CONFIGURATION

if 'SLACK_WEBHOOK_URL' not in os.environ:
    print("Please set the SLACK_WEBHOOK_URL environ variable")
    sys.exit(1)

# The webhook url
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

# When you first run the script all ips from status cake will be retreived
# This will be used to compare if new ips are configured in the future.
# Should we notify on first ips retreiving or only on change.
NOTIFY_FIRST_RUN = True if 'NOTIFY_FIRST_RUN' not in os.environ else strtobool(
    os.environ.get('NOTIFY_FIRST_RUN'))

# Should we notify if there is a error when retreiving status cake ip
NOTIFY_RETREIVE_ERROR = True if 'NOTIFY_RETREIVE_ERROR' not in os.environ else strtobool(
    os.environ.get('NOTIFY_RETREIVE_ERROR'))

# Number of retreiving error before notifying
RETREIVE_THRESHOLD = 3 if 'RETREIVE_THRESHOLD' not in os.environ else strtobool(
    os.environ.get('RETREIVE_THRESHOLD'))

# Interval beetween 2 check in minute (default 60 (1h))
INTERVAL = 60 if 'INTERVAL' not in os.environ else int(
    os.environ.get('INTERVAL'))

# Number of second between retreival of status cake ip in case of error
INTERVAL_RETREIVE_ERROR = 10 if 'INTERVAL_RETREIVE_ERROR' not in os.environ else int(
    os.environ.get('INTERVAL_RETREIVE_ERROR'))

# Global variables
STATUS_CAKE_IP_URL = "https://app.statuscake.com/Workfloor/Locations.php?format=json"
# List of currenlty knowned ips
IPS = list()
# Count number of retreive error
RETREIVE_ERROR_COUNT = 0


class BadReturnException(Exception):
    """
    Exception should be raise if we are not able to
    retreive status cake ips
    """


def get_ips():
    """
    Return a list of all status cake ip
    """
    global RETREIVE_ERROR_COUNT
    try:
        ips = requests.get(STATUS_CAKE_IP_URL)

        if ips.status_code != 200:
            raise BadReturnException

        return [s[1]['ip'] for s in ips.json().items()]
    except BadReturnException as exp:
        RETREIVE_ERROR_COUNT += 1
        if RETREIVE_ERROR_COUNT >= RETREIVE_THRESHOLD:
            if NOTIFY_RETREIVE_ERROR:
                notify("Unable to retreive status cake ips")
            raise exp
        time.sleep(INTERVAL_RETREIVE_ERROR)
        get_ips()


def initial_populate():
    """
    Initial populate the IPS list
    """
    global IPS
    IPS = get_ips()

    print("List of StatusCake IP : {ips}".format(ips=IPS))

    notify("Statuscake ip monitor has just started")


def notify(message):
    """
    Send a slack message
    """
    global SLACK_WEBHOOK_URL

    slack_data = {'text': message}

    response = requests.post(SLACK_WEBHOOK_URL,
                             data=json.dumps(slack_data),
                             headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s' %
            (response.status_code, response.text))


def check():
    """
    Check if new status cake ip appear and notify
    """
    if len(IPS) == 0:
        initial_populate()

    current_ips = get_ips()
    new_ips = []

    for srv_ip in current_ips:
        if srv_ip not in IPS:
            new_ips.append(srv_ip)
        IPS.append(srv_ip)

    if len(new_ips) > 0:
        notify("New status cake ip detected : {ips}".format(ips=new_ips))


def run():
    """
    Main loop
    """
    initial_populate()

    while True:
        time.sleep(INTERVAL * 60)
        check()


if __name__ == '__main__':
    run()
