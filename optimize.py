from hashlib import sha256
import pickle
import xxhash


list_hashes = []
catalog = {}
candidatess = {}


def generate_hashes_to_one_skin_name(skin_name, seed=1000):
    hashes = []
    name = skin_name.lower()

    for i in range(seed):
        start = i % max(1, len(name) - 2)
        end = min(start + 3, len(name))
        substr = name[start:end] + str(i)
        hash_val = xxhash.xxh64(substr).intdigest()
        hashes.append(hash_val)

    return hashes
def hashes_to_backets(skin_name, hashes, count_buck=100):
    numbers = []
    step = len(hashes) // count_buck
    for i in range(0, len(hashes), step):
        stripe = hashes[i:i + step]
        numbers.extend(stripe)
    return {skin_name: numbers}

def create_catalog():
    for item in list_hashes:
        for skin_name, numbers in item.items():
            for number in numbers:
                if number not in catalog:
                    catalog[number] = []
                if skin_name not in catalog[number]:
                    catalog[number].append(skin_name)

def write_lshashes_to_file():
    with open("hash_skins.pkl", "wb") as file:
        pickle.dump(catalog, file)

def load_lshashes_in_file():
    with open("hash_skins.pkl", "rb") as file:
        loaded_skins = pickle.load(file)
    return loaded_skins

def main_hashes(skins):
    global  list_hashes, catalog
    count_skins = len(skins)
    for i in range(count_skins):
        hashes = generate_hashes_to_one_skin_name(skins[i][0])
        dict_one_hash = hashes_to_backets(skins[i][0], hashes)
        list_hashes.append(dict_one_hash)
    create_catalog()
    write_lshashes_to_file()

def is_in_skins(name):
    global  candidatess
    hashs = generate_hashes_to_one_skin_name(name)
    buckets = hashes_to_backets(name, hashs)
    user_buckets = buckets[name]
    skins_in_base = load_lshashes_in_file()
    # print(skins_in_base)
    for number in user_buckets:

        if number in skins_in_base.keys():
            # print(number)
            skins_one = skins_in_base[number]
            for skin_name in skins_one:
                if skin_name == name:
                    candidatess[skin_name] = candidatess.get(skin_name, 0) + 1
    candidatess = sorted(candidatess.items(), key=lambda x: x[1], reverse=True)
    if len(candidatess) > 0:
        print("skin in base")
    else:
        print("skin not in base")














