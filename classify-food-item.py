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
import io
import timeit
import json
from decimal import Decimal

import boto3
from PIL import Image

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
    parser.add_argument('-i', '--imagename', help='Image file to classify', required=True)
    parser.add_argument('-o', '--database', default='WFM_Images', help='Database table to output results to')
    parser.add_argument('-t', '--top', help='Number of top matches ot list', default=5, type=int)

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

def preprocess_image(im):
    width, height = im.size  # Get dimensions

    left = 0
    top = 0
    right = width
    bottom = height
    if height > width:
        top = (height - width) / 2
        bottom = (height + width) / 2
    elif width > height:
        left = (width - height) / 2
        right = (width + height) /2

    # Crop the center of the image
    return im.crop((left, top, right, bottom)).resize((320,320))

def infer_image(imagefile, rek_client):
    print(imagefile)
    image = Image.open(open(imagefile, 'rb'))
    file_format = image.format
    image = preprocess_image(image)
    print(image.size)
    stream = io.BytesIO()
    image.save(stream, format=file_format)
    image_binary = stream.getvalue()

    start = timeit.default_timer()
    response = rek_client.detect_labels(Image={'Bytes': image_binary}, MaxLabels=10, MinConfidence=50.0)
    end = timeit.default_timer() - start
    print(f"inference time: {end}\n")

    response_json = json.loads(json.dumps(response), parse_float=Decimal)

    return response_json,end

def calculate_match(inference, class_weights):
    # extract weights from inferences
    inference_weights = {}
    for i in inference['Labels']:
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

    rek = boto3.client('rekognition')
    test_inference,runtime = infer_image(args.imagename, rek_client=rek)
    # print(json.dumps(test_inference, cls=DecimalEncoder))

    item_match = calculate_match(test_inference, weights)

    for key, value in sorted(item_match.items(), key=lambda item: item[1], reverse=True)[:args.top]:
        print(f"{key}: {value:.2f}")


if __name__ == "__main__":
    main()

