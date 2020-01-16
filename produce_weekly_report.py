import os
import argparse
import xlsxwriter

import phood_api
# So what we need to draw from the raw data for Kim is:
# A tab for each store location and their items with the quantity put out, quantity sold, and quantity shrunk. Items
# should be able to be filtered by breakfast, hot bar, salad bar, and soup. Each item should have its own netquantity
# displayed in an organized fashion
# A tab that shows quantity put out, quantity sold, and quantity shrunk for every item across all stores (Gross totals)
#    - whether it would be easier to have breakfast, hot bar, salad bar, and soup as a filtering option or as separate tabs is your call
loggedDays = 7

def get_parser():
    parser = argparse.ArgumentParser(description='Create shrink report')
    parser.add_argument('-l', '--location', default=None, help='location to generate report for')
    parser.add_argument('-o', '--output', default="test_wb.xlsx", help='output file name')
    parser.add_argument('-s', ' --startday', default=None, help='day to generate report for')
    parser.add_argument('-n', '--dryrun', default=False, action='store_true', help='pull data but do not generate a report')

    return parser


class WFMStore:

    def __init__(self, location, base_url='https://api.phoodsolutions.com/shim/', username=None, password=None):
        self.location = location
        if username is None:
            username = location
        self.server = phood_api.PhoodAPI(base_url)
        self.server.login(username, password)
        self.workbook = None


    def logout(self):
        # do not logout
        # self.server.logout()
        pass


    def get_site_info(self):
        hotBar,saladBar,soupBar = set(),set(),set()

        res = self.server.getPersistentItems().json()
        for pItem in res:
            if pItem['station'].lower().startswith('hot bar'):
                hotBar.add(pItem['clientId'])
            elif pItem['station'].lower().startswith('salad bar'):
                saladBar.add(pItem['clientId'])
            elif pItem['station'].lower().startswith('soup'):
                soupBar.add(pItem['clientId'])
            else:
                print(f'unclassified item {pItem}')

        return {'HotBar': list(sorted(hotBar)), 'SaladBar': list(sorted(saladBar)), 'Soup': list(sorted(soupBar))}


    def get_site_logs(self, startDate=None, endDate=None):
        from datetime import date, timedelta

        res = self.server.getPanInfo().json()
        panInfo = {}
        for pan in res:
            panInfo[pan["id"]] = {"name": pan["name"], "weight": pan["weightQuantity"]}

        # test reading of food logs
        # startDate = date.today()
        if startDate is None:
            startDate = date.today()
        if endDate is None:
            endDate = date.today() + timedelta(days=1)

        print(f'getting logs from {startDate} to {endDate}')

        res = self.server.get_food_logs(startDate, endDate)
        if res.status_code == 200:
            res = res.json()
        else:
            return None

        # discarding any entries without panId info
        validEntries = filter(lambda x: x['panId'] or x['panWeight'], res)
        validEntries = filter(lambda x: x['quantity'] > 0, validEntries)

        itemInfo = {}
        for item in validEntries:
            # print(json.dumps(item, indent=4, sort_keys=True))
            if 'panId' in item and item['panId']:
                panWeight = panInfo[item['panId']]['weight']
            else:
                panWeight = item['panWeight']
            PLU = item['clientId']

            if PLU not in itemInfo:
                itemInfo[PLU] = {}
                itemInfo[PLU]['Name'] = item['itemName']

            action = item['actionTaken']
            if panWeight < item['quantity']:
                if action not in itemInfo[PLU]:
                    itemInfo[PLU][action] = (item['quantity'] - panWeight)
                else:
                    itemInfo[PLU][action] += (item['quantity'] - panWeight)
            else:
                if 'panId' in item and item['panId']:
                    print(f'total {item["quantity"]} is less than empty {panInfo[item["panId"]]["name"]} pan {panWeight} for {item["itemName"]}?!?')
                else:
                    print(f'total {item["quantity"]} is less than empty pan {panWeight} for {item["itemName"]}?!?')

        return itemInfo


    # def initialize_workbook(self, outFileName='wb_test.xlsx'):
    #     import xlsxwriter
    #     self.workbook = xlsxwriter.Workbook(outFileName)


