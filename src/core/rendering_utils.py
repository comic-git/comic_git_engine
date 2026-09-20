import logging
import os
from configparser import RawConfigParser
from time import strftime

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound
from markdown2 import Markdown

from core import stdlib_utils

logger = logging.getLogger(__name__)

jinja_environment: Environment | None = None
markdown_parser: Markdown | None = None


def build_jinja_environment(comic_info: RawConfigParser, template_folders: list[str]) -> None:
    global jinja_environment
    try:
        jinja_environment = Environment(
            loader=FileSystemLoader(template_folders),
            undefined=StrictUndefined,
        )
    except Exception as e:
        raise ValueError(
            f"Error initializing Jinja2 environment with template folders: {template_folders}\n"
            f"Verify all template folders exist and are readable. {e}"
        ) from e


def build_markdown_parser(comic_info: RawConfigParser) -> None:
    global markdown_parser
    extras = comic_info.get("Comic Settings", "Markdown extras", fallback="")
    markdown_parser = Markdown(extras=["metadata"] + stdlib_utils.str_to_list(extras))


def build_md_page(template_name: str, data_dict: dict | None = None) -> str | None:
    """Render an optional themed Markdown page, or return ``None`` when it does not exist."""
    if markdown_parser is None or jinja_environment is None:
        raise RuntimeError("Rendering helpers were not initialized before build_md_page was called.")
    theme = data_dict["theme"]
    md_path = f"your_content/themes/{theme}/pages/{template_name}.md"
    if not os.path.isfile(md_path):
        return None
    try:
        with open(md_path, "rb") as f:
            converted_md = markdown_parser.convert(f.read())
    except IOError as e:
        raise ValueError(
            f"Error reading markdown file {md_path}\n"
            f"Verify the file exists and is readable."
        ) from e
    except Exception as e:
        raise ValueError(
            f"Error converting markdown file {md_path}: {e}\n"
            f"Verify the file is valid markdown and uses UTF-8 encoding."
        ) from e
    metadata = converted_md.metadata
    new_data_dict = data_dict.copy()
    new_data_dict["text"] = converted_md
    template = jinja_environment.get_template(metadata.get("template", "md_page.tpl"))
    return template.render(**new_data_dict)


def write_to_template(template_name: str, html_path: str, data_dict: dict | None = None) -> None:
    """Render a themed template and write it to the configured output directory."""
    if jinja_environment is None:
        raise RuntimeError("Jinja environment was not initialized before write_to_template was called.")
    if data_dict is None:
        data_dict = {}
    data_dict["template_name"] = template_name
    file_contents = build_md_page(template_name, data_dict)
    if file_contents is None:
        for ext in (".html", ".tpl"):
            try:
                file_contents = jinja_environment.get_template(template_name + ext).render(**data_dict)
                break
            except TemplateNotFound:
                pass
        else:
            raise TemplateNotFound(
                f"Template matching '{template_name}' not found\n"
                f"Verify the template file exists in your theme's templates folder or the default templates folder, "
                f"and that the filename matches (case-sensitive)."
            )

    output_dir = stdlib_utils.get_output_dir()
    if output_dir:
        html_path = os.path.join(output_dir, html_path)
    dir_name = os.path.dirname(html_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    logger.info("[%s] Writing %s", strftime("%Y-%m-%d %H:%M:%S"), html_path)
    try:
        with open(html_path, "wb") as f:
            f.write(bytes(file_contents, "utf-8"))
    except (OSError, IOError) as e:
        raise ValueError(
            f"Could not write to {html_path}\n"
            f"Verify the directory exists and you have write permissions."
        ) from e
