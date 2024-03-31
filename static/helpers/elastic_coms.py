# imports
import warnings
warnings.filterwarnings('ignore')
import json
import plotly
import time
import os
import sys

import pandas as pd
import plotly.express as px

from elasticsearch import Elasticsearch
from unidecode import unidecode
from dotenv import load_dotenv

# elastic host
load_dotenv()

es_host = os.getenv('DAB_ES_HOST')
es_user = os.getenv('DAB_ES_USER')
es_password = os.getenv('DAB_ES_PASSWORD')

# kijk of user credentials heeft gegeven
if es_host == None:
    print("Environment variable 'DAB_ES_HOST' is not set!")
    sys.exit(1)
if es_user == None:
    print("Environment variable 'DAB_ES_USER' is not set!")
    sys.exit(1)
if es_password == None:
    print("Environment variable 'DAB_ES_PASSWORD' is not set!")
    sys.exit(1)

es = Elasticsearch(
    hosts=[
        es_host
    ],
    http_auth=(es_user, es_password),
    verify_certs=False,
)

# word counts df
word_count_csv = "static/helpers/proper_word_counts.csv"

df_word_count = pd.read_csv(word_count_csv)

# lijst van vertaalde landen (geen GB omdat het al engels is)
translated_countries = ["AT", "BA", "BE", "BG", "CZ", "DK", "EE", "ES-CT", "ES-GA", "FR", "GR", "HR", "HU", "IS", "IT", "LV", "NL", "NO", "PL", "PT", "RS", "SE", "SI", "TR", "UA"]
ngram_legend_names = {"AT": "Austria", "BA": "Bosnia Herzegovina", "BE": "Belgium", "BG": "Bulgaria", "CZ": "Czech Republic", "DK": "Denmark", "EE": "Estonia", "ES-CT": "Spain Catalonia", "ES-GA": "Spain Galicia", "FR": "France", "GB": "Great Britain", "GR": "Greece", "HR": "Croatia", "HU": "Hungary", "IS": "Iceland", "IT": "Italy", "LV": "Latvia", "NL": "the Netherlands", "NO": "Norway", "PL": "Poland", "PT": "Portugal", "RS": "Serbia", "SE": "Sweden", "SI": "Slovenia", "TR": "Turkiye", "UA": "Ukraine"}
ngram_legend_colors = {"AT": "#325A9B", "BA": "#EECA3B", "BE": "#FECB52", "BG": "#00CC96", "CZ": "#636EFA", "DK": "#19D3F3", "EE": "#0D2A63", "ES-CT": "#AB63FA", "ES-GA": "#FF6692", "FR": "#BAB0AC", "GB": "#EF553B", "GR": "#6A76FC", "HR": "#E45756", "HU": "#479B55", "IS": "#72B7B2", "IT": "#1CBE4F", "LV": "#FF97FF", "NL": "#FF8000", "NO": "#B82E2E", "PL": "#FFA15A", "PT": "#54A24B", "RS": "#1C8356", "SE": "#FBE426", "SI": "#B6E880", "TR": "#AF0033", "UA": "#0099C6"}

#####################################################################################

#                           Ngram creation functions

#####################################################################################

# query ngram function (summarize=None, year.keyword, month.keyword)
def query_ngram(search_dict, summarize=None):
    processed_search_list = []
    
    # loop door alle search elements heen
    for k, v in search_dict.items():
        
        # filter de ngram voor de term query
        if k != "ngram":
            processed_search_list.append({"match_phrase" : {k : v}})
            
        else:
            ngram = {"term": {"ngram.keyword" : v}}

            index_num = len(v.split(' '))
            index = f"ngrams{index_num}"
    
            if index_num > 5:
                return {'hits': {'total': {'value': 0, 'relation': 'eq'}, 'max_score': None, 'hits': []}, 'aggregations': {'categories': {'doc_count_error_upper_bound': 0, 'sum_other_doc_count': 0, 'buckets': []}}}

    # check of er een groupby sum query moet worden gedaan
    if summarize != None:
        
        result = es.search(
        index = index,
        size = 0,
        query = {
            "bool": {
                "must": processed_search_list,
                "filter": ngram
            }
        },
        aggs = {
            "categories": {
                "multi_terms": {
                    "terms": [{
                        "field": summarize,
                        
                    }, {
                        "field": "country.keyword",
                        
                    }],
                    "size": 1000
                },
                "aggs": {
                    "total_count": {
                        "sum": {
                            "field": "count"
                        }
                    } 
                }
            } 
        },
        request_timeout=30)
        
    else:
        result = es.search(
        index = index,
        size = 10000,
        query = {
            "bool": {
                "must": processed_search_list,
                "filter": ngram
            }
        },
        request_timeout=30)
    
    return result

