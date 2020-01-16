import os

import treepoem
import argparse

# def get_logs_for_day(reportingDay):
from io import BytesIO

def get_parser():
    parser = argparse.ArgumentParser(description='Create shrink report')
    parser.add_argument('-l', '--location', default=None, help='location to generate report for')
    parser.add_argument('-o', '--output', default="example_shrink_report.pdf", help='output file name')
    parser.add_argument('-n', '--dryrun', default=False, action='store_true', help='pull data but do not generate a report')
    parser.add_argument('-d', '--day', default=None, help='day to generate report for')

    return parser

def generate_shrink_report(wastedItems, outFilename):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, inch
    from reportlab.platypus import SimpleDocTemplate, Image, Table, TableStyle

    doc = SimpleDocTemplate(outFilename, pagesize=letter)
    # container for the 'Flowable' objects
    elements = []

    data = []
    for i in wastedItems:
        item = wastedItems[i]
        imagefilename = f"barcodes/0{i.replace('-','')}.png"
        if not os.path.exists(imagefilename):
            image = treepoem.generate_barcode(
                barcode_type='ean13',
                data=f"0{i.replace('-','')}",
                options={'includetext': True, 'guardwhitespace': True})
            image.convert('1').save(imagefilename)

        barcode = Image(imagefilename, 2.25*inch, 0.9*inch)
        data.append([barcode, f"{item['name']}", f"{item['amount']:.2f}"])

    t = Table(data, [2.75*inch, 3.0*inch, 1.5*inch], len(data) * [1.0 * inch])
    t.setStyle(TableStyle([('ALIGN', (0, 0), (0, -1), 'CENTER'),
                           ('TEXTCOLOR', (0, 0), (0, -1), colors.blue),
                           ('ALIGN', (1, 0), (2, -1), 'LEFT'),
                           ('VALIGN', (0, 0), (2, -1), 'MIDDLE'),
                           ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
                           ('TEXTCOLOR', (2, 0), (2, -1), colors.red),
                           ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                           ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                           ]))

    elements.append(t)
    print(elements)
    # write the document to disk
    doc.build(elements)



def main():
    import phood_api
    import config_prod as config
    import json
    from datetime import date, timedelta

    parser = get_parser()
    args = parser.parse_args()

    username = config.username
    if args.location is not None:
        username = args.location

    phoodServer = phood_api.PhoodAPI(config.base_url)
    try:
        res = phoodServer.login(username, config.password).json()
        # print(json.dumps(res, indent=4, sort_keys=True))

        res = phoodServer.getPanInfo().json()
        panInfo = {}
        for pan in res:
            panInfo[pan["id"]] = { "name": pan["name"], "weight": pan["weightQuantity"] }

        # test reading of food logs
        startDate = date.today()
        # startDate = date.today() - timedelta(days=1)
        endDate = startDate + timedelta(days=1)
        print(f'getting logs from {startDate} to {endDate}')

        res = phoodServer.get_food_logs(startDate, endDate).json()
        discardEntries = filter(lambda x: x['actionTaken'] == "Discarded", res)
        discardEntries = filter(lambda x: x['panWeight'], discardEntries)
        # discardEntries = list(filter(lambda x: x['loggedTime'].startswith('2019-10-01'), discardEntries))
        orderedEntries = list(sorted(discardEntries, key=lambda x: x["loggedTime"]))
        print(f'{len(orderedEntries)} entries')

        foodWaste = {}
        for item in orderedEntries:
            if args.dryrun:
                print(json.dumps(item, indent=4, sort_keys=True))
            id = item['clientId']
            panWeight = panInfo[item['panId']]['weight']
            if panWeight < item['quantity']:
                if id in foodWaste:
                    foodWaste[id]['amount'] += (item['quantity'] - panWeight)
                else:
                    foodWaste[id] = {'name': item['itemName'].strip(), 'amount': (item['quantity'] - panWeight) }
            else:
                if (item['quantity'] > 0):
                    print(f'{item["loggedTime"]}: total {item["quantity"]} is less than empty {panInfo[item["panId"]]["name"]} pan {panWeight} for {item["itemName"]}?!?')

        print(f'{len(foodWaste)} unique items')

        if not args.dryrun:
            generate_shrink_report(foodWaste, args.output)

    finally:
        pass
        # phoodServer.logout()


if __name__ == "__main__":
    main()
