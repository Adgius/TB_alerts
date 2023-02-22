import pandas as pd
import datetime as dt
import random
import time
import sys

# App Store
from itunes_app_scraper.scraper import AppStoreScraper
from app_store_scraper import AppStore

# Google Play
from google_play_scraper import app, Sort, reviews
from datetime import datetime, timedelta

from tqdm import tqdm

import logging
logging.getLogger("Base").setLevel(logging.CRITICAL)


def gp_rating():
	result = app(
	    'goldapple.ru.goldapple.customers',
	    lang='ru', # defaults to 'en'
	    country='ru' # defaults to 'us'
	)

	df = pd.Series({'score': result['score'], 
					 'ratings': result['ratings'], 
					 'date': dt.datetime.now(),
					 'source': 'GooglePlay'})
	return df

def as_rating():

	def find_score(app_res):
	    score = 0
	    for s in app_res:
	        score += app_res[s] * s
	    return score / sum(app_res.values())

	scraper = AppStoreScraper()
	app_res = scraper.get_app_ratings(1154436683, countries='ru')

	df = pd.Series({'score': find_score(app_res), 
					 'ratings': sum(app_res.values()), 
					 'date': dt.datetime.now(),
					 'source': 'AppStore'})
	return df

def save_df():

	df_gp = gp_rating()
	df_as = as_rating()
	res = pd.concat([df_gp, df_as], axis=1).T
	res_old = pd.read_csv('./ds/res.csv')
	res = pd.concat([res_old, res])
	res.drop_duplicates(inplace=True)
	res.to_csv('./ds/res.csv', index=False)


def scrap_reviews(n=200):
    country_lang_pairs = [('ru', 'ru'), ('ru', 'kz'), ('kz', 'kz'), ('ru', 'by'), ('by', 'by')]
    #GP
    sys.stdout.write('Processing GooglePlay reviews:')
    gp = pd.DataFrame()
    for pair in tqdm(country_lang_pairs):
        result, _ = reviews(
            'goldapple.ru.goldapple.customers',
            lang=pair[0], 
            country=pair[1],
            sort=Sort.NEWEST, # defaults to Sort.NEWEST
            count=n, # defaults to 100
        )
        gp_ = pd.DataFrame(result)
        gp_ = gp_[['content', 'score', 'at']]
        gp = pd.concat([gp, gp_])
    gp = gp.drop_duplicates('content')

    #AS
    sys.stdout.write('Processing AppStore reviews:')
    ap_s = pd.DataFrame()
    for country in tqdm(['ru', 'kz', 'by']):
        my_app = AppStore(
        country=country,  
        app_name='Золотое Яблоко'.encode('utf-8'),
        app_id=1154436683 
        ) 
        my_app.review(after=dt.datetime.now()-timedelta(days=3))
        ap_s_ = pd.DataFrame(my_app.reviews)
        if ap_s_.shape[0] > 0:
            ap_s_ = ap_s_[['review', 'rating', 'date']]
            ap_s = pd.concat([ap_s, ap_s_]).drop_duplicates()

    # saving
    pd.concat([pd.read_csv('./ds/AS_reviews.csv', dtype={'review': str, 'rating': int}, parse_dates=['date']), ap_s]).drop_duplicates().to_csv('./ds/AS_reviews.csv', index=False)
    pd.concat([pd.read_csv('./ds/GP_reviews.csv', dtype={'content': str, 'score': int}, parse_dates=['at']), gp]).drop_duplicates().to_csv('./ds/GP_reviews.csv', index=False)

    sys.stdout.write('Successfully')