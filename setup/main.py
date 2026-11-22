import random
import time
import math
import sqlite3
import api
import filling_skin_data as fd

all_collections = ['Splash', 'Project_z9', 'Rival', 'Hot_winter_party_2023', 'Fable', 'Space_vision', 'Sunstrike', 'Frosty_chaos', 'Vibe', 'Dragon_rise', 'Event5years', 'Winter_fun_2022', 'Rainbow', 'Chameleon', 'Reforged', 'Halloween_2020', 'Assistance', 'Competitive', 'Nightmare', 'Collaboration', 'Revenge', 'Standoff_2', 'Sharp', 'Prey', 'Newyear2020', 'Esports', 'Kitsune_dreams', 'Flow', 'Scorpion', 'Outcast', 'Revival', 'Fun_and_sun', 'Nameless', 'Origin', 'Project_pandora', 'Shine', 'Joy', 'New_year_2021', 'Furious', 'Legends', 'Event2years', 'Halloween_2019', 'Fireborn', 'Subjectx', 'Empire', 'Dynasty', 'Cursed_souls', 'Travelers_bag', 'Event4years']
prefered_collections = ['Rival', 'Empire', 'Revenge', 'Halloween_2020', 'Sharp', 'Fable', 'Fireborn', 'Scorpion', 'Nightmare', 'Prey', 'Newyear2020', 'Space_vision', 'Sunstrike', 'Subjectx', 'Reforged', 'Assistance', 'Competitive', 'Fun_and_sun', 'Kitsune_dreams', 'Event2years', 'Esports', 'Furious', 'Halloween_2019', 'Origin', 'Outcast']

classical_collections = ['Origin', 'Furious', 'Rival', 'Fable', 'Empire', 'Sharp', 'Chameleon', 'Dynasty', 'Revenge', 'Scorpion']
halloween_collections = ['Cursed_souls', 'Halloween_2020', 'Nightmare',  'Project_pandora', 'Subjectx', 'Halloween_2019']
winter_collections = ['Newyear2020', 'Kitsune_dreams', 'Hot_winter_party_2023', 'Frosty_chaos', 'New_year_2021', 'Winter_fun_2022']
summer_collections = ['Legends', 'Sunstrike', 'Fun_and_sun']
autumn_collections = ['Revival', 'Dragon_rise', 'Reforged']

""" PRINTS """

def print_all_collections_from_site():
    print(api.get_collections())

def print_all_skin_names_from_list():
    print(api.get_skin_list())

def print_all_skin_names_from_info():
    temp = []
    for skin in api.get_skin_info():
        temp.append(skin['name'])
    print(temp)

def print_all_skin_infos():
    print(api.get_skin_info())

def print_all_skin_types_from_site():
    print(api.get_skin_types())


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
    
def check_collection_exist_in_site(collection_name):
    for collection in api.get_collections():
        if collection == collection_name:
            return True
    print(f"no such collection in site: {collection_name}")
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

def check_skin_name_exist_in_site(skin_name):
    for skin in api.get_skin_info():
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
    
def check_skin_exist_in_site(skin_name, collection_name, skin_type):
    for skin in api.get_skin_info():
        if skin['name'] == skin_name:
            if skin['type'] == skin_type and skin['Collection'] == collection_name:
                return True
            else:
                print(f"no such skin in site: {skin_name}, {collection_name}, {skin_type}. Should be: {skin['name']}, {skin['Collection']}, {skin['type']}")
                return False
    print(f"no such skin in site: {skin_name}")
    return False

def check_prices_exist_in_db(cursor, skin_name):
    cursor.execute("SELECT * FROM skin_prices WHERE skin_name = ?", (skin_name,))
    if cursor.fetchone() is None:
        return False
    return True 
    

""" ADD NEW ITEM/STATUS INTO DATABASE """

def add_cagr(cursor, skin_name):
    cursor.execute('''
        WITH base AS (
            SELECT
                (julianday(recorded_at)
                 - MIN(julianday(recorded_at)) OVER ()) / 365.25 AS t,
                skin_price
                skin_price
            FROM skin_prices
            WHERE skin_name = ?
              AND skin_price > 0
        ),
        stats AS (
            SELECT
                COUNT(*)                AS n,
                SUM(t)                  AS sum_t,
                SUM(LN(skin_price))     AS sum_y,
                SUM(t * LN(skin_price)) AS sum_ty,
                SUM(t * t)              AS sum_tt
            FROM base
        )
        SELECT
            (n * sum_ty - sum_t * sum_y) / (n * sum_tt - sum_t * sum_t) AS k
        FROM stats
    ''', (skin_name,))

    row = cursor.fetchone()
    if row is None or row[0] is None:
        print("cagr dosen't exist")
        return

    k = row[0]
    cagr = math.exp(k) - 1

    cursor.execute(
        'UPDATE skins SET cagr = ? WHERE skin_name = ?',
        (cagr, skin_name)
    )
    return cagr


