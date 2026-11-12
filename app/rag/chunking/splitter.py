

MAX_WORDS = 500
OVERLAP_WORD = 80

def split_text(text:str,max_words:int=MAX_WORDS,overlap:int=OVERLAP_WORD) -> list[str]:
    text = text.strip()

    if not text:
        return []

    words = text.split()
    if len(words) <= max_words:
        return [text]

    step = max_words - overlap
    chunks = []

    for start in range(0,len(words),step):
        chunks.append(" ".join(words[start:start + max_words]))
        if start + max_words >= len(words):
            break

    return chunks