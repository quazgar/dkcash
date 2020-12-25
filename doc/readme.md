# Overview
DKCash is a loan managing program, developed primarily for community living
projects in the [[https://syndikat.org][Mietshäuser Syndikat]].

It stores its data in a GnuCash database file and uses the high-level Python
library [[https://pypi.org/project/piecash/][piecash]] and SQLAlchemy for
accessing the database.  It aims at always keeping the database consistent for
use by GnuCash.  It has a user-friendly GUI written in PyQt.

# Current State
Not much implementation yet.

# How To Run
Start piecash by writing `./dkcash` in the `dkcash` directory, or by
double-clicking on the file.

# Technical Information
Information about technical issues follows here.

## The Big Picture
dkcash is split into several components which work together to ease the loan
management.

### dkgui
This is a GUI frontend, written with PyQt.  It may also feature a headless mode
for command line functionality.

### dkdata
This module handles the database.  It connects to a GnuCash database or creates
a new one. It handles and writes "dumb" transactions such as creations,
deletions, increases or decreases of loans or interest payments.  To the
outside, it presents an object-oriented model of the loans (in the `common`
module).

It needs specific information where in the database exactly the loans are to be
stored.  It can make some deductions from the database content though.

### common

Utility classes for high-level handling of creditors, contracts etc.

### dkhandle

This module does more high-level handling of loans, such as interest
calculations, calculations of important dates, changing loan conditions etc.

### Graphical Overview
```ditaa
+----------------------+
|        dkgui         |
+----------+-----------+
| dkhandle |   common  |
+----------+-----------+
|                      |
|        dkdata        |
|                      |
+---------+------------+
| piecash | SQLAlchemy |
+---------+------------+
|  GnuCash data base   |
+----------------------+
```

## Particular modules
Detailed documentation can be found in separate locations:
- [`common` library, home of the `Creditor` and `Contract` classes](common.md)
- [dkhandle](dkhandle.md)
- [dkdata.md](dkdata.md)
- [dkgui](dkgui.md)
- [database schema](db_schema.md)

