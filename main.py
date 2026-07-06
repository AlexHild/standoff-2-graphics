import requests
import sqlite3
import urllib.parse
import time
import random

cookies = {
    '_ym_uid': '1775584153167443545',
    '_ym_d': '1775584153',
    '_ym_visorc': 'w',
    '_ym_isad': '2',
}

headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'priority': 'u=1, i',
    'referer': 'https://standoff-2.com/shop/?skin=%22Dia+de+Muertos%22+Knife+Case&type=all&rare=all&category=all&collection=all',
    'sec-ch-ua': '"Not/A)Brand";v="99", "Chromium";v="148"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    # 'cookie': '_ym_uid=1775584153167443545; _ym_d=1775584153; _ym_visorc=w; _ym_isad=2',
}

params = {
    'command': 'getStat',
    'name': '',
}

collections = set()
types = set()
skin_list = {}
skin_info = {}

""" PRINTS """

def print_all_collections():
    print(collections)

def print_all_skin_names_from_list():
    print(skin_list)

def print_all_skin_names_from_info():
    temp = []
    for skin in skin_info:
        temp.append(skin['name'])
    print(temp)

def print_all_skin_infos():
    print(skin_info)

def print_all_skin_types():
    print(types)


""" UPDATES """

def update_skin_list():
    global skin_list
    time.sleep(random.uniform(0.4, 0.8))
    response = requests.get('https://standoff-2.com/skins.php?command=getNames')
    if response.status_code == 200:
        skin_list = response.json()
        # print(skin_list)
        print("skin list updated")
    else:
        print("fail to load skin list")

def update_skin_info():
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



""" CHECKS """

def check_skin_exist_in_db(cursor, skin_name):
    cursor.execute("SELECT skin_name FROM skins WHERE skin_name = ?", (skin_name,))
    # take first
    result = cursor.fetchone()

    if result is None:
        print(f"no such skin in db: {skin_name}")
        return False
    else:
        return True
    
def check_collection_exist_in_site(collection_name, update = True):
    global collections
    if update == True:
        update_skin_info()
    for collection in collections:
        if collection == collection_name:
            return True
    print(f"no such collection: {collection_name}")
    return False

def check_collection_exist_in_db(cursor, collection_name):
    cursor.execute("SELECT collection_name FROM collection_names WHERE collection_name = ?", (collection_name,))
    # take first
    result = cursor.fetchone()

    if result is None:
        print(f"no such collection in db: {collection_name}")
        return False
    else:
        return True

def check_skin_name_exist_in_site(skin_name, update = True):
    global skin_info
    if update == True:
        update_skin_info()
    for skin in skin_info:
        if skin['name'] == skin_name:
            return True
    print(f"no such skin name in site: {skin_name}")
    return False

def check_skin_type_exist_in_db(cursor, skin_type):
    if skin_type == "":
        return True
    cursor.execute("SELECT skin_type FROM skin_types WHERE skin_type = ?", (skin_type,))
    # take first
    result = cursor.fetchone()

    if result is None:
        print(f"no such skin type: {skin_type}")
        return False
    else:
        return True
    
def check_skin_exist_in_site(skin_name, collection_name, skin_type, update = True):
    global skin_info
    if update == True:
        update_skin_info()
    for skin in skin_info:
        if skin['name'] == skin_name:
            if skin['type'] == skin_type and skin['Collection'] == collection_name:
                return True
            else:
                print(f"no such skin in site: {skin_name}, {collection_name}, {skin_type}. Should be: {skin['name']}, {skin['Collection']}, {skin['type']}")
                return False
    print(f"no such skin in site: {skin_name}")
    return False
    

""" ADD NEW ITEM INTO DATABASE """

def add_collection(cursor, collection_name, check = True, update = True):
    if check == True:
        if check_collection_exist_in_site(collection_name, update) == False:
            return
    cursor.execute("INSERT OR IGNORE INTO collection_names(collection_name) VALUES(?)", (collection_name,))

def add_skin_type(cursor, skin_type):
    cursor.execute("INSERT OR IGNORE INTO skin_types(skin_type) VALUES(?)", (skin_type,))

