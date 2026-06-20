import os


MAIN_COMIC_INFO_TOML = os.path.join("your_content", "comic_info.toml")
MAIN_COMIC_INFO_INI = os.path.join("your_content", "comic_info.ini")
PAGE_INFO_TOML = "info.toml"
PAGE_INFO_INI = "info.ini"
SOCIAL_MEDIA_JSON = "social_media.json"
WEBRING_JSON = os.path.join("your_content", "webring.json")


def get_main_comic_info_candidates() -> tuple[str, str]:
    return MAIN_COMIC_INFO_TOML, MAIN_COMIC_INFO_INI


def get_extra_comic_info_candidates(folder_name: str) -> tuple[str, str]:
    return (
        os.path.join("your_content", folder_name, "comic_info.toml"),
        os.path.join("your_content", folder_name, "comic_info.ini"),
    )


def get_page_info_candidates(page_path: str) -> tuple[str, str]:
    return (
        os.path.join(page_path, PAGE_INFO_TOML),
        os.path.join(page_path, PAGE_INFO_INI),
    )


def get_page_social_media_path(page_dir: str) -> str:
    if page_dir.endswith(("/", "\\")):
        return page_dir + SOCIAL_MEDIA_JSON
    return page_dir + "/" + SOCIAL_MEDIA_JSON


def get_comic_social_media_paths(comic_folder: str) -> list[str]:
    if comic_folder:
        filepaths = [os.path.join(comic_folder, f"your_content/{SOCIAL_MEDIA_JSON}")]
    else:
        filepaths = [f"your_content/{SOCIAL_MEDIA_JSON}"]
    if comic_folder:
        filepaths.append(f"your_content/{SOCIAL_MEDIA_JSON}")
    return filepaths
