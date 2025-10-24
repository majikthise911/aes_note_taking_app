"""
Predefined project categories for note classification.
Based on: Crescent / Felix PV — Living Project Status Log
"""

CATEGORIES = [
    "General",
    "Development/Reliance Material",
    "GIS updates",
    "Interconnection",
    "Land",
    "Facility location",
    "Environmental/Biological Cultural",
    "Schedule",
    "Breakers",
    "MPT",
    "Modules",
    "Owner's Engineer",
    "30% Package",
    "60% Package",
    "Geotech investigation",
    "Structural",
    "Civil",
    "Electrical",
    "Substation",
    "Construction Milestones",
    "Pricing",
    "Risk Register",
    "Permanent Utilities",
    "Contracting",
    "LNTP",
    "BOP-EPC",
    "PWC",
    "Action Items",
]

# Category validation
def validate_category(category: str) -> bool:
    """
    Validate if a category is in the predefined list.

    Args:
        category: Category string to validate

    Returns:
        True if valid, False otherwise
    """
    return category in CATEGORIES


def get_categories_list() -> list:
    """
    Get list of all valid categories.

    Returns:
        List of category strings
    """
    return CATEGORIES.copy()
