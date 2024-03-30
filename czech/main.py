from typing import List, Dict, NamedTuple
from genanki import Deck, Note, Model, Package
import requests
from datetime import datetime
import logging as log

class Definition(NamedTuple):
    definition: str
    example: str
    example_en: str = None     # The translation in English
    audio: str = None          # The audio file name
    target: str = None         # The target word in the example
    target_en: str = None      # The target word in English

# Data from Wiktionary
class WordData(NamedTuple):
    word: str               # the root word
    rank: int               # its frequency rank
    wk_link: str            # url for its Wiktionary page
    defs: List[Definition]  # list of definitions and usage examples
    english: List[str]      # the English word translation

def main(args: List[str]) -> int:
    assert len(args) == 2, "Usage: main OUTPUT"
    out = args[1]
    # Get the words, definitions, and examples from Wiktionary
    data = scrape_wiktionary("1-1000")
    # Get translations from DeepL
    get_translations(data)
    # Get TTS.
    get_tts(data)
    # Build and write the deck object to an .apkg file
    deck = build_deck(data)
    write_deck(out, deck)
    log.info('Done.')
    return 0


def scrape_wiktionary(page: str) -> Dict[str, WordData]:
    pass

def get_translations(data: Dict[str, WordData]):
    pass

def get_tts(data: Dict[str, WordData]):
    pass

def build_deck(data: Dict[str, WordData]) -> Deck:
    # Define note type
    model = Model(
        3923034357,  # Unique model ID randomly generated
        'Czech Definition',
        fields=[
            {"name": "Word"},
            {"name": "EnglishWord"},
            {"name": "Rank"},
            {"name": "Definition"},
            {"name": "Example"},
            {"name": "ExampleAudio"},
            {"name": "EnglishExample"},
            {"name": "Wiktionary"},
        ],
        templates=[
            {
                'name': 'CzEnExample',
                'qfmt': '{{Example}}<br>{{ExampleAudio}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{EnglishExample}}<br><a href={{Wiktionary}}>Wiktionary</a>',
            }
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
        8898791874,  # Unique deck ID randomly generated
        'My Refold Czech'
    )
    # Add notes
    for d in data.values():
        deck.add_note(make_note(d, model))
    # Return
    return deck

def make_note(datum: WordData, model: Model) -> Note:
    my_note = Note(
        model=model,
        fields=[
            # TODO
        ]
    )
    return my_note

def write_deck(out: str, deck: Deck, data: Dict[str, WordData]) -> None:
    package = Package(deck)
    files = None   # TODO: using data
    package.media_files = [f'../audio/{file}' for file in files]
    package.write_to_file(out)

if __name__ == "__main__":
    import sys
    # Logging config
    log.basicConfig(stream=sys.stdout, level=log.INFO)
    # Run program
    status = main(sys.argv)
    sys.exit(status)
