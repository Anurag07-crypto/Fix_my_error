import re

# Each rule: (error_type, message_regex or None, category, human label)
# First match wins, so put the specific rules before the general ones.
RULES = [
    # TypeError (specific cases first)
    ("TypeError", r"'NoneType' object", "none_misuse", "Using None like a real value"),
    ("TypeError", r"unsupported operand type|can only concatenate|must be str, not|must be int, not",
     "type_mismatch", "Mixing incompatible types in an operation"),
    ("TypeError", r"object is not callable", "not_callable", "Calling something that isn't a function"),
    ("TypeError", r"not subscriptable", "not_subscriptable", "Indexing something that doesn't support it"),
    ("TypeError", r"not iterable", "not_iterable", "Looping over something that isn't iterable"),
    ("TypeError", r"positional argument|required argument|unexpected keyword argument|takes \d+ arguments?",
     "wrong_arguments", "Wrong number or names of function arguments"),
    ("TypeError", None, "type_error", "Wrong type used"),

    # AttributeError
    ("AttributeError", r"'NoneType' object", "none_misuse", "Using None like a real value"),
    ("AttributeError", None, "missing_attribute", "Accessing an attribute that doesn't exist"),

    # Lookup errors
    ("KeyError", None, "missing_key", "Missing dictionary key"),
    ("IndexError", None, "index_out_of_range", "Index outside the list/string range"),

    # Names and imports
    ("NameError", None, "undefined_name", "Using a name that was never defined"),
    ("UnboundLocalError", None, "undefined_name", "Using a variable before assigning it"),
    ("ModuleNotFoundError", None, "import_error", "Module not installed or misspelled"),
    ("ImportError", None, "import_error", "Import failed"),

    # Math / values
    ("ZeroDivisionError", None, "division_by_zero", "Dividing by zero"),
    ("ValueError", r"invalid literal|could not convert", "bad_conversion", "Converting text to a number failed"),
    ("ValueError", None, "value_error", "Right type, wrong value"),

    # Files
    ("FileNotFoundError", None, "file_not_found", "File or path doesn't exist"),

    # Syntax
    ("IndentationError", None, "syntax", "Indentation problem"),
    ("TabError", None, "syntax", "Mixed tabs and spaces"),
    ("SyntaxError", None, "syntax", "Code isn't valid Python syntax"),
]

# Pull one useful detail out of the message so the LLM gets facts, not guesses
DETAIL_PATTERNS = {
    "undefined_name": (r"name '(.+?)' is not defined", "name"),
    "missing_key": (r"^(.+)$", "key"),
    "missing_attribute": (r"has no attribute '(.+?)'", "attribute"),
    "import_error": (r"No module named '(.+?)'", "module"),
    "file_not_found": (r"'(.+?)'", "path"),
}


def classify(parsed: dict) -> dict:
    """Map a parsed traceback to a category, a label, and extracted details."""
    etype = parsed.get("error_type")
    msg = parsed.get("message") or ""

    if not etype:
        return {"category": "unknown", "label": "Couldn't read the error", "details": {}}

    for rule_type, pattern, category, label in RULES:
        if rule_type != etype:
            continue
        if pattern is None or re.search(pattern, msg):
            return {"category": category, "label": label, "details": _details(category, msg)}

    return {"category": "other", "label": f"{etype}", "details": {}}


def _details(category: str, msg: str) -> dict:
    spec = DETAIL_PATTERNS.get(category)
    if not spec:
        return {}
    pattern, key = spec
    m = re.search(pattern, msg)
    return {key: m.group(1)} if m else {}