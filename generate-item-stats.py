# Copyright 2010-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# This file is licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License. A copy of the
# License is located at
#
# http://aws.amazon.com/apache2.0/
#
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import argparse
import decimal
import timeit
import json

import boto3
from boto3.dynamodb.conditions import Key, Attr
from pprint import pprint

food_list = [
'AlooGobi',
'AmericanChopSuey',
'ArtichokeHearts',
'AsparagusHazelnutPastaSalad',
'BBQChicken',
'BeefMeatballMarinara',
'BeetsShredded',
'BlackOlives',
'BlueCheeseCrumbles',
'CarrotFeta&SpringOnionSalad',
'CheeseLasagna',
'ChickenBroccoliAlfredoPasta',
'ChickenCaccaitore',
'ChickenCeasarPastaSalad',
'ChickenTikkaMasala',
'CilantroLimeChickenWings',
'CitrusMarinatedOlives',
'Corn',
'Corn&ArugulaSalad',
'Cucumber',
'Dolmas',
'Edamame',
'EggplantRiccottaRollonti',
'FetaMintQuinoa&WatercressSalad',
'FriedPlantains',
'GarlicWinePoachedPollock',
'GigandeBeans',
'GoldenBeatSalad',
'GreenGoddessEggSalad',
'GreenPeas',
'HerbRoastedPotatoes',
'Hummus',
'KaleWhiteBeanSalad',
'Macaroni&Cheese',
'MarinatedFetaCheese',
'MashedPotatoes',
'MixedBellPeppers',
'Quinoa',
'QuinoaSalad',
'Radishes',
'RedCabbage',
'RedOnions',
'RoastedBrusselSprouts',
'RoastedButternutSquash',
'SauteedCollaredGreens',
'SauteedGarlicMushrooms',
'SeasonalPickMushrooms',
'ShreddedCarrots',
'Spinach',
'SteamBroccoli',
'TahiniChickapeaSalad',
'TailgateColeslaw',
'Tomatoes',
'TurmericRoastedSweetPotatoes',
'Tzatziki',
'VeganAsparagusGoldenBeatApricotSalad',
'VeganIsrealiCucumberSalad',
'VeganRoastedVegtables',
'VegtableKorma',
'VegtableZuccini',
'YellowCurryRice',
'YuccaFries',
]

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def get_parser():
    parser = argparse.ArgumentParser(description='Query dynamo db for a particular food type')
    parser.add_argument('-i', '--fooditem', help='Food item to query for')
    # parser.add_argument('-a', '--all', help='Run statistics for all fooditems', acton='store_true')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')

    return parser

def get_records(foodtype):
    # Get the service resource.
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('WFM_ImageTime')

    start = timeit.default_timer()
    response = table.query(KeyConditionExpression=Key('foodtype').eq(foodtype))
    end = timeit.default_timer() - start
    print(f"{len(response['Items'])} records for {foodtype} queried time: {end}")

    return response['Items']

def calculate_label_weights(db_records):
    record_cnt = len(db_records)
    label_weights = {}
    for r in db_records:
        label_names = []
        for i in r['inference']:
            label,confidence = i['Name'],i['Confidence']
            if label not in label_weights:
                label_weights[label] = confidence/record_cnt
            else:
                label_weights[label] += confidence/record_cnt
            label_names.append(label)

    return label_weights,record_cnt

def save_weights_to_dyanmo(item_weights, verbose=None):
    dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table('WFM_LabelWeights')

    with table.batch_writer() as batch:
        for i in item_weights:
            if verbose:
                print(json.dumps(i, cls=DecimalEncoder))
            batch.put_item(Item=i)

def main():
    global food_list

    parser = get_parser()
    args = parser.parse_args()

    print(args.fooditem)

    if args.fooditem:
        food_list = [args.fooditem]

    fooditem_info = []
    for foodname in food_list:
        records = get_records(foodname)
        w,rc = calculate_label_weights(records)
        fooditem_info.append(
            {
                'foodtype': foodname,
                'record_count': rc,
                'label_weights': w,
                'label_count': len(w),
            })

    if args.verbose:
        print(json.dumps(fooditem_info, cls=DecimalEncoder))

    save_weights_to_dyanmo(fooditem_info, verbose=args.verbose)

if __name__ == "__main__":
    main()