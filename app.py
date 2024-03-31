from flask import Flask, render_template, request, jsonify, redirect, url_for

from static.helpers.elastic_coms import create_fig, create_search_list, create_file, get_unique_keyword, autocomplete, query_ngram_suggestions
from static.helpers.unpack_settings import unpack_ngram_settings, unpack_debate_settings
from static.helpers.redirect import redirect_ngram, redirect_debate
from static.helpers.query_highlighter import highlight_sentence

app = Flask(__name__, template_folder="templates", static_folder="static")

#####################################################################################

#                                  Ngrams page

#####################################################################################

# NOTE: hardcoded dataset definities (in elastic_coms staat een lijst met landen waarvan vertalingen beschikbaar zijn)
# nav options voor ngrams
ngram_nav_options = {}
ngram_nav_options["countries"] = {"AT": "Austria", "BA": "Bosnia Herzegovina", "BE": "Belgium", "BG": "Bulgaria", "CZ": "Czech Republic", "DK": "Denmark", "EE": "Estonia", "ES-CT": "Spain Catalonia", "ES-GA": "Spain Galicia", "FR": "France", "GB": "Great Britain", "GR": "Greece", "HR": "Croatia", "HU": "Hungary", "IS": "Iceland", "IT": "Italy", "LV": "Latvia", "NL": "the Netherlands", "NO": "Norway", "PL": "Poland", "PT": "Portugal", "RS": "Serbia", "SE": "Sweden", "SI": "Slovenia", "TR": "Turkiye", "UA": "Ukraine"}

# nav options voor debates
debate_nav_options = {}
debate_nav_options["countries"] = ngram_nav_options["countries"]
debate_nav_options["search_translation"] = ["Browse in English translations of countries", "Browse in every original language"]
debate_nav_options["person"] = "Person"
debate_nav_options["party"] = "Party"
debate_nav_options["year"] = [2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005, 2004, 2003, 2002, 2001, 2000, 1999, 1998, 1997, 1996]
debate_nav_options["month"] = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
debate_nav_options["day"] = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31"]

@app.route("/ngrams", methods=(['GET', 'POST']))
def home():
    
    # redirect ngram search query
    if request.method == "POST":
        query, settings = redirect_ngram(request.form, settings="all")
        
        if query == "":
            query = "no_query_yet"

        return redirect(url_for(".home_query", query=query, timespan="year", settings=settings))

    # render default home page
    else:

        return render_template("main.html", nav_options=ngram_nav_options)

@app.route("/ngrams/<query>/<timespan>/<settings>", methods=(['GET', 'POST']))
def home_query(query, timespan, settings):
    # redirect navbar search
    if request.method == "POST":
        
        query, settings = redirect_ngram(request.form, settings=request.path.split("/")[4])

        query = query.lower().replace('"', '').replace("'", '')

        # reset zoom bij clear filters button
        if settings == "all":
            timespan = "year"
        
        # haal query uit url als er geen query is in de form
        if query == "no_query_yet" or query == "":
            query = request.path.split("/")[2]

        return redirect(url_for(".home_query", query=query, timespan=timespan, settings=settings))

    # jaren, jaar of maand weergave
    if timespan == "year":
        countries = unpack_ngram_settings(timespan, settings)

        query = query.lower()
        
        if countries != None:
            graphJSON = create_fig({"ngram": query,
                                    "country": countries}, timespan)
        else:
            graphJSON = create_fig({"ngram": query}, timespan)
        
        timespan = "month"

    elif timespan == "month":
        year, countries = unpack_ngram_settings(timespan, settings)

        if countries != None:
            graphJSON = create_fig({"ngram": query,
                                    "year": year,
                                    "country": countries}, timespan)

        else:
            graphJSON = create_fig({"ngram": query,
                                    "year": year}, timespan)
        
        timespan = "day"
        
    else:
        year, month, countries = unpack_ngram_settings(timespan, settings)

        if countries != None:
            graphJSON = create_fig({"ngram": query,
                                    "year": year,
                                    "month": month,
                                    "country": countries}, timespan)
            
        else:
            graphJSON = create_fig({"ngram": query,
                                    "year": year,
                                    "month": month}, timespan)
        
        timespan = "complete"

    # definieer selected settings
    selected_settings = {}
    if countries != None:
        selected_settings["countries"] = countries
    
    return render_template("main.html", graphJSON=graphJSON, query=query, timespan=timespan, nav_options=ngram_nav_options, settings=settings, selected_settings=selected_settings)


