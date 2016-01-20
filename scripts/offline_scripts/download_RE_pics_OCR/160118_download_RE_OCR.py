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
    if not os.path.exists('pics_raw'):
        os.mkdir('pics_raw')
    if not os.path.exists('pics_cut'):
        os.mkdir('pics_cut')
    if not os.path.exists('ocr'):
        os.mkdir('ocr')

    for i in range(1, 1441, 2):
        i_str = add_zeros(i, 4)
        picture = requests.get(url='http://ia601407.us.archive.org/34/items/PWRE05-06/Pauly-Wissowa_III1_{}.png'.format(i_str)) #573, 749, 903, 1121, 1375 fehlen auf dem Server
        print(picture.status_code)
        if picture.status_code == 404:
            fobj = open("pics_raw/{}".format(i_str) +".ERROR", "wb")
            fobj.close()
        else:
            fobj = open("pics_raw/{}".format(i_str) +".png", "wb")
            fobj.write(picture.content)
            fobj.close()
        if picture.status_code != 404:
            im = Image.open("pics_raw/{}".format(i_str) +".png")
            im.save("pics_raw/{}.jpg".format(i_str), "JPEG", quality=80, optimize=True, progressive=True)
            (width, height) = im.size
            #calculate the real half
            half_width = int(width/2)
            list_of_colorsums = []
            counter = 0
            range_slice = range(-200, 201, 1)
            for k, j in enumerate(range_slice):
                crop_image = im.crop((half_width+j, 0, half_width+j+1, height))
                #crop_image.show()
                list_of_colorsums.append(sum(list(crop_image.getdata()))/height)
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
