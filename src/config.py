import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths — always absolute; src/ is one level below the project root
_ROOT = Path(__file__).parent.parent
DB_PATH = str(_ROOT / "fintrack.db")
RULES_PATH = str(_ROOT / "rules.json")

# Ollama LLM
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))

# KBC account identifiers — loaded from .env, never hardcoded
CHECKING_ACCOUNT = os.getenv("CHECKING_ACCOUNT", "")
OWN_NAME_VARIANTS = [
    v.strip()
    for v in os.getenv("OWN_NAME_VARIANTS", "").split(",")
    if v.strip()
]

# Full taxonomy: type → { category: [subcategories] }
# See docs/taxonomy.md for descriptions and labelling guidance.
TAXONOMY = {
    "Income": {
        "Income": [
            "Salary & Bonuses",
            "Refunds & Reimbursements",
            "Other Income",
        ],
    },
    "Expense": {
        "Housing & Utilities": [
            "Rent",
            "Electricity & Gas",
            "Water",
            "Internet & Phone",
            "Home Insurance",
            "Maintenance & Repairs",
        ],
        "Transportation": [
            "Public Transport",
            "Parking & Tolls",
            "Occasional Transport",
            "Bike Maintenance",
        ],
        "Groceries & Household": [
            "Supermarket",
            "Household Supplies",
            "Personal Care",
        ],
        "Food & Drinks": [
            "Restaurants",
            "Cafés & Bars",
            "Takeaway & Delivery",
        ],
        "Health & Wellbeing": [
            "Health Insurance",
            "Pharmacy",
            "Doctor & Specialists",
            "Gym & Sports",
        ],
        "Shopping": [
            "Clothing & Accessories",
            "Electronics & Gadgets",
            "Home & Furniture",
            "Arts & Culture",
            "Other Shopping",
        ],
        "Leisure & Entertainment": [
            "Service Subscriptions",
            "Hobbies & Activities",
            "Events",
            "Travel & Holidays",
        ],
    },
    "Transfer": {
        "Transfer": [
            "Savings Deposit",
            "Internal Transfer",
            "Investment Contribution",
        ],
    },
    "Financial Obligation": {
        "Financial Obligation": [
            "Loan Repayment",
            "Credit Card Payment",
            "Bank Fees & Charges",
            "Fines",
        ],
    },
}

# Derived: category → type (for quick reverse lookup)
CATEGORY_TO_TYPE: dict = {}
for _type, _cats in TAXONOMY.items():
    for _cat in _cats:
        CATEGORY_TO_TYPE[_cat] = _type
