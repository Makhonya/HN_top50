import requests_cache
import requests
from flask import Flask
import logging
from prometheus_flask_exporter import PrometheusMetrics
import datetime

requests_counter = 0
start = 0    # counter for service response time

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# logging config
logging.basicConfig(level=logging.INFO, filename="logs/logfile", filemode="w+",
                    format="%(asctime)-15s %(levelname)-8s %(message)s")

# static metric for gathering service response time
info = metrics.info('response_time', 'Response time for request')
@app.route('/stories')
def index():
    global start
    global requests_counter
    start = datetime.datetime.now()
    # create a session object and set it to never expire
    session = requests_cache.CachedSession(expire_after=-1)
    try:
        # request for top 500 stories
        top_comments = session.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=30).json()
        requests_counter += 1
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.Timeout) as err:
        print(err)

    stories = []   # list to return
    counter = 0
    authors = {}   # dictionary for storing dup users

    while len(stories) < 50:
        try:
            # gathering story data and fetching author
            post_url = f"https://hacker-news.firebaseio.com/v0/item/{top_comments[counter]}.json"
            requests_counter += 1
            response = session.get(post_url, timeout=30)
            comment = response.json()
            comment_author = comment['by']

            # checking if we already now the karma of this author
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

    # sorting by number of comments and adding position key.
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
