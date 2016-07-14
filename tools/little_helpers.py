import re

def load_password(filehandler):
    return re.search("^(.*)\n?", filehandler.read()).group(1)

if __name__ == "__main__":
    print(load_password(open('dummy_password.pwd')))