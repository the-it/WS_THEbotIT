import os
import internetarchive
import patoolib

list_of_archives = [['Pauly Supp.rar', 'PaulySupp'],
                    ['Pauly-Wissowa_54-66.rar', 'PaulyWissowa5466'],
                    ['Pauly-Wissowa_41-53.rar', 'PaulyWissowa4153_201412'],
                    ['Pauly-Wissowa_31-40.rar', 'PaulyWissowa3140_201412'],
                    ['Pauly-Wissowa_21-30.rar', 'PaulyWissowa2130'],
                    ['Pauly-Wissowa_11-20.rar', 'PaulyWissowa1120'],
                    ['Pauly-Wissowa_1-10.rar', 'PaulyWissowa110']]

folder = 'archives_IA'


def get_archive(filename, item):
    session = internetarchive.ArchiveSession()
    download = session.get_item(item).get_file(filename)
    download.download(os.getcwd() + os.sep + folder + os.sep + filename)


def unrar(item):
    patoolib.extract_archive(os.getcwd() + os.sep + folder + os.sep + item,
                             outdir=os.getcwd() + os.sep + folder,
                             interactive=False)


def get_archives_and_unzip():
    if not os.path.exists(os.getcwd() + os.sep + folder):
        os.makedirs(os.getcwd() + os.sep + folder)
    for item in list_of_archives:
        if not os.path.isfile(os.getcwd() + os.sep + folder + os.sep + item[0]):
            get_archive(item[0], item[1])
            unrar(item[0])


if __name__ == "__main__":
    get_archives_and_unzip()
