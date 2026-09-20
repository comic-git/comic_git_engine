from collections import OrderedDict
from configparser import RawConfigParser

from markdown2 import Markdown

from build.content.transcript_sources import (
    load_transcript_source_texts,
    load_transcript_sources_from_folder,
    sort_transcript_languages,
)

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


def load_transcripts_from_folder(transcripts_dir: str, page_name: str):
    return render_transcript_sources(load_transcript_sources_from_folder(transcripts_dir, page_name))


def render_transcript_sources(transcript_texts: OrderedDict[str, str]) -> OrderedDict:
    transcripts = OrderedDict()
    for language, text in transcript_texts.items():
        transcripts[language] = MARKDOWN.convert(text)
    return transcripts
