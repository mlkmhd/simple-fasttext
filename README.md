# simple-fasttext
simple and ultra fast library on top of facebook fasttext

## install

```
$ git clone --recursive https://github.com/mlkmhd/simple-fasttext`
$ cd simple-fasttext
$ install.sh
$ python run.py
```

## Usage:

index all your documents. each document should have a text and array of labels:

```
$ curl -XPOST http://localhost:8020/document/{document_id} -d '{
    "labels": ["java", "python"],
    "text": "java and python are very simple!"
}'
```

and then you can start training by this:

```
$ curl -XGET http://localhost:8020/train
```

it'll take a few minute to train (or maybe an hour. it depends on your training data size)

then you can use classifier like this:

```
$ curl -XPOST http://localhost:8020/classify -d '{
    "text": "some example text"
}'


response: 
[
    {
        "key": "java",
        "prob": 0.98
    },
    {
        "key": "python",
        "prob": 0.01
    }
]
```