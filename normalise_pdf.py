import re
from typing import Callable, Dict, Iterable, List


Matcher = Callable[[str], bool]


def _clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).strip())


def _match_percent(value: str) -> bool:
    return bool(re.fullmatch(r"\d+\s*%(?:\s+\S+)?", value))


def _match_fixation_losses(value: str) -> bool:
    return bool(re.fullmatch(r"\d+\s*/\s*\d+(?:\s+\S+)?", value))


def _match_duration(value: str) -> bool:
    return bool(re.fullmatch(r"\d{1,2}:\d{2}", value))


def _match_fovea(value: str) -> bool:
    return bool(re.fullmatch(r"off|-?\d+(?:\.\d+)?\s*(?:db)?", value, re.IGNORECASE))


def _match_stimulus(value: str) -> bool:
    return bool(re.search(r"\b(?:i{1,3}|iv|v)\b\s*,\s*\w+", value, re.IGNORECASE))


def _match_background(value: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:\.\d+)?\s*asb", value, re.IGNORECASE))


def _match_strategy(value: str) -> bool:
    return "sita" in value.lower()


def _match_pupil_diameter(value: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:\.\d+)?\s*mm\s*\*?", value, re.IGNORECASE))


def _match_visual_acuity(value: str) -> bool:
    return bool(
        re.fullmatch(
            r"(?:\d+/\d+|cf|hm|lp|nlp)(?:\s*(?:\+|-)?\d+)?(?:\s+\S+)?",
            value,
            re.IGNORECASE,
        )
    )


def _match_rx(value: str) -> bool:
    return bool(
        re.search(
            r"(?:^|\s)[+-]?\d+(?:\.\d{1,2})?\s*(?:DS|DC|D|CYL|SPH)\b",
            value,
            re.IGNORECASE,
        )
    )


def _match_date(value: str) -> bool:
    month = r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
    return bool(
        re.fullmatch(
            rf"(?:{month})\.?\s+\d{{1,2}},?\s+\d{{4}}|\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}}",
            value,
            re.IGNORECASE,
        )
    )


def _match_clock_time(value: str) -> bool:
    return bool(re.fullmatch(r"\d{1,2}:\d{2}\s*(?:AM|PM)?", value, re.IGNORECASE))


def _match_age(value: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}", value))


_HEADER_MATCHERS: Dict[str, Matcher] = {
    "Fixation Losses": _match_fixation_losses,
    "False POS Errors": _match_percent,
    "False Positive Errors": _match_percent,
    "False NEG Errors": _match_percent,
    "False Negative Errors": _match_percent,
    "Test Duration": _match_duration,
    "Exam Duration": _match_duration,
    "Fovea": _match_fovea,
    "Stimulus": _match_stimulus,
    "Background": _match_background,
    "Strategy": _match_strategy,
    "Pupil Diameter": _match_pupil_diameter,
    "Visual Acuity": _match_visual_acuity,
    "Rx": _match_rx,
    "Date": _match_date,
    "Time": _match_clock_time,
    "Age": _match_age,
}


def _score(label: str, value: str) -> int:
    matcher = _HEADER_MATCHERS.get(label)
    if matcher is None:
        return 1 if value else 0
    return 6 if matcher(value) else -8


def normalise_header_values(values: Iterable[object], labels: List[str]) -> Dict[str, str]:
    """
    Map positional PDF header values onto template labels without shifting later
    fields when optional values are missing.

    The PDF text extractor often returns only values, not their labels. Instead
    of blindly zipping by index, this uses a small ordered alignment: values must
    stay in reading order, labels may be left blank, and recognizable fields such
    as Rx/date/time/age are allowed to anchor the tail of the row.
    """
    cleaned_values = [_clean(value) for value in values if _clean(value)]
    label_count = len(labels)
    value_count = len(cleaned_values)

    # dp[i][j] is the best score after considering labels[:i] and values[:j].
    gap_penalty = -2
    dp = [[-10**9] * (value_count + 1) for _ in range(label_count + 1)]
    back: list[list[tuple[int, int, bool] | None]] = [
        [None] * (value_count + 1) for _ in range(label_count + 1)
    ]
    dp[0][0] = 0

    for i in range(label_count + 1):
        for j in range(value_count + 1):
            current = dp[i][j]
            if current <= -10**8:
                continue

            if i < label_count:
                candidate = current + gap_penalty
                if candidate > dp[i + 1][j]:
                    dp[i + 1][j] = candidate
                    back[i + 1][j] = (i, j, False)

            if i < label_count and j < value_count:
                candidate = current + _score(labels[i], cleaned_values[j])
                if candidate > dp[i + 1][j + 1]:
                    dp[i + 1][j + 1] = candidate
                    back[i + 1][j + 1] = (i, j, True)

            # Ignore unexpected extra tokens without disturbing the label order.
            if j < value_count:
                candidate = current - 5
                if candidate > dp[i][j + 1]:
                    dp[i][j + 1] = candidate
                    back[i][j + 1] = (i, j, False)

    mapped = {label: "" for label in labels}
    i, j = label_count, value_count
    while i > 0 or j > 0:
        previous = back[i][j]
        if previous is None:
            break
        prev_i, prev_j, used_value = previous
        if used_value and prev_i < label_count and prev_j < value_count:
            mapped[labels[prev_i]] = cleaned_values[prev_j]
        i, j = prev_i, prev_j

    return mapped


def normalise_pdf_header(values: Iterable[object], labels: List[str], section_name: str = "header") -> Dict[str, str]:
    return {
        f"{section_name}_{label}": value
        for label, value in normalise_header_values(values, labels).items()
    }


# American spelling aliases for callers that prefer it.
normalize_header_values = normalise_header_values
normalize_pdf_header = normalise_pdf_header
