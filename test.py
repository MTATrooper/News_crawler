import json
import os
from pymongo import MongoClient
import requests

DATA_DIR = './data'
client = MongoClient(port=27017)
db=client.newspaper

def insertDB(page):
    PAGE_DIR = os.path.join(DATA_DIR, page)
    for filename in os.listdir(PAGE_DIR):
        print(filename)
        with open(os.path.join(PAGE_DIR, filename), 'r') as f:
            data = json.loads(f.read())
        for news in data:
            if len(news['content']) >= 5:
                content = ' '.join(news['content'] if len(news['content'][-1]) > 30 else news['content'][:-1])
                dic = {'text': content}
                respond = requests.post('http://localhost:5555/summary', json=dic)
                news['summary'] = respond.json()['key']
                print(news['summary'])
insertDB('dantri')