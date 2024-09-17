import streamlit as st
from openai import OpenAI, AsyncOpenAI
import requests
import json
import pandas as pd
from pandas import json_normalize
from typing import List, Literal, Generator



class OddsData:
    def __init__(self, eventId: str):
        self.eventId = eventId
        self.initialize()
        self.format_url()
        self.get_data()
    
    def initialize(self):
        self.headers = {'Accept': 'application/json', 'Accept-Encoding': 'gzip, deflate, br', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36', 'Connection': 'keep-alive'}
        self.base_url = st.secrets.draftkings.odds_url
        self.json_path = st.secrets.draftkings.odds_data_json
        self.csv_path = st.secrets.draftkings.odds_data_csv

    def format_url(self):
        self.request_url = self.base_url.format(self.eventId)

    def get_data(self):
        self._request_data()
        self._write_json_data()
        self._load_data()
        self._get_dataframe()
        self._write_csv_data()

    def _request_data(self):
        self.response = requests.get(url=self.request_url, headers=self.headers)
        self.data = self.response.json()
        

    def _write_json_data(self):
        with open(self.json_path, "w") as file:
            json.dump(obj=self.data, fp=file, indent=4)

    def _load_data(self):
        with open(file=self.json_path, mode="r") as file:
            self.file_data = json.load(fp=file)
            self.odds_data = self.file_data['eventGroup']['offerCategories']

    def _get_dataframe(self):
        self.all_dfs = []
        for category in self.odds_data:
            for descriptor in category.get('offerSubcategoryDescriptors', []):
                for offer_list in descriptor.get('offerSubcategory', {}).get('offers', []):
                    # Since offer_list is a list of lists, iterate over it
                    for offer in offer_list:
                        # Ensure 'outcomes' is a list before proceeding
                        if isinstance(offer.get('outcomes'), list):
                            for outcome in offer['outcomes']:
                                # Collect data at this level
                                flattened_data = {
                                    'eventGroupId': self.file_data['eventGroup']['eventGroupId'],
                                    'displayGroupId': self.file_data['eventGroup']['displayGroupId'],
                                    'eventGroupName': self.file_data['eventGroup']['name'],
                                    'offerCategoryId': category['offerCategoryId'],
                                    'offerCategoryName': category['name'],
                                    'subcategoryId': descriptor['subcategoryId'],
                                    'subcategoryName': descriptor['name'],
                                    'offerSubcategoryName': descriptor['offerSubcategory']['name'],
                                    'offerSubcategoryId': descriptor['offerSubcategory']['subcategoryId'],
                                    'offerLabel': offer.get('label', ''),
                                    'outcomeLabel': outcome.get('label', ''),
                                    'oddsAmerican': outcome.get('oddsAmerican', ''),
                                    'oddsDecimal': outcome.get('oddsDecimal', ''),
                                    'participant': outcome.get('participant', ''),
                                    # Add any additional fields you need here
                                }
                                self.all_dfs.append(flattened_data)
        self.df = pd.DataFrame(self.all_dfs)
    
    def _write_csv_data(self):
        self.df.to_csv(path_or_buf=self.csv_path)


class EventsData:
    def __init__(self, sportId: str):
        self.sportId = sportId
        self.initialize()
        self.format_url()
        self.get_data()
    
    def initialize(self):
        self.headers = {'Accept': 'application/json', 'Accept-Encoding': 'gzip, deflate, br', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36', 'Connection': 'keep-alive'}
        self.base_url = st.secrets.draftkings.events_url
        self.json_path = st.secrets.draftkings.events_data_json
        self.csv_path = st.secrets.draftkings.events_data_csv

    def format_url(self):
        self.request_url = self.base_url.format(self.sportId)

    def get_data(self):
        self._request_data()
        self._write_json_data()
        self._load_data()
        self._get_dataframe()
        self._write_csv_data()

    def _request_data(self):
        self.response = requests.get(url=self.request_url, headers=self.headers)
        self.data = self.response.json()
        

    def _write_json_data(self):
        with open(self.json_path, "w") as file:
            json.dump(obj=self.data, fp=file, indent=4)

    def _load_data(self):
        with open(file=self.json_path, mode="r") as file:
            self.file_data = json.load(fp=file)
            self.events_data = self.file_data['events']

    def _get_dataframe(self):
        self.df = json_normalize(data=self.events_data)

    def _write_csv_data(self):
        self.df.to_csv(path_or_buf=self.csv_path)


sportid = "1"
events = EventsData(sportId=sportid)
df = events.df
print(df)

eventid = "88808"
odds = OddsData(eventId=eventid)
df = odds.df
print(df)