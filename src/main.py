import numpy as np
import os
import json
from scipy import spatial as sp
from PrepareHeroItemInfo import prepare_hero_item_info
import re
import PrepareHeroItemInfo as pi

DATA_FILE_PATH = '../data/'

WIN_SCORE = 1.2
LOSE_SCORE = 0.8

# 267->196 spirit vessel
# 220->48 travel boots
# 193->106 necronominon
syn_iids = [121,123,98,250,252,263,104,141,145,147,110,249,154,158,164,235,185,229,196,242,190,231,206,208,210,212,79,81,90]
syn_iid_child = {121:[129],123:[69],98:[67,67],250:[98,149],252:[67],263:[102,236,75],104:[77],141:[149],145:[69],147:[170],110:[69,69],249:[152],154:[162,170],158:[166],164:[94],235:[129],185:[73],229:[187],196:[92],242:[86,125],190:[77,77],231:[79,180],206:[73,73],208:[125,143],210:[162],212:[75,88],79:[86,94],81:[88,94],90:[131,94]}
consume_iids = [216,40,42,43,218,44,241,257,265,237,38,39]
basic_iids = [21, 31, 37, 45, 55, 57, 59, 61, 56, 58, 60, 13, 15, 17, 19, 23, 25, 27, 29, 215, 12, 240, 52, 51, 53, 54, 3, 5, 7, 9, 11, 2, 4, 6, 8, 10, 244, 182, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 41, 84, 181]
inter_iids = [48, 92,98, 102, 143, 149, 236, 152, 162, 166, 170, 187, 129,131, 73,75,77, 79,86, 88, 125,67, 69, 94, 180]
final_iids = [160, 196, 48, 50, 106, 119, 121, 123, 96, 250, 252, 100, 232, 263, 104, 108, 141, 145, 147, 223, 225, 256, 259, 110, 112, 114, 116, 139, 151, 249, 154, 156, 158, 164, 172, 174, 176, 178, 235, 185, 229, 196, 242, 127, 133, 135, 137, 168, 190, 231, 206, 239, 208, 210, 212, 214, 63, 81, 90, 1, 247, 65, 36, 254, 71]


# no consumes, no recipe
def is_consider(iname, mname):

    if mname == 'cost':
        return item_costs[iname] >= 500
    else:
        raise Exception("no consider function is defined!")

# if we do not consider time, rather we consider
# all the necessary items in all time, then our method should also be effective
# in this case we may recommend more items like 15-20 that captures early-mid-final
# k can be determined following:
# 1. get the avg total items throughout every match for every hero
# 2. guess
def base_rec(heroes, model, k):
    res = []
    for h in heroes:
        hifreq = model[h]
        hifreq = hifreq.sort()
        r1 = hifreq[0:k]
        r1 = dict((r, 1) for r in r1)
        res.append(r1)
    return res

def base_rec_h(h, model, k):
    hifreq = model[h]
    #print "hifreq: "
    #print hifreq
    #print "k is: " + str(k)
    #print "top k index: "

    tki = topk_index(hifreq, k)
    print "recommended length: " + str(len(tki))
    return tki

def topk_index(arr, k):
    arr = np.array(arr)
    return arr.argsort()[-k:][::-1]

# in matches won, recommend items, compute similarity with actual items
# OR
# in all games, find which side had items more similar to recommended, then compute winning percentage
# calculate the similarity between item purchase log
# per hero

# sim: similarity between item purchases
# ideal evaluation: P(Exactly same purchase log) 
# @hp: actual hero-purchase counter dict array
# @hp_rec: recommended hero-purchase counter dict array
# @opt: aggregation function, average and etc
# TODO: for diff heroes, we may have different weight when calc total similarity
def team_purchase_sim_calc(hp, hp_rec, norm=False, aggr_opt='avg'):
    #print "len(hero purchase): " + str(len(hp))
    sim_vec=[]
    tot_sim=0
    for (h, hpr) in zip(hp, hp_rec):
        #print h
        #print hpr
        # item purchase counter to feature vector
        h, hpr=feature_vec(h, hpr)
        # do normalization if needed
        if norm:
            norm1=np.linalg.norm(hp)
            norm2=np.linalg.norm(hpr)
            h=h/norm1
            hpr=hpr/norm2
        # calc cosine similarity
        sim=1-sp.distance.cosine(h, hpr)
        # append current hero item similarity
        sim_vec.append(sim)
    print "per hero similarity vector:"
    print sim_vec
    if aggr_opt=='avg':
        #print len(hp)
        # the length should always be 5
        assert(len(hp)==5)
        #print "sim_vec: "
        #print sim_vec
        tot_sim=sum(sim_vec)/len(sim_vec)
    else:
        print "no such aggr function is pre defined!"
        tot_sim=-1
    return tot_sim

