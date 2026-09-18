import re
import unicodedata


class TextCleaner:
    """Sanitizes raw text while retaining ecological context."""

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""

        # Unicode normalization
        text = unicodedata.normalize("NFKD", text)

        # Rejoin hyphenated words split across lines
        text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)

        # Remove header/footer page markers (e.g., "Page 12 of 45", "12 | FAO Report")
        text = re.sub(r"(?i)page\s+\d+\s+(of\s+\d+)?", "", text)

        # Replace single line breaks with spaces, retain double line breaks as paragraph split markers
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
        text = re.sub(r"\n{2,}", "\n\n", text)

        # Collapse excess whitespace
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()