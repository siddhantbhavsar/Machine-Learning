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

dynamodb = None
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
    parser.add_argument('-i', '--fooditem', help='Name of food to query for', required=True)
    parser.add_argument('-m', '--max', help='Maximum number of images to infer', default=-1, type=int)
    parser.add_argument('-t', '--top', help='Number of top matches ot list', default=3, type=int)

    return parser

def get_label_weights(table_name='WFM_LabelWeights'):
    # Get the service resource.
    table = dynamodb.Table(table_name)

    label_weights = {}

    response = table.scan()
    for i in response['Items']:
        # print(json.dumps(i, cls=DecimalEncoder))
        label_weights[i['foodtype']] = i['label_weights']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        for i in response['Items']:
            # print(json.dumps(i, cls=DecimalEncoder))
            label_weights[i['foodtype']] = i['label_weights']

    return label_weights

def get_records(foodtype, maxrecords=-1):
    global dynamodb
    # Get the service resource.
    table = dynamodb.Table('WFM_ImageTime')

    # start = timeit.default_timer()
    response = table.query(KeyConditionExpression=Key('foodtype').eq(foodtype))
    # end = timeit.default_timer() - start
    # print(f"query time: {end}\n")

    if maxrecords > 0:
        return response['Items'][:maxrecords]

    return response['Items']

def calculate_match(inference, class_weights):
    # extract weights from inferences
    # print(json.dumps(inference, cls=DecimalEncoder))
    inference_weights = {}
    for i in inference:
        inference_weights[i['Name']] = i['Confidence']
    inference_labels = set(inference_weights.keys())

    type_match = {}
    for foodtype in class_weights:
        foodtype_weights = class_weights[foodtype]
        food_labels = set(foodtype_weights.keys())

        type_match[foodtype] = 0
        matching_labels = food_labels.intersection(inference_labels)
        for l in matching_labels:
            type_match[foodtype] += inference_weights[l] * foodtype_weights[l]

    return type_match

def main():
    global dynamodb
    parser = get_parser()
    args = parser.parse_args()

    # Get the service resource.
    dynamodb = boto3.resource('dynamodb')
    weights = get_label_weights()
    # print(json.dumps(weights, cls=DecimalEncoder))

    records = get_records(args.fooditem, maxrecords=args.max)
    print(f"testing {len(records)} items of type {args.fooditem}")
    matches = {}
    for rec in records:
        filename = rec['imageName'].split('/')[-1]
        matches[filename] = calculate_match(rec['inference'], weights)

    for m in matches:
        print(f"match for {m}:")
        i = 1
        for key, value in sorted(matches[m].items(), key=lambda item: item[1], reverse=True)[:args.top]:
            print(f"{i}: {key}: {value:.2f}")
            i += 1
        print()

if __name__ == "__main__":
    main()

