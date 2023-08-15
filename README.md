# Identity Reconciliation

Identifying and keeping track of a customer's identity across multiple purchases by linking different orders made with different contact information to the same person.

One customer can have multiple **`Contact`** rows in the database against them. All of the rows are linked together with the oldest one being treated as "primary” and the rest as “secondary” . 

**`Contact`** rows are linked if they have either of **`email`** or **`phone`** as common.