# maak grote getallen leesbaar
def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

# geeft een ngram df
# NOTE: query["country"] = list(), normaal is dat een string
def create_ngram(query, timespan="year"):
    countries = ngram_legend_names.keys()
    
    # aantal woorden van de ngram
    multiplier = len(query["ngram"].split(" "))
    
    # return dataframe
    df = pd.DataFrame({'date': [],
                       'percentage': [],
                       'country': [],
                       'count': [],
                      })
    
    # kijk door welke landen er moet worden gezocht
    if "country" in query.keys():
        countries = query["country"]
        query.pop("country")
    
    # voeg result toe aan df en format timespan
    def append_to_df(date_format, timespan):
        results_total = 0
        month = "1"
        
        # kijk of er door summed values moet worden gezocht
        if timespan in ["year", "month"]:
            timespan = timespan + ".keyword"
        
            results = query_ngram(query, summarize=timespan)
            
            # loop door de samengevoegde data heen
            for result in results["aggregations"]["categories"]["buckets"]:
                country = result["key"][1]
                count = result["total_count"]["value"]
                
                results_total += count
                
                # output zetten voor maanden
                if timespan == "month.keyword":
                    year = query["year"]
                    month = result["key"][0]
                    total_counts = sum(df_word_count[(df_word_count["date"].str.contains(f"{year}-{month}")) & (df_word_count["country"] == country)]["words"])

                # output zetten voor jaren
                else:
                    year = result["key"][0]
                    total_counts = sum(df_word_count[(df_word_count["date"].str.contains(year)) & (df_word_count["country"] == country)]["words"])
                    
                date = date_format.format(year, month)
                percentage = round(((count * multiplier) / total_counts) * 100, 4)
                
                df.loc[len(df.index)] = [date, percentage, country, human_format(count)]

            return int(results_total)
        
        else:
            results = query_ngram(query)
            
            # loop door de results van alle landen heen
            for result in results["hits"]["hits"]:
                src = result["_source"]

                count = src["count"] 
                
                results_total += count
                
                country = src["country"]
                date = date_format.format(src["year"], src["month"], src["day"])
                total_count = df_word_count[(df_word_count["date"] == date) & (df_word_count["country"] == country)]["words"].values[0]
                percentage = round(((count * multiplier) / total_count) * 100, 4)
                
                df.loc[len(df.index)] = [date, percentage, country, human_format(count)]

            return results_total
    
    # timespan formatting
    if timespan == "year":
        res = append_to_df("{}-1-1", timespan)
        
    elif timespan == "month":
        res = append_to_df("{}-{}-1", timespan)
        
    else:
        res = append_to_df("{}-{}-{}", timespan)
    
    return df[df["country"].isin(countries)].sort_values(by=["date", "country"]), res

# doe de formatting vooraf aan de create_ngram functie
def process_create_ngram(query, timespan="year"):

    # combineer queries
    if "," in query["ngram"] and "country" in query.keys() and len(query["country"]) == 1:
        combined = True

        ngrams = query.pop("ngram").split(",")
        
        ngram_total = 0
        ngram_df_frames = []
        for ngram in ngrams:
            ngram = ngram.lstrip(" ")
            ngram = ngram.rstrip(" ")
            
            # kopieer de query zodat er elke keer een andere ngram in kan
            new_query = query.copy()
            new_query["ngram"] = ngram
            
            # voer de normale functie uit
            ngram_df, ngram_query_total = create_ngram(new_query, timespan=timespan)
            
            # voeg alles samen
            ngram_total += ngram_query_total
            ngram_df["country"] = ngram
            ngram_df_frames.append(ngram_df)
        
        result_ngram_df = pd.concat(ngram_df_frames)
        
        return result_ngram_df, ngram_total, combined
    
    # normale query
    else:
        # haal vage spaces weg
        query["ngram"] = query["ngram"].split(",")[0]
        query["ngram"] = query["ngram"].lstrip(" ")
        query["ngram"] = query["ngram"].rstrip(" ")
        
        result_ngram_df, ngram_total = create_ngram(query, timespan=timespan)

        combined = query["ngram"]

        return result_ngram_df, ngram_total, combined

