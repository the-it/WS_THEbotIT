import os
import requests
import internetarchive



def from_IA(book, pattern, start, steps, finish):
    if not os.path.exists(os.getcwd() + os.sep + 'pages' + os.sep + book):
        os.makedirs(os.getcwd() + os.sep + 'pages' + os.sep + book)
    for i in range(start, finish+steps, steps):
        print(pattern.format(i))

        if not os.path.exists(os.getcwd() + os.sep + 'pages' + os.sep + book + os.sep + '{0:04d}.png'.format(i)):
            response = requests.get(url=pattern.format(i), headers={'User-Agent': 'Python-urllib/3.1'}, timeout=1000)
            if response.status_code == 200:
                with open(os.getcwd() + os.sep + 'pages' + os.sep + book + os.sep + '{0:04d}.png'.format(i), 'wb') as filehandler:
                    filehandler.write(response.content)
            else:
                raise ConnectionError(response.status_code)


def make_single_pages():
    if not os.path.exists(os.getcwd() + os.sep + 'pages'):
        os.makedirs(os.getcwd() + os.sep + 'pages')
    from_IA(book='I,1', pattern='http://ia800202.us.archive.org/2/items/PWRE01-02/Pauly-Wissowa_I1_{0:04d}.png', start=1, steps=2, finish=1439)


if __name__ == "__main__":
    make_single_pages()