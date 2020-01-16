import treepoem
import csv
import pandas as pd


def generate_shrink_report(wastedItems):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, inch
    from reportlab.platypus import SimpleDocTemplate, Image, Table, TableStyle

    doc = SimpleDocTemplate("shrinkreport.pdf", pagesize=letter)
    # container for the 'Flowable' objects
    elements = []

    data = []
    for i in wastedItems:
        item = wastedItems[i]
        image = treepoem.generate_barcode(
            barcode_type='ean13',
            data=f'0{i}',
            options={'includetext': True, 'guardwhitespace': True})

        imagefilename = f'barcodes/0{i}.png'
        image.convert('1').save(imagefilename)
        barcode = Image(imagefilename, 1.8*inch, 0.9*inch)

        data.append([barcode, item['name'], f"{item['amount']:.2f}"])
    #print(data)
    print(type(data))
    df = pd.DataFrame(data)
    df.to_csv('shrinkreport.csv', index=False)


    t = Table(data, [2.0*inch, 3.0*inch, 1.5*inch], len(data) * [1.0 * inch])
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
    '''print(type(elements))
    df1 = pd.DataFrame(data)
    df1.to_csv('shrinkreport1.csv', index=False)'''
    # write the document to disk
    doc.build(elements)
    print(type(elements))
    df1 = pd.DataFrame(data)
    df1.to_csv('shrinkreport1.csv', index=False)

def main():
    import phood_api
    import config_prod as config
    from datetime import date, timedelta

    phoodServer = phood_api.PhoodAPI(config.base_url)

    # try:
    res = phoodServer.login(config.username, config.password).json()
    # print(json.dumps(res, indent=4, sort_keys=True))

    # res = phoodServer.getLocationInfo().json()
    # print(json.dumps(res, indent=4, sort_keys=True))

    # test reading of food logs
    endDate = date.today()
    startDate = endDate - timedelta(days=1)

    res = phoodServer.get_food_logs(startDate, endDate).json()
    # print(json.dumps(res, indent=4, sort_keys=True))
    discardEntries = list(filter(lambda x: x['actionTaken'] == "Discarded", res))
    discardEntries = list(filter(lambda x: x['panWeight'], discardEntries))
    print(f'{len(discardEntries)} entries')
    orderedEntries = sorted(discardEntries, key=lambda x: x["loggedTime"])

    foodWaste = {}
    for i in orderedEntries:
        # print(i)
        id = i['clientId']
        if id in foodWaste:
            foodWaste[id]['amount'] += (i['quantity'] - i['panWeight'])
        else:
            foodWaste[id] = {'name': i['itemName'].strip(), 'amount': (i['quantity'] - i['panWeight'])}

    print(f'{len(foodWaste)} unique items')

    generate_shrink_report(foodWaste)

    # finally:
    #     phoodServer.logout()

if __name__ == "__main__":
    main()