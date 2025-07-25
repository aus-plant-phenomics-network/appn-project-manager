import re


def slugify(text: str) -> str:
    """Generate a slug from a text

    Used for generating project name and url slug

    https://developer.mozilla.org/en-US/docs/Glossary/Slug

    Example:
    - The Plant Accelerator -> the-plant-accelerator

    - APPN -> appn

    Args:
        text (str): source text

    Returns:
        str: slug
    """
    text = text.lower()
    # Replace non slug characters
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    # Replace spaces with hyphens
    text = re.sub(r"[\s\-]+", "-", text)
    return text.strip("-")
