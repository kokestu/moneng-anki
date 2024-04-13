from typing import List, Dict, NamedTuple
from genanki import Deck, Note, Model, Package
import requests
from datetime import datetime
import logging as log
from html.parser import HTMLParser


class Definition(NamedTuple):
    definition: str
    example: str               # An example sentence
    example_en: str = None     # The example in English
    audio: str = None          # The audio file name

# Data from Wiktionary
class WordData(NamedTuple):
    word: str                   # the root word
    rank: int                   # its frequency rank
    wk_link: str                # url for its Wiktionary page
    defs: List[Definition]      # list of definitions and usage examples
    english: List[str]          # the English word translations

# Mapping from word to word data
Data = Dict[str, WordData]


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
                    # to be filled in later:
                    defs = [],
                    english = []
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
            # We've got to the words: these headers top each word section.
            self.in_words = True


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


def _get_word_translation(text):
    with open("deepl-api.txt") as f:
        api_key = f.readline()
    url = 'https://api-free.deepl.com/v2/translate'
    headers = {
        'Authorization': f'DeepL-Auth-Key {api_key}'
    }
    data = {
        'text': text,
        "source_lang": 'CS',
        'target_lang': 'EN',
        'tag_handling': 'html',
        'split_sentences': 0
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json()["translations"][0]["text"]


def get_translations(data: Data):
    """Translate example and fill in example_en for each value in data

    Args:
        data (Data): The word data
    """
    for entry in data.values():
        for definition in entry.defs:
            definition.example_en = _get_word_translation(definition.example)


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
                'qfmt': "{{Example}}<br>{{#ExampleAudio}}{{ExampleAudio}}{{/ExampleAudio}}",
                'afmt': ("{{FrontSide}}<hr id=\"answer\">"
                         "{{EnglishExample}}<br>"
                         "<a href={{Wiktionary}} style=\"font-size:10px\">Wiktionary</a><br>"
                         "<a href=https://glosbe.com/cs/en/{{Word}} style=\"font-size:10px\">Glosbe</a>"
                        ),
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
    for word in data.values():
        # Make a note for every definition, not every word (since a word
        # can mean quite different things in different conditions).
        for definition in word.defs:
            deck.add_note(make_note(definition, word, model))
    # Return
    return deck

def make_note(
    definition: Definition, word: WordData, model: Model
) -> Note:
    my_note = Note(
        model=model,
        fields=[
            # Word
            word.word,
            # EnglishWord
            word.english.join(", "),
            # Rank
            word.rank,
            # Definition
            definition.definition,
            # Example
            definition.example,
            # ExampleAudio
            None,    # TODO
            # EnglishExample
            definition.example_en,
            # Wiktionary
            word.wk_link
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
