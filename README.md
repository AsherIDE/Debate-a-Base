# Set up: step-by-step guide

## 1. Docker
1. Make sure you have Docker installed
2. Create a `docker-compose.yml` file in order to launch everything at once
    - With this you should be able to pull Elasticsearch and possibly Kibana
        - Kibana might come in handy with debugging
    - `docker-compose.yml` examples: 
        - https://github.com/AsherIDE/EU-scale-search/tree/main
        - Inside of DockerCompose folder
        - Note that the windows version runs a locally created image of the website, the linux version runs a pulled image of the website
        - If you are making changes to the website, you should use the windows `docker-compose.yml` approach
    - Create the following structure
```sh
[ROOT]
|- docker-compose.yml
|- .env
```
3. Run `docker-compose pull` to pull latest versions of all images
    - You should now have the website and Elasticsearch (and possibly Kibana)
4. Obtain Elasticsearch credentials
    - Host: https://localhost:9200 by default
    - User: elastic by default
    - Password
5. Inside of the `.env` file should be the following: 
```
ELASTIC_PASSWORD=PASSWORDGOESHERE
```
6. One important thing to note is that you will need to create another `.env` file within the main folder of the website
    - These are also credentials to Elasticsearch
    - The contents of the file should look like this:
```
DAB_ES_HOST=https://localhost:9200
DAB_ES_USER=elastic
DAB_ES_PASSWORD=PASSWORDGOESHERE
```
4. Run `docker-compose up -d` to start the stack
5. The website is should now be available at `0.0.0.0:5000`, however we do still need the data
6. Run `docker-compose down` to shut all containers down again
    - Some of the upcoming notebook steps require docker to be running, but that will become clear from the notebook markdown cells
7. Alternatively you can decide to pull the website from this Github page, if you want to make some alterations yourself
    - The third chapter will go more on debth on that

## 2. Data generation
Now we will focus on getting all Parlamint data into the right formats and then into Elasticsearch.

### 2.1 Install original and translated versions of Parlamint 4.1
- Untranslated data --> https://www.clarin.si/repository/xmlui/handle/11356/1912
- Translated data --> https://www.clarin.si/repository/xmlui/handle/11356/1910

### 2.2 Extract .tgz files
This process takes up hundreds of GB's so make sure some storage spage is available.
1. Create 2 folders:
    - EU --> Untranslated data
    - EN --> Translated data
2. Delete:
    - ParlaMint-4.1.tgz (EU and EN folder)
    - ParlaMint-4.1-Logs.tgz (EN folder)
3. Extract all remaining `.tgz` files
4. Delete everything but the `.TEI` and `.TEI.ANA` folders
5. Create the following file structure with the remaining `.TEI` and `.TEI.ANA` folders:
```sh
[ROOT]
|- data
    |- original
        |- EN (29 folders)
            |- ParlaMint-AT-en.TEI.ana
            |- ParlaMint-{country}-en.TEI.ana
        |- EU (29 folders)
            |- ParlaMint-AT.TEI
            |- ParlaMint-{country}.TEI
    |- preprocessed
|- notebooks
```

### 2.3 Convert .xml files into .csv
1. Download notebooks: https://github.com/AsherIDE/EU-scale-search/tree/main/Notebooks/Parlamint_v4.1
    - Now we will download the notebooks required to process the obtained data
    - Notebooks will be used, since it will be easier to test for possible errors with future Parlamint data updates
    - All notebooks use relative paths, so you should be fine if you create the following file structure:
```sh
[ROOT]
|- data
|- notebooks
    |- debates_4.1.ipynb
    |- ngrams_csv_4.1.ipynb
    |- ngrams_csvcount_4.1.ipynb (when youre not working with Parlamint 4.1)
    |- ngrams_4.1.ipynb
```
2. Execute `debates_4.1.ipynb` and follow instruction from the notebook
    - This will upload all ParlaMint data to Elasticsearch for the debates page
    - You are processing 262GBs, expect it to take a bit over a day
    - We aren't multiprocessing, so just let it run in the background and you can still use your device
3. Execute `ngrams_csv_4.1.ipynb` and follow instruction from the notebook
    - Creates `.csv` files with spoken lines from every debate
    - This ensures faster n-gram generation times later on
    - Runtime is about a few hours, although we are multiprocessing here so you might have some lag
4. Create `uploaded_ngram_dates.csv` inside of the `data` folder
    - For the next step this will keep track of which files have been processed into Ngrams and uploaded to Elasticsearch
    - Put the following information inside of the file, including the empty line
```
key, value

```
5. Execute `ngrams_4.1.ipynb` and follow instruction from the notebook
    - This will upload all ParlaMint data to Elasticsearch for the ngrams page
    - You are processing insane amounts of data, which will take about 3 days straight
    - Multiprocessing is set to 15 processes at the same time, you can tweak this to your liking and system capabilities


## 3. Website
- If you were not planning on altering anything and you are working with Parlamint 4.1, that means you should now be able to use the website
    - In that case run `docker-compose up -d` and if the website is inside of the `docker-compose.yml` it should be available at `0.0.0.0:5000`
- If you are making alterations to the website, please read the information below

### Updating Ngrams page with future Parlamint datasets
- Update word counts file, which is used to calculate term relevancy for the Ngrams page. These word counts have to be calculated for new dates aswell
    1. Execute `ngrams_csvcount_4.1.ipynb` and follow instruction from the notebook
        - Creates a `xml_word_counts.csv` file inside of the `data` folder
        - File contains total word count for every date, for every country 
    2. Rename `xml_word_counts.csv` to `proper_word_counts.csv` and place it inside of `static/helpers/`

### Adding or removing countries
- Change `ngram_nav_options["countries"]` line 19 in `app.py` if you want to add or remove countries
- Change `translated_countries` line 49 in `elastic_coms.py` to add or remove countries that have the "translate" option availablem on the debates page
    - GB is excluded, since it already is in English
- Change `ngram_legend_names` and `ngram_legend_colors` on line 50 and 51 in `elastic_coms.py` to add and remove the possibility to visualize a country on the ngrams page
- Changing about page image with countries part of dataset
    1. Create new image
        - Current image created on: https://www.mapchart.net/europe.html
    2. Resize image to 898x799 pixels
    3. Rename image to `Country_Dataset.png`
    4. Place it inside of folder `static/icons/`

## Update notes 4.1
- `Update elastic debates 3.0.ipynb` --> `debates_4.1_.ipynb`
    - Removed automatic `.tgz` extraction due to many variables changing per update
    - Now working with relative paths
- `Ngrams preparation 3.0.ipynb` --> `ngrams_prep_4.1_`
    - Now working with relative paths
- New countries: ES-PV, ES, FI
- Fixed issue where queries for countries with a "-" like ES-PV would be counted as 2 separate countries, making it impossible to find the country. Changes on:
    - `app.py` line 363: countries.split("-") --> [country.replace("+", "-") for country in countries.split("-")]
    - `redirect.py` line 24, 64: added .replace("-", "+")
    - `unpack_settings.py` line 8, 38: added .replace("+", "-")