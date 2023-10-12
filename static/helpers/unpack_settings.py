def unpack_ngram_settings(timespan, settings):
    countries = []
    if "_ct_" in settings:
        countries_text = settings.split("_ct_")[-1]
        settings = settings.split("_ct_")[0]

        for country in countries_text.split("-"):
            countries.append(country)

    if "all" not in settings:
        year, month, day = settings.split("-")
    
    if len(countries) == 0:
        countries = None

    if timespan == "year":
        return countries

    elif timespan == "month":
        return year, countries
    
    elif timespan == "day":
        return year, month, countries
    

def unpack_debate_settings(settings):
    filters = {}

    settings_dict = {}
    for setting in settings.split("__"):
        if setting != "" and setting != "none":
            filter, title = setting.split("_")
            settings_dict[title] = filter
    
    if "_ct__" in settings:
        countries = []
        for country in settings_dict["ct"].split("-"):
            countries.append(country)

        filters["countries"] = countries

    if "_ftr__" in settings:
        filters["file_translation"] = settings_dict["ftr"]

    if "_str__" in settings:
        filters["search_translation"] = settings_dict["str"]

    if "_p__" in settings:
        filters["person"] = settings_dict["p"]

    if "_pa__" in settings:
        filters["party"] = settings_dict["pa"]

    if "_y__" in settings:
        filters["year"] = settings_dict["y"]

    if "_m__" in settings:
        filters["month"] = settings_dict["m"]

    if "_d__" in settings:
        filters["day"] = settings_dict["d"]

    if "_fc__" in settings:
        filters["file_count"] = settings_dict["fc"]
    
    return filters