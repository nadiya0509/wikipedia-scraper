"""
Script that loads links to the wikipedia pages
of the leaders of a number of countries using and API,
scraps the first paragraph of the wikipedia pages,
cleans from tags associated with [] and ⓘ symbols,
and writes in a csv file.

Notes:
- Session functionality has not been implemented due to lack of time (tech-talk preparation).
- First paragraph is identified as one that follows a "super-short" paragraph,
    but it does not work for russian leaders. Alternative identification using <b> tag
    has not been completely implemented due to lack of time.  
- Printing on-screen fine, but writing to json file stll needs to be improved.    

To launch type:
    python3 leaders_scraper.py
"""

import requests
from bs4 import BeautifulSoup
import re
import json

root_url="https://country-leaders.onrender.com"
cookie_url="/cookie"
countries_url="/countries"
leaders_url="/leaders"
        
def get_first_paragraph(wikipedia_url):
    soup=BeautifulSoup(requests.get(wikipedia_url).text)
    paragraphs=[]
    for par in soup.find_all("p"): paragraphs.append(par.text)
    # First paragraph is taken as a paragraph that is preceded by an empty line (len()<5)
    # Does not work for Yeltsin -> use presence of the <b> tag instead?
    i=0
    for par in paragraphs:
        if i > 1 and i < len(par)+1:
            if len(par[i-1])<5:
                first_paragraph=par
                break
        i+=1
    # does not work yet !!!!!!!!    
    # for par in paragraphs:
    #     if (par.count('<b>') > 0):
    #         print(par)
    #         first_paragraph=par
    #         break

    pattern_square_brackets = r"\[(.*?)\]" # removing expressions surrounded by square brackets
    cleaned_first_paragraph = re.sub(pattern_square_brackets, "", first_paragraph)

    pattern_str_before_symbol=r"^.*ⓘ" # then removing word finishing with ⓘ
    match = re.match(pattern_str_before_symbol,first_paragraph)
    if match != None:
        pattern_word_before_symbol = match[0].split()[-1]
        cleaned_first_paragraph = re.sub(pattern_word_before_symbol, "", cleaned_first_paragraph)
    cleaned_first_paragraph = re.sub('[ ]+,', ",", cleaned_first_paragraph) # then removing spaces in front of a comma
    
    #print(f"Original:\n {first_paragraph}")
    #print(f"Cleaned:\n {cleaned_first_paragraph}")
    return cleaned_first_paragraph


def get_leaders():
    user_cookie=requests.get(root_url+cookie_url).cookies   
    countries=requests.get(root_url+countries_url, cookies=user_cookie, params={"user_cookie":user_cookie})
    list_countries=countries.json()
    leaders_per_country={} # dic: str(=country):list[dic(president info)]
    for country in list_countries:
        leaders_list=requests.get(root_url+leaders_url, cookies=user_cookie,
                                   params={"user_cookie":user_cookie, "country": country}).json()
        leaders_per_country[country]=leaders_list

    for country, list_leaders in leaders_per_country.items():
        for leader in list_leaders:
            wiki_url=leader["wikipedia_url"] 
            leader_surname=leader["last_name"]

            print(country, leader_surname)

            try:
                cleaned_first_paragraph = get_first_paragraph(wiki_url)
            except:
                cleaned_first_paragraph = "Error getting or cleaning wikipedia first paragraph"

            print(cleaned_first_paragraph)      

            leader["wiki_first_paragraph"]=cleaned_first_paragraph

    print("Done scraping wiki!")

    with open('leaders.json', 'w') as fp:
        for country, list_leaders in leaders_per_country.items():
            for leader in list_leaders:
                json.dump (f"{country},{leader["last_name"]},{leader["wiki_first_paragraph"]}", fp)

    print("Done writing scrapped and cleaned info to leaders.json!")

    #return leaders_per_country  

leaders_per_country = get_leaders()
