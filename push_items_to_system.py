import phood_api
import csv
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode
import argparse

global locationID
global database

def get_parser():
    parser = argparse.ArgumentParser(description='Cross reference wfm items')
    parser.add_argument('--location', default=None, help='name of location to upload to')
    parser.add_argument('--hbfile', default=None, help='csv file containing hot bar items')
    parser.add_argument('--sbfile', default=None, help='csv file containing salad bar items')
    parser.add_argument('--sfile', default=None, help='csv file containing soup items')
    parser.add_argument('--pfile', default=None, help='csv file containing pan tares')
    parser.add_argument('--flushitems', default=False, action='store_true', help='Deletes all items for location from the DB!!!')
    parser.add_argument('--applytoprod', default=False, action='store_true', help='Apply changes to production system instead of dev')

    return parser


def add_item(itemlist, id, itemdata):
    if id not in itemlist:
        itemlist[id] = itemdata
    else:
        print('id conflict!!! id: {}'.format(id))
        print(itemlist[id])
        print(itemdata)


def load_menu_items(hotbarfile, saladbarfile=None, soupfile=None):
    items = {}

    fileList = { 'hot': hotbarfile }
    if saladbarfile:
        fileList['salad'] = saladbarfile
    if soupfile:
        fileList['soup'] = soupfile

    for bar in fileList:
        with open(fileList[bar], mode='r', encoding='utf-8-sig') as csvfile:
            menu = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in menu:
                if bar is 'soup':
                    row['STATION'] = 'Soup'
                if row["PLU"]:
                    id = f"{row['PLU'].strip()}:{row['STATION'].strip()}"
                    add_item(items, id, row)
                else:
                    print(f'Missing info for item {row}')

    return items


def load_pan_tares(pantarefile):
    pans = []
    with open(pantarefile, mode='r', encoding='utf-8-sig') as csvfile:
        tares = csv.DictReader(csvfile,  delimiter=',', quotechar='"')
        for row in tares:
            print(row)
            if row["Name"] and row["Tare"]:
                pans.append(row)
            else:
                print(f'Missing info for row {row}')
    return pans


def connect_to_db(host, dbname, username, password):
    try:
        connection = mysql.connector.connect(host=host,
                                             database=dbname,
                                             user=username,
                                             password=password)
        if connection.is_connected():
            return connection
    except Error as e:
        print("Error while connecting to MySQL", e)


def disconnect_from_db(db):
    if (db.is_connected()):
        cursor = db.cursor()
        cursor.close()
        db.close()
        print("MySQL connection is closed")


def test_db_connection(db):
    global database
    try:
        if db.is_connected():
            db_Info = db.get_server_info()
            print("Connected to MySQL Server version ", db_Info)
            cursor = db.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            print("Your connected to database: ", record)
    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if (db.is_connected()):
            cursor = db.cursor()
            cursor.close()


def query_items(db):
    global locationId
    try:
        if db.is_connected():
            sql_select_Query = f'select * from {database}.persistent_items where locationId={locationId}'
            print(sql_select_Query)
            cursor = db.cursor()
            cursor.execute(sql_select_Query)
            records = cursor.fetchall()

            print(f"Total number of rows in persistent items is: {cursor.rowcount}")
            for r in records:
                print(r)

    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if (db.is_connected()):
            cursor = db.cursor()
            cursor.close()


def insert_menu_item(db, item):
    global database
    # global locationId
    # print(item)
    try:
        if db.is_connected():
            attrList = 'meal, name, dayOfTheWeek, locationId, clientId, station'
            valueList = f"'{item['meal']}', "
            valueList += f"'{item['name']}', "
            valueList += f"'{item['dayOfTheWeek']}', "
            valueList += f"{item['locationId']}, "
            valueList += f"'{item['clientId']}', "
            valueList += f"'{item['station']}'"

            mySql_insert_query = f"""INSERT INTO {database}.persistent_items ({attrList})
                                    VALUES
                                    ({valueList}) """
            # print(mySql_insert_query)
        cursor = db.cursor()
        result = cursor.execute(mySql_insert_query)
        db.commit()
        # print(f'Record inserted "{item["name"]}" successfully into {dbname}.persistent_items table')
        cursor.close()
    except mysql.connector.Error as error:
        print(f"Failed to insert record into {database}.persistent_items table {error}")
    finally:
        if (db.is_connected()):
            cursor = db.cursor()
            cursor.close()


