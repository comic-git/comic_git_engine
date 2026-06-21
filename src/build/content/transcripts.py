import os
from collections import OrderedDict
from configparser import RawConfigParser
from glob import iglob

from markdown2 import Markdown

MARKDOWN = Markdown(extras=["strike", "break-on-newline", "markdown-in-html"])


def get_transcripts(
        comic_folder: str,
        comic_info: RawConfigParser,
        page_name: str,
        page_info: dict | None = None,
) -> OrderedDict:
    if not comic_info.getboolean("Transcripts", "Enable transcripts"):
        return OrderedDict()
    if page_info and page_info.get("_toml_managed"):
        transcript_texts = sort_transcript_languages(
            OrderedDict(page_info.get("_inline_transcripts", {}).items()),
            comic_info,
        )
        return render_transcript_sources(transcript_texts)
    transcript_texts = sort_transcript_languages(load_transcript_source_texts(comic_folder, comic_info, page_name), comic_info)
    return render_transcript_sources(transcript_texts)


def load_transcript_source_texts(comic_folder: str, comic_info: RawConfigParser, page_name: str) -> OrderedDict[str, str]:
    transcripts = OrderedDict()
    if comic_info.getboolean("Transcripts", "Load transcripts from comic folder", fallback=True):
        transcripts.update(load_transcript_sources_from_folder(f"your_content/{comic_folder}comics", page_name))
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


def load_transcripts_from_folder(transcripts_dir: str, page_name: str):
    return render_transcript_sources(load_transcript_sources_from_folder(transcripts_dir, page_name))


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


def render_transcript_sources(transcript_texts: OrderedDict[str, str]) -> OrderedDict:
    transcripts = OrderedDict()
    for language, text in transcript_texts.items():
        transcripts[language] = MARKDOWN.convert(text)
    return transcripts
