import time
import json
import bz2
import sys
from qwikidata.entity import WikidataItem
from qwikidata.json_dump import WikidataJsonDump
from qwikidata.linked_data_interface import get_entity_dict_from_api
from qwikidata.utils import dump_entities_to_json
from PIL import Image
import hashlib
import requests
import cv2
import os

#politician ID in wikidata
Q_POLITICIAN = "Q82955" 
#property IDs in wikidata
P_OCCUPATION = "P106"
P_COUNTRY = "P27"
P_POSITION_HELD = "P39"
P_GENDER = "P21"
P_CITIZENSHIP = "P27"
P_RELIGION = "P140"
P_US_CONGRESS_ID = "P1157"
P_CANDIDACY = "P3602"
P_PARTY = "P102"
P_START_TIME = "P580"
P_END_TIME = "P582"
P_DEAD = "P570"


def has_occupation_politician(item: WikidataItem, truthy: bool = True) -> bool:
    """Return True if the Wikidata Item has occupation politician. Adapted from template of qwikidata property query"""
    # Might also be interesting to filter millitary officers (Q189290). (not implemented here)
    if truthy:
        claim_group = item.get_truthy_claim_group(P_OCCUPATION)
    else:
        claim_group = item.get_claim_group(P_OCCUPATION)
    occupation_qids = [
        claim.mainsnak.datavalue.value["id"]
        for claim in claim_group
        if claim.mainsnak.snaktype == "value"
    ]
    return Q_POLITICIAN in occupation_qids #return if Q_POLITICIAN appears in P_OCCUPATION values

