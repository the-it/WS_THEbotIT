__author__ = 'erik'

import os
import subprocess
import re
import requests
from PIL import Image

def add_zeros(number, digits):
    number_str = str(number)
    if number < 10:
        for members in range(digits-1):
            number_str = "0" + number_str
    elif number < 100:
        for members in range(digits-2):
            number_str = "0" + number_str
    elif number < 1000:
        for members in range(digits-3):
            number_str = "0" + number_str
    return number_str

def main():
    # create the neccessary subfolders
    if not os.path.exists('pics_raw'):
        os.mkdir('pics_raw')
    if not os.path.exists('pics_cut'):
        os.mkdir('pics_cut')
    if not os.path.exists('ocr'):
        os.mkdir('ocr')

    # iterating over all
    for i in range(1803, 2909, 2):
        i_str = add_zeros(i, 4)
        picture = requests.get(url='http://ia801407.us.archive.org/34/items/PWRE05-06/Pauly-Wissowa_III2_{}.png'.format(i_str))
        print(picture.status_code)
        error_code = picture.status_code
        ending = ".png"
        # is there content?
        if error_code == 404:
            #errorhandling
            picture = requests.get(url='http://ia801407.us.archive.org/34/items/PWRE05-06/Pauly-Wissowa_III2_{}.jpg'.format(i_str))
            error_code = picture.status_code
            ending = ".jpg"
            if error_code == 404:
                fobj = open("pics_raw/{}".format(i_str) +".ERROR", "wb")
                fobj.close()
        if error_code == 200:
            #save the picture in the raw folder and start the conversion
            fobj = open("pics_raw/{}".format(i_str) + ending, "wb")
            fobj.write(picture.content)
            fobj.close()

            im = Image.open("pics_raw/{}".format(i_str) + ending)
            #converting into JPG
            if ending == ".png":
                im.save("pics_raw/{}.jpg".format(i_str), "JPEG", quality=80, optimize=True, progressive=True)
            #calculate the half between the columns
            (width, height) = im.size
            half_width = int(width/2)
            list_of_colorsums = []
            range_slice = range(-200, 201, 1)
            #check every slice around the middle for the color value
            for k, j in enumerate(range_slice):
                im = im.convert("L")
                crop_image = im.crop((half_width+j, 0, half_width+j+1, height))
                list_of_colorsums.append(sum(list(crop_image.getdata()))/height)
            # the slice with the highest colorvalue should
            first_max_index = list_of_colorsums.index(max(list_of_colorsums))
            half = half_width+range_slice[first_max_index]

            crop_image_1 = im.crop((0, 0, half, height))
            crop_image_2 = im.crop((half, 0, width, height))
            crop_image_1.save("pics_cut/{}.png".format(add_zeros(i, 4)), "PNG")
            crop_image_2.save("pics_cut/{}.png".format(add_zeros(i+1, 4)), "PNG")
            print(i, ",",i+1)

            os.system('tesseract pics_cut/{}.png ocr/{}.txt -l deu'.format(add_zeros(i, 4), add_zeros(i, 4)))
            os.system('tesseract pics_cut/{}.png ocr/{}.txt -l deu'.format(add_zeros(i+1, 4), add_zeros(i+1, 4)))

if  __name__ =='__main__':main()
