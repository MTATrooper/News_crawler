import json
import os
from pymongo import MongoClient
import requests

DATA_DIR = './data'
client = MongoClient(port=27017)
db=client.newspaper

pages = db.source.find({}, {'_id':0,'name':1, 'fullname':1})
print(list(pages))