import os
import re
from configparser import RawConfigParser
from time import strftime
from typing import List, Dict, Optional

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound
from markdown2 import Markdown

jinja_environment: Optional[Environment] = None
markdown_parser: Optional[Markdown] = None


def build_jinja_environment(comic_info: RawConfigParser, template_folders: List[str]):
    global jinja_environment
    if comic_info.getboolean("Comic Settings", "Allow missing variables in templates", fallback=False):
        jinja_environment = Environment(loader=FileSystemLoader(template_folders))  # noqa
    else:
        jinja_environment = Environment(loader=FileSystemLoader(template_folders), undefined=StrictUndefined)  # noqa


def build_markdown_parser(comic_info: RawConfigParser):
    global markdown_parser
    extras = comic_info.get("Comic Settings", "Markdown extras", fallback="")
    markdown_parser = Markdown(extras=["metadata"] + str_to_list(extras))


def get_comic_url(comic_info: RawConfigParser):
    # Let user-defined comic domain and base directory override all other values
    comic_domain = comic_info.get("Comic Settings", "Comic domain", fallback=None)
    base_directory = comic_info.get("Comic Settings", "Comic subdirectory", fallback=None)
    if comic_domain is None:
        # If we have a CNAME file, use that for the comic domain
        if os.path.isfile("CNAME"):
            with open("CNAME") as f:
                comic_domain = f.read().strip('/')
                base_directory = ""
        # If this is running in GitHub and the domain and base directory were not user-defined, derive them here
        elif "GITHUB_REPOSITORY" in os.environ:
            repo_author, repo_name = os.environ["GITHUB_REPOSITORY"].split("/")
            if not comic_domain:
                comic_domain = f"{repo_author}.github.io"
            if base_directory is None:
                base_directory = repo_name
                if base_directory.lower() == f"{repo_author.lower()}.github.io":
                    # In this case, GitHub will try to deploy to http://<username>.github.io/ so we unset base_directory
                    base_directory = ""
    # Helpful error for dumb schmucks trying to build locally for the first time
    if not comic_domain:
        raise ValueError(
            'Set "Comic domain" in the [Comic Settings] section of your comic_info.ini file '
            'before building your site locally. Please see the comic_git documentation for more information.'
        )
    if comic_domain.startswith("http://"):
        comic_domain = comic_domain.replace("http://", "https://")
    if not comic_domain.startswith("http"):
        comic_domain = "https://" + comic_domain
    # Clean up values and make sure we don't have extraneous slashes
    comic_domain = comic_domain.strip("/")
    base_directory = base_directory.strip("/")
    if base_directory:
        base_directory = "/" + base_directory
    comic_url = comic_domain + base_directory
    print(f"Base URL: {comic_url}, base subdirectory: {base_directory}")
    return comic_url, base_directory


def str_to_list(s: str, delimiter: str = ",", max_split: int = -1) -> List[str]:
    """
    split(), but with extra stripping of white space and leading/trailing delimiters
    """
    if not s:
        return []
    return [item.strip(" ") for item in s.strip(delimiter + " ").split(delimiter, max_split)]


def find_project_root():
    while not os.path.exists("your_content"):
        last_cwd = os.getcwd()
        os.chdir("..")
        if os.getcwd() == last_cwd:
            raise FileNotFoundError("Couldn't find a folder in the path matching 'your_content'. Make sure you're "
                                    "running this script from within the comic_git repository.")


def build_md_page(template_name: str, data_dict: Dict=None) -> Optional[str]:
    """
    Searches in the `pages` directory in the given theme directory for a file named {template_name}.md. If it doesn't
    find it, it returns None. Otherwise, the contents of that file are parsed as Markdown, and the md_page.tpl
    template file is used to build a page using those contents. The template file to use can be overridden by the
    "template" variable in the Markdown file's metadata.
    :param template_name: The name of the Markdown file to look for, minus the `.md` file extension
    :param data_dict: The list of Jinja2 variables to be passed to the template file when it's rendered. This will be
     copied, and a `text` field will be added to the copy with the parsed Markdown file contents.
    :return: None, if the given *.md file can't be found.
    """
    theme = data_dict["theme"]
    md_path = f"your_content/themes/{theme}/pages/{template_name}.md"
    if not os.path.isfile(md_path):
        return None
    with open(md_path, "rb") as f:
        converted_md = markdown_parser.convert(f.read())
    metadata = converted_md.metadata
    new_data_dict = data_dict.copy()
    new_data_dict["text"] = converted_md
    template = jinja_environment.get_template(metadata.get("template", "md_page.tpl"))
    return template.render(**new_data_dict)


def write_to_template(template_name: str, html_path: str, data_dict: Dict=None) -> None:
    """
    Searches for an MD, HTML, or TPL file named `template_name` in the "templates" folder of your
    theme directory, or the "templates" directory. It then builds that template at the specified `html_path` using
    the given `data_dict` as a list of variables to pass into the template when it's rendered.

    Will prioritize an MD or HTML file over a TPL file so that a user can easily replace any default template with their own files.
    E.g., We'd prefer to run a user's `archive.html` over the default `archive.tpl`

    :param template_name: The name of the template file or HTML file you wish to load
    :param html_path: The path to write the HTML file, relative to the repository root. If you want it to write to a
    directory (e.g. ...github.io/comic_git/cool_stuff/), then add "index.html" at the end.
    (e.g., "cool_stuff/index.html")
    :param data_dict: The dictionary of values to pass to the template when it's rendered.
    :return: None
    """
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
            raise TemplateNotFound(f"Template matching '{template_name}' not found")

    output_dir = os.getenv("OUTPUT_DIR", "")
    if output_dir:
        html_path = os.path.join(output_dir, html_path)
    dir_name = os.path.dirname(html_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    t = strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{t}] Writing {html_path}")
    with open(html_path, "wb") as f:
        f.write(bytes(file_contents, "utf-8"))


def read_info(filepath, to_dict=False):
    with open(filepath, "rb") as f:
        info_string = f.read().decode("utf-8")
    if not re.search(r"^\[.*?]", info_string):
        # print(filepath + " has no section")
        info_string = "[DEFAULT]\n" + info_string
    info = RawConfigParser()
    info.optionxform = str
    info.read_string(info_string)
    if to_dict:
        # TODO: Support multiple sections
        if not list(info.keys()) == ["DEFAULT"]:
            raise NotImplementedError("Configs with multiple sections not yet supported")
        return dict(info["DEFAULT"])
    return info
