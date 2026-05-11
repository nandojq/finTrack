# FinTrack — Category Taxonomy

> Every transaction is assigned one **type**, one **category**, and one **subcategory**.

---

## Data model

The three fields form a hierarchy:

```
type → category → subcategory
```

**Expense** is the only type with multiple categories. The other three types (Income, Transfer, Financial Obligation) each have a single category that shares the type's name — this is intentional, keeping the data model uniform without adding a meaningless extra level.

| Type | Category | Subcategory (examples) |
|------|----------|----------------------|
| Income | Income | Salary & Bonuses |
| Expense | Food & Drinks | Restaurants |
| Expense | Housing & Utilities | Rent |
| Transfer | Transfer | Savings Deposit |
| Financial Obligation | Financial Obligation | Loan Repayment |

---

## Transaction Types

Four mutually exclusive types cover every possible transaction:

| Type | Description | Examples |
|------|-------------|---------|
| **Income** | Money flowing in from external sources | Salary, refund, freelance payment |
| **Expense** | Money consumed on goods or services | Groceries, rent, restaurant |
| **Transfer** | Money moving between your own accounts | Savings deposit, internal transfer |
| **Financial Obligation** | Debt repayment, fees, penalties | Loan repayment, bank charges, fines |

---

## Categories & Subcategories

### Income
- Salary & Bonuses
- Refunds & Reimbursements
- Other Income

### Expense

#### Housing & Utilities
- Rent
- Electricity & Gas
- Water
- Internet & Phone
- Home Insurance
- Maintenance & Repairs

#### Transportation
- Public Transport
- Parking & Tolls
- Occasional Transport *(taxi, scooters, rental bikes)*
- Bike Maintenance

#### Groceries & Household
- Supermarket
- Household Supplies
- Personal Care

#### Food & Drinks
- Restaurants
- Cafés & Bars
- Takeaway & Delivery

#### Health & Wellbeing
- Health Insurance
- Pharmacy
- Doctor & Specialists
- Gym & Sports

#### Shopping
- Clothing & Accessories
- Electronics & Gadgets
- Home & Furniture
- Arts & Culture
- Other Shopping

#### Leisure & Entertainment
- Service Subscriptions
- Hobbies & Activities
- Events
- Travel & Holidays

### Transfer
- Savings Deposit
- Internal Transfer
- Investment Contribution

### Financial Obligation
- Loan Repayment
- Credit Card Payment
- Bank Fees & Charges
- Fines

---

## Labelling Rules

- A transaction has exactly one type, one category, and one subcategory — never multiple.
- When in doubt between Expense and Financial Obligation: if it's recurring structured debt, use Financial Obligation; if it's a one-off spend, use Expense.
- Income from salary or employer always uses **Income / Income / Salary & Bonuses** regardless of how the bank describes it.

### Self-transfer and savings rules (auto-applied at ingest)

| Scenario | Amount | Label |
|----------|--------|-------|
| Savings account CSV — deposit | positive | Transfer / Transfer / Savings Deposit |
| Savings account CSV — withdrawal | negative | Transfer / Transfer / Internal Transfer |
| Checking account — outflow to own name | negative | Transfer / Transfer / Internal Transfer |
| Checking account — inflow from own name | positive | Transfer / Transfer / Internal Transfer |

Both legs of any money movement between your own accounts are always **Transfer**, never Income. This ensures self-transfers cancel out in spending reports.
