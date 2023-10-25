import sys

issue = int(sys.argv[1])
first_page = int(sys.argv[2])
count = int(sys.argv[3])

print(f"Nr. {issue}")
for i in range(first_page, first_page + count):
    print(f"[[Seite:Das Ausland (1828)_{i:04d}.jpg|{i-29}]]")
