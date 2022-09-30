import pymongo
import pandas as pd
import json


df=pd.read_csv("VaccineSlots.csv")
df.head()
data=df.to_dict(orient="records")

client = pymongo.MongoClient(
    "mongodb+srv://ashwinig:Test123456@cluster0.qpps0of.mongodb.net/?retryWrites=true&w=majority")
database = client['VaccineDB']
collections = database['VaccineSlots']

#collections.insert_many(data)

print(collections)