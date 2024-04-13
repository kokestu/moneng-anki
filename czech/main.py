from typing import List, Dict, NamedTuple
from genanki import Deck, Note, Model, Package
import requests
from datetime import datetime
import logging as log
from html.parser import HTMLParser

class WkWordListHTMLParser(HTMLParser):
    # Have we got to the words yet?
    in_words = False
    # The data collected so far.
    data = {}
    # Keep track of the rank of the current word.
    wordrank = 1
    # Handle the HTML tags.
    def handle_starttag(self, tag, attrs):
        if self.in_words:
            if tag == "a" and "title" in [k for (k,v) in attrs]:
                # Build the word data.
                attrs = dict(attrs)
                word = attrs["title"]
                self.data[word] = WordData(
                    word = word,
                    rank = self.wordrank,
                    wk_link = f"https://cs.wiktionary.org{attrs['href']}",
                    defs = []  # to be filled in later
                )
                # Bump the word rank tracker
                self.wordrank += 1
        else:
            pass
    # Handle the closing tags.
    def handle_endtag(self, tag):
        # The words are only between the p tags after the header.
        if self.in_words and tag == "p":
            self.in_words = False
        elif tag == "h5":
            # We've got to the words.
            self.in_words = True

class Definition(NamedTuple):
    definition: str
    english: List[str]         # the English word translation
    example: str               # An example sentence
    example_en: str = None     # The example in English
    audio: str = None          # The audio file name
    target: str = None         # The target word in the example
    target_en: str = None      # The target word in English

# Data from Wiktionary
class WordData(NamedTuple):
    word: str               # the root word
    rank: int               # its frequency rank
    wk_link: str            # url for its Wiktionary page
    defs: List[Definition]  # list of definitions and usage examples

# Mapping from word to word data
Data = Dict[str, WordData]

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


def scrape_wiktionary(page: str) -> Data:
    # Build the string to get the right page of the list.
    url = (
        "https://cs.wiktionary.org/wiki/P%C5%99%C3%ADloha:Frekven%C4%8Dn%"
        f"C3%AD_seznam_(%C4%8De%C5%A1tina)/%C4%8CNK_SYN2005/{page}"
    )
    resp = requests.get(url)
    parser = WkWordListHTMLParser()
    parser.feed(resp.content.decode("utf-8"))
    return parser.data

def get_translations(data: Data):
    pass

def get_tts(data: Data):
    pass

def build_deck(data: Data) -> Deck:
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
                'afmt': '{{FrontSide}}<hr id="answer">{{EnglishExample}}<br><a href={{Wiktionary}}>Wiktionary</a><br><a href=https://glosbe.com/cs/en/{{Word}}>Glosbe</a>',
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

def write_deck(out: str, deck: Deck, data: Data) -> None:
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
