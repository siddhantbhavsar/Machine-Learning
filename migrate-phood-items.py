#
#  Copyright 2010-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#  This file is licensed under the Apache License, Version 2.0 (the "License").
#  You may not use this file except in compliance with the License. A copy of
#  the License is located at
#
#  http://aws.amazon.com/apache2.0/
#
#  This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#  CONDITIONS OF ANY KIND, either express or implied. See the License for the
#  specific language governing permissions and limitations under the License.
#
from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
# from boto3.dynamodb.conditions import Key, Attr

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table('WFM_Images')
table2 = dynamodb.Table('WFM_ImageTime')

response = table.scan( )

with table2.batch_writer() as batch:
    for i in response['Items']:
        # print(json.dumps(i, cls=DecimalEncoder))
        batch.put_item(Item=i)

while 'LastEvaluatedKey' in response:
    response = table.scan( ExclusiveStartKey=response['LastEvaluatedKey'] )

    with table2.batch_writer() as batch:
        for i in response['Items']:
            # print(json.dumps(i, cls=DecimalEncoder))
            batch.put_item(Item=i)
