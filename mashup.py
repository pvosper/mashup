"""
For your homework this week, you’ll be polishing this mashup.

Begin by sorting the results of our search by the average score (can you do
this and still use a generator for getting the geojson?).

Then, update your script to allow the user to choose how to sort, by average,
high score or most inspections:

(soupenv)$ python mashup.py highscore

Next, allow the user to choose how many results to map:

(soupenv)$ python mashup.py highscore 25

Or, allow them to reverse the results, showing the lowest scores first:

(soupenv)$ python mashup.py highscore 25 reverse

Notes

html = load_inspection_page('inspection_page.html')

source, dest = sys.argv[1:3]
[0] file name
[1] first string
[2] second string

dict_keys([
    'Longitude'
    'High Score'
    'Average Score'
    'Phone'
    'Latitude'
    'Address'
    'Total Inspections'
    'Business Name'
    'Business Category'
"""

from bs4 import BeautifulSoup
import geocoder
import json
import pathlib
import re
import requests
import operator
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("sort_key", help="Sort Key")
parser.add_argument("entry_count", type=int, help="Number of entries returned")
parser.add_argument("sort_order", help="Sort order")
args = parser.parse_args()
print("Args:\n\tSort key: {}\n\tEntry count: {}\n\tSort order: {}\n".format(
    args.sort_key, args.entry_count, args.sort_order))


INSPECTION_DOMAIN = 'http://info.kingcounty.gov'
INSPECTION_PATH = '/health/ehs/foodsafety/inspections/Results.aspx'
INSPECTION_PARAMS = {
    'Output': 'W',
    'Business_Name': '',
    'Business_Address': '',
    'Longitude': '',
    'Latitude': '',
    'City': '',
    'Zip_Code': '',
    'Inspection_Type': 'All',
    'Inspection_Start': '',
    'Inspection_End': '',
    'Inspection_Closed_Business': 'A',
    'Violation_Points': '',
    'Violation_Red_Points': '',
    'Violation_Descr': '',
    'Fuzzy_Search': 'N',
    'Sort': 'H'
}


def get_inspection_page(**kwargs):
    url = INSPECTION_DOMAIN + INSPECTION_PATH
    params = INSPECTION_PARAMS.copy()
    for key, val in kwargs.items():
        if key in INSPECTION_PARAMS:
            params[key] = val
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.text


def parse_source(html):
    parsed = BeautifulSoup(html, "html5lib")
    return parsed


def load_inspection_page(name):
    file_path = pathlib.Path(name)
    return file_path.read_text(encoding='utf8', errors='ignore')


def restaurant_data_generator(html):
    id_finder = re.compile(r'PR[\d]+~')
    return html.find_all('div', id=id_finder)


def has_two_tds(elem):
    is_tr = elem.name == 'tr'
    td_children = elem.find_all('td', recursive=False)
    has_two = len(td_children) == 2
    return is_tr and has_two


def clean_data(td):
    return td.text.strip(" \n:-")


def extract_restaurant_metadata(elem):
    restaurant_data_rows = elem.find('tbody').find_all(
        has_two_tds, recursive=False
    )
    rdata = {}
    current_label = ''
    for data_row in restaurant_data_rows:
        key_cell, val_cell = data_row.find_all('td', recursive=False)
        new_label = clean_data(key_cell)
        current_label = new_label if new_label else current_label
        rdata.setdefault(current_label, []).append(clean_data(val_cell))
    return rdata


def is_inspection_data_row(elem):
    is_tr = elem.name == 'tr'
    if not is_tr:
        return False
    td_children = elem.find_all('td', recursive=False)
    has_four = len(td_children) == 4
    this_text = clean_data(td_children[0]).lower()
    contains_word = 'inspection' in this_text
    does_not_start = not this_text.startswith('inspection')
    return is_tr and has_four and contains_word and does_not_start


def get_score_data(elem):
    inspection_rows = elem.find_all(is_inspection_data_row)
    samples = len(inspection_rows)
    total = 0
    high_score = 0
    average = 0
    for row in inspection_rows:
        strval = clean_data(row.find_all('td')[2])
        try:
            intval = int(strval)
        except (ValueError, TypeError):
            samples -= 1
        else:
            total += intval
            high_score = intval if intval > high_score else high_score

    if samples:
        average = total/float(samples)
    data = {
        u'Average Score': average,
        u'High Score': high_score,
        u'Total Inspections': samples
    }
    return data


def result_generator(count):
    use_params = {
        'Inspection_Start': '2/1/2013',
        'Inspection_End': '2/1/2015',
        'Zip_Code': '98101'
    }
    # html = get_inspection_page(**use_params)
    # Use pre-existing page
    html = load_inspection_page('inspection_page.html')
    # Parse using method that uses BeautifulSoup
    parsed = parse_source(html)
    content_col = parsed.find("td", id="contentcol")
    data_list = restaurant_data_generator(content_col)
    #Todo sort data list so entries used below are highest, lowest, etc
    for data_div in data_list[:count]:
        metadata = extract_restaurant_metadata(data_div)
        inspection_data = get_score_data(data_div)
        # Update metadata dictionary with inspection data
        metadata.update(inspection_data)
        # print(metadata,"\n")
        yield metadata


def sort_list_of_dictionaries(list_dicts, sort_key, rev=False):
    list_dicts.sort(key=operator.itemgetter(sort_key), reverse=rev)
    print(list_dicts)


def get_geojson(result):
    address = " ".join(result.get('Address', ''))
    if not address:
        return None
    geocoded = geocoder.google(address)
    geojson = geocoded.geojson
    inspection_data = {}
    use_keys = (
        'Business Name', 'Average Score', 'Total Inspections', 'High Score'
    )
    for key, val in result.items():
        if key not in use_keys:
            continue
        if isinstance(val, list):
            val = " ".join(val)
        inspection_data[key] = val
    geojson['properties'] = inspection_data
    return geojson


if __name__ == '__main__':
    # create dictionary with 'features' as a list
    total_result = {'type': 'FeatureCollection', 'features': []}
    for result in result_generator(10):
        print(result.keys())
        geojson = get_geojson(result)
        total_result['features'].append(geojson)
    # So features is a list of dictionaries that we can sort
    # sort_list_of_dictionaries(total_result['features'], 'High Score')
    with open('my_map.json', 'w') as fh:
        json.dump(total_result, fh)