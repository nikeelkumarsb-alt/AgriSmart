"""Curated Indian market examples and transparent soil-report matching."""

CATALOG = [
    ("Coromandel Gromor SSP", "0-16-0", "P",
     "Supplies phosphate, sulfur and calcium without adding N or K.",
     "Lower phosphate concentration by weight than DAP. Confirm whether sulfur and calcium are suitable."),
    ("Coromandel Gromor MOP", "Potassium chloride", "K",
     "Supplies potash without adding N or P.",
     "Contains chloride. Check the crop's chloride sensitivity and local guidance."),
    ("IFFCO Neem Coated Urea", "46-0-0", "N",
     "Supplies nitrogen without adding phosphorus or potassium.",
     "Supplies no P or K. Nitrogen losses are possible if poorly timed."),
    ("IFFCO DAP", "18-46-0", "NP",
     "Supplies phosphorus and nitrogen in one product.",
     "Adds nitrogen even if only phosphorus is needed. Supplies no K."),
    ("IFFCO NPK 10-26-26", "10-26-26", "NPK",
     "Supplies all three nutrients in one grade.",
     "Fixed ratio may add nutrients the field already has enough of."),
    ("IFFCO NPK 12-32-16", "12-32-16", "NPK",
     "Supplies N, P and K with more phosphate than potash by label percentage.",
     "Fixed grade may not match the field's nutrient balance."),
    ("IFFCO NP(S) 20-20-0-13", "20-20-0 + 13 S", "NP",
     "Supplies nitrogen, phosphate and sulfur.",
     "Adds sulfur and supplies no potash. Verify that the grade fits the soil report."),
]


def market_matches(ratings):
    if not isinstance(ratings, dict) or not all(
        ratings.get(n) in ("low", "adequate", "high") for n in "npk"
    ):
        return [], "Enter all three Low, Adequate or High ratings from the soil lab report to rank products."
    gaps = {n.upper() for n in "npk" if ratings[n] == "low"}
    if not gaps:
        return [], "The report ratings show no low N, P or K. Check crop-specific guidance before adding fertilizer."
    high = {n.upper() for n in "npk" if ratings[n] == "high"}
    matched = []
    for name, grade, nutrients, pros, cons in CATALOG:
        nutrients = set(nutrients)
        covers = sorted(gaps & nutrients)
        extra = sorted(nutrients - gaps)
        if not covers or nutrients & high:
            continue
        matched.append({
            "name": name, "grade": grade, "covers": covers, "extra": extra,
            "pros": pros, "cons": cons,
        })
    matched.sort(key=lambda item: (-len(item["covers"]), len(item["extra"])))
    rank = 0
    previous = None
    for item in matched:
        fit = (len(item["covers"]), len(item["extra"]))
        if fit != previous:
            rank += 1
        item["rank"] = rank
        previous = fit
    message = (
        "Products rank by coverage of low-rated nutrients, then by fewer extras. "
        "Ties have equal fit under these rules. Rankings exclude grades supplying a high-rated nutrient."
        if matched else
        "No catalog grade fits these ratings. Ask a local KVK or dealer about suitable single-nutrient alternatives."
    )
    return matched, message
