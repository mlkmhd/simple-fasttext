#!/usr/bin/env python3
import codecs
import configparser
import json
import subprocess
import uuid
import redis
from bottle import post, run, template, request, delete, get
import os
import glob

dir_path = os.path.dirname(os.path.realpath(__file__))
rs = redis.Redis()
#db = shelve.open('db')
document_dir = dir_path + '/documents'
training_dir = dir_path + '/training'


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


@post('/document/<doc_id>')
def index(doc_id):
    body = request.body.read().decode('utf-8')

    body = json.loads(body)

    text = ""

    for label in body['labels']:
        text += "label__" + label.replace(' ', '_') + " "

    text += body['text'].replace('\n', ' ').replace('\r', ' ')

    with open(document_dir + "/" + doc_id, "a") as document_file:
        document_file.write(text)

    return {"acknowledgment": True}


@delete('/document/<doc_id>')
def delete(doc_id):
    file_path = document_dir + '/' + doc_id

    if os.path.isfile(file_path):
        os.remove(file_path)
        return {"acknowledgment": True}
    else:
        return {'error': 'file not found'}


@get('/train')
def create_training_file():

    training_file = training_dir + '/training.txt'

    if os.path.isfile(training_file):
        os.remove(training_file)

    with open(training_file, 'a') as outfile:
        for filename in glob.glob(document_dir + '/*'):
            with open(filename, 'rb') as readfile:
                outfile.write(readfile.read().decode('utf-8') + '\n')

    os.system(dir_path + '/fastText/fasttext supervised -input ' + training_file + ' -output '+ training_dir + '/model')

    return "ok"


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

    if not os.path.isdir(document_dir):
        os.mkdir(document_dir)

    if not os.path.isdir(training_dir):
        os.mkdir(training_dir)

    run(port=int(config.get('http_service', 'port')))
