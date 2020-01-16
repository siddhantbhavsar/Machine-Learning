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
    # parser.add_argument('-m', '--max', help='Maximum number of images to infer', default=100, type=int)

    return parser

def get_records(foodtype):
    # Get the service resource.
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('WFM_ImageTime')

    start = timeit.default_timer()
    response = table.query(KeyConditionExpression=Key('foodtype').eq(foodtype))
    end = timeit.default_timer() - start
    print(f"query time: {end}\n")

    return response['Items']

def main():
    parser = get_parser()
    args = parser.parse_args()

    records = get_records(args.fooditem)
    print(len(records))
    # for i in records:
    #     print(json.dumps(i, cls=DecimalEncoder))


if __name__ == "__main__":
    main()

