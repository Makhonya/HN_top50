import requests_cache
import requests
from flask import Flask
import logging
from prometheus_flask_exporter import PrometheusMetrics
import datetime

requests_counter = 0
start = 0

app = Flask(__name__)
metrics = PrometheusMetrics(app)

logging.basicConfig(level=logging.INFO, filename="logs/logfile", filemode="w+",
                    format="%(asctime)-15s %(levelname)-8s %(message)s")

info = metrics.info('response_time', 'Response time for request')
@app.route('/stories')
def stories():
    global start
    global requests_counter
    start = datetime.datetime.now()
    session = requests_cache.CachedSession()
    try:
        top_comments = session.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=30).json()
        requests_counter += 1
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.Timeout) as err:
        print(err)

    stories = []
    counter = 0
    authors = {}

    while len(stories) < 50:
        try:
            post_url = f"https://hacker-news.firebaseio.com/v0/item/{top_comments[counter]}.json"
            requests_counter += 1
            response = session.get(post_url, timeout=30)
            comment = response.json()
            comment_author = comment['by']

            if comment_author not in authors:
                user_url = f"https://hacker-news.firebaseio.com/v0/user/{comment_author}.json"
                requests_counter += 1
                user_info = session.get(user_url, timeout=30)
                user = user_info.json()
                authors[user['id']] = user['karma']

            if authors[comment_author] > 2413:
                story = {
                    "author": comment_author,
                    "karma": user['karma'],
                    "comments": comment['descendants'],
                    "title": comment['title']
                }
                stories.append(story)
            counter += 1
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.Timeout) as err:
            print(err)

    stories.sort(key=lambda x: x['comments'], reverse=True)
    for i in range(len(stories)):
        stories[i]['position'] = i + 1

    logging.info(f"Total number of requests - {requests_counter}")
    start = datetime.datetime.now() - start
    info.set(start.total_seconds())
    return {"stories": stories}

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=57729)