def add_skin(cursor, skin_name, collection_name, skin_type, check = True, update = True):
    if check == True:
        if check_skin_exist_in_db(cursor, skin_name) == True:
            print(f"{skin_name} already exist in db")
            return
        if check_skin_type_exist_in_db(cursor, skin_type) == False:
            return
        if check_collection_exist_in_db(cursor, collection_name) == False:
            return
        if check_skin_name_exist_in_site(skin_name, update) == False:
            return
        if check_collection_exist_in_site(collection_name, update) == False:
            return
        if check_skin_exist_in_site(skin_name, collection_name, skin_type, update) == False:
            return
    if skin_type == '':
        skin_type = None
    cursor.execute("INSERT INTO skins(skin_name, collection_name, skin_type) VALUES(?, ?, ?)", (skin_name, collection_name, skin_type))
    print(f'skin added to db: {skin_name}')

def add_all_collections(cursor):
    global collections
    update_skin_info()
    # print_all_collections()
    for collection in collections:
        add_collection(cursor, collection, check = False, update = False)
    print("all collection added")

def add_all_types(cursor):
    global types
    update_skin_info()
    # print_all_skin_types()
    for type in types:
        if type != '':
            add_skin_type(cursor, type)
    print("all types added")

def add_skins_by_collection(cursor, collection_name, update = True):
    if update == True:
        update_skin_info()
    if check_collection_exist_in_db(cursor, collection_name) == False:
        return
    if check_collection_exist_in_site(collection_name, update = False) == False:
        return
    global skin_info
    for skin in skin_info:
        if skin['Collection'] == collection_name:
            add_skin(cursor, skin['name'], collection_name, skin['type'], check = True, update = False)
    print(f'skins of collection {collection_name} added')


""" UPDATE PRICES """

def record_skin_price(cursor, skin_name, skin_price, recorded_at, check = True):
    if check == True:
        if check_skin_exist_in_db(cursor, skin_name) == False:
            return
    cursor.execute("INSERT OR IGNORE INTO skin_prices(skin_name, skin_price, recorded_at) VALUES(?, ?, ?)", (skin_name, skin_price, recorded_at))

def record_skin_prices_history(cursor, skin_name):
    if check_skin_exist_in_db(cursor, skin_name) == False:
            return
    params['name'] = skin_name
    encoded_name = urllib.parse.quote(skin_name)
    headers['referer'] = f'https://standoff-2.com/shop/?skin={encoded_name}&rare=all&category=all&collection=all'
    time.sleep(2)
    response = requests.get('https://standoff-2.com/skins-new.php', params=params, cookies=cookies, headers=headers)
    if response.status_code == 200:
        skin_prices = response.json()
        print(f'prices will be added for {skin_name}')
        for price in skin_prices:
            record_skin_price(cursor, price['Name'], price['purchase_price'], price['Date'], check = False)
        print(f'prices are added for {skin_name}')
    else:
        print(f'failed to get response from site for {skin_name}')

def record_skin_prices_from_collection(cursor, collection_name):
    update_skin_info()
    if check_collection_exist_in_db(cursor, collection_name) == False:
        return
    if check_collection_exist_in_site(collection_name, update = False) == False:
        return
    print(f'recording skins from {collection_name}')
    for skin in skin_info:
        if skin['Collection'] == collection_name:
            record_skin_prices_history(cursor, skin['name'])
    
    
        


    

conn = sqlite3.connect("database.db")
cur = conn.cursor()

update_skin_list()
update_skin_info()



add_all_collections(cur)
add_all_types(cur)


prefered_collections = ['Rival', 'Cursed_souls', 'Empire', 'Project_z9', 'Revenge', 'Halloween_2020', 'Sharp', 'Fable', 'Fireborn', 'Scorpion', 'Travelers_bag', 'Nightmare', 'Prey', 'Newyear2020', 'Event5years', 'Space_vision', 'Sunstrike', 'Project_pandora', 'Dynasty', 'Subjectx', 'Chameleon', 'Event4years', 'Reforged', 'Assistance', 'Legends', 'Collaboration', 'Competitive', 'Fun_and_sun', 'Nameless', 'Kitsune_dreams', 'Event2years', 'Hot_winter_party_2023', 'Dragon_rise', 'Frosty_chaos', 'Esports', 'Furious', 'Halloween_2019', 'Revival', 'Origin', 'New_year_2021', 'Outcast', 'Winter_fun_2022']
for collection in prefered_collections:
    add_skins_by_collection(cur, collection, update = False)
    time.sleep(random.uniform(0.4, 0.8))


record_skin_prices_from_collection(cur, 'Rival')

conn.commit()
cur.close()
conn.close()
