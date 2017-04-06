from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import tagme

SAMPLE_TEXT = "Obama visited uk"

def main():
    # Annotate a text.
    print("Annotating text: ", SAMPLE_TEXT)
    resp = tagme.annotate(SAMPLE_TEXT)
    print(resp)
    for ann in resp.annotations:
        print(ann)

    # Find mentions in a text.
    print("Finding mentions in text: ", SAMPLE_TEXT)
    resp = tagme.mentions(SAMPLE_TEXT)
    print(resp)
    for mention in resp.mentions:
        print(mention)

    # Find relatedness between one pair of entities, by title.
    resp = tagme.relatedness_title(["Barack_Obama", "Italy"])
    print(resp)
    for rel in resp.relatedness:
        print(rel)

    # Find relatedness between pairs of entities, by title.
    resp = tagme.relatedness_title([("Barack_Obama", "Italy"),
                                ("Italy", "Germany"),
                                ("Italy", "BAD ENTITY NAME")])
    print(resp)
    for rel in resp.relatedness:
        print(rel)

    # Access the relatedness response as a dictionary.
    resp_dict = dict(resp)
    print("Relatedness between Italy and Germany: ", resp_dict[("Italy", "Germany")])

    # Find relatedness between one pair of entities, by wikipedia id
    resp = tagme.relatedness_wid((31717, 534366))
    print(resp)
    for rel in resp.relatedness:
        print(rel)

    # Find relatedness between pairs of entities, by wikipedia id
    resp = tagme.relatedness_wid([(534366, 534366 + a) for a in range (1010)])
    print(resp)
    for rel in resp.relatedness:
        print(rel)

if __name__ == "__main__":
    tagme.GCUBE_TOKEN = sys.argv[1]
    assert tagme.normalize_title(" barack Obama  ") == "Barack_Obama"
    assert tagme.title_to_uri(" barack Obama  ") == "https://en.wikipedia.org/wiki/Barack_Obama"
    assert tagme.wiki_title("Barack_Obama") == ("Barack Obama")
    main()