# styling van de plotly plot
def create_fig(ngram_input, timespan):
        timer = time.time()

        ngram_term = ngram_input["ngram"]

        # maak df en plot
        ngram_df, ngram_total, combined = process_create_ngram(ngram_input, timespan=timespan)
        
        # geen resultaten gevonden
        if ngram_total == 0:
            return 0
        
        fig = px.line(ngram_df, 
                      x="date", 
                      y="percentage", 
                      color="country",
                      custom_data=["count"],
                      title=f'Results for: "{ngram_term if combined == True else combined}" (from {human_format(ngram_total)} total hits in {round(time.time() - timer, 2)} seconds)', 
                      labels={'date': 'Date', 'percentage':'Percentage'}).update_layout(
                            template='plotly_dark',
                            plot_bgcolor='rgba(0, 0, 0, 0)',
                            paper_bgcolor='rgba(0, 0, 0, 0)')
        
        # styling
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#3A3C42')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#3A3C42')
        fig.update_traces(mode="markers+lines", 
                          hovertemplate=" ".join([
                                "%{y:.4f}%",
                                "(%{customdata[0]} hits)"
                            ])
                        )
        fig.update_layout(hovermode="x unified", hoverlabel=dict(bgcolor="#36373D"), legend=dict(title=("Ngrams" if combined == True else "Countries")), yaxis_tickformat=".4f%", yaxis_ticksuffix = "%")

        # combined true is als er meerdere ngrams zijn gecombineerd ipv landen
        if combined != True:
            fig.for_each_trace(lambda t: t.update(name = ngram_legend_names[t.name], line_color=ngram_legend_colors[t.name]))

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return graphJSON


#####################################################################################

#                           Detailed debate search function

#####################################################################################

# NOTE: input is {search_key: value, search_key2: value2}
# query function
def query_detailed(search_dict, size, index="search"):
    processed_search_list = []
    
    # loop door alle search elements heen
    for k, v in search_dict.items():
        processed_search_list.append({"match_phrase" : {k : v}})
        
    # stel de uitkomst samen
    result = es.search(
        index = index,
        size = size,
        query = {
            "bool" : {
                "must": processed_search_list,},},
        request_timeout=30)
    
    return result

# helpt onderstaande functie om party goed te formatten
def get_party_tag(party):
    # src["party"]  .split(" ")[0] if src["party"] != "None" else "Party unknown"
    if party != "None" and party != None:
        party_split = party.split("(")[0].split(" ")

        if len(party_split) <= 5:
            return " ".join(party_split)

        # maak een afkorting
        else:
            abbreviation = ""
            for word in party_split:
                abbreviation += word[:1]

            return abbreviation

    else:
        return "Unknown party"

# zet resultaten op een leesbare manier voor html
def create_search_list(query_dict, size):
    translate = True
    
    countries = []
    if "countries" in query_dict.keys():
        countries = query_dict.pop("countries")

    query_string = ""
    if "query" in query_dict.keys():
        query_string = query_dict.pop("query")
    
    # vorm dict om naar elastic query materiaal
    query = {}
    for k, v in query_dict.items():

        if k == "search_translation":
            if v == "ON":
                query["content_translated"] = query_string
            else:
                query["content_simplified"] = query_string
                translate = False
        elif k == "person":
            query["person_simplified"] = v
        else:
            query[k] = v
    
    # default naar content_translated
    if "content_simplified" not in query.keys() and "content_translated" not in query.keys():
        query["content_translated"] = query_string
        
    result = query_detailed(query, size=100)

    # voorkom errors bij lege queries
    if result['hits']['total']['value'] == 0:
        return None

    render_list = []

    # houd een unique id per file bij
    file_ids = {}

    counter = 0
    for hit in result['hits']['hits']:
        src = hit["_source"]

        file = src["file"]

        if counter == size:
            break

        if len(countries) == 0 or src["country"] in countries:
            sentence = {}

            sentence["person"] = src["person"]
            sentence["country"] = src["country"]
            sentence["party"] = get_party_tag(src["party"])
            sentence["date"] = src["day"] + "-" + src["month"] + "-" + src["year"]
            if translate:
                sentence["content"] = src["content_translated"]
            else:
                sentence["content"] = src["content"]
            sentence["file"] = file

            # geef elke file een id voor overzicht
            if file not in file_ids.keys():
                file_ids[file] = (len(file_ids) + 1)
            sentence["file_id"] = file_ids[file]

            render_list.append(sentence)

            counter += 1

    return render_list

