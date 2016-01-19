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
    for i in range(471,1441,2):
        print(i)
        try:
            os.mkdir('pics_raw')
            os.mkdir('pics_slice')
            os.mkdir('pics_cut')
            os.mkdir('ocr')
        except:
            pass
        i_str = add_zeros(i, 4)
        picture = requests.get(url='http://ia601407.us.archive.org/34/items/PWRE05-06/Pauly-Wissowa_III1_{}.png'.format(i_str))
        fobj = open("pics_raw/{}".format(i_str) +".png", "wb")
        fobj.write(picture.content)
        fobj.close()

        im = Image.open("pics_raw/{}".format(i_str) +".png")
        print(list(im.getdata()))

        process = subprocess.Popen(['identify', 'pics_raw/{}.png'.format(i_str)], stdout=subprocess.PIPE)
        x = str(process.stdout.read())
        result = re.search('(\d{1,4})x(\d{1,4})', x)
        half = int(result.group(1))/2

        #calculate the real half
        for j in range(-20, 22, 2):
            process_string = 'convert pics_raw/{}.png -crop 1x{}+{}+0 pics_slice/b_{}.png'.format(add_zeros(i, 4), result.group(2), int(half + j), j)
            print(process_string)
            os.system(process_string)


        print(add_zeros(i, 4), int(half), result.group(2), add_zeros(i, 4))
        os.system('convert pics_raw/{}.png -crop {}x{}+0+0 pics_cut/{}.png'.format(add_zeros(i, 4), int(half), result.group(2), add_zeros(i, 4)))
        os.system('convert pics_raw/{}.png -crop {}x{}+{}+0 pics_cut/{}.png'.format(add_zeros(i, 4), int(half), result.group(2), int(half), add_zeros(i+1, 4)))

        os.system('tesseract pics_cut/{}.png ocr/{}.txt -l deu'.format(add_zeros(i, 4), add_zeros(i, 4)))
        os.system('tesseract pics_cut/{}.png ocr/{}.txt -l deu'.format(add_zeros(i+1, 4), add_zeros(i+1, 4)))

if  __name__ =='__main__':main()
