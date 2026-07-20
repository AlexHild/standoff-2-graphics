import sqlite3
import api

from optimize import main_hashes, is_in_skins

""" PRINTS """


def print_all_collections():
    print(api.get_collections())


def print_all_skin_names_from_list():
    print(api.get_skin_list())

def return_all_skins_from_list():
    return api.get_skin_list()


def print_all_skin_names_from_info():
    temp = []
    for skin in api.get_skin_info():
        temp.append(skin['name'])
    print(temp)


def print_all_skin_infos():
    print(api.get_skin_info())


def print_all_skin_types():
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


def check_collection_exist_in_site(collection_name, update=True):
    if update == True:
        api.fetch_skin_info()
    for collection in api.get_collections():
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


def check_skin_name_exist_in_site(skin_name, update=True):
    if update == True:
        api.fetch_skin_info()
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


def check_skin_exist_in_site(skin_name, collection_name, skin_type, update=True):
    if update == True:
        api.fetch_skin_info()
    for skin in api.get_skin_info():
        if skin['name'] == skin_name:
            if skin['type'] == skin_type and skin['Collection'] == collection_name:
                return True
            else:
                print(
                    f"no such skin in site: {skin_name}, {collection_name}, {skin_type}. Should be: {skin['name']}, {skin['Collection']}, {skin['type']}")
                return False
    print(f"no such skin in site: {skin_name}")
    return False


""" ADD NEW ITEM INTO DATABASE """


def add_collection(cursor, collection_name, check=True, update=True):
    if check == True:
        if check_collection_exist_in_site(collection_name, update) == False:
            return
    cursor.execute("INSERT OR IGNORE INTO collection_names(collection_name) VALUES(?)", (collection_name,))


def add_skin_type(cursor, skin_type):
    cursor.execute("INSERT OR IGNORE INTO skin_types(skin_type) VALUES(?)", (skin_type,))


def add_skin(cursor, skin_name, collection_name, skin_type, check=True, update=True):
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
    cursor.execute("INSERT INTO skins(skin_name, collection_name, skin_type) VALUES(?, ?, ?)",
                   (skin_name, collection_name, skin_type))
    print(f'skin added to db: {skin_name}')


def add_all_collections(cursor):
    api.fetch_skin_info()
    # print_all_collections()
    for collection in api.get_collections():
        add_collection(cursor, collection, check=False, update=False)
    print("all collection added")


def add_all_types(cursor):
    api.fetch_skin_info()
    # print_all_skin_types()
    for type in api.get_skin_types():
        if type != '':
            add_skin_type(cursor, type)
    print("all types added")


def add_skins_by_collection(cursor, collection_name, update=True):
    if update == True:
        api.fetch_skin_info()
    if check_collection_exist_in_db(cursor, collection_name) == False:
        return
    if check_collection_exist_in_site(collection_name, update=False) == False:
        return
    for skin in api.get_skin_info():
        if skin['Collection'] == collection_name:
            add_skin(cursor, skin['name'], collection_name, skin['type'], check=True, update=False)
    print(f'skins of collection {collection_name} added')


""" UPDATE PRICES """


def record_skin_price(cursor, skin_name, skin_price, recorded_at, check=True):
    if check == True:
        if check_skin_exist_in_db(cursor, skin_name) == False:
            return
    cursor.execute("INSERT OR IGNORE INTO skin_prices(skin_name, skin_price, recorded_at) VALUES(?, ?, ?)",
                   (skin_name, skin_price, recorded_at))


def record_skin_prices_history(cursor, skin_name):
    if check_skin_exist_in_db(cursor, skin_name) == False:
        return
    skin_prices = api.fetch_prices_by_skin(skin_name)
    print(f'prices will be added for {skin_name}')
    for price in skin_prices:
        record_skin_price(cursor, price['Name'], price['purchase_price'], price['Date'], check=False)
    print(f'prices are added for {skin_name}')


def record_skin_prices_from_collection(cursor, collection_name):
    api.fetch_skin_info()
    if check_collection_exist_in_db(cursor, collection_name) == False:
        return
    if check_collection_exist_in_site(collection_name, update=False) == False:
        return
    print(f'recording skins from {collection_name}')
    for skin in api.get_skin_info():
        if skin['Collection'] == collection_name:
            record_skin_prices_history(cursor, skin['name'])


""" DELETE """


def delete_prices_from_skin(cursor, skin_name, check=True):
    print(f'deleting skin prices of: {skin_name}')
    if check == True:
        if check_skin_exist_in_db(cursor, skin_name) == False:
            return
    cursor.execute("DELETE FROM skin_prices WHERE skin_name = ?", (skin_name,))


def delete_prices_from_collection(cursor, collection_name, check=True):
    print(f'deleting skin prices from collection: {collection_name}')
    if check == True:
        if check_collection_exist_in_db(cursor, collection_name) == False:
            return
    cursor.execute("DELETE FROM skin_prices WHERE skin_name IN (SELECT skin_name FROM skins WHERE collection_name = ?)",
                   (collection_name,))


""" CONFIGS """


def setup(cursor):
    api.fetch_skin_list()
    add_all_collections(cursor)
    add_all_types(cursor)


def main():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    setup(cur)

    prefered_collections = ['Rival', 'Cursed_souls', 'Empire', 'Project_z9', 'Revenge', 'Halloween_2020', 'Sharp',
                            'Fable', 'Fireborn', 'Scorpion', 'Travelers_bag', 'Nightmare', 'Prey', 'Newyear2020',
                            'Event5years', 'Space_vision', 'Sunstrike', 'Project_pandora', 'Dynasty', 'Subjectx',
                            'Chameleon', 'Event4years', 'Reforged', 'Assistance', 'Legends', 'Collaboration',
                            'Competitive', 'Fun_and_sun', 'Nameless', 'Kitsune_dreams', 'Event2years',
                            'Hot_winter_party_2023', 'Dragon_rise', 'Frosty_chaos', 'Esports', 'Furious',
                            'Halloween_2019', 'Revival', 'Origin', 'New_year_2021', 'Outcast', 'Winter_fun_2022']
    import random
    import time
    for collection in prefered_collections:
        add_skins_by_collection(cur, collection, update=False)
        time.sleep(random.uniform(0.4, 0.8))

    record_skin_prices_from_collection(cur, 'Rival')
    name_skin = input('Format: (VAL "Iron Wolf"): ')
    skins = return_all_skins_from_list()
    main_hashes(skins)
    is_in_skins(name_skin)

    conn.commit()

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()