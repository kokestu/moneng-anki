from typing import List, Dict, Tuple
from genanki import Deck, Note, Model, Package
import requests
from datetime import datetime
import logging as log


def main(args: List[str]) -> int:
    assert len(args) == 2, "Usage: main OUTPUT"
    out = args[1]
    # Scrape the data from Wikidata
    data, images = scrape_wikidata()
    # Build the deck object
    deck = build_deck(data)
    # Write the deck object to an .apkg file
    write_deck(out, deck, images)
    log.info('Done.')
    return 0


def download_image(filename: str, uri: str) -> str:
    import os.path
    # Build filename with extension
    ext = uri.split('.')[-1]
    with_ext = f'{filename}.{ext}'
    path = '../img/' + with_ext
    if not os.path.exists(path):
        # Wikimedia requires descriptive headers
        log.info(f'Downloading image for {filename}...')
        headers = {'user-agent':
            'moneng-anki/0.0.0 (https://github.com/kokestu/moneng-anki)'}
        img_data = requests.get(uri+'?width=300px', headers=headers).content
        with open(path, 'wb') as file:
            file.write(img_data)
    else:
        log.info(f'Image for {filename} already present...')

    return with_ext


# Test queries at: https://query.wikidata.org/
def scrape_wikidata() -> Tuple[List[Dict[str, str]], List[str]]:
    # Make the query to Wikidata
    url = 'https://query.wikidata.org/sparql'
    query = '''
    SELECT (?itemLabel as ?name)
    # Get first start date
    (min(?start) as ?start_date)
    # Get last end date
    (max(?end) as ?end_date)
    # Make a list
    (GROUP_CONCAT(DISTINCT ?replacesLabel; SEPARATOR=", ") AS ?predecessors)
    (GROUP_CONCAT(DISTINCT ?replaced_byLabel; SEPARATOR=", ") AS ?followers)
    # Get a random image
    (SAMPLE(?pic) AS ?pics)
    WHERE {
        # Define positions "monarch of UK" and "monarch of England"
        VALUES ?positions {wd:Q18810062 wd:Q9134365}
        # Filter by "position held" == "monarch of UK" or "monarch of England"
        ?item p:P39 ?statement.
        ?statement ps:P39 ?positions.
        # Select relevant parameters
        OPTIONAL { ?statement pq:P580 ?start. }          # Start time
        OPTIONAL { ?statement pq:P582 ?end. }            # End time
        OPTIONAL { ?statement pq:P1365 ?replaces. }      # Predecessor
        OPTIONAL { ?statement pq:P1366 ?replaced_by. }   # Successor
        OPTIONAL { ?item wdt:P18 ?pic}                   # Image
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".
                                ?item rdfs:label ?itemLabel.
                                ?replaces rdfs:label ?replacesLabel.
                                ?replaced_by rdfs:label ?replaced_byLabel.}
    }
    # Group records by the monarch name
    GROUP BY (?itemLabel)
    ORDER BY DESC (?start)
    '''
    log.info('Making Wikidata request...')
    r = requests.get(url, params={'format': 'json', 'query': query})
    data = r.json()['results']['bindings']

    def get_value(monarch, name):
        return monarch.get(name, {}).get('value', '')

    def get_year(iso_date):
        if iso_date:
            return str(datetime.strptime(iso_date, '%Y-%m-%dT%H:%M:%SZ').year)
        return 'Present'

    # Collect the monarch records and image filenames
    monarchs = []
    images = []
    for entry in data:
        if get_value(entry, 'name') in [
                'Eleanor of Aquitaine',
                ]:
            continue
        image_uri = get_value(entry, 'pics')
        if not image_uri:
            raise ValueError(f'No image for {entry}')
        img_name = download_image(
            get_value(entry, 'name').replace(' ', '-'),
            get_value(entry, 'pics')
        )
        images.append(img_name)
        monarch = dict(
            Monarch=get_value(entry, 'name'),
            ReignedFrom=get_year(get_value(entry, 'start_date')),
            ReignedTo=get_year(get_value(entry, 'end_date')),
            Image=f'<img src="{img_name}">',
            Predecessor=get_value(entry, 'predecessors'),
            Successor=get_value(entry, 'followers'),
        )
        monarchs.append(monarch)

    return monarchs, images


def build_deck(data: List[Dict[str, str]]) -> Deck:
    # Define note type
    model = Model(
        7499558394,  # Unique model ID randomly generated
        'Monarch',
        fields=[
            {"name": "Monarch"},
            {"name": "ReignedFrom"},
            {"name": "ReignedTo"},
            {"name": "Image"},
            {"name": "Predecessor"},
            {"name": "Successor"},
        ],
        templates=[
            {
                'name': 'Dates',
                'qfmt': 'Reigned {{ReignedFrom}} - {{ReignedTo}}?',
                'afmt': '{{FrontSide}}<hr id="answer">{{Monarch}}<br>{{#Image}}{{Image}}{{/Image}}',
            },
            {
                'name': 'Start',
                'qfmt': 'Reigned from {{ReignedFrom}}?',
                'afmt': '{{FrontSide}}<hr id="answer">{{Monarch}}<br>{{#Image}}{{Image}}{{/Image}}',
            },
            {
                'name': 'End',
                'qfmt': 'Reigned to {{ReignedTo}}?',
                'afmt': '{{FrontSide}}<hr id="answer">{{Monarch}}<br>{{#Image}}{{Image}}{{/Image}}',
            },
            {
                'name': 'Predecessor',
                'qfmt': '{{#Predecessor}}Reigned after {{Predecessor}}?{{/Predecessor}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Monarch}}<br>{{#Image}}{{Image}}{{/Image}}',
            },
            {
                'name': 'Successor',
                'qfmt': '{{#Successor}}Reigned before {{Successor}}?{{/Successor}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Monarch}}<br>{{#Image}}{{Image}}{{/Image}}',
            },
            {
                'name': 'Image',
                'qfmt': '{{#Image}}{{Image}}{{/Image}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Monarch}}',
            },
        ],
        css="""
        .card {
        font-family: arial;
        font-size: 20px;
        text-align: center;
        color: black;
        background-color: white;
        }
        """,   # custom styling
    )
    # Create deck
    deck = Deck(
        4276883578,  # Unique deck ID randomly generated
        'Monarchs of England'
    )
    # Add notes
    for d in data:
        deck.add_note(make_note(d, model))
    # Return
    return deck


def make_note(datum: Dict[str, str], model: Model) -> Note:
    my_note = Note(
        model=model,
        fields=[
            datum.get("Monarch"),
            datum.get("ReignedFrom"),
            datum.get("ReignedTo"),
            datum.get("Image"),
            datum.get("Predecessor"),
            datum.get("Successor"),
        ]
    )
    return my_note

def write_deck(out: str, deck: Deck, images: List[str]) -> None:
    package = Package(deck)
    package.media_files = [f'../img/{img}' for img in images]
    package.write_to_file(out)

if __name__ == "__main__":
    import sys
    # Logging config
    log.basicConfig(stream=sys.stdout, level=log.INFO)
    # Run program
    status = main(sys.argv)
    sys.exit(status)