# resultaten voor een volledige file
def create_file(query_dict, translate):
    result = query_detailed(query_dict, size=10000)
    content = "content_translated"

    # kijk of vertaling beschikbaar is
    if len(result['hits']['hits']) == 0:
        return None, None

    # Bepaal de tekst voor de translation knop rechtsboven
    language = result['hits']['hits'][0]["_source"]["country"]
    if language in translated_countries:
        
        if translate == "translate":
            language_info = {"language": [language, "Translated"]}
        else:
            language_info = {"language": [language, "Translation available"]}
            content = "content"

    else:
        language_info = {"language": [language, "Translation unavailable"]}

    # Stel de file zelf op
    render_list = []
    for hit in result['hits']['hits']:
        sentence = {}

        src = hit["_source"]

        sentence["person"] = src["person"]
        sentence["party"] = src["party"]
        
        if content != "content_translated":
            sentence["content"] = src[content]

        else:
            if content in src.keys():
                sentence["content"] = src[content]
            else:
                sentence["content"] = f"[TRANSLATION MISSING] {src['content']}"
            

        render_list.append(sentence)
    
    return render_list, language_info


#####################################################################################

#                           Search suggestions section

#####################################################################################

# vraag unieke items op voor een colom
def get_unique_keyword(column):
    res = es.search(
        index="search",
        body={
            "size": 0,
            "aggs": {
                "unique_key_word": {
                    "terms": {
                        "field": column + ".keyword",
                        "size": 15000
                    }
                }
            }
        },
        request_timeout=30
    )

    return [bucket['key'] for bucket in res['aggregations']['unique_key_word']['buckets']]

# geef een autocomplete suggestion
def autocomplete(possibilities, query, limit=5):
    count = 0
    matches = []
    
    if query == "":
        return matches

    query_split = query.lower().split(" ")
    
    # voornaam zoeken / 1 woord
    if len(query_split) == 1:
        for possibility in sorted(possibilities):
            
            if query.lower() in unidecode(possibility.lower()):
                
                count += 1
                matches.append(possibility)

                if count == limit:
                    return matches
                
        return matches
                
    # volledige naam
    else:
        for possibility in sorted(possibilities):
            possibility_split = unidecode(possibility.lower()).split(" ")
            
            if len(possibility_split) == 2 and len(query_split) == 2:
                
                if query_split[0] in possibility_split[0] and query_split[1] in possibility_split[1] or query_split[1] in possibility_split[0] and query_split[0] in possibility_split[1]:
                    count += 1
                    matches.append(possibility)

                    if count == limit:
                        return matches
            
            elif len(possibility_split) == 3 and len(query_split) == 3:
                
                if query_split[0] in possibility_split[0] and query_split[1] in possibility_split[1] and query_split[2] in possibility_split[2]:
                    count += 1
                    matches.append(possibility)

                    if count == limit:
                        return matches
            elif len(possibility_split) == 4 and len(query_split) == 4:
                
                if query_split[0] in possibility_split[0] and query_split[1] in possibility_split[1] and query_split[2] in possibility_split[2] and query_split[3] in possibility_split[3]:
                    count += 1
                    matches.append(possibility)

                    if count == limit:
                        return matches
                        
        return matches
    
# autocomplete suggestions voor zoekbalk
def query_ngram_suggestions(query):
    processed_results = []
    
    # zorg dat er door een goede index kan worden gezocht
    index_num = len(query.split(' '))
    if index_num < 5:
        index_num += 1
    else:
        index_num = 5

    index = f"ngrams{index_num}"

    # stel de uitkomst samen
    results = es.search(
        index = index,
        size = 50,
        query = {
            "bool" : {
                "must": {"match_phrase" : {"ngram" : query}},},},
        request_timeout=30)

    for hit in results["hits"]["hits"]:
        find = hit["_source"]["ngram"]
        
        # kijk of de query begint met de user input
        if find[:len(query)] == query:
            # haal query uit found als die al eerder voorkomt in de result zelf
            found = [x.replace(query, '') for x in find.split(query) if x != '' and x != ' ']
            
            # filter de ongeschikte resultaten
            if len(found) != 0:
                processed_results.append(query + found[0])
    
    # haal de spatie op het einde weg als die er is
    processed_results = list(dict.fromkeys(processed_results))[:5]
    strip_spacing = []
    for result in processed_results:
        result_length = len(result)
        
        if result[(result_length - 1):result_length]:
            strip_spacing.append(result[:(result_length - 1)])
        else:
            strip_spacing.append(result)
    
    return strip_spacing