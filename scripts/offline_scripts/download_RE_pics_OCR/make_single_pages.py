import os
import requests
import internetarchive

folder = 'pages'

def from_IA(book, item, filepattern, start, steps, finish):
    if not os.path.exists(os.getcwd() + os.sep + folder + os.sep + book):
        os.makedirs(os.getcwd() + os.sep + folder + os.sep + book)

    session = internetarchive.ArchiveSession()
    re_item = session.get_item(item)
    list_of_pages = range(start, finish + steps, steps)
    for idx, i in enumerate(list_of_pages):
        print('Band: {}, Seite:{}/{}, {}'.format(book, idx, len(list_of_pages), filepattern.format(i)))
        file_on_harddisk = os.getcwd() + os.sep + folder + os.sep + book + os.sep + '{0:04d}.png'.format(i)
        if not os.path.isfile(file_on_harddisk):
            try:
                re_file = re_item.get_file(filepattern.format(i))
                re_file.download(file_on_harddisk, silent = True)
            except:
                print('{} is not an item'.format(filepattern.format(i)))



def make_single_pages():
    if not os.path.exists(os.getcwd() + os.sep + folder):
        os.makedirs(os.getcwd() + os.sep + folder)
    from_IA(book='I,1', item='PWRE01-02', filepattern='Pauly-Wissowa_I1_{0:04d}.png', start=1, steps=2, finish=1439)
    from_IA(book='I,2', item='PWRE01-02', filepattern='Pauly-Wissowa_I2_{0:04d}.png', start=1441, steps=2, finish=2901)


if __name__ == "__main__":
    make_single_pages()