# GnuCash accounts
Requirements for the GnuCash account structure are specified here.

## Base accounts
The GnuCash account structure must contain at least the following:
| name               | type      | description                     |
|--------------------+-----------+---------------------------------|
| Direktkredite      | Liability | parent to the contracts         |
| DK-Ausgleich       | Asset     | source and sink for the credits |
| Direktkreditzinsen | Expense   | interests go here               |

If these accounts do not exist yet, they will be created below the specified
accounts.

## Contract accounts
There will be exactly one liability account for each contract, where all the
transaction go to or come from.  This account will be a child to the
`Direktkredite` account, its account code will be the concatenation of the
parent account code and the contract ID.

If the creditor chose to collect the interests with neither immediate pay-out
nor re-investment, the contract account has another sub-account (code: "1"
appended) for those collected interests.

An example:

| Account name  | Account code |  Parent |
|---------------+--------------+---------|
| Direktkredite |         1234 |         |
| DK 01         |      1234001 |    1234 |
| ...           |              |         |
| DK 06         |      1234006 |    1234 |
| DK 06 Zinsen  |     12340061 | 1234006 |


## Booking

| Action              | To            | From               |
|---------------------+---------------+--------------------|
| Increasing a loan   | Direktkredite | DK-Ausgleich       |
| Booking interest    | Direktkredite | Direktkreditzinsen |
| Paying out interest | DK-Ausgleich  | Direktkredite      |
| Paying back a loan  | DK-Ausgleich  | Direktkredite      |

# The database tables
For storing loan specific information, a few new tables are necessary, and
created if they do not exist yet.  These additional tables are:

## creditors

| name       | type     | required | default | comment                 |
|------------+----------+----------+---------+-------------------------|
| id         | integer  | True     |         | auto-generated          |
|------------+----------+----------+---------+-------------------------|
| name       | str(100) | True     |         |                         |
| address1   | str(100) | True     |         |                         |
| address2   | str(100) | False    |         |                         |
| address3   | str(100) | False    |         |                         |
| address4   | str(100) | False    |         |                         |
| phone      | str(100) | False    |         |                         |
| email      | str(100) | False    |         | must be a valid email   |
| newsletter | bool     | True     | False   | may newsletter be sent? |

## contracts
| name                | type            | required | default | comment           |
|---------------------|-----------------|----------|---------|-------------------|
| id                  | str(10)         | True     |         | same as on paper  |
| `minor_id`          | str(3)          | False    | NULL    | sub-version [1]   |
|---------------------|-----------------|----------|---------|-------------------|
| creditor            | cred.id         | True     |         | foreign key       |
| account             | accounts.guid   | True     |         | foreign key       |
| date                | str(YYYY-MM-DD) | True     |         | last signature    |
| amount              | float           | True     |         |                   |
| interest            | float           | True     |         | as percent        |
| `interest_payment`  | str [2]         | True     |         |                   |
| version             | str             | False    |         |                   |
|---------------------|-----------------|----------|---------|-------------------|
| period_type         | str [3]         | True     |         | see explanation   |
| period_notice       | str(YYYY-MM-DD) | [4]      |         | cancel notice     |
| period_end          | str(YYYY-MM-DD) | [4]      |         | fixed end         |
|---------------------|-----------------|----------|---------|-------------------|
| `cancellation_date` | str(YYYY-MM-DD) | False    | NULL    | end of contract   |
| active              | bool            | True     | True    | False if canceled |

1. The final ID will be extended like `${ID}.${MINOR}`, where minor is
   1,2,3,..., to indicate new sub-versions of the same contract.
2. One of: payout, cumulative, reinvest
3. One of: fixed_duration, fixed_period_notice, initial_plus_n
4. The required columns in this section depend on the period type, the period
   type also defines the meaning of these columns.

### Period type of contracts
- `fixed_duration` :: There is a fixed duration of the contract. `period_notice`
  is `null` in this case.  `period_end` is the date when the contract will end.
- `fixed_period_notice` :: The contract runs forever, but can be canceled with
  notice as given in the `period_notice` field.  `period_end` is `null` in this
  case.
- `initial_plus_n` :: The contract first runs without possibility to cancel
  until the date given in `period_end`, then it cn be canceled with
  `period_notice`, just as for *fixed_period_notice*.

