#!/usr/bin/env python3
import codecs
import configparser
import json
import os
import subprocess
import uuid

import redis
from bottle import post, run, template, request, delete

dir_path = os.path.dirname(os.path.realpath(__file__))
rs = redis.Redis()
ids = {}


@post('/classify')
def index():
    body = request.body.read().decode('utf-8')

    query = json.loads(body)['text']

    result_count = 50

    redis_cache = None
    if is_redis_available():
        redis_cache = rs.get(query)

    if redis_cache is None:

        temp_file_path = "/tmp/" + str(uuid.uuid1())

        temp_file = codecs.open(temp_file_path, "w", "utf-8")
        temp_file.write(query)
        temp_file.close()

        result_count = 50

        command = dir_path + '/fastText/fasttext predict-prob ' + dir_path + '/fastText/model.bin ' + temp_file_path + ' %i' % result_count
        res = subprocess.getoutput(command)
        os.remove(temp_file_path)

        if is_redis_available():
            rs.setex(query, res, 24 * 60 * 60)
    else:
        res = redis_cache.decode('utf-8')

    outputs = []
    segments = res.split()
    if len(segments) > 1:
        for i in range(0, result_count):
            key = segments[i * 2].replace('__label__', '').replace('_', ' ')
            prob = float(segments[(i * 2) + 1])

            if prob < 0.005:
                break

            outputs.append({
                "key": key,
                "prob": prob
            })

    return template(json.dumps(outputs))


@post('/document/{docId}')
def index(doc_id):
    body = request.body.read().decode('utf-8')

    line_number = ids[doc_id]
    if line_number is None:
        with open("training.txt", "a") as training_file:
            training_file.write(body.replace('\n', ' ').replace('\r', ' ') + '\n')
    else:
        #sed -i '5d' file.txt
        print()


@delete('/document/{docId}')
def delete(doc_id):
    #@TODO: delete line from index file and training file
    print()


def init_index():
    with open("index.txt", "r") as index_file:
        content = index_file.readlines()
    counter = 0
    for line in content:
        ids[line] = counter
        counter += 1


def is_redis_available():
    try:
        rs.get(None)  # getting None returns None or throws an exception
    except (redis.exceptions.ConnectionError,
            redis.exceptions.BusyLoadingError):
        return False
    return True

if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read(dir_path + "/config.ini")

    init_index()

    run(port=int(config.get('http_service', 'port')))
