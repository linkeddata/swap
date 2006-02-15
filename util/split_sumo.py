"""
split_sumo -- split the SUMO ontology into modules
==================================================

Usage
-----

Invoke a la::

   python split_sumo.py SUMO_173.kif

where SUMO_173.kif_ was announced by `Adam Pease`_
in a message_ of 07 Oct 2005 to the `IEEE SUO WG`_.

.. _Adam Pease: http://home.earthlink.net/~adampease/professional/
.. _IEEE SUO WG: http://suo.ieee.org/
.. _message: http://grouper.ieee.org/groups/suo/email/msg13231.html

It produces::

  sumo_BASE_ONTOLOGY.kif      sumo_SET_CLASS_THEORY.kif
  sumo_GRAPH_THEORY.kif       sumo_STRUCTURAL_ONTOLOGY.kif
  sumo_MEREOTOPOLOGY.kif      sumo_TEMPORAL_CONCEPTS.kif
  sumo_NUMERIC_FUNCTIONS.kif  sumo_UNITS_OF_MEASURE.kif
  sumo_OBJECTS.kif            sumo_head.kif
  sumo_PROCESSES.kif          sumo_name_map
  sumo_QUALITIES.kif

where sumo_head.kif has the copyright and such
and sumo_name_map contains a path for each name::

  BASE_ONTOLOGY#AbstractionFn
  BASE_ONTOLOGY#BackFn
  BASE_ONTOLOGY#BinaryFunction
  ...
  GRAPH_THEORY#BeginNodeFn
  GRAPH_THEORY#CutSetFn
  GRAPH_THEORY#EndNodeFn
  ...

Future Work
-----------

The idea is to ground all the SUMO_ terms in URI space in manageable
chunks. First, each .kif file gets converted to XHTML with embedded
MathML (my preferred design for RIF syntax); then the MathML gets
converted to N3 rules and the N3 gets converted to RDF/XML. The result
would be browseable using normal web browers, useable with cwm, and
useable with RDF/XML tools.

The copyright seems to be held by IEEE, but with plenty
of license to produce derivative works.

Also, Adam Pease licenses it under the GPL on
ontologyportal.org.

See also: `owl bookmarks`_ especially in Feb 2005.

.. _SUMO_173.kif: http://suo.ieee.org/SUO/SUMO/SUMO_173.kif
.. _SUMO: http://www.ontologyportal.org/
.. _owl bookmarks: http://del.icio.us/connolly/owl

Colophon
--------

This document is written in ReStructuredText_. To
get HTML, try this::

  $ python -c 'import split_sumo; print split_sumo.__doc__'| rst2html


.. _ReStructuredText: http://docutils.sourceforge.net/docs/user/rst/quickstart.html


"""

__version__ = '$Id$'


def split(lines):
    head = None
    parts = {}
    part = []
    name = None

    where = {}
    names = []
    
    for l in lines:
        if l.strip() == ";; BEGIN FILE":
            if head is None: head = part
            else:
                parts[name] = part
                name = None
            part = []
        elif (head is not None) and (name is None) and l.startswith(";; "):
            name = l[2:-4].strip()
            name = name.replace(" ", "_").replace("/", "_")

        elif l.startswith("(instance ") or l.startswith("(subclass ") \
                 or l.startswith("(subrelation ") :
            n = l.split()[1]
            if not n.startswith("?"):
                if not where.has_key(n): where[n] = name

        part.append(l)

    out(file("sumo_head.kif", "w"), head)
    for n in parts.keys():
        out(file("sumo_%s.kif" % n, "w"), parts[n])

    paths = ["%s#%s" % (where[n], n) for n in where.keys()]
    paths.sort()
    out(file("sumo_name_map", "w"), ["%s\n" % p for p in paths])

def out(f, lines):
    for l in lines:
        f.write(l)

if __name__ == '__main__':
    import sys
    sumofn = sys.argv[1]
    split(file(sumofn))
