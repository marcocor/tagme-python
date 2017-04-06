============
tagme-python
============

Official TagMe API wrapper for Python.

Installation and setup
----------------------

This library is hosted by PyPI. You can install it with:

``pip install tagme``

To access the TagMe API you have to register (for free!) at the D4Science platform and obtain an authorization *token*.

- Register to the `D4Science TagMe VRE <https://services.d4science.org/group/tagme/>`_.
- After login, click the *show* button on the left panel to get your authorization token.

Using TagMe
-----------

Before making any call to the web service, you will need to set the module-wise ``GCUBE_TOKEN`` variable. You can do so with:

.. code-block:: python

 import tagme
 # Set the authorization token for subsequent calls.
 tagme.GCUBE_TOKEN = "<Your token goes here>"

As an alternative to setting the module-wise variable, you can pass the token at each call with the optional ``gcube_token`` parameter. 

Annotation
----------
The annotation service lets you find entities mentioned in a text and link them to Wikipedia.
This is the so-called Sa2KB problem. You can annotate a text with:

.. code-block:: python

 lunch_annotations = tagme.annotate("My favourite meal is Mexican burritos.")
 
 # Print annotations with a score higher than 0.1
 for ann in lunch_annotations.get_annotations(0.1):
     print ann

The ``annotate`` method accepts parameters to set the language (parameter ``lang``, that defaults to ``en``) and other stuff.
See the code for more information.
Annotations are associated a rho-score indicating the likelihood of an annotation being correct. In the example, we discard
annotations with a score lower than 0.1.

Mention finding
---------------

The mention finding service lets you find what parts of text may be a mention of an entity, without linking them to any entity.

.. code-block:: python

 tomatoes_mentions = tagme.mentions("I definitely like ice cream better than tomatoes.")

 for mention in tomatoes_mentions.mentions:
     print mention

The ``mentions`` parameter accepts an optional language parameter ``lang`` that defaults to ``en``.

Entity relatedness
------------------

Tagme also gives you the semantic relatedness among pairs of entities. Entities can be either specified as Wikipedia titles
(like ``Barack Obama``) or as Wikipedia IDs (like ``534366``, the ID of the entity Barack Obama).
The two methods for obtaining the relatedness among entities are ``relatedness_title`` (that accepts titles) and
``relatedness_wid`` (that accepts Wikipedia IDs). Both methods accept either a single pair of entities or a list of pairs.
You can submit a list of pairs of any size, but the TagMe web service will be issued one query every 100 pairs.
If one entity does not exist, the result will be ``None``.

.. code-block:: python

 # Get relatedness between a pair of entities specified by title.
 rels = tagme.relatedness_title(("Barack Obama", "Italy"))
 print "Obama and italy have a semantic relation of", rels.relatedness[0].rel
 
 # Get relatedness between a pair of entities specified by Wikipedia ID.
 rels = tagme.relatedness_wid((31717, 534366))
 print "IDs 31717 and 534366 have a semantic relation of ", rels.relatedness[0].rel
 
 # Get relatedness between three pairs of entities specified by title.
 # The last entity does not exist, hence the value for that pair will be None.
 rels = tagme.relatedness_title([("Barack_Obama", "Italy"),
                                 ("Italy", "Germany"),
                                 ("Italy", "BAD ENTITY NAME")])
 for rel in rels.relatedness:
     print rel

 # You can also build a dictionary
 rels_dict = dict(rels)
 print rels_dict[("Barack Obama", "Italy")]
 
Changelog
---------

See the [Changelog](CHANGELOG.rst)
