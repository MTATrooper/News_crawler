import json
import os
from pymongo import MongoClient
import requests

DATA_DIR = './data'
client = MongoClient(port=27017)
db=client.newspaper

find = db.source.find_one({'name': 'vnexpress'})
if find is None:
    db.source.insert_one({'name': 'vnexpress'})