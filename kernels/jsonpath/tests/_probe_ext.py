import json
from jsonpath_ng.ext import parse as p

STORE = {
    "store": {
        "book": [
            {"category": "reference", "author": "Nigel Rees", "title": "Sayings", "price": 8.95},
            {"category": "fiction", "author": "Evelyn Waugh", "title": "Sword", "price": 12.99},
            {"category": "fiction", "author": "Herman Melville", "title": "Moby", "isbn": "0-553-21311-3", "price": 8.99},
            {"category": "fiction", "author": "J. R. R. Tolkien", "title": "LOTR", "isbn": "0-395-19395-8", "price": 22.99},
        ],
        "bicycle": {"color": "red", "price": 19.95},
    }
}

cases = [
    "$..book[?(@.isbn)]",
    "$.store.book[?(@.price < 10)].title",
    "$.store.book[?(@.price <= 8.99)].title",
    "$.store.book[?(@.price > 20)].title",
    "$.store.book[?(@.price >= 12.99)].title",
    "$.store.book[?(@.price == 8.99)].title",
    "$.store.book[?(@.price != 8.99)].title",
    "$.store.book[?(@.category == 'fiction')].title",
    "$.store.book[?(@.price)].title",
    "$.store.book[?(@.price < 9)].title",
    "$.store.book[?(@.price == 9)].title",
    "$..book[?(@.price < 10 & @.category == 'fiction')].title",
    "$.store.book[?(@.category == 'fiction')].title",
    "$[?(@.price)]",
]
for e in cases:
    try:
        m = p(e).find(STORE)
        print(repr(e), "->", json.dumps([x.value for x in m], ensure_ascii=False))
    except Exception as ex:
        print(repr(e), "EXC", type(ex).__name__, ex)