def main():
    # import config_devel as config
    import config_prod as config
    from datetime import date, timedelta

    parser = get_parser()
    args = parser.parse_args()

    locations = ['dedham', 'hingham', 'westford', 'westhartford', 'cranston']
    # locations = ['westford']

    if args.location is not None:
        locations = [args.location]

    # open workbook to save info in
    workbook = xlsxwriter.Workbook(args.output)
    number_format = workbook.add_format()
    number_format.set_num_format('0.00')
    worksheets = {}

    for location in locations:
        print(f"generating report for {location}")
        wfmLocation = WFMStore(location, username=location, password=config.password)
        locSheets = worksheets[location] = {}

        for station in ['HB', 'SB', 'Soup']:
            sheet_name = f'{station} - {location}'
            locSheets[station] = workbook.add_worksheet(sheet_name)
            locSheets[station].set_column(0, 0, 15)  # PLU
            locSheets[station].set_column(1, 1, 30)  # Item Name

            # Start from the first cell. Rows and columns are zero indexed.
            for col_num, data in enumerate(['PLU', 'Item Name']):
                locSheets[station].write(1, col_num, data)

        print(f"getting static data for {location}")
        itemStationInfo = wfmLocation.get_site_info()

        itemInfo = {}
        for day in range(loggedDays):
            startTime = date.today() - timedelta(days=(loggedDays-day))
            endTime = startTime + timedelta(days=1)

            itemInfo[day] = wfmLocation.get_site_logs(startTime, endTime)
            if itemInfo[day] is None:
                continue

        fullList = {'HB': set(), 'SB': set(), 'Soup': set() }
        allItemNames = {}
        for day in range(loggedDays):
            if itemInfo[day] is not None:
                print(f"Day {day} has {len(itemInfo[day])} items")
                for itemId in itemInfo[day]:
                    allItemNames[itemId] = itemInfo[day][itemId]['Name']
                    for stationId, barName in zip(['HB', 'SB', 'Soup'],['HotBar', 'SaladBar', 'Soup']):
                        if itemId in itemStationInfo[barName]:
                            fullList[stationId].add(itemId)

        for station in ['HB', 'SB', 'Soup']:
            # generate report
            row = 2
            for itemId in sorted(fullList[station]):
                locSheets[station].write(row, 0, itemId)
                locSheets[station].write(row, 1, allItemNames[itemId])
                row += 1

            for day in range(loggedDays):
                reportDate = date.today() - timedelta(days=(loggedDays-day))
                # start of data for first day
                col = 3 + 5*day
                locSheets[station].write(0, col + 1, reportDate.strftime('%m/%d/%y'))
                for col_num, data in enumerate(['Served', 'Saved', 'Shrink', 'Sold']):
                    locSheets[station].write(1, col + col_num, data)
                row = 2

                if itemInfo[day] is not None:
                    for itemId in sorted(fullList[station]):
                        served, saved, discarded, sold = None, None, None, None
                        served_weight, saved_weight, discarded_weight = 0,0,0
                        if (itemId in itemInfo[day]):
                            item = itemInfo[day][itemId]
                            if 'Served' in item:
                                served_weight = served = item['Served']
                            if 'Saved' in item:
                                saved_weight = saved = item['Saved']
                            if 'Discarded' in item:
                                discarded_weight = discarded = item['Discarded']
                            sold = served_weight - saved_weight - discarded_weight

                            # print(f"Item: {item['Name']}")
                            # print(f"{itemId}: {served:.2f}, {saved:.2f}, {discarded:.2f}")

                        for col_num, data in enumerate([served, saved, discarded, sold]):
                            locSheets[station].write(row, col + col_num, data, number_format)
                        row += 1

    # if not args.dryrun:
    #     generate_report(itemInfo, username, args.output)
    workbook.close()


if __name__ == "__main__":
    main()
