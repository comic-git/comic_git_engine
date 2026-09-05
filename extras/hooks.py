def preprocess(comic_info):
    """
    Runs immediately after the main comic configuration is loaded.

    INI and TOML configuration both arrive through the same RawConfigParser
    interface.

    :param comic_info: The resolved main comic configuration.
    :return: None
    """
    pass


def extra_page_info_processing(comic_folder, comic_info, page_path, page):
    """
    Runs after one page source is parsed and its fallback values are resolved.

    :param comic_folder: Blank for the main comic; otherwise the Extra Comic's
        folder name.
    :param comic_info: The resolved configuration for the current comic.
    :param page_path: The current page folder, such as
        your_content/comics/197/.
    :param page: The normalized ComicPage, including its ordered ComicImage list.
    :return: A replacement ComicPage, or None to keep the original page.
    """
    return page


def extra_comic_dict_processing(comic_folder, comic_info, page):
    """
    Runs after one ComicPage receives navigation and rendered post content.

    The historical hook name remains unchanged even though pages are no longer
    passed as dictionaries.

    :param comic_folder: Blank for the main comic; otherwise the Extra Comic's
        folder name.
    :param comic_info: The resolved configuration for the current comic.
    :param page: The enriched ComicPage.
    :return: A replacement ComicPage, or None to keep the original page.
    """
    return page


def extra_get_storylines_processing(comic_info, pages, storylines):
    """
    Runs after the Archive's storyline groups and entries are assembled.

    :param comic_info: The resolved configuration for the current comic.
    :param pages: The current comic's complete list of ComicPage objects.
    :param storylines: Ordered storyline groups containing ArchiveEntry objects.
    :return: Replacement storyline groups, or None to keep the originals.
    """
    return storylines


def extra_global_values(comic_folder, comic_info, pages):
    """
    Adds custom global values before the current comic's templates are rendered.

    :param comic_folder: Blank for the main comic; otherwise the Extra Comic's
        folder name.
    :param comic_info: The resolved configuration for the current comic.
    :param pages: The current comic's complete list of ComicPage objects.
    :return: A dictionary of additional global template values.
    """
    return {}


def build_other_pages(comic_folder, comic_info, pages):
    """
    Runs after comic_git builds the current comic's standard HTML files.

    :param comic_folder: Blank for the main comic; otherwise the Extra Comic's
        folder name.
    :param comic_info: The resolved configuration for the current comic.
    :param pages: The current comic's complete list of ComicPage objects.
    :return: None
    """
    pass


def postprocess(comic_info, pages, global_values):
    """
    Runs at the end of the main comic build.

    :param comic_info: The resolved main comic configuration.
    :param pages: The main comic's complete list of ComicPage objects.
    :param global_values: The final global values passed to templates.
    :return: None
    """
    pass
