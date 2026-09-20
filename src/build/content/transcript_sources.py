import os
from collections import OrderedDict
from configparser import RawConfigParser
from glob import iglob


def load_transcript_source_texts(
        comic_folder: str,
        comic_info: RawConfigParser,
        page_name: str,
        content_root: str = "your_content",
) -> OrderedDict[str, str]:
    """Load unrendered transcript text without importing the Markdown renderer."""
    transcripts = OrderedDict()
    if comic_info.getboolean("Transcripts", "Load transcripts from comic folder", fallback=True):
        transcripts.update(
            load_transcript_sources_from_folder(
                os.path.join(content_root, comic_folder, "comics"),
                page_name,
            )
        )
    transcripts_dir = comic_info.get("Transcripts", "Transcripts folder", fallback="")
    if transcripts_dir:
        transcripts.update(load_transcript_sources_from_folder(transcripts_dir, page_name))
    return transcripts


def sort_transcript_languages(transcript_texts: OrderedDict[str, str], comic_info: RawConfigParser) -> OrderedDict:
    transcripts = OrderedDict(transcript_texts)
    default_language = comic_info.get("Transcripts", "Default language", fallback="English")
    if default_language in transcripts:
        transcripts.move_to_end(default_language, last=False)
    return transcripts


def load_transcript_sources_from_folder(transcripts_dir: str, page_name: str) -> OrderedDict[str, str]:
    extensions = ["*.txt", "*.md"]
    transcripts = OrderedDict()
    for ext in extensions:
        for transcript_path in sorted(iglob(os.path.join(transcripts_dir, page_name, ext))):
            if transcript_path.endswith("post.txt"):
                continue
            language = os.path.splitext(os.path.basename(transcript_path))[0]
            with open(transcript_path, "rb") as f:
                text = f.read()
                try:
                    text = text.decode("utf-8")
                except UnicodeDecodeError:
                    text = text.decode("latin-1")
                transcripts[language] = text
    return transcripts
