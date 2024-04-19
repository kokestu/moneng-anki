from typing import List, Dict
from genanki import Deck, Note, Model, Package
import requests
import logging as log
from html.parser import HTMLParser
from dataclasses import dataclass
from tqdm import tqdm

@dataclass
class Definition:
    definition: str
    english: List[str]       # the English word translations
    examples: List[str]      # The example sentences
    example_en: str = None   # The example in English
    audio: str = None        # The audio file name

@dataclass
class WordData:
    word: str                   # the root word
    rank: int                   # its frequency rank
    wk_link: str                # url for its Wiktionary page
    defs: List[Definition]      # list of definitions and usage examples

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
                    defs = []
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


class WkWordPageHTMLParser(HTMLParser):
    # the id of a given section
    current_section = None
    # Are we in the list of examples?
    in_examples = False
    # Are we building a definition or example out of parts?
    process_line = False
    # Hold the definition or example so far -- as we're building it.
    text = ""
    # Keep track of the definition that the current translation goes with.
    def_no = -1
    # Are we collecting translations?
    collect_trans = False
    # Keeping track of language
    is_h2 = False
    is_czech = False

    def __init__(self, *, convert_charrefs: bool = True) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        # Track the definitions we've found.
        self.defs = []

    def _sort_current_section(self, id):
        if "význam" in (id or ""):
            self.current_section = "význam"
            return "význam"
        elif "překlady" in (id or ""):
            self.current_section = "překlady"
            return "překlady"
        return None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        # Until we get to the section on Czech, ignore everything.
        if tag == "h2":
            self.is_h2 = True
            self.is_czech = False
            return
        if self.is_h2 and attrs.get("id") == "čeština":
            self.is_czech = True
        if not self.is_czech:
            return
        # We're looking at czech, keep going
        # Keep track of the current section.
        new_id = self._sort_current_section(attrs.get("id"))
        if new_id == "význam":
            # New definitions section. Want to start the translations
            # counter at the end of this list.
            self.def_no = len(self.defs) - 1
        # When we're in "význam", get the definitions and examples.
        if self.current_section == "význam":
            if tag == 'ul':
                # When we get here, we've gotten to the end of the definition,
                # so handle it now.
                self.defs.append(
                    Definition(
                        definition=self.text.strip("\n"),
                        # to be filled in later:
                        examples=[],
                        english=[]
                    )
                )
                # Unordered lists are where the examples are.
                self.in_examples = True
            elif tag == 'li':
                # Found a definition or an example!
                self.process_line = True
                self.text = ""
            elif tag == 'b' and self.process_line:
                # Keep emphasis on words.
                self.text += "<b>"
            else:
                # We sometimes find "a" tags in the definitions. Don't need
                # to deal with them here, since we only care about their
                # content (in handle_data).
                pass
        # When we're in "překlady", get the English translations.
        elif self.current_section == "překlady":
            if (
                tag == 'span' and
                attrs.get("class") == "translation-item" and
                attrs.get("lang") == "en"
            ):
                # We've found an English translation!
                self.collect_trans = True
            elif tag == "div" and attrs["class"] == "translations":
                # Start of the next translation, bump the count.
                self.def_no += 1


    def handle_data(self, data: str) -> None:
        if self.process_line:
            # When we're processing a line, keep all the content of tags.
            self.text += data
        elif self.collect_trans:
            # Collect the translation.
            if len(self.defs) <= self.def_no:
                print(self.def_no)
                print(self.defs)
                print(data)
            self.defs[self.def_no].english.append(data)
            self.collect_trans = False

    # Handle the closing tags.
    def handle_endtag(self, tag):
        # Until we get to the section on Czech, ignore everything.
        if tag == "h2":
            self.is_h2 = False
            return
        if not self.is_czech:
            return
        # we're looking at czech, keep going
        if self.current_section == "význam":
            if tag == 'ul':
                # We've gotten to the end of the unordered list of
                # examples.
                self.in_examples = False
            if tag == 'li':
                if self.in_examples:
                    # This is the start of the next example, so finish the last
                    # one, and add it to the list in the current definition.
                    self.defs[-1].examples.append(self.text)
                    self.text = ""
                elif self.text:
                    # special case: no examples for a word (we don't hit <ul>)
                    # alternatively, if we are not in examples, this is the end
                    # or a defintition with no examples
                    self.defs.append(
                        Definition(
                            definition=self.text.strip("\n"),
                            # to be filled in later:
                            examples=[],
                            english=[]
                        )
                    )
                    self.text = ""
                self.process_line = False
            if tag == 'b':
                # Keep emphasis on words.
                self.text += "</b>"
        if tag == 'ol':
            # Found the end of the current section.
            self.current_section = None

def test_parse():
    url = "https://cs.wiktionary.org/wiki/a"
    resp = requests.get(url)
    parser = WkWordPageHTMLParser()
    parser.feed(resp.content.decode("utf-8"))
    return parser.defs


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
    # Get the word list.
    resp = requests.get(url)
    if resp.status_code != 200:
        raise RuntimeError(resp.status_code)
    parser = WkWordListHTMLParser()
    parser.feed(resp.content.decode("utf-8"))
    words = parser.data
    # For each word, get all of the word data. Display a progress bar
    # with tqdm.
    for word in tqdm(words.values()):
        resp = requests.get(word.wk_link)
        if resp.status_code != 200:
            raise RuntimeError(resp.status_code)
        parser = WkWordPageHTMLParser()
        parser.feed(resp.content.decode("utf-8"))
        word.defs = parser.defs
    return words


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
