from setup.config import cookies, headers, params
import requests
import urllib.parse
import time
import random


collections = set()
types = set()
skin_list = {}
skin_info = {}

""" GET FUNCTIONS """

def get_skin_list():
    return skin_list

def get_skin_info():
    return skin_info

def get_skin_types():
    return types

def get_collections():
    return collections

""" FETCH FROM SITE """

def fetch_skin_list():
    global skin_list
    time.sleep(random.uniform(0.4, 0.8))
    response = requests.get('https://standoff-2.com/skins-new.php?command=getNames')
    if response.status_code == 200:
        skin_list = response.json()
        # print(skin_list)
        print("skin list updated")
    else:
        print("fail to load skin list")

def fetch_skin_info():
    global skin_info
    time.sleep(random.uniform(0.4, 0.8))
    response = requests.get('https://standoff-2.com/skins-new.php?command=getModelInfo')
    if response.status_code == 200:
        skin_info = response.json()
        # print(skin_info)
        print("skin info updated")
        global collections
        for elem in skin_info:
            collections.add(elem['Collection'])
            types.add(elem['type'])
    else:
        print("fail to load skin info")

def fetch_prices_by_skin(skin_name):
    params['name'] = skin_name
    encoded_name = urllib.parse.quote(skin_name)
    headers['referer'] = f'https://standoff-2.com/shop/?skin={encoded_name}&rare=all&category=all&collection=all'
    time.sleep(2)
    response = requests.get('https://standoff-2.com/skins-new.php', params=params, cookies=cookies, headers=headers)
    if response.status_code == 200:
        skin_prices = response.json()
        print(f'succesed getting prices from site for {skin_name}')
        return skin_prices
    else:
        print(f'failed to get response from site for {skin_name}')

