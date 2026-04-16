import os
from collections import OrderedDict
from configparser import RawConfigParser
from glob import iglob

from markdown2 import Markdown

MARKDOWN = Markdown(extras=["strike", "break-on-newline", "markdown-in-html"])


def get_transcripts(comic_folder: str, comic_info: RawConfigParser, page_name: str) -> OrderedDict:
    if not comic_info.getboolean("Transcripts", "Enable transcripts"):
        return OrderedDict()
    transcripts = OrderedDict()
    if comic_info.getboolean("Transcripts", "Load transcripts from comic folder", fallback=True):
        transcripts.update(load_transcripts_from_folder(f"your_content/{comic_folder}comics", page_name))
    transcripts_dir = comic_info.get("Transcripts", "Transcripts folder", fallback="")
    if transcripts_dir:
        transcripts.update(load_transcripts_from_folder(transcripts_dir, page_name))
    default_language = comic_info.get("Transcripts", "Default language", fallback="English")
    if default_language in transcripts:
        transcripts.move_to_end(default_language, last=False)
    return transcripts


def load_transcripts_from_folder(transcripts_dir: str, page_name: str):
    extensions = ["*.txt", "*.md"]
    transcripts = {}
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
                transcripts[language] = MARKDOWN.convert(text)
    return transcripts
