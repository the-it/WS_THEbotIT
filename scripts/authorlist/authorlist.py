__author__ = 'erik'

from tools.catscan import CatScan
import os

class AuthorList:
    def __init__(self, age):
        self.last_run = age

    def run(self):
        searcher = CatScan()
        # is there pre rawdata existend?
        if os.path.isfile('raw_data.json') is True:
            #import database
            pass
        else:
            #creating database
            searcher.max_age(self.last_run + 1) #all changes from age + 1 hour
        searcher.add_namespace(0) # search in main namespace
        searcher.add_positive_category('Autoren')
        searcher.add_yes_template('Personendaten')
        result = searcher.run()

if __name__ == "__main__":
    run = AuthorList(1000000)
    run.run()