from flask import Flask, render_template, request, jsonify, redirect, url_for
from static.helpers.elastic_coms import create_fig, create_search_list, create_file

app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/", methods=(['GET', 'POST']))
def home():
    
    # search query van user ontvangen 
    if request.method == "POST":

        # if "query" in request.form.keys():
        query = request.form["query"]

        # timer = time.time()

        graphJSON = create_fig({"ngram": query}, "year")

        # print(f"'{ngram_term}' took {round(time.time() - timer, 2)}s, for {ngram_total} results", file=sys.stderr)

        return render_template("main.html", graphJSON=graphJSON, query=query, timespan="year")

    # render default home page     
    else:
        print(request.form.keys())
        return render_template("main.html")

@app.route("/debates", methods=(['GET', 'POST']))
def debates():
    
    if request.method == "POST":
        
        # search query van user ontvangen 
        if "query" in request.form.keys():
            query = request.form["query"]

            # return render_template("debates.html", render_list=render_list)

            return redirect(url_for(".debates_file", query=query, file=create_search_list({"content_simplified": query}, 1)[0]["file"]))

    else:
        
        return render_template("debates.html")

# open een specifieke file
@app.route("/debates/<query>/<file>", methods=(['GET', 'POST']))
def debates_file(query, file):
    
    if request.method == "POST":
        query = request.form["query"]

        query_dict = {"content_simplified": query}
        file_dict = {"file": file}
        
        render_list = create_search_list(query_dict, 20)
        render_file = create_file(file_dict)
        
        return render_template("debates.html", render_list=render_list, render_file=render_file, query=query)

    # laad alle zoekresultaten en open bovenste doc
    else:
        query_dict = {"content_simplified": query}
        file_dict = {"file": file}

        render_list = create_search_list(query_dict, 20)
        render_file = create_file(file_dict)

        # return redirect(url_for(".debates_file", query=query, file=file))
        return render_template("debates.html", render_list=render_list, render_file=render_file, query=query)

# zoom in op de ngram
@app.route('/zoom', methods=(['GET', 'POST']))
def zoom():
    
    if request.method == "POST":
        jsonData = request.get_json()
        x = jsonData["x"]
        query = jsonData["query"]
        timespan = jsonData["timespan"]

        # zoom in op MAAND
        if timespan == "year":
            year = x.split("-")[0]

            graphJSON = create_fig({"ngram": query,
                                    "year": year}, "month")

            return jsonify({"template": render_template("main.html"), "graphJSON": graphJSON, "query": query, "timespan": "month"})
        
        # zoom in op DAGEN
        elif timespan == "month":
            
            year = x.split("-")[0]
            month = x.split("-")[1]

            graphJSON = create_fig({"ngram": query,
                                    "year": year,
                                    "month": month}, "day")

            return jsonify({"template": render_template("main.html"), "graphJSON": graphJSON, "query": query, "timespan": "day"})

if __name__ == "__main__":
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(
        host = "127.0.0.1",
        port = 5000,
        debug = True
    )