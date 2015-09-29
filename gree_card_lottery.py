"""
Author: Marco Bonvini
Date: September 27 2015

This script scrapes the pages of the Department of State website to gather statistics and information
about the Diversity Visa (DV) lottery, aka green card lottery.

The Department of State publishes every month a visa bulletin at

    http://travel.state.gov/content/visas/en/law-and-policy/bulletin.html

this script generates URLs of the bulletins that have been released over the last
years and look for information. In particular, the script looks for information
regarding the DV lottery that are typically located in section B of the page,

    B. DIVERSITY IMMIGRANT (DV) CATEGORY FOR THE MONTH OF ...

This section contains a table that states which DV lottery numbers will be able to 
move forward with their application for the green card.
The scripts collectes all the data from the tables and generate Pandas DataFrames
that can be used to anamyze the data and compute some statistics.

LICENSE
++++++++

This code is released under MIT licenseThe MIT License (MIT)

Copyright (c) 2015 Marco Bonvini

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import urllib2
import re
import unicodedata
from datetime import datetime
from bs4 import BeautifulSoup, Tag
import pandas as pd
import numpy as np
import json

# Months and year ranges. Because the bulletins refer to fiscal year (FY), the first month is October.
years = range(2003,2016)
months = ['october','november','december','january','february','march','april','may','june','july','august','september']

# Initialize empty pandas DataFrames that will contain the final data for every continent
df_europe = pd.DataFrame(np.NAN*np.zeros((len(months),len(years))), index = months, columns = years)
df_africa = pd.DataFrame(np.NAN*np.zeros((len(months),len(years))), index = months, columns = years)
df_asia = pd.DataFrame(np.NAN*np.zeros((len(months),len(years))), index = months, columns = years)
df_oceania = pd.DataFrame(np.NAN*np.zeros((len(months),len(years))), index = months, columns = years)
df_north_america = pd.DataFrame(np.NAN*np.zeros((len(months),len(years))), index = months, columns = years)
df_south_america = pd.DataFrame(np.NAN*np.zeros((len(months),len(years))), index = months, columns = years)

# When the table contains the string "Current", "current", "c" or "C" instead of the number,
# replace it with a np.NaN in the DataFrames
current_number = np.NaN

# The pattern of the URL where one can fond the information about the DV lottery
pattern = "http://travel.state.gov/content/visas/english/law-and-policy/bulletin/{0}/visa-bulletin{3}-{1}-{2}.html"

# Iterate over all the years and months, generate the URLs and look for the
# data regarding the DV lottery. For each year of each month multiple URLS are built.
# This is necessary because the URLs haven't been managed in a consistent way over the years,
# for example sometimes the month starts with a lowercase letter but in other cases it does not.
for fy in years:
	for m in months:
                # Initialize list of URLs to check
		page_urls = []

                # The months of Oct, Nov and Dec needs to be treated differently
                # because, for example, Oct 2014 belongs to FY 2015.
		if m in ['october','november','december']:
			page_urls.append(pattern.format(fy,m,fy-1,"-for"))
			page_urls.append(pattern.format(fy,m,fy-1,""))
			page_urls.append(pattern.format(fy,m.title(),fy-1,""))
			page_urls.append(pattern.format(fy,m.title(),fy-1,"-for"))
		else:
			page_urls.append(pattern.format(fy,m,fy,"-for"))
			page_urls.append(pattern.format(fy,m,fy,""))
			page_urls.append(pattern.format(fy,m.title(),fy,""))
			page_urls.append(pattern.format(fy,m.title(),fy,"-for"))

                # Test the URLs, verify if they're legitimate, and get the
                # content of the HTML page
		page_ok = False
		i = 0
		while not page_ok and i<len(page_urls):
			print "Reading page: {0}".format(page_urls[i])
                        try:
                                response = urllib2.urlopen(page_urls[i])
			        html_text = response.read()
		        
			        if "404 - Page Not Found" not in html_text:
				        page_ok = True
                        except urllib2.HTTPError, e:
                                print "Failed reading the URL: {0}".format(page_urls[i])
                                print str(e)
                                
			i += 1

                # If there was a successful read, parse the HTML page and populate the
                # columns/rows of the pandas DataFrames
		if page_ok:
			soup = BeautifulSoup(html_text)
			soup.encode('utf-8')
			
			for tag in soup.find_all('script'):
				tag.replaceWith('')
			
			text = unicode(soup.get_text('|', strip=True))
			text = text.encode('ascii',errors='ignore')
			text = re.sub(',','',text)
			text = re.sub('\\r','',text)
			text = re.sub('\\n','',text)
			text = re.sub(':','',text)
			text = re.sub('-','',text)
			text = re.sub('\s+','',text)
			text = text.lower()
                        
			g_europe = re.search('(europe[|]*[\s*eu[r]*\s*]*[|]*(\d+|current|c))', text)
			if g_europe:
				df_europe[fy][m] = g_europe.groups()[1] if g_europe.groups()[1] not in ['c','current'] else current_number
			else:
				print "Missing Europe..."
				
			g_africa = re.search('(africa[|]*[\s]*[af]*[\s]*[|]*(\d+|current|c))', text)
			if g_africa:
				df_africa[fy][m] = g_africa.groups()[1] if g_africa.groups()[1] not in ['c','current'] else current_number
			else:
				print "Missing Africa..."
		
			g_oceania = re.search('(oceania[|]*[\s]*[oc]*[\s]*[|]*(\d+|current|c))', text)
			if g_oceania:
				df_oceania[fy][m] = g_oceania.groups()[1] if g_oceania.groups()[1] not in ['c','current'] else current_number
			else:
				print "Missing Oceania..."
			
			g_asia = re.search('(asia[|]*[\s]*[as]*[\s]*[|]*(\d+|current|c))', text)
			if g_asia:
				df_asia[fy][m] = g_asia.groups()[1] if g_asia.groups()[1] not in ['c','current'] else current_number
			else:
				print "Missing Asia..."
				
			g_north_america = re.search('(northamerica[|]*\(bahamas\)[|]*[\s]*[na]*[\s]*[|]*(\d+|current|c))', text)
			if g_north_america:
				df_north_america[fy][m] = g_north_america.groups()[1] if g_north_america.groups()[1] not in ['c','current'] else current_number
			else:
				print "Missing North America..."
			
			g_south_america = re.search('(southamerica[|]*and[|]*the[|]*caribbean[|]*[\s]*[sa]*[\s]*[|]*(\d+|current|c))', text)
			if g_south_america:
				df_south_america[fy][m] = g_south_america.groups()[1] if g_south_america.groups()[1] not in ['c','current'] else current_number
			else:
				print "Missing South America..."

def convert_month_to_date(d):
        """
        This function converts a string representing a month like ``october``
        and converts it into a format like ``2015-10-01``.
        """
        if d in ["october", "november", "december"]:
                return datetime.strptime(d+"-2014", "%B-%Y").strftime("%Y-%m-%d")
        else:
                return datetime.strptime(d+"-2015", "%B-%Y").strftime("%Y-%m-%d")

# Export all the data in the data frames to JSON
data_frames = [df_europe, df_africa, df_asia, df_oceania, df_north_america, df_south_america]
data_names = ["europe", "africa", "asia", "oceania", "north_america", "south_america"]

mean_df = pd.DataFrame()
std_df = pd.DataFrame()
min_df = pd.DataFrame()
max_df = pd.DataFrame()
for name, df in zip(data_names, data_frames):
        
        # Generate statistics for every DataFrame
        mean_df[name] = df.mean(axis = 1)
        std_df[name] = df.std(axis = 1)
        min_df[name] = df.min(axis = 1)
        max_df[name] = df.max(axis = 1)

data = []
for mo in months:
        data_point = {"date": convert_month_to_date(mo)}
        for c in data_names:
                data_point["avg_"+c] = mean_df[c][mo]
                data_point["u_"+c] = mean_df[c][mo] + std_df[c][mo]
                data_point["l_"+c] = mean_df[c][mo] - std_df[c][mo]
                data_point["min_"+c] = min_df[c][mo]
                data_point["max_"+c] = max_df[c][mo]
        data.append(data_point)

# Save the data in a JSON file
with open("dv_lottery.json", "w") as fp:
        json.dump(data, fp, indent = 2)
        
                        
