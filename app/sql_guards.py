import re

# DDL/DML/admin keywords yang harus diblok di adhoc query
_FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
    "MERGE", "TRUNCATE", "GRANT", "REVOKE", "CALL", "EXECUTE",
]

_FORBIDDEN_PATTERN = re.compile(
    r"\b(" + "|".join(_FORBIDDEN_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# Match LIMIT N (case insensitive, allow trailing whitespace/semicolon)
_LIMIT_PATTERN = re.compile(r"\bLIMIT\s+\d+\b", re.IGNORECASE)


def strip_sql_comments(sql: str) -> str:
    """Buang -- single line dan /* */ block comments supaya guard tidak ketipu."""
    sql = re.sub(r"--[^\n]*", "", sql)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql.strip()


def ensure_select_only(sql: str) -> None:
    """
    Pastikan SQL hanya SELECT (atau WITH ... SELECT).
    Raises ValueError kalau ada keyword berbahaya.
    """
    cleaned = strip_sql_comments(sql)

    if not cleaned:
        raise ValueError("SQL kosong.")

    # Block multiple statements
    if ";" in cleaned.rstrip(";"):
        raise ValueError("Multiple statements tidak diizinkan.")

    # Cek forbidden keywords
    match = _FORBIDDEN_PATTERN.search(cleaned)
    if match:
        raise ValueError(
            f"Keyword '{match.group(1).upper()}' tidak diizinkan. "
            f"Hanya SELECT yang boleh."
        )

    # First meaningful keyword harus SELECT atau WITH
    first_word = cleaned.lstrip("(").split(None, 1)[0].upper()
    if first_word not in ("SELECT", "WITH"):
        raise ValueError(
            f"Query harus dimulai dengan SELECT atau WITH, ditemukan: {first_word}"
        )


def ensure_limit(sql: str, default_limit: int = 1000) -> str:
    """
    Pastikan SQL punya LIMIT. Kalau belum ada, inject LIMIT default.
    Kalau sudah ada LIMIT > default, turunkan ke default.
    """
    cleaned = sql.rstrip().rstrip(";").rstrip()

    match = _LIMIT_PATTERN.search(cleaned)
    if match:
        # Ada LIMIT, cek angkanya
        existing_limit = int(re.search(r"\d+", match.group(0)).group(0))
        if existing_limit > default_limit:
            cleaned = _LIMIT_PATTERN.sub(f"LIMIT {default_limit}", cleaned)
        return cleaned

    # Tidak ada LIMIT — inject
    return f"{cleaned}\nLIMIT {default_limit}"


def validate_adhoc_sql(sql: str, default_limit: int = 1000) -> str:
    """
    One-shot validator untuk adhoc query.
    Returns SQL yang sudah disanitize + di-limit.
    Raises ValueError kalau tidak aman.
    """
    ensure_select_only(sql)
    return ensure_limit(sql, default_limit)