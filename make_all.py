import os
import csv

# dateFormatted = Date(Left([date],4),Right(left([date],6),2),right([date],2))
written_header = False
with open('all.csv', 'w', newline='', encoding='utf-8') as out_file:
    w = csv.writer(out_file)
    for filename in os.listdir('data'):
        path = os.path.join('data', filename)
        with open(path, 'r', newline='', encoding='utf-8') as in_file:
            r = csv.reader(in_file)
            for row in r:
                if row[0] == 'id':
                    if not written_header:
                        w.writerow(row)
                        written_header = True
                else:
                    w.writerow(row)
