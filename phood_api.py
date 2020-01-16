import requests
import json
import csv
#import pandas

class PhoodAPI:

    def __init__(self, base_url="https://api.phoodsolutions.com/shim/"):
        self.BASE_URL = base_url
        self.userId = None
        self.locationId = None
        self.orginizationId = None
        self.AUTH_TOKEN = None

    def login(self, user, pw):
        API_URL = self.BASE_URL + "auth/login"
        r = requests.post(API_URL, json={"username": user, "password": pw})
        res = r.json()
        self.AUTH_TOKEN = res['authorization']
        self.userId = res['user']['id']
        for role in res['roles']:
            if role['entityType'] == 'Location' and role['roleName'] == 'ManageLocation':
                self.locationId = int(role['entityId'])
        return r

    def logout(self):
        API_URL = self.BASE_URL + "auth/logout"
        r = requests.post(API_URL, headers={'authorization': self.AUTH_TOKEN})
        return r

    def getLocationId(self):
        return self.locationId

    def getOrganizationId(self):
        if self.orginizationId is None:
            self.getLocationInfo()
        return self.orginizationId

    def getLocationInfo(self):
        API_URL = f'{self.BASE_URL}locations/getLocationById?id={self.locationId}'
        r = requests.get(API_URL, headers={'authorization': self.AUTH_TOKEN})
        res = r.json()
        self.orginizationId = res['organizationId']
        return r

    def upload_ml(self, im):
        API_URL = f"{self.BASE_URL}ml/upload/{self.locationId}?analyze=true"
        r = requests.post(API_URL, headers={'authorization': self.AUTH_TOKEN}, files={'foodImage': im})
        return r

    def get_food_logs(self, startDate, endDate):
        API_URL = self.BASE_URL + "foodLogs/getLocationFoodLogs"
        API_URL = f'{API_URL}?locationId={self.locationId}&startDate={startDate}&endDate={endDate}'
        r = requests.get(API_URL, headers={'authorization': self.AUTH_TOKEN})
        return r

    def getPersistentItems(self):
        API_URL = f'{self.BASE_URL}persistentItems/getPersistentItemsByLocationId?locationId={self.locationId}'
        r = requests.get(API_URL, headers={'authorization': self.AUTH_TOKEN})
        return r

    def getPanInfo(self):
        API_URL = f'{self.BASE_URL}pans/getPansByLocationId?locationId={self.locationId}'
        r = requests.get(API_URL, headers={'authorization': self.AUTH_TOKEN})
        return r


def main():
    # import config_devel as config
    import config_prod as config
    from datetime import date, timedelta

    phoodServer = PhoodAPI(config.base_url)

    try:
        res = phoodServer.login(config.username, config.password).json()
        print(res)
        for entry in res:
            print(f'\nEntry: {entry}')
            print(res[entry])

        # res = phoodServer.getLocationInfo().json()
        # print(json.dumps(res, indent=4, sort_keys=True))

        # test reading of food logs
        endDate = date.today()
        startDate = endDate - timedelta(days=20)

        res = phoodServer.get_food_logs(startDate, endDate)
        logEntries = sorted(res.json(), key=lambda x: x["loggedTime"])

        #with open('dedhamdata.json', 'w', encoding='utf-8') as f:
            #c = csv.writer(f)
        for i in logEntries:
                #c.writerow(i)
            print(json.dumps(i, indent=4, sort_keys=True))
                #json.dump(i, f, ensure_ascii=False, indent=4)
        #print(type(logEntries[0]))

        with open('dedhamdata.csv', 'w', encoding='utf8', newline='') as output_file:
            fc = csv.DictWriter(output_file,
                                fieldnames=logEntries[0].keys(),

                                )
            fc.writeheader()
            fc.writerows(logEntries)
        '''dataframe = pandas.read_csv('dedhamdata.csv')
        list_of_dictionaries = dataframe.to_dict('records')
        dataframe.to_csv('dedhamdata.csv')'''

    finally:
        # phoodServer.logout()
        pass

if __name__ == "__main__":
    main()
