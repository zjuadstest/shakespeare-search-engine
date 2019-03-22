from flask import Flask, render_template, request

from query import query
import json

result = []

app = Flask(__name__)


@app.route('/', methods=['post', 'get'])
def index():
    search_term = request.form.get('search-box')
    # only one word supported
    if not search_term:
        links = []
    else:
        links = query(search_term)

    return render_template("index.html", links=links)

if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=80)


