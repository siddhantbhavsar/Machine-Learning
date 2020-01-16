import argparse
import os
import json

import phood_api

def get_parser():
    parser = argparse.ArgumentParser(description='Test phood ml api with image')
    parser.add_argument('-d', '--datapath', help='Path to images for inference')
    parser.add_argument('-i', '--imagename', help='Image file to classify')
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


def main():
    import config_prod as config

    parser = get_parser()
    args = parser.parse_args()

    # images = list_images(args.datapath)
    # print(images)

    phoodServer = phood_api.PhoodAPI(config.base_url)

    try:
        phoodServer.login(config.username, config.password).json()

        # test posting of an image
        image = open(args.imagename, 'rb')
        res = phoodServer.upload_ml(image)
        # print(res.json())
        print(json.dumps(res.json()['categoryOptions2'], indent=4, sort_keys=True))
    finally:
        pass
        # phoodServer.logout()


if __name__ == "__main__":
    main()
