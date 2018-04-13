import re
import json

# construct item/hero-id based on json data
# reformat the id sequence if iflag is True
# iflag=True=>1. id reformat, 2. upgrade item check, 3. repeat name ignore
# iflag=False=>1. repeat name ignore
def build_name_id_mapping(data, iflag=False):
    id_data = dict()
    cost_data = dict()
    repeat = 0
    for i in range(0, len(data)):
        # substitute prefix part
        name = re.sub('(npc_dota_hero_|item_)', '', data[i]['name'])
        iid = data[i]['id']
        # not repeated item/hero
        if name not in id_data:
            if iflag:
                cost_data[name] = int(data[i]['cost'])
                id_data[name] = i-repeat
            else:
                id_data[name] = int(data[i]['id'])
        else:
            print "repeated item: " + str(name) + "\t" + str(iid)
            repeat += 1
    return id_data, cost_data

def is_upgrade_item(iid):
    up_lst = [201, 202, 203, 204, 193, 194, 220]
    up_dic = {201: 104, 202: 104, 203: 104,
              204: 104, 193: 106, 194: 106, 220: 48}
    if iid in up_lst:
        return up_dic[iid]
    else:
        return -1

def reverse_dict(dict):
    return { v: k for k, v in dict.items() }

def prepare_hero_item_info():
    hero_list = json.load(open('../heroes.json'))['rows']
    item_list = json.load(open('../items.json'))['rows']

    hero_name2id, _ = build_name_id_mapping(hero_list, False)
    item_name2id, icosts = build_name_id_mapping(item_list, True)

    hid2name = reverse_dict(hero_name2id)
    iid2name = reverse_dict(item_name2id)

    return hero_name2id, item_name2id, hid2name, iid2name, icosts
