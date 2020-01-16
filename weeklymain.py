import pandas as pd
import config_prod as config
#import json
from datetime import date, timedelta
import phood_api

names = pd.read_excel('Phood Solutions List Names.xlsx')
names=names.drop([0,1,2])
names=names.iloc[:,0:2]

names.columns = ['PLU', 'Item_Names']
names.reset_index(drop=True)
ndic = names.set_index('PLU').to_dict('index')

locations = ['dedham', 'hingham', 'westford', 'westhartford', 'cranston']
unnamedplu = []
masterlist = []
# print(ndic)
locationinfo = {51: {'name': 'Dedham'}, 52: {'name': 'Hingham'}, 53: {'name': 'Westford'},
                54: {'name': 'West hartford'}, 55: {'name': 'Cranston'}}
for location in locations:
    phoodServer = phood_api.PhoodAPI(config.base_url)
    username = location
    res = phoodServer.login(username, config.password).json()
    endDate = date.today() - timedelta(days=date.today().weekday())
    startDate = endDate - timedelta(days=7)
    # endDate = date.today()- timedelta(days=1)
    # startDate = endDate - timedelta(days=6)
    res = phoodServer.get_food_logs(startDate, endDate).json()
    PLUEntries = filter(lambda x: x['clientId'], res)
    orderedEntries = list(sorted(PLUEntries, key=lambda x: x["loggedTime"]))
    hotBar, saladBar, soupBar = set(), set(), set()
    res = phoodServer.getPersistentItems().json()
    for pItem in res:
        if pItem['station'].lower().startswith('hot bar'):
            hotBar.add(pItem['clientId'])
        elif pItem['station'].lower().startswith('salad bar'):
            saladBar.add(pItem['clientId'])
        elif pItem['station'].lower().startswith('soup'):
            soupBar.add(pItem['clientId'])
        else:
            print(f'unclassified item {pItem}')

    res = phoodServer.getPanInfo().json()
    panInfo = {}
    for pan in res:
        panInfo[pan["id"]] = {"name": pan["name"], "weight": pan["weightQuantity"]}
    # print(panInfo)

    for item in orderedEntries:
        item['clientId'] = item['clientId'].replace("-", "")
        # print(item['clientId'])
        if item['itemName'] in ndic.keys():
            item['itemName'] = ndic[int(item['clientId'])]['Item_Names']
        else:
            unnamedplu.append(item)
        # print(item['Item_Names'])
        if item['clientId'] in hotBar:
            item['station'] = 'HB'
        elif item['clientId'] in saladBar:
            item['station'] = 'SB'
        elif item['clientId'] in soupBar:
            item['station'] = 'SO'
        item['Location'] = locationinfo[item['locationId']]['name']
        item['Served'] = item['Saved'] = item['Sold'] = item['Shrink'] = 0
        if 'panId' in item and item['panId']:
            panWeight = panInfo[item['panId']]['weight']
        else:
            panWeight = item['panWeight']
        if item['actionTaken'] == 'Served':
            item['Served'] = +item['quantity'] - panWeight
        if item['actionTaken'] == 'Discarded':
            item['Shrink'] = +item['quantity'] - panWeight
        if item['actionTaken'] == 'Saved':
            item['Saved'] = +item['quantity'] - panWeight
        item['Sold'] = item['Served'] - item['Saved'] - item['Shrink']
        if item['clientId'] == '00449791900':
            item['station'] = 'HB'
            # print(item)

    masterlist.extend(orderedEntries)

    