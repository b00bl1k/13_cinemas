import datetime
import json
import requests
from bs4 import BeautifulSoup

AFISHA_URL = "https://www.afisha.ru/msk/schedule_cinema/"
KINOPOISK_URL = "https://www.kinopoisk.ru"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36"
PROXY_FILE = "proxies.txt"


def load_proxies_list(filepath):
    with open(filepath, "r") as fh:
        return fh.read().splitlines()


def fetch_afisha_titles():
    now_date = datetime.datetime.now().strftime("%d-%m-%Y")
    resp = requests.get(
        AFISHA_URL,
        headers={
            "accept": "application/json"
        },
        params={
            "sort": "popular",
            "date": now_date
        }
    )
    movies = json.loads(resp.text)
    return [movie["Name"] for movie in movies["ScheduleWidget"]["Items"]]


def fetch_movie_id(movie_title):
        resp = requests.get(
            KINOPOISK_URL,
            params={
                "kp_query": movie_title
            },
            headers={
                "User-Agent": USER_AGENT
            }
        )

        page = BeautifulSoup(resp.text, "html.parser")
        most_wanted = page.find("div", {"class": "most_wanted"})
        if not most_wanted:
            return None

        try:
            return page.find("a", text=movie_title)["data-id"]
        except (KeyError, TypeError):
            return None


def fetch_movie_info(proxies, movie_id, timeout=3):
    for proxy in proxies:
        try:
            resp = requests.get(
                "{}/film/{}/".format(
                    KINOPOISK_URL,
                    movie_id
                ),
                headers={
                    "User-Agent": USER_AGENT
                },
                proxies={"https": proxy},
                timeout=timeout
            )
        except requests.exceptions.RequestException:
            continue

        page = BeautifulSoup(resp.text, "html.parser")
        block_rating = page.find("div", {"id": "block_rating"})
        if not block_rating:
            continue

        try:
            rating_value = page.find("meta", itemprop="ratingValue")["content"]
            rating_count = page.find("meta", itemprop="ratingCount")["content"]
            return float(rating_value), int(rating_count)
        except (KeyError, TypeError):
            return None


def output_movies_to_console(movies, max_movies=10):
    for movie in movies[:max_movies]:
        print("{} *{} / {}".format(*movie))


def main():
    proxies = load_proxies_list(PROXY_FILE)
    movie_titles = fetch_afisha_titles()
    movies = []
    for movie_title in movie_titles:
        movie_id = fetch_movie_id(movie_title)
        if not movie_id:
            continue
        movie_rating = fetch_movie_info(proxies, movie_id)
        if not movie_rating:
            continue
        movies.append((movie_title, movie_rating[0], movie_rating[1]))
    top_movies = sorted(movies, key=lambda k: k[1], reverse=True)
    output_movies_to_console(top_movies)


if __name__ == "__main__":
    main()
