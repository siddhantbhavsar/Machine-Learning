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
import timeit
import hashlib
import os
from datetime import datetime
from decimal import Decimal
import json

import boto3
import io
from PIL import Image
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
    parser = argparse.ArgumentParser(description='Test rekognition response time given a set of images on the file system')
    parser.add_argument('-d', '--datapath', help='Path to images for inference', required=True)
    parser.add_argument('-o', '--database', default='WFM_ImageInfo', help='Database table to output results to')
    parser.add_argument('-m', '--max', help='Maximum number of images to infer (-1 to process them all)', default=-1, type=int)

    return parser

def list_images(datadir='./images'):
    item_list = {}
    food_names = []
    for root, dirs, files in os.walk(datadir, topdown=False):
        for name in dirs:
            dir_name = os.path.join(root, name).split('/')[-1]
            item_list[dir_name] = []
            food_names.append(dir_name)

    for root, dirs, files in os.walk(datadir, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            foodtype = filename.split('/')[-2]
            item_list[foodtype].append(filename)

    return item_list

def infer_image(imagefile, rek_client):
    start = timeit.default_timer()
    print(imagefile)
    image = Image.open(open(imagefile, 'rb'))
    stream = io.BytesIO()
    image.save(stream, format=image.format)
    image_binary = stream.getvalue()

    response = rek_client.detect_labels(Image={'Bytes': image_binary}, MaxLabels=10, MinConfidence=50.0)
    # pprint(response['Labels'])
    end = timeit.default_timer() - start
    print(f"inference time: {end}\n")

    return response,end

def infer_images(image_list=None, max_images=-1, dest_db='WFM_ImageInfo'):
    rek = boto3.client('rekognition')
    # Get the service resource.
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(dest_db)

    rek_results = {}

    for foodtype in image_list:
        print(foodtype)
        if max_images > 0:
            food_images = image_list[foodtype][:max_images]
        else:
            food_images = image_list[foodtype]

        image_results = []
        for imagename in food_images:
            hash_object = hashlib.md5(imagename.encode())
            # print(hash_object.hexdigest())

            response,runtime = infer_image(imagename, rek_client=rek)

            result_item = {
                'foodtype': foodtype,
                'timestamp': datetime.timestamp(datetime.now()),
                'imageId': hash_object.hexdigest(),
                'dataset': 'WFM001',
                'imageName': imagename,
                'inferenceTime': runtime,
                'inference': response['Labels'],
            }
            image_results.append(json.loads(json.dumps(result_item), parse_float=Decimal))

        # start = timeit.default_timer()
        # print(f"pushing inferences for {len(food_images)} of type {foodtype}")

        with table.batch_writer() as batch:
            for item in image_results:
                batch.put_item(Item=item)

        # end = timeit.default_timer() - start
        # print(f"execution time: {end}\n")

    return rek_results


def main():
    parser = get_parser()

    args = parser.parse_args()

    images = list_images(args.datapath)

    for food in images:
        print(f"{food}: {len(images[food])}")

    infer_images(images, max_images=args.max, dest_db=args.database)

if __name__ == "__main__":
    main()

