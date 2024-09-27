import streamlit as st
import pandas as pd

df = pd.read_csv("data/ref/sports.csv")

dfsportid = df["sportId"]
dfeventgroupid = df['eventGroupId']
print(dfsportid)
print(dfeventgroupid)

eventgroupids = ["88808", "84240", "42133", "42648", "87637", "92483", "92694", "9034"] 
sportgroupids = ["1", "2", "3", "4", "5", "6", "7", "25"]