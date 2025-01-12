# redirect functie voor overzicht in app.py
def redirect_ngram(form, settings):
    form_keys = form.keys()

    # voorkom error als iemand een leeg country filter submit
    if len(form_keys) == 0:
        if "_ct_" in settings:
            settings = settings.split("_ct_")[0]

        return "no_query_yet", settings

    form_key_first = list(form_keys)[0]
    query = "no_query_yet"
    
    # clear filters
    if "clear_filters" in form_keys:
        settings = "all"

    # landen filter
    if "ct=" in form_key_first:
        countries = "_ct_"

        for country in form:
            countries += (country.replace("-", "+").replace("ct=", "") + "-")

        if "_ct_" in settings:
            settings = settings.split("_ct_")[0]

        settings += countries[:-1]

    # query filter
    elif "query" in form_keys:
        query = form["query"]

    return query, settings


# redirect functie voor overzicht in app.py
def redirect_debate(form, settings):
    query = "no_query_yet"
    if len(form) == 0:
        settings = "none"
        return query, settings

    form_keys = form.keys()
    form_key_first = list(form_keys)[0]

    settings_dict = {}
    # voeg al bestaande settings toe aan de dict (wordt geoverwrite wanneer er een update is)
    for setting in settings.split("__"):
        if setting != "" and setting != "none":
            filter, title = setting.split("_")
            settings_dict[title] = filter
    

    # reset infinite scroller
    if "fc" in settings_dict.keys() and "ftr=" not in form_keys:
        settings_dict.pop("fc")

    # NOTE: onderstaande kijkt welk filter is toegevoegd in de POST request

    # landen filter
    if "ct=" in form_key_first:
        countries = ""

        for country in form:
            countries += (country.replace("-", "+").replace("ct=", "") + "-")

        settings_dict["ct"] = countries[:-1]
        
    # search translations filter
    elif "str=" in form_key_first:
        
        if form_key_first == "str=Browse in every original language":
            settings_dict["str"] = "OFF"
            settings_dict["ftr"] = "original"
        else:
            settings_dict["str"] = "ON"
            settings_dict["ftr"] = "translate"

    # person filter
    elif "p=" in form_key_first and form[form_key_first] != "":

        settings_dict["p"] = form[form_key_first]

    # party filter
    elif "pa=" in form_key_first and form[form_key_first] != "":
        settings_dict["pa"] = form[form_key_first]

    # year filter
    elif "y=" in form_key_first:
        settings_dict["y"] = form_key_first.replace("y=", "")

    # month filter
    elif "m=" in form_key_first:
        settings_dict["m"] = form_key_first.replace("m=", "")

    # day filter
    elif "d=" in form_key_first:
        settings_dict["d"] = form_key_first.replace("d=", "")

    # file translations filter
    elif "ftr=" in form_keys:
        settings_dict["ftr"] = form["ftr="]

    # infinite scroll filter
    elif "fc=" in form_keys:
        settings_dict["fc"] = form["fc="]

    # query filter
    elif "query" in form_keys:
        query = form["query"]


    # clear fitlers
    if "clear_filters" in form_keys or not len(settings_dict.keys()) > 0:
        settings = "none"


    # voeg alle settings samen in een URL
    else:
        settings = ""
        for k, v in settings_dict.items():
            settings += (f"{v}_{k}__")

    return query, settings