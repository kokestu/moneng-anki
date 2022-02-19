from typing import List, Dict
from genanki import Deck, Note, Model, Package
import requests
from datetime import datetime


def main(args: List[str]) -> int:
    assert len(args) == 2, "Usage: main OUTPUT"
    out = args[1]
    # Scrape the data from Wikidata
    data, images = scrape_wikidata()
    # Build the deck object
    deck = build_deck(data)
    # Write the deck object to an .apkg file
    write_deck(out, deck, images)
    return 0


def download_image(filename: str, uri: str) -> str:
    img_data = requests.get(uri).content
    ext = uri.split('.')[-1]
    with open('../img/' + filename + ext, 'wb') as file:
        file.write(img_data)
    return filename


def scrape_wikidata() -> (List[Dict[str, str]], List[str]):
    url = 'https://query.wikidata.org/sparql'
    query = '''
    SELECT (?itemLabel as ?name)
    (SAMPLE(?start) as ?start)
    (SAMPLE(?end) as ?end)
    (GROUP_CONCAT(DISTINCT ?replacesLabel; SEPARATOR=", ") AS ?predecessors)
    (GROUP_CONCAT(DISTINCT ?replaced_byLabel; SEPARATOR=", ") AS ?followers)
    (SAMPLE(?pic) AS ?pics)
    WHERE {
    VALUES ?positions {wd:Q18810062 wd:Q9134365}
    ?item p:P39 ?statement.
    ?statement ps:P39 ?positions.
    OPTIONAL { ?statement pq:P580 ?start. }
    OPTIONAL { ?statement pq:P582 ?end. }
    OPTIONAL { ?statement pq:P1365 ?replaces. }
    OPTIONAL { ?statement pq:P1366 ?replaced_by. }
    OPTIONAL { ?item wdt:P18 ?pic}
    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".
                            ?item rdfs:label ?itemLabel.
                            ?replaces rdfs:label ?replacesLabel.
                            ?replaced_by rdfs:label ?replaced_byLabel.
                            }
    }
    group by (?itemLabel)
    ORDER BY DESC (?start)
    '''
    r = requests.get(url, params={'format': 'json', 'query': query})
    data = r.json()['results']['bindings']

    monarchs = []

    def get_value(monarch, name):
        return monarch.get(name, {}).get('value', '')

    def get_year(iso_date):
        if iso_date:
            return str(datetime.strptime(iso_date, '%Y-%m-%dT%H:%M:%SZ').year)
        return 'Present'

    images = []
    for entry in data:
        img_name = download_image(
            get_value(entry, 'name').replace(' ', '-'),
            get_value(entry, 'pics')
        )
        images.append(img_name)
        monarch = dict(
            Monarch=get_value(entry, 'name'),
            ReignedFrom=get_year(get_value(entry, 'start')),
            ReignedTo=get_year(get_value(entry, 'end')),
            Image=f'<img src="{img_name}">',
            Predecessor=get_value(entry, 'predecessors'),
            Successor=get_value(entry, 'followers'),
        )
        monarchs.append(monarch)

    return monarchs, images


def build_deck(data: List[Dict[str, str]]) -> Deck:
    # Define model
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
                'afmt': '{{FrontSide}}<hr id="answer">{{Monarch}}',
            },
            {
                'name': 'Start',
                'qfmt': 'Reigned from {{ReignedFrom}}?',
                'afmt': '{{FrontSide}}<hr id="answer">{{Monarch}}',
            },
            {
                'name': 'End',
                'qfmt': 'Reigned to {{ReignedTo}}?',
                'afmt': '{{FrontSide}}<hr id="answer">{{Monarch}}',
            },
            {
                'name': 'Predecessor',
                'qfmt': '{{#Predecessor}}Reigned after {{Predecessor}}?{{/Predecessor}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Monarch}}',
            },
            {
                'name': 'Successor',
                'qfmt': '{{#Successor}}Reigned before {{Successor}}?{{/Successor}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Monarch}}',
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
    status = main(sys.argv)
    sys.exit(status)
