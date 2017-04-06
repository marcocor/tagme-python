
'''
This module provides a wrapper for the TagMe API.
'''
import logging
import requests
import json

from iso8601utils import parsers
from HTMLParser import HTMLParser

__all__ = [
    'annotate', 'mentions', 'relatedness_wid', 'relatedness_title', 'Annotation',
    'AnnotateResponse', 'Mention', 'MentionsResponse', 'Relatedness', 'RelatednessResponse',
    'normalize_title', 'title_to_uri',
    ]

__author__ = 'Marco Cornolti <cornolti@di.unipi.it>'

DEFAULT_TAG_API = "https://tagme.d4science.org/tagme/tag"
DEFAULT_SPOT_API = "https://tagme.d4science.org/tagme/spot"
DEFAULT_REL_API = "https://tagme.d4science.org/tagme/rel"
DEFAULT_LANG = "en"
DEFAULT_LONG_TEXT = 3
WIKIPEDIA_URI_BASE = u"https://{}.wikipedia.org/wiki/{}"
MAX_RELATEDNESS_PAIRS_PER_REQUEST = 100
GCUBE_TOKEN = None
HTML_PARSER = HTMLParser()

class Annotation(object):
    '''
    An annotation, i.e. a link of a part of text to an entity.
    '''
    def __init__(self, ann_json):
        self.begin = int(ann_json.get("start"))
        self.end = int(ann_json.get("end"))
        self.entity_id = int(ann_json.get("id"))
        self.entity_title = ann_json.get("title")
        self.score = float(ann_json.get("rho"))
        self.mention = ann_json.get("spot")

    def __str__(self):
        return u"{} -> {} (score: {})".format(self.mention, self.entity_title, self.score)

    def uri(self, lang=DEFAULT_LANG):
        '''
        Get the URI of this annotation entity.
        :param lang: the Wikipedia language.
        '''
        return title_to_uri(self.entity_title, lang)


class AnnotateResponse(object):
    '''
    A response to a call to the annotation (/tag) service. It contains the list of annotations
    found.
    '''
    def __init__(self, json_content):
        self.annotations = [Annotation(ann_json) for ann_json in json_content["annotations"] if "title" in ann_json]
        self.time = int(json_content["time"])
        self.lang = json_content["lang"]
        self.timestamp = parsers.datetime(json_content["timestamp"])

    def get_annotations(self, min_rho=None):
        '''
        Get the list of annotations found.
        :param min_rho: if set, only get entities with a rho-score (confidence) higher than this.
        '''
        return (a for a in self.annotations if min_rho is None or a.score > min_rho)

    def __str__(self):
        return "{}msec, {} annotations".format(self.time, len(self.annotations))


class Mention(object):
    '''
    A mention, i.e. a part of text that may mention an entity.
    '''
    def __init__(self, mention_json):
        self.begin = int(mention_json.get("start"))
        self.end = int(mention_json.get("end"))
        self.linkprob = float(mention_json.get("lp"))
        self.mention = mention_json.get("spot")

    def __str__(self):
        return u"{} [{},{}] lp={}".format(self.mention, self.begin, self.end, self.linkprob)


class MentionsResponse(object):
    '''
    A response to a call to the mention finding (/spot) service. It contains the list of mentions
    found.
    '''
    def __init__(self, json_content):
        self.mentions = [Mention(mention_json) for mention_json in json_content["spots"]]
        self.time = int(json_content["time"])
        self.lang = json_content["lang"]
        self.timestamp = parsers.datetime(json_content["timestamp"])

    def get_mentions(self, min_lp=None):
        '''
        Get the list of mentions found.
        :param min_lp: if set, only get mentions with a link probability higher than this.
        '''
        return (m for m in self.mentions if min_lp is None or m.linkprob > min_lp)

    def __str__(self):
        return "{}msec, {} mentions".format(self.time, len(self.mentions))


class Relatedness(object):
    '''
    A relatedness, i.e. a real value between 0 and 1 indicating how semantically close two entities
    are.
    '''
    def __init__(self, rel_json):
        self.title1, self.title2 = (wiki_title(t) for t in rel_json["couple"].split(" "))
        self.rel = float(rel_json["rel"]) if "rel" in rel_json else None

    def as_pair(self):
        '''
        Get this relatedness value as a pair (titles, rel), where rel is the relatedness value and
        titles is the pair of the two titles/Wikipedia IDs.
        '''
        return ((self.title1, self.title2), self.rel)

    def __str__(self):
        return u"{}, {} rel={}".format(self.title1, self.title2, self.rel)


class RelatednessResponse(object):
    '''
    A response to a call to the relatedness (/rel) service. It contains the list of relatedness for
    each pair.
    '''
    def __init__(self, json_contents):
        self.relatedness = [Relatedness(rel_json)
                            for json_content in json_contents
                            for rel_json in json_content["result"]]
        self.lang = json_contents[0]["lang"]
        self.timestamp = parsers.datetime(json_contents[0]["timestamp"])
        self.calls = len(json_contents)

    def __iter__(self):
        for rel in self.relatedness:
            yield rel.as_pair()

    def get_relatedness(self, i=0):
        '''
        Get the relatedness of a pairs of entities.
        :param i: the index of an entity pair. The order is the same as the request.
        '''
        return self.relatedness[i].rel

    def __str__(self):
        return "{} relatedness pairs, {} calls".format(len(self.relatedness), self.calls)