def add_collection(cursor, collection_name, check = True):
    if check == True:
        if check_collection_exist_in_site(collection_name) == False:
            return
    cursor.execute("INSERT OR IGNORE INTO collection_names(collection_name) VALUES(?)", (collection_name,))

def add_skin_type(cursor, skin_type):
    cursor.execute("INSERT OR IGNORE INTO skin_types(skin_type) VALUES(?)", (skin_type,))

def add_skin(cursor, skin_name, collection_name, skin_type, check = True):
    if check == True:
        if check_skin_exist_in_db(cursor, skin_name) == True:
            print(f"{skin_name} already exist in db")
            return
        if check_skin_type_exist_in_db(cursor, skin_type) == False:
            return
        if check_collection_exist_in_db(cursor, collection_name) == False:
            return
        if check_skin_name_exist_in_site(skin_name) == False:
            return
        if check_collection_exist_in_site(collection_name) == False:
            return
        if check_skin_exist_in_site(skin_name, collection_name, skin_type) == False:
            return
    if skin_type in (None, ''):
        detected = fd.detect_skin_type(skin_name)
        if detected is None:
            print(f"не удалось определить тип для {skin_name}")
        else:
            skin_type = detected
    if skin_type == '':
        skin_type = None
    is_stat_track = fd.detect_stat_track(skin_name)
    cursor.execute("INSERT INTO skins(skin_name, skin_type, stat_track, cagr, collection_name) VALUES(?, ?, ?, ?, ?)", (skin_name, skin_type, is_stat_track, 'NULL', collection_name))
    print(f'skin added to db: {skin_name}')

def add_all_collections(cursor):
    api.fetch_skin_info()
    # print_all_collections()
    for collection in api.get_collections():
        add_collection(cursor, collection, check = False)
    print("all collection added")

def add_all_types(cursor):
    api.fetch_skin_info()
    # print_all_skin_types()
    for type in api.get_skin_types():
        if type != '':
            add_skin_type(cursor, type)
    for type in fd.types:
        if type != '':
            add_skin_type(cursor, type)
    print("all types added")

def add_skins_by_collection(cursor, collection_name):
    if check_collection_exist_in_db(cursor, collection_name) == False:
        return
    if check_collection_exist_in_site(collection_name) == False:
        return
    for skin in api.get_skin_info():
        if skin['Collection'] == collection_name:
            add_skin(cursor, skin['name'], collection_name, skin['type'], check = True)
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
    if check_prices_exist_in_db(cursor, skin_name) == True:
            print(f'prices already exist for {skin_name}')
            return
    skin_prices = api.fetch_prices_by_skin(skin_name)
    print(f'prices will be added for {skin_name}')
    for price in skin_prices:
        record_skin_price(cursor, price['Name'], price['purchase_price'], price['Date'], check = False)
    add_cagr(cursor, skin_name)
    print(f'prices are added for {skin_name}')


def record_skin_prices_from_collection(cursor, collection_name, check = True):
    if check == True:
        if check_collection_exist_in_db(cursor, collection_name) == False:
            return
        if check_collection_exist_in_site(collection_name) == False:
            return
    print(f'recording skins from {collection_name}')
    for skin in api.get_skin_info():
        if skin['Collection'] == collection_name:
            record_skin_prices_history(cursor, skin['name'])
    

""" DELETE """

def delete_prices_from_skin(cursor, skin_name, check = True):
    print(f'deleting skin prices of: {skin_name}')
    if check == True:
        if check_skin_exist_in_db(cursor, skin_name) == False:
            return
    cursor.execute("DELETE FROM skin_prices WHERE skin_name = ?", (skin_name,))


def delete_prices_from_collection(cursor, collection_name, check = True):
    print(f'deleting skin prices from collection: {collection_name}')
    if check == True:
        if check_collection_exist_in_db(cursor, collection_name) == False:
            return
    cursor.execute("DELETE FROM skin_prices WHERE skin_name IN (SELECT skin_name FROM skins WHERE collection_name = ?)", (collection_name,))


""" CONFIGS """

def setup(cursor):
    api.fetch_skin_list()
    api.fetch_skin_info()
    add_all_collections(cursor)
    add_all_types(cursor)


def main():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    setup(cur)
    for collection in all_collections:
        add_skins_by_collection(cur, collection)
        record_skin_prices_from_collection(cur, collection, check = False)
        conn.commit()
        time.sleep(random.uniform(0.4, 0.6))

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()