#####################################################################################

#                                  Debates page

#####################################################################################
@app.route("/debates", methods=(['GET', 'POST']))
def debates():
    
    if request.method == "POST":
        query, settings = redirect_debate(request.form, settings="none")
        file = "no_file_found"

        # als er geen query is geen file ophalen
        if query == "" or query == "no_query_yet":
            query = "no_query_yet"
        else:
            file = create_search_list({"query": query}, 1)

            if file == None:
                file = "no_file_found"
            else:
                file = file[0]["file"]

        return redirect(url_for(".debates_file", query=query, file=file, settings=settings))

    else:
        return render_template("debates.html", nav_options=debate_nav_options)

# open een specifieke file
@app.route("/debates/<query>/<file>/<settings>", methods=(['GET', 'POST']))
def debates_file(query, file, settings):
    
    # redirect navbar search
    if request.method == "POST":
        query, settings = redirect_debate(request.form, settings=settings)

        # als er geen query is ingevoerd kijken of die al in url zit
        if query == "" or query == "no_query_yet":
            query = request.path.split("/")[2]

        # behoud de al geopende file als die ook voorkomt in de nieuwe resultaten
        filters = unpack_debate_settings(settings)
        filters["query"] = query
        if "file_translation" in filters.keys():
            filters.pop("file_translation")
        
        # vernader filecount als die is ingesteld
        file_count = 20
        if "file_count" in filters.keys():
            file_count = filters.pop("file_count")

        current_file = request.path.split("/")[3]
        files_list = create_search_list(filters, file_count)
        if files_list == None or len(files_list) == 0:
            file = "no_file_found"
            
        else:
            files = [f["file"] for f in files_list]
            if current_file in files:
                file = current_file

            else:
                file = files[0]

        return redirect(url_for(".debates_file", query=query, file=file, settings=settings))

    # laad alle zoekresultaten en open bovenste doc
    else:
        search_list_size = 20

        # haal alle geselecteerde settings op
        filters = unpack_debate_settings(settings)
        
        file_translation = "translate"
        if "file_translation" in filters.keys():
            file_translation = filters.pop("file_translation")

        # set infinite scroll size
        if "file_count" in filters.keys():
            search_list_size = int(filters.pop("file_count"))
        
        query_dict = filters.copy()
        query_dict["query"] = query
        file_dict = {"file": file}
        
        render_list = create_search_list(query_dict, search_list_size)
        render_file, file_info = create_file(file_dict, file_translation)

        # als er geen file beschikbaar is
        if render_file == None and file_info == None or render_list == None:
            
            return render_template("debates.html", render_list=render_list, query=query, file=file, nav_options=debate_nav_options, settings=settings, selected_settings=filters)
        

        # text modificaties

        # list links
        total_highlighted_words = 0
        for sentence in render_list:
            sentence["content"] = highlight_sentence(query, sentence, file=False)

        # file rechts

        # mensen die in de resultaten voorkomen en ook in de file
        matches = []
        for sentence in render_list:
            if sentence["file"] == file:
                matches.append(sentence["person"])

        # segment counter om highlighted zinnen bij te houden
        seg = 0

        # pas alle zinnen aan
        for count, file_sentence in enumerate(render_file):
            file_sentence["content"], sentence_highlighted_words = highlight_sentence(query, file_sentence)

            # highlighted zinnen tracker
            if sentence_highlighted_words > 0:
                seg += 1
                file_sentence["id"] = seg
            else:
                file_sentence["id"] = 0

            # counter voor mooie statistieken bij search
            total_highlighted_words += sentence_highlighted_words
            
            # persoon komt links en rechts voor
            if file_sentence["person"] in matches:
                file_sentence["person"] = f"<span style='color: #28A745;'>{file_sentence['person']}</span> - {file_sentence['party']}"

            # persoon komt niet overeen met match
            else:
                file_sentence["person"] = f"<span style='color: #17A2B8;'>{file_sentence['person']}</span> - {file_sentence['party']}"
            
            render_file[count] = file_sentence
        
        # geladen files aantal bijhouden in info


        file_count = search_list_size

        # geef totaal aantal gevonden hits in het bestand
        if total_highlighted_words > 0:
            file_info["hits"] = f"{total_highlighted_words}"
            file_info["total_segs"] = seg
        else:
            file_info["hits"] = "Viewing translated document"

        return render_template("debates.html", render_list=render_list, render_file=render_file, query=query, file=file, nav_options=debate_nav_options, settings=settings, selected_settings=filters, file_info=file_info, file_count=file_count)