def normalize_title(title):
    '''
    Normalize a title to Wikipedia format. E.g. "barack Obama" becomes "Barack_Obama"
    :param title: a title to normalize.
    '''
    title = title.strip().replace(" ", "_")
    return title[0].upper() + title[1:]


def wiki_title(title):
    '''
    Given a normalized title, get the page title. E.g. "Barack_Obama" becomes "Barack Obama"
    :param title: a wikipedia title.
    '''
    return HTML_PARSER.unescape(title.strip(" _").replace("_", " "))


def title_to_uri(entity_title, lang=DEFAULT_LANG):
    '''
    Get the URI of the page describing a Wikipedia entity.
    :param entity_title: an entity title.
    :param lang: the Wikipedia language.
    '''
    return WIKIPEDIA_URI_BASE.format(lang, normalize_title(entity_title))


def annotate(text, gcube_token=None, lang=DEFAULT_LANG, api=DEFAULT_TAG_API,
             long_text=DEFAULT_LONG_TEXT):
    '''
    Annotate a text, linking it to Wikipedia entities.
    :param text: the text to annotate.
    :param gcube_token: the authentication token provided by the D4Science infrastructure.
    :param lang: the Wikipedia language.
    :param api: the API endpoint.
    :param long_text: long_text parameter (see TagMe documentation).
    '''
    payload = [("text", text.encode("utf-8")),
               ("long_text", long_text),
               ("lang", lang)]
    json_response = _issue_request(api, payload, gcube_token)
    return AnnotateResponse(json_response) if json_response else None


def mentions(text, gcube_token=None, lang=DEFAULT_LANG, api=DEFAULT_SPOT_API):
    '''
    Find possible mentions in a text, do not link them to any entity.
    :param text: the text where to find mentions.
    :param gcube_token: the authentication token provided by the D4Science infrastructure.
    :param lang: the Wikipedia language.
    :param api: the API endpoint.
    '''
    payload = [("text", text.encode("utf-8")),
               ("lang", lang)]
    json_response = _issue_request(api, payload, gcube_token)
    return MentionsResponse(json_response) if json_response else None


def relatedness_wid(wid_pairs, gcube_token=None, lang=DEFAULT_LANG, api=DEFAULT_REL_API):
    '''
    Get the semantic relatedness among pairs of entities. Entities are indicated by their
    Wikipedia ID (an integer).
    :param wid_pairs: either one pair or a list of pairs of Wikipedia IDs.
    :param gcube_token: the authentication token provided by the D4Science infrastructure.
    :param lang: the Wikipedia language.
    :param api: the API endpoint.
    '''
    return _relatedness("id", wid_pairs, gcube_token, lang, api)


def relatedness_title(tt_pairs, gcube_token=None, lang=DEFAULT_LANG, api=DEFAULT_REL_API):
    '''
    Get the semantic relatedness among pairs of entities. Entities are indicated by their
    Wikipedia ID (an integer).
    :param tt_pairs: either one pair or a list of pairs of entity titles.
    :param gcube_token: the authentication token provided by the D4Science infrastructure.
    :param lang: the Wikipedia language.
    :param api: the API endpoint.
    '''
    return _relatedness("tt", tt_pairs, gcube_token, lang, api)


def _relatedness(pairs_type, pairs, gcube_token, lang, api):
    if not isinstance(pairs[0], (list, tuple)):
        pairs = [pairs]

    if isinstance(pairs[0][0], (str, unicode)):
        pairs = [(normalize_title(p[0]), normalize_title(p[1])) for p in pairs]

    json_responses = []
    for chunk in range(0, len(pairs), MAX_RELATEDNESS_PAIRS_PER_REQUEST):
        payload = [("lang", lang)]
        payload += ((pairs_type, u"{} {}".format(p[0], p[1]))
                    for p in pairs[chunk:chunk + MAX_RELATEDNESS_PAIRS_PER_REQUEST])
        json_responses.append(_issue_request(api, payload, gcube_token))
    return RelatednessResponse(json_responses) if json_responses and json_responses[0] else None


def _issue_request(api, payload, gcube_token):
    if not gcube_token:
        gcube_token = GCUBE_TOKEN
    if not gcube_token:
        raise RuntimeError("You must define GCUBE_TOKEN before calling this function or pass the "
                           "gcube_token parameter.")

    payload.append(("gcube-token", gcube_token))
    logging.debug("Calling %s", api)
    res = requests.post(api, data=payload)
    if res.status_code != 200:
        logging.warning("Tagme returned status code %d message:\n%s", res.status_code, res.content)
        return None
    return json.loads(res.content)
