import json
import re

def is_recipe(iname):
    return re.match('recipe_', iname)!=None
def is_upgrade(iname):
    return re.match('^[A-Za-z0-9_-]*_[0-9]$', iname)!=None
def is_consume(iname):
    return False
    #return (iname2iid[iname] in consume_iids)
def is_not_consider(name):
    return (is_recipe(name) or is_upgrade(name) or is_consume(name))
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
            # for item
            if iflag:
                cost_data[name] = int(data[i]['cost'])
                id_data[name] = i-repeat
            # for hero
            else:
                id_data[name] = int(data[i]['id'])
        else:
            print "repeated item: " + str(name) + "\t" + str(iid)
            repeat += 1
    return id_data, cost_data

def build_iname_iid_map(data):
    id_data = dict()
    cost_data = dict()
    iid_org2new = dict()
    ignore = 0
    for i in range(0, len(data)):
        # substitute prefix part
        name = re.sub('(npc_dota_hero_|item_)', '', data[i]['name'])
        iid = data[i]['id']
        # not repeated item/hero
        if name not in id_data:
            # TODO: 
            # 1. remove recipe item
            # 2. remove consume item
            # 3. remove upgraded versions of an item

            if is_not_consider(name):
                ignore += 1
            else:
                cost_data[name] = int(data[i]['cost'])
                newid = i - ignore
                id_data[name] = newid
                iid_org2new[iid] = newid
        else:
            print "ignored item: " + str(name) + "\t" + str(iid)
            ignore += 1
    return id_data, cost_data, iid_org2new

def build_hname_hid_map(data):
    id_data = dict()
    repeat = 0
    for i in range(0, len(data)):
        # substitute prefix part
        name = re.sub('(npc_dota_hero_|item_)', '', data[i]['name'])
        iid = data[i]['id']
        # not repeated item/hero
        if name not in id_data:
            id_data[name] = int(data[i]['id'])
        else:
            print "repeated item: " + str(name) + "\t" + str(iid)
            repeat += 1
    return id_data

#def is_upgrade_item(iid):
#    up_lst = [201, 202, 203, 204, 193, 194, 220]
#    up_dic = {201: 104, 202: 104, 203: 104,
#              204: 104, 193: 106, 194: 106, 220: 48}
#    if iid in up_lst:
#        return up_dic[iid]
#    else:
#        return -1

def reverse_dict(dict):
    return { v: k for k, v in dict.items() }

def prepare_hero_item_info():
    hero_list = json.load(open('../heroes.json'))['rows']
    item_list = json.load(open('../items.json'))['rows']

    #hero_name2id, _ = build_name_id_mapping(hero_list, False)
    #item_name2id, icosts = build_name_id_mapping(item_list, True)
    hero_name2id = build_hname_hid_map(hero_list)
    item_name2id, icosts, iid_org2new = build_iname_iid_map(item_list)

    hid2name = reverse_dict(hero_name2id)
    iid2name = reverse_dict(item_name2id)

    return hero_name2id, item_name2id, hid2name, iid2name, icosts, iid_org2new