#####################################################################################

#                                  About page

#####################################################################################

@app.route("/", methods=(['GET', 'POST']))
def about():
    # redirect ngram search query
    if request.method == "POST":
        
        # ga naar debates
        if "debates" in request.form.keys():
            query, settings = redirect_debate(request.form, settings="none")

            if query == "":
                query = "no_query_yet"

            file = create_search_list({"query": query}, 1)

            if file == None:
                file = "no_file_found"
            else:
                file = file[0]["file"]

            return redirect(url_for(".debates_file", query=query, file=file, settings=settings))
            
        else:
            query, settings = redirect_ngram(request.form, settings="all")

            if query == "":
                query = "no_query_yet"

            return redirect(url_for(".home_query", query=query, timespan="year", settings=settings))
            

    return render_template("about.html", about="true")

#####################################################################################

#                                   Error handling

#####################################################################################
@app.errorhandler(500)
def internal_server_error(e):
    return render_template("error.html", error=["Internal server error", "Your request probably took too long"])

@app.errorhandler(404)
def internal_server_error(e):
    return render_template("error.html", error=["Page not found", "Your requested URL does not exist"])

#####################################################################################

#                                   Fetch handling

#####################################################################################

# zoom in op de ngram (door middel van redirects)
@app.route('/zoom', methods=(['POST']))
def zoom():
    
    if request.method == "POST":
        jsonData = request.get_json()
        
        x = jsonData["x"]
        query = jsonData["query"]
        timespan = jsonData["timespan"]
        settings = jsonData["settings"]
        
        # voeg filters toe aan url
        countries_text = ""
        if "_ct_" in settings:
            countries_text = "_ct_" + settings.split("_ct_")[-1]
        
        # zoom in op maanden
        if timespan == "month":
            return jsonify({"url": f"/ngrams/{query}/{timespan}/{x}{countries_text}"})

        # zoom in op dagen
        elif timespan == "day":
            return jsonify({"url": f"/ngrams/{query}/{timespan}/{x}{countries_text}"})
        
        # ga naar debates
        else:
            year, month, day = x.split("-")
            setting = f"{year}_y__{month}_m__{day}_d__ON_str__translate_ftr__"
            search_dict = {'content_translated': query,
                            'year': year,
                            'month': month,
                            'day': day}
            
            if "_ct_" in settings:
                countries = settings.split("_ct_")[1]
                setting += countries + "_ct__"
                search_dict["countries"] = countries.split("-")

            file = create_search_list(search_dict, 1)
            if file == None:
                # bij een combined ngram query met meerdere terms
                return jsonify({"url": "none"})
            elif len(file) == 0:
                file = "no_file_found"
            else:
                file = file[0]['file']

            return jsonify({"url": f"/debates/{query}/{file}/{setting}"})

# search autocomplete
@app.route("/search", methods=(['POST']))
def search_autocomplete():
    jsonData = request.get_json()
    query = jsonData["query"]
    category = jsonData["category"]

    # zoek door ngrams
    if category == "ngram":
        return query_ngram_suggestions(query)
    
    # zoek door person
    elif category == "person":
        persons = get_unique_keyword("person_simplified")
        persons.pop(0)
        
        return autocomplete(persons, query, 5)
    
    # zoek door party
    elif category == "party":
        parties = get_unique_keyword("party")
        parties.pop(0)
        
        # kort te lange namen in
        parties_list = autocomplete(parties, query, 5)
        corrected_parties_list = []
        for party in parties_list:

            if len(party) > 70:
                corrected_parties_list.append(party[:70] + "...")

            else:
                corrected_parties_list.append(party)

        return corrected_parties_list

