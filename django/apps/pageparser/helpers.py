import re

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from html import unescape
from lxml.html import etree
from lxml.html.clean import Cleaner
from urllib.parse import urlparse


def absolutize_url(address, path):
    """
    Takes website address, a path relative to that address, and concatenates them
    :param address: A string that represents website address, like 'https://example.com/' with no path whatsoever
    :param path: A string that represents path, relative to website address
    :return: A string that represents absolute URL
    """
    # XOR: TT=F, TF=T, FT=T, FF=F
    if address.endswith('/') ^ path.startswith('/'):
        # 'https://example.com/' + 'path' or 'https://example.com' + '/path' = 'https://example.com/path'
        return address + path

    elif address.endswith('/') and path.startswith('/'):
        # 'https://example.com/' + '/path'[1:] = 'https://example.com/path'
        return address + path[1:]


def reinforce_text(text):
    """
    Takes a text fragment, splits it in words and wraps every word that is longer than 4 symbols with <strong></strong>
    Does not account for words with ' , like "user's", "town's" and so on. Words like "manual's" will be wrapped like
    "<strong>manual</strong>'s"
    :param text: A string, text fragment from tree traversal and text extraction
    :return: A string, with no excessive whitespaces, that contains all the words from original string
    """

    # We take original phrase and parse it character by character. If character is not alphanumeric, it is replaced
    # with whitespace; we don't need to replace anything in text just yet
    # Next, we join-split it to proper list and make set of it, so each word will be wrapped exactly once, if needed
    for word in set(''.join((char if char.isalpha() else ' ') for char in text).split()):

        # Here goes our condition from the task and replacement of the word in the original text fragment
        if len(word) > 4:
            text = re.sub(fr'\b{word}\b', f'<strong>{word}</strong>', text)

    # Getting rid of excessive whitespaces, while we are here
    return ' '.join(text.split()) + ' '


def schemeful_domain(target_url):
    """
    Parses an URL ino scheme and net location, so they can be used in making relative URLs absolute
    :param target_url: A string, an URL given by user
    :return: A string, well-formed URL, which leads to root of a website
    """
    parsed_uri = urlparse(target_url)
    return f'{parsed_uri.scheme}://{parsed_uri.netloc}/'


def sterilize_page(page_source):
    """
    Replaces \n, \r and \t with spaces, then extracts all the text with anchors only, discards everything else,
    e.g. <script></scipt>, <style>, and so on
    :param page_source: A string that represents page source in HTML
    :return: A string that represents HTML-safe sterilized page source in HTML with text and anchors
    """
    # Replace new lines and tabs with whitespace
    for character in ['\n', '\r', '\t']:
        page_source = page_source.replace(character, ' ')

    # Clean page_source from scripts, styles and all other tags, except anchors, but retain text
    cleaner = Cleaner(
        style=True,
        allow_tags=['a'],
        remove_unknown_tags=False,
        safe_attrs_only=True,
        safe_attrs=['href']
    )

    return ' '.join(cleaner.clean_html(page_source).split())


def process_page(sterile_page, target_url):
    """
    Process the page so all the links has it's text wrapped in <em></em> and all the words that are longer than 4
    symbols are wrapped in <strong></strong>
    :param sterile_page: A string, target page's source stripped from all the tags, but <a></a>
    :param target_url: A string, an URL which user gave us
    :return: A string, processed page ready to render in template
    """
    # Parse the inbound page into element tree with lxml
    root = etree.fromstring(sterile_page)

    # First, let's deal with <a></a>
    for a_tag in root.xpath(".//a"):

        # If <a></a> has some text in it
        if a_tag.text and a_tag.text.strip():

            # Create new element <em></em>, assign the text from <a></a> to it, delete the text from <a></a>,
            # and insert <em></em> element instead
            em = etree.Element('em')
            em.text = a_tag.text
            a_tag.text = None
            a_tag.insert(0, em)

            # While we are at it, let's fix all the broken relative links we got from page source
            # #crutch_alert
            try:
                # If it works, we don't need to do anything with the a_tag's href
                valid = URLValidator()
                valid(a_tag.attrib['href'])

            except ValidationError:
                # Good chances are, that this malformed url is _relative_ to target url's domain
                a_tag.attrib['href'] = absolutize_url(schemeful_domain(target_url), a_tag.attrib['href'])

        else:
            # If <a></a> is empty (e.g., after removing an image from anchor's text), remove it altogether with hrefs.
            a_tag.getparent().remove(a_tag)

    # Take every element in the tree and traverse the tree, checking if it has text in it
    # If it does, inflict reinforce_text() which will wrap the words in <strong></strong> if they are longer than 4
    for element in root.iter():

        if element.text and element.text.strip():
            element.text = reinforce_text(element.text)

        if element.tail and element.tail.strip():
            element.tail = reinforce_text(element.tail)

    # The final bit: flatten the modified tree back to string, decode it and then unescape everything what was escaped
    # (< and > in <strong></strong>)
    return unescape(etree.tostring(root, method='html').decode())