def dump_politicians(wjd,WIKI_DATA_FILTERED,verbose = False):
    '''
    Function for dumping alive politician entities from full wiki data dump to a compressed json file.
    The dumped data includes politicians' names (including aliases), gender (in QID), religion, parties, held positions (with time periods), us_congress_id, candidacy_election
    '''
    politicians = []
    t1 = time.time()
    with bz2.open(WIKI_DATA_FILTERED, 'wb') as d_file:
        for ii, entity_dict in enumerate(wjd):
            if entity_dict["type"] == "item":
                entity = WikidataItem(entity_dict)
                try:
                    if has_occupation_politician(entity):
                        if (P_DEAD not in entity_dict['claims'].keys() 
                            and P_CITIZENSHIP in entity_dict['claims'].keys()):
                            try:
                                temp_position_held = []
                                temp_parties = []
                                temp_usid = ""
                                temp_religion = ""
                                temp_aliases= []
                                temp_candiacy = []
                                #position held and start/end time(optinal field)
                                if (P_POSITION_HELD in entity_dict['claims'].keys()):
                                    for v in entity_dict["claims"][P_POSITION_HELD]:
                                        temp_qualifiers = []
                                        if (v["mainsnak"].get("datavalue", {}).get("value", {}).get("id") is not None):
                                            temp_qualifiers.append(v['mainsnak']['datavalue']['value']['id'])#position held
                                            try:
                                                temp_qualifiers.append(v['qualifiers'][P_START_TIME][0]['datavalue']['value']['time'])#start time
                                            except:
                                                temp_qualifiers.append("")
                                            try:
                                                temp_qualifiers.append(v['qualifiers'][P_END_TIME][0]['datavalue']['value']['time'])#start time
                                            except:
                                                temp_qualifiers.append("")
                                        temp_position_held.append(temp_qualifiers)
                                #Party members (optinal field)
                                if (P_PARTY in entity_dict['claims'].keys()):
                                    for v in entity_dict["claims"][P_PARTY]:
                                        if (v["mainsnak"].get("datavalue", {}).get("value", {}).get("id") is not None):
                                            temp_parties.append(v['mainsnak']['datavalue']['value']['id']) #parties held **NOTE: there could be people switching parties but wiki doesn't give any temporal information
                                #Candidacy in election (optinal field)
                                if (P_CANDIDACY in entity_dict['claims'].keys()):
                                    for v in entity_dict["claims"][P_CANDIDACY]:
                                        if (v["mainsnak"].get("datavalue", {}).get("value", {}).get("id") is not None):
                                            temp_candiacy.append(v['mainsnak']['datavalue']['value']['id']) 
                                # US Congress Bio ID (optinal field)
                                if (P_US_CONGRESS_ID in entity_dict['claims'].keys()):#there are some corrupted data on wikidata with this field but no data
                                    if ('datavalue' in entity_dict['claims'][P_US_CONGRESS_ID][0]['mainsnak']):
                                        temp_usid = entity_dict["claims"][P_US_CONGRESS_ID][0]['mainsnak']['datavalue']['value']
                                # Religion (optinal field)
                                if (P_RELIGION in entity_dict['claims'].keys()):
                                    temp_religion = entity_dict["claims"][P_RELIGION][0]['mainsnak']['datavalue']['value']['id']
                                #aliases (optional field)
                                
                                if ("aliases" in entity_dict.keys()):
                                    if len(entity_dict.get("aliases", {}).get("en", [])) > 0:
                                        for v in entity_dict["aliases"]["en"]:
                                            temp_aliases.append(v["value"])
                                #qid, name, gender, nationality are compulsory fields
                                politicians.append(dict(zip(['qid',
                                                            'name',
                                                            'gender',
                                                            'nationality',
                                                            'aliases',
                                                            'parties',
                                                            'positions held',
                                                            'religion',
                                                            'us_congress_id',
                                                            'candidacy_election'],
                                                            [entity_dict['id'],#Qid
                                                            entity_dict['labels']['en']['value'], #name
                                                            entity_dict['claims'][P_GENDER][-1]['mainsnak']['datavalue']['value']['id'], #latest gender
                                                            entity_dict['claims'][P_CITIZENSHIP][-1]['mainsnak']['datavalue']['value']['id'], #latest country of citizenship
                                                            temp_aliases,
                                                            temp_parties,
                                                            temp_position_held,
                                                            temp_religion,
                                                            temp_usid,
                                                            temp_candiacy
                                                            ])))# dump entity qid, name and nationality only
                            except KeyError as e: #missing important keys (name, qid, country, gender)
                                if verbose:
                                    print(e,entity_dict['id'])
                except Exception:
                    if verbose:
                        print (Exception)
            if ii % 20000 == 0:
                t2 = time.time()
                dt = t2 - t1
                print(
                    "Dumped {} politicians among {} entities [entities/s: {:.2f}]".format(
                        len(politicians), ii, ii / dt
                    )
                )
                d_file.write(('\n'.join(map(json.dumps, politicians))+'\n').encode('utf-8'))
                politicians = []

def dump_figures(US_qid,path,verbose=False):
    tx = 300
    ty = 400
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    count = 1
    t1 = time.time()
    for qid in US_qid:
        try:
            Q_dict = get_entity_dict_from_api(qid)
            if 'P18' in Q_dict['claims'].keys():
                img_name = Q_dict['claims']['P18'][0]['mainsnak']['datavalue']['value'].replace(' ','_')
                img_md5 = hashlib.md5(img_name.encode(encoding='UTF-8')).hexdigest()
                image_url = "https://upload.wikimedia.org/wikipedia/commons/"+img_md5[0]+"/"+img_md5[0:2]+"/"+img_name
                image_request = requests.get(image_url, headers=headers)
                if (image_request.status_code==200):
                    with open(path+'/tmp//'+img_name, 'wb') as f:     
                        f.write(image_request.content)
                    im = cv2.imread(path+"/tmp//"+img_name)
                    (y,x)=im.shape[:2]
                    if(tx/x<ty/y):
                        ratio = tx/x
                    else:
                        ratio = ty/y
                    cv2.imwrite(path+'/'+qid+'.jpg',cv2.resize(im,(int(im.shape[1]*ratio),int(im.shape[0]*ratio))))
                    os.remove(path+'/tmp//'+img_name)
                    count += 1
        except Exception as e:
            if verbose:
                print(qid)
                print(e)
        if verbose:
            if count%1000==0:
                t2 = time.time()
                dt = t2 - t1
                print( "Dumped {} politician figures. [figures/s: {:.2f}]".format(count, count / dt))