# assumes: we have tot_count[h] that stores the avg total "vital" item purchased by hero h
# assumes: dummy_is_vital(iid)
# necissity evaluation
# calculating probability 
def nec_eva(fpath, model, items, icosts, pred=base_rec_h):
    mcount=0
    sim_sum=0
    for fname in os.listdir(fpath):
        data=json.load(open(fpath+fname))
        wplayers=[]
        # assumes: the first 5 is radiant hero
        # get the winner players
        if(data['radiant_win']):
            wplayers=data['players'][0:5]
        else:
            wplayers=data['players'][5:10]
        hero_vitem=[]
        rec_vitem=[]
        for p in wplayers:
            # vital items that we consider
            vitem=dict()
            purchase=p['purchase']
            hid=p['hero_id']
            #print "purchase length of hero " + str(hid) + ": " + str(len(purchase))
            for k in purchase:
                #iid=items[k]
                if pi.is_recipe(k) or pi.is_upgrade(k) or pi.is_consume(k):
                    pass
                #if dummy_is_vital(iid):
                else:
                    vitem[k]=purchase[k]
            hero_vitem.append(vitem)
            print hid2name[hid]
            print "actual purchase: "
            print vitem
            #print "hero item avg count: " + str(hero_item_count[hid])
            
            rec=base_rec_h(hid, model, len(vitem))
            rec_vitem.append(rec)
            # print recommended items
            print "recommended: "
            rec_name=[iid2name[iid] for iid in rec]
            print rec_name
            print ""
        #print hero_vitem
        #print rec_vitem
        sim=team_purchase_sim_calc(hero_vitem, rec_vitem)
        print "rec-actual item purchase similarity of match " + str(fname) + ": " + str(sim)
        if not np.isnan(sim):
            sim_sum=(sim_sum*mcount+sim)/(mcount+1)
            mcount+=1
    print "all winners similarity avg: " + str(sim_sum)

# sufficiency evaluation
# def suf_eva():
# utils
# transform two dict to feature vector
# dic1: <iname, 1/0>
# arr2: list of iname recommended
def feature_vec(dic1, arr2):
    kvec = []
    vec1 = []
    for k, v in dic1.iteritems():
        kvec.append(k)
        # changed from counter to 1
        vec1.append(1)
    vec2 = [0]*len(kvec)
    for iid in arr2:
        name = iid2name[iid]
        if name in kvec:
            index = kvec.index(name)
            vec2[index] = 1
        else:
            kvec.append(name)
            vec1.append(0)
            vec2.append(1)
    return vec1, vec2

def count_purchased_items(purchases, price_threshold=500):
    total_purchase_num = 0
    for item_name, num_purchased in purchases.items():
        if num_purchased is None:
            continue

        item_cost = item_costs[item_name]
        if item_cost >= price_threshold:
            total_purchase_num += num_purchased
    return total_purchase_num

def calc_base_freq(hname2hid, iname2iid, consider_func='cost'):
    hero_count = max(hname2hid.values()) + 1
    item_count = len(iname2iid)

    basic_freq = np.zeros((hero_count, item_count))

    # contains the number of items each hero purchased in each game
    #hero_num_item_records = []
    #for i in range(hero_count):
    #    hero_num_item_records.append([])

    for match_file_name in os.listdir(DATA_FILE_PATH):
        match_file = open(DATA_FILE_PATH + match_file_name)
        match_data = json.load(match_file)

        for player in match_data['players']:
            hero_id = player['hero_id']
            purchases = player['purchase']

            #num_purchased_items = count_purchased_items(purchases)
            #hero_num_item_records[hero_id].append(num_purchased_items)

            win = player['isRadiant'] == player['radiant_win']

            for item_name in purchases:
                if item_name in iname2iid:
                    item_id = iname2iid[item_name]

                    #if is_consider(item_name, consider_func) and purchases[item_name] is not None:
                    hero_freq = basic_freq[hero_id]
                    hero_freq[item_id] += WIN_SCORE if win else LOSE_SCORE

        match_file.close()

#    hero_item_count = []

#    for item_count_list in hero_num_item_records:
#        if len(item_count_list) == 0:
#            hero_item_count.append(0)
#        else:
#            hero_item_count.append(int(round(sum(item_count_list) / float(len(item_count_list)))))
    return basic_freq

def lst_dict_iid_org2new(syn_iids, syn_iid_child, consume_iids, basic_iids, inter_iids, final_iids, iid_org2new):
    syn_iids = [iid_org2new[i] for i in syn_iids]
    consume_iids = [iid_org2new[i] for i in consume_iids]
    basic_iids = [iid_org2new[i] for i in basic_iids]
    inter_iids = [iid_org2new[i] for i in inter_iids]
    final_iids = [iid_org2new[i] for i in final_iids]
    new_dict = {}
    for k, v in syn_iid_child.iteritems():
        new_dict[iid_org2new[k]]=[iid_org2new[i] for i in v]
    syn_iid_child = new_dict
    return syn_iids, syn_iid_child, consume_iids, basic_iids, inter_iids, final_iids

hname2hid, iname2iid, hid2name, iid2name, item_costs, iid_org2new = prepare_hero_item_info()
syn_iids, syn_iid_child, consume_iids, basic_iids, inter_iids, final_iids = lst_dict_iid_org2new(syn_iids, syn_iid_child, consume_iids, basic_iids, inter_iids, final_iids, iid_org2new)
basic_freq = calc_base_freq(hname2hid, iname2iid)

nec_eva('../test/', basic_freq, iname2iid, item_costs)

