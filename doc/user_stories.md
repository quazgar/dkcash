# User stories dkhandle #

Some (few) of these possibly could also be done directly in dkdata?

## Management ##

- Add Creditor > dkdata
- Create contract > dkdata? Or for consistency in dkhandle?
- Pay money for contract
- Calculate interest (for specified date range) and book the interest into
  account.
  - If interests need to be calculated for another, overlapping, range, the old
    interests have to be removed manually from the GnuCash file.
- Modify contract conditions
  - This will calculate and book the interest until the change date.
  - Technically this ends the previous contract and starts a new one?

## Reporting ##

- Find creditors
  - All
  - with name matching an expression
  - wants to get emails
- Find contracts
  - to a certain user
  - which end before a certain date
- Calculate interest for a contract for a year
- Create report / account statement
  - For all contracts of a creditor
- Generate spreadsheet
  - all creditors, all active contracts, all transactions, including interests
- Calculate the average interest for all active contracts


# User stories GUI #
