"""
Script that loads links to the wikipedia pages
of the leaders of a number of countries using and API,
scraps the first paragraph of the wikipedia pages,
cleans from tags associated with [] and ⓘ symbols,
and writes and reads from a json file.
 
To launch type in cmd:
    py leaders_scraper.py
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from requests import Session

root_url="https://country-leaders.onrender.com"
cookie_url="/cookie"
countries_url="/countries"
leaders_url="/leaders"

def print_timing(func):
    '''Create a timing decorator function use @print_timing just above the function you want to time.'''
    def wrapper(*arg):
        start = time.perf_counter()       
        # Run the function decorated
        result = func(*arg)
        end = time.perf_counter()
        execution_time = round((end - start), 2)
        print(f'{func.__name__} took {execution_time} sec')
        return result
    return wrapper
        
def get_first_paragraph(wikipedia_url, session):
    soup=BeautifulSoup(session.get(wikipedia_url).text)
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


def get_first_paragraph_Alberto(wikipedia_url, session):
    soup = BeautifulSoup(session.get(wikipedia_url).content, 'html.parser')

    # Try to find main content using known class names
    # First we search by classs "mw-content-ltr"
    main_content = soup.find("div", class_ = "mw-content-ltr")

    # If not found, then we search by class "mw-content-rtl"
    if not main_content:
        print("Didn't find main content by class [mw-content-ltr], searching by class [mw-content-rtl]")
        main_content = soup.find("div", class_ = "mw-content-rtl")

    if main_content:
        # Get all the pragraphs from the main content section
        paragraphs = main_content.find_all("p")
    else:
        # As fallback, we get all the pragraphs from the page
        paragraphs = soup.find_all("p")
    
    print(f"Number of paragraphs found: {len(paragraphs)}")

    cleaned_first_paragraph=""

    for par in paragraphs:
        # Look for a <b> tag in the paragraph
        b_tag = par.find("b")

        # If we find the <b> tag and is not empty and it's not the only tag inside the paragraph, 
        # then we assume that we found a reliable first paragraph
        if b_tag:
            b_tag_text = b_tag.get_text().rstrip()
            p_tag_text = par.get_text().rstrip()

            if b_tag_text != "" and len(b_tag_text) != len(p_tag_text):
                print("Par",par)
                first_paragraph=par.text
                break

    pattern_square_brackets = r"\[(.*?)\]" # removing expressions surrounded by square brackets
    cleaned_first_paragraph = re.sub(pattern_square_brackets, "", first_paragraph)
    pattern_str_before_symbol=r"^.*ⓘ" # then removing word finishing with ⓘ
    match = re.match(pattern_str_before_symbol,first_paragraph)
    if match != None:
        pattern_word_before_symbol = match[0].split()[-1]
        cleaned_first_paragraph = re.sub(pattern_word_before_symbol, "", cleaned_first_paragraph)
    cleaned_first_paragraph = re.sub('[ ]+,', ",", cleaned_first_paragraph) # then removing spaces in front of a comma    
    cleaned_first_paragraph=cleaned_first_paragraph.strip()

    #print(f"Original:\n {first_paragraph}")
    #print(f"Cleaned:\n {cleaned_first_paragraph}")
    return cleaned_first_paragraph


@print_timing
def get_leaders():
    # Slow way
    #user_cookie=requests.get(root_url+cookie_url).cookies   
    #countries=requests.get(root_url+countries_url, cookies=user_cookie, params={"user_cookie":user_cookie})
    # Fast way
    with Session() as session:
        user_cookie=session.get(root_url+cookie_url, verify=False).cookies  # verifuy=False added by me because of the error of expired certificate of the website 
        countries=session.get(root_url+countries_url, cookies=user_cookie, params={"user_cookie":user_cookie})
        list_countries=countries.json()
        leaders_per_country={} # dic: str(=country):list[dic(president info)]
        for country in list_countries:
            leaders_list=session.get(root_url+leaders_url, cookies=user_cookie,
                                   params={"user_cookie":user_cookie, "country": country}).json()
            leaders_per_country[country]=leaders_list    
    for country, list_leaders in leaders_per_country.items():
        for leader in list_leaders:
            wiki_url=leader["wikipedia_url"] 
            leader_surname=leader["last_name"]
            print(country, leader_surname)
            try:
                cleaned_first_paragraph = get_first_paragraph_Alberto(wiki_url, session) # Alberto's method, works for yeltsin
                #cleaned_first_paragraph = get_first_paragraph(wiki_url, session) # my method, does not work for yeltsin
            except Exception as ex:
                cleaned_first_paragraph = "Error getting or cleaning wikipedia first paragraph: {ex}"
            print(cleaned_first_paragraph)      
            leader["wiki_first_paragraph"]=cleaned_first_paragraph
    
    print("Done scraping wiki!")
    with open('leaders.json', 'w',encoding="utf-8") as f:
        json.dump(leaders_per_country, f, ensure_ascii=False, indent=4)

    print("Done writing scrapped and cleaned info to leaders.json!")

    # Example of reading leaders.json file: print keys
    with open('leaders.json', "r", encoding="utf-8") as f:
        leaders_per_country = json.load(f)
    print(leaders_per_country.keys()) # for checking

get_leaders()
