"""DkCash errors.

These error denote e.g. consistency problems (duplicate IDs, non-existent
references, ...)

"""

class ConsistencyError(RuntimeError):
    """Some consistency was found to be violated."""
    pass

class DatabaseError(ConsistencyError):
    """The database would be in an inconsistent state if the operation had been
performed as intended.
    """

    def __init__(self, datatype, column, desc=""):
        """

        Parameters
        ----------
        datatype : str
        The problematic datatype.

        column : str
        The problematic column.

        desc : str, optional
        """

        self.datatpe = datatype
        self.column = column
        self.desc = desc

    def __str__(self):
        return_str = "There is a problem with {} ({})".format(self.datatpe,
                                                              self.column)
        if self.desc:
            return_str += ":\n{}".format(self.desc)
        else:
            return_str += "."
        return return_str
