from config import cookies, headers, params
import requests
import urllib.parse
import time
import random
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

collections = set()
types = set()
skin_list = {}
skin_info = {}

def get_skin_list():
    return skin_list

def get_skin_info():
    return skin_info

def get_skin_types():
    return types

def get_collections():
    return collections

def fetch_skin_list():
    global skin_list
    time.sleep(random.uniform(0.4, 0.8))
    response = requests.get(
        'https://standoff-2.com/skins.php?command=getNames',
        verify=False
    )
    if response.status_code == 200:
        skin_list = response.json()
        print("skin list updated")
    else:
        print(f"fail to load skin list: {response.status_code}")

def fetch_skin_info():
    global skin_info
    time.sleep(random.uniform(0.4, 0.8))
    response = requests.get(
        'https://standoff-2.com/skins-new.php?command=getModelInfo',
        verify=False
    )
    if response.status_code == 200:
        skin_info = response.json()
        print("skin info updated")
        global collections
        for elem in skin_info:
            collections.add(elem['Collection'])
            types.add(elem['type'])
    else:
        print(f"fail to load skin info: {response.status_code}")

def fetch_prices_by_skin(skin_name):
    params['name'] = skin_name
    encoded_name = urllib.parse.quote(skin_name)
    headers['referer'] = f'https://standoff-2.com/shop/?skin={encoded_name}&rare=all&category=all&collection=all'
    time.sleep(2)
    response = requests.get(
        'https://standoff-2.com/skins-new.php',
        params=params,
        cookies=cookies,
        headers=headers,
        verify=False
    )
    if response.status_code == 200:
        skin_prices = response.json()
        print(f'succesed getting prices from site for {skin_name}')
        return skin_prices
    else:
        print(f'failed to get response from site for {skin_name}: {response.status_code}')
        return []