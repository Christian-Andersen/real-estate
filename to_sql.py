import csv
import sqlalchemy

url = 'mysql://root:Q1w2e3r4@127.0.0.1/real_estate'
engine = sqlalchemy.create_engine(url, echo=True)
connection = engine.connect()
metadata = sqlalchemy.MetaData()
test = sqlalchemy.Table('properties', metadata, autoload=True, autoload_with=engine)
values_list = []
# with open('data/4553.csv', 'r', encoding='utf-8') as f:
#     r = csv.DictReader(f)
#     for row in r:
#         new_row = row
#         for key, value in new_row.items():
#             if value == '':
#                 new_row[key] = None
#         values_list.append(new_row)

query = sqlalchemy.insert(test)
ResultProxy = connection.execute(query, values_list)
