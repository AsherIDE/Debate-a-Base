# imports
import warnings
warnings.filterwarnings('ignore')
import json
import plotly

import pandas as pd
import plotly.express as px

from elasticsearch import Elasticsearch

# elastic host
es = Elasticsearch(
    hosts=[
            "https://localhost:9200"
    ],
    http_auth=("elastic", "NES9DZ-QwhanXAQf9caV"),
#     use_ssl=True,
    verify_certs=False,
#     ca_certs="./ca.crt"
)

# word counts df
word_count_csv = 'C:/Users/Asher/Documents/School/_Scriptie/Data/xml_word_counts.csv'

df_word_count = pd.read_csv(word_count_csv)

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
    
    # check of er een groupby sum query moet worden gedaan
    if summarize != None:
        
        result = es.search(
        index = "ngrams",
        size = 0, # TODO: Zorg dat er een groter limit is dan 10000
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
        })
        
    else:
        
        result = es.search(
        index = "ngrams",
        size = 10000, # TODO: Zorg dat er een groter limit is dan 10000
        query = {
            "bool": {
                "must": processed_search_list,
                "filter": ngram
            }
        })
    
    return result

# geeft een ngram df
# NOTE: query["country"] = list(), normaal is dat een string
def create_ngram(query, timespan="year"):
    countries = ["BG", "CZ", "DK", "NL", "SI", "GB"]
    
    # aantal woorden van de ngram
    multiplier = len(query["ngram"].split(" "))
    
    # return dataframe
    df = pd.DataFrame({'date': [],
                       'percentage': [],
                       'country': []
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
                
                df.loc[len(df.index)] = [date, percentage, country]

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
                
                df.loc[len(df.index)] = [date, percentage, country]

            return results_total
    
    # timespan formatting
    if timespan == "year":
        res = append_to_df("{}-1-1", timespan)
        
    elif timespan == "month":
        res = append_to_df("{}-{}-1", timespan)
        
    else:
        res = append_to_df("{}-{}-{}", timespan)
    
    return df[df["country"].isin(countries)].sort_values(by=["date", "country"]), res

def create_fig(ngram_input, timespan):
        ngram_term = ngram_input["ngram"]

        # maak df en plot
        ngram_df, ngram_total = create_ngram(ngram_input, timespan=timespan)

        fig = px.line(ngram_df, x="date", y="percentage", color="country", title=f'Ngram: "{ngram_term}"').update_layout(
                                template='plotly_dark',
                                plot_bgcolor='rgba(0, 0, 0, 0)',
                                paper_bgcolor='rgba(0, 0, 0, 0)',
                            )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return graphJSON


#####################################################################################

#                           Detailed debate search function

#####################################################################################

# NOTE: input is {search_key: value, search_key2: value2}
# query function
def query_detailed(search_dict, size):
    processed_search_list = []
    
    # loop door alle search elements heen
    for k, v in search_dict.items():
        processed_search_list.append({"match_phrase" : {k : v}})
        
    # stel de uitkomst samen
    result = es.search(
    index = "search",
    size = size, # TODO: Zorg dat er een groter limit is dan 10000
    query = {
        "bool" : {
            "must": processed_search_list,},})
    
    return result

# zet resultaten op een leesbare manier voor html
def create_search_list(query_dict, size):
    result = query_detailed(query_dict, size=size)

    render_list = []
    for hit in result['hits']['hits']:
        sentence = {}

        src = hit["_source"]
        # id = hit["_id"]

        sentence["person"] = src["person"]
        sentence["date"] = src["day"] + "-" + src["month"] + "-" + src["year"]
        sentence["content"] = src["content"]
        sentence["file"] = src["file"]

        render_list.append(sentence)

    return render_list

# resultaten voor een volledige file
def create_file(query_dict):
    result = query_detailed(query_dict, size=10000)

    render_list = []
    for hit in result['hits']['hits']:
        sentence = {}

        src = hit["_source"]
        # id = hit["_id"]

        sentence["person"] = src["person"]
        sentence["content"] = src["content"]

        render_list.append(sentence)

    return render_list