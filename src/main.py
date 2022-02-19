from typing import List, Dict
from genanki import Deck, Note, Model, Package

def main(args: List[str]) -> int:
    # Scrape the data from Wikidata
    data = scrape_wikidata()
    # Build the deck object
    deck = build_deck(data)
    # Write the deck object to an .apkg file
    write_deck(deck)
    return 0

def scrape_wikidata() -> List[Dict[str, str]]:
    return [
        {
            "Monarch": "Purrincess Felicity II",
            "ReignedFrom": "1986",
            "ReignedTo": "present",
            "Image": '<img src="miaownarch.jpg">',
            "Predecessor": "King Joseph I",
            "Successor": "",
        }
    ]


def build_deck(data: List[Dict[str, str]]) -> Deck:
    # Define model
    model = Model(
        7499558394,  # Unique model ID randomly generated
        'Monarch Model',
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
        ]
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
            datum.get("Monarch") or "",
            datum.get("ReignedFrom") or "",
            datum.get("ReignedTo") or "",
            datum.get("Image") or "",
            datum.get("Predecessor") or "",
            datum.get("Successor") or "",
        ]
    )
    return my_note


def write_deck(deck: Deck) -> None:
    package = Package(deck)
    package.media_files = ['../img/miaownarch.jpg']
    package.write_to_file('test.apkg')

if __name__ == "__main__":
    import sys
    status = main(sys.argv)
    sys.exit(status)