# search autocomplete
@app.route("/search_confirm", methods=(['POST']))
def search_confirm():
    jsonData = request.get_json()
    query = jsonData["selected_query"]
    url = jsonData["url"].split("/")
    category = jsonData["category"]
    new_url = "/debates"
    
    # ngram search category
    if category == "ngram":
        # redirect /debates/<query>/<file>/<settings>
        if url[1] == "debates":
            
            # nog geen gespecificeerde dingen
            if len(url) == 2:
                file = create_search_list({"query": query}, 1)

                if file == None:
                    file = "no_file_found"
                else:
                    file = file[0]["file"]

                new_url = f"/debates/{query}/{file}/none"
            
            else:
                settings = url[4]

        # redirect ngrams /ngrams/<query>/<timespan>/<settings>
        else:
            # nog geen gespecificeerde dingen
            if len(url) == 2:
                new_url = f"/ngrams/{query}/year/all"
            
            else:
                timespan = url[3]
                settings = url[4]
                
                new_url = f"/ngrams/{query}/{timespan}/{settings}"
                return jsonify({"url": new_url})

    # person clicked in dropdown
    elif category == "person":

        # nog geen gespecificeerde dingen
        if len(url) == 2:
            new_url = f"/debates/no_query_yet/no_file_found/{query}_p__"

        else:
            q, settings = redirect_debate({"p=": query}, url[4].replace("%20", " "))

    # party clicked in dropdown
    elif category == "party":
        
        # nog geen gespecificeerde dingen
        if len(url) == 2:
            new_url = f"/debates/no_query_yet/no_file_found/{query}_pa__"

        else:
            q, settings = redirect_debate({"pa=": query}, url[4].replace("%20", " "))

    # behoud de al geopende file als die ook voorkomt in de nieuwe resultaten
    if len(url) > 2:
        search_list_size = 20
        filters = {}

        # query halen uit url omdat huidige query een setting is
        if category != "ngram":
            query = url[2]
        
            filters = unpack_debate_settings(settings)
        filters["query"] = query
        if "file_translation" in filters.keys():
            filters.pop("file_translation")

        # set infinite scroll size
        if "file_count" in filters.keys():
            search_list_size = int(filters.pop("file_count"))

        current_file = url[3]
        files_list = create_search_list(filters, search_list_size)
        if files_list == None or len(files_list) == 0:
            file = "no_file_found"
            
        else:
            files = [f["file"] for f in files_list]
            if current_file in files:
                file = current_file

            else:
                file = files[0]

        new_url = f"/debates/{query}/{file}/{settings}"

    return jsonify({"url": new_url})

# load new file scroll contents (debates)
@app.route("/continue_scrolling", methods=(['POST']))
def continue_scrolling():
    jsonData = request.get_json()
    url = jsonData["url"].split("/")
    file_count = jsonData["file_count"]

    query = url[2]
    settings = url[4].replace("%20", " ")

    # haal alle geselecteerde settings op
    filters = unpack_debate_settings(settings)

    if "file_translation" in filters.keys():
        filters.pop("file_translation")

    # verwijder file count
    if "file_count" in filters.keys():
        filters.pop("file_count")

    query_dict = filters.copy()
    query_dict["query"] = query

    render_list = create_search_list(query_dict, (file_count + 10))

    # er zijn nieuwe resultaten laadbaar
    if render_list != None and len(render_list) > file_count:

        # haal het al ingeladen deel weg
        new_list = render_list[file_count:]

        # houd het aantal ingeladen files bij
        file_count += len(new_list)

        # highlight nieuwe resultaten
        for sentence in new_list:
            sentence["content"] = highlight_sentence(query, sentence, file=False)
        
        q, settings = redirect_debate({"fc=": str(file_count)}, settings)

    # geen nieuwe resultaten meer
    else:
        new_list = []

    return jsonify({"file_count": file_count, "files": new_list, "settings": settings})

# app init
if __name__ == "__main__":
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(
        host = "127.0.0.1",
        port = 5000,
        debug = True
    )