def flush_items_for_location(db):
    global locationId
    global database
    try:
        if db.is_connected():
            mySql_delete = f"DELETE FROM {database}.persistent_items WHERE locationId={locationId}"

            cursor = db.cursor()
            result = cursor.execute(mySql_delete)
            db.commit()
            print(f'Deleted all items from {database}.persistent_items for {locationId}')
            cursor.close()
    except mysql.connector.Error as error:
        print(f"Failed to flush records from {database}.persistent_items for {locationId}")
    finally:
        if (db.is_connected()):
            cursor = db.cursor()
            cursor.close()


def insert_menu(db, menu_items):
    global database
    # print(item)
    try:
        if db.is_connected():
            attrList = 'meal, name, dayOfTheWeek, locationId, clientId, station'
            valueList = '%s, %s, %s, %s, %s, %s'

            mySql_insert_query = f"""INSERT INTO {database}.persistent_items ({attrList})
                                    VALUES
                                    ({valueList})"""
            # print(mySql_insert_query)
            cursor = db.cursor()
            result = cursor.executemany(mySql_insert_query, menu_items)
            db.commit()
            print(f'Inserted {len(menu_items)} records successfully into {database}.persistent_items table')
            cursor.close()
    except mysql.connector.Error as error:
        print(f"Failed to insert {len(menu_items)} records into {database}.persistent_items table {error}")
    finally:
        if (db.is_connected()):
            cursor = db.cursor()
            cursor.close()


def insert_pans(db, pan_items):
    global database
    try:
        if db.is_connected():
            attrList = 'name, weightQuantity, weightUnit, organizationId, locationId'
            valueList = '%s, %s, %s, %s, %s'

            mySql_insert_query = f"""INSERT INTO {database}.pans ({attrList})
                                    VALUES
                                    ({valueList})"""
            # print(mySql_insert_query)
            cursor = db.cursor()
            result = cursor.executemany(mySql_insert_query, pan_items)
            db.commit()
            print(f'Inserted {len(pan_items)} records successfully into {database}.pans table')
            cursor.close()
    except mysql.connector.Error as error:
        print(f"Failed to insert {len(pan_items)} records into {database}.pans table {error}")
    finally:
        if (db.is_connected()):
            cursor = db.cursor()
            cursor.close()


if __name__ == "__main__":
    global locationId
    global database

    parser = get_parser()
    args = parser.parse_args()

    if args.applytoprod:
        import config_prod as config
    else:
        import config_devel as config

    updateItems = True
    updatePans = True

    database = config.database
    phoodServer = phood_api.PhoodAPI(config.base_url)

    username = config.username
    if args.location is not None:
        username = args.location
    res = phoodServer.login(username, config.password).json()

    locationId = phoodServer.getLocationId()

    try:
        db = connect_to_db(config.dbhost, database, config.dbuser, config.dbpass)

        if updateItems and args.hbfile is not None:
            items = load_menu_items(args.hbfile, args.sbfile, args.sfile)
            if args.flushitems:
                print(f'Deleting all items for location {locationId}!!!')
                flush_items_for_location(db)

            # test_db_connection(db)
            # query_items(db)
            itemCnt = 0
            menu_entries = []
            for i in dict(list(items.items())[0:]):
                itemCnt += 1
                item = items[i]
                for day in 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday':
                    menu_entries.append(('Breakfast',
                                         item['NAME'].strip(),
                                         day,
                                         locationId,
                                         item['PLU'],
                                         item['STATION'].strip()
                                         ))

                if (0 == (itemCnt % 30)):
                    insert_menu(db, menu_entries)
                    menu_entries = []
            insert_menu(db, menu_entries)
            menu_entries = []

        orgId = phoodServer.getOrganizationId()

        if updatePans and args.pfile is not None:
            pans = load_pan_tares(args.pfile)
            pan_entries = []
            for pan in pans:
                pan_entries.append((pan['Name'].strip(),
                                    pan['Tare'],
                                    'lbs',
                                    orgId,
                                    locationId))
            insert_pans(db, pan_entries)

        disconnect_from_db(db)
    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if (db.is_connected()):
            cursor = db.cursor()
            cursor.close()
            db.close()
            print("MySQL connection is closed")
