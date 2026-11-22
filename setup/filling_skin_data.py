weapon_begin = ['G22 ', 'USP ', 'P350 ', 'Berettas ', 'TEC-9 ', 'F/S ', 'Desert Eagle ', 'MAC10 ', 'UMP45 ', 'MP5 ', 'MP7 ', 'Akimbo Uzi ', 'P90 ', 'FN FAL ', 'FAMAS ', 'VAL ', 'M4 ', 'M4A1 ', 'AKR ', 'AKR12 ', 'M16 ', 'FabM ', 'SM1014 ', 'SPAS ', 'M60 ', 'M40 ', 'Mallard ', 'M110 ', 'AWM ', ]
knifes_begin = ['M9 Bayonet ', 'Karambit ', 'jKommando ', 'Butterfly ', 'Flip ', 'Kunai ', 'Scorpion ', 'Tanto ', 'Dual Daggers ', 'Kukri ', 'Stiletto ', 'Mantis ', 'Fang ', 'Sting ']
grenades_begin = ['Flash ', 'HE ', 'Smoke ', 'Molotov ', 'Thermite']
containers_end = [' Box', ' Create', ' Case', ' Graffiti Pack', ' Sticker Pack', ' Charm Pack']
fragment_end = ['Fragment']
stattrack_end = ['StatTrack']
charms_begin = ['Charm ']
gloves_begin = ['Gloves ']
graffiti_begin = ['Graffiti ']

types = ['Пушки', 'Ножи', 'Гранаты', 'Контейнеры', 'Фрагменты', 'Брелоки', 'Перчатки', 'Граффити']

def detect_skin_type(skin_name: str):
    for suf in containers_end:
        if skin_name.endswith(suf):
            return 'Контейнеры'

    for suf in fragment_end:
        if skin_name.endswith(suf):
            return 'Фрагменты'

    for pre in knifes_begin:
        if skin_name.startswith(pre):
            return 'Ножи'

    for pre in grenades_begin:
        if skin_name.startswith(pre):
            return 'Гранаты'

    for pre in weapon_begin:
        if skin_name.startswith(pre):
            return 'Пушки'
        
    for pre in charms_begin:
            if skin_name.startswith(pre):
                return 'Брелоки'
            
    for pre in gloves_begin:
            if skin_name.startswith(pre):
                return 'Перчатки'

    for pre in graffiti_begin:
            if skin_name.startswith(pre):
                return 'Граффити'

    return None

def detect_stat_track(skin_name: str):
    for suf in stattrack_end:
        if skin_name.startswith(suf):
            return True
    return False