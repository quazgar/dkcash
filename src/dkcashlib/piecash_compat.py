"""Compatibility tools for piecash.

E.g. classes need some special methods.

Code copied partly from piecash.
"""

from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import sessionmaker, object_session


@as_declarative()
class DeclarativeBase:
    @property
    def book(self):
        """Return the gnc book holding the object
        """
        s = object_session(self)
        return s and s.book

    def object_to_validate(self, change):
        """yield the objects to validate when the object is modified (change="new"
        "deleted" or "dirty").  For instance, if the object is a Split, if it
        changes, we want to revalidate not the split but its transaction and its
        lot (if any). split.object_to_validate should yeild both
        split.transaction and split.lot

        """
        return
        yield

    def validate(self):
        """Always valid."""
        pass

    def get_all_changes(self):
        try:
            return self.book.session._all_changes[id(self)]
        except KeyError:
            return {"STATE_CHANGES": ["unchanged"],
                    "OBJECT": self}

    def __str__(self):
        return self.__unirepr__()

    def __repr__(self):
        return self.__unirepr__()

    def __unicode__(self):
        return self.__unirepr__()

    def __unirepr__(self):
        return "decl_class<{}>".format(self.__hash__())
