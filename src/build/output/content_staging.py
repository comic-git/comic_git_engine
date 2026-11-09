"""Folder-level publication policy and non-destructive selective staging."""

import shutil
from configparser import RawConfigParser
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

from build.content.page_models import ComicPage
from build.output.site_output import PYTHON_CACHE_DIR, validate_hidden_path_policy

@dataclass(frozen=True)
class ContentCopyPolicy:
    selective_copy: bool = False
    hidden_paths: str | None = None

    def allows(self, path: str) -> bool:
        """Whether a final output file/subtree is public (not just traversable)."""
        candidate = PurePosixPath(path.replace('\\', '/').rstrip('/'))
        if self.selective_copy and PYTHON_CACHE_DIR in candidate.parts:
            return False
        if self.hidden_paths is None or not any(p.startswith('.') for p in candidate.parts):
            return True
        return any(candidate == entry or entry in candidate.parents
                   for line in self.hidden_paths.splitlines() if line.strip()
                   for entry in [PurePosixPath(line.strip().rstrip('/'))])


def resolve_copy_policy(comic_info: RawConfigParser, *, selective_copy: bool | None = None,
                        hidden_paths: str | None = None) -> ContentCopyPolicy:
    selective = (comic_info.getboolean('Build', 'Selective copy', fallback=False)
                 if selective_copy is None else selective_copy)
    if hidden_paths is None and comic_info.has_option('Build', 'Hidden paths'):
        hidden_paths = comic_info.get('Build', 'Hidden paths')
    if hidden_paths is None and selective:
        hidden_paths = ''
    return ContentCopyPolicy(selective, hidden_paths)


def managed_comic_roots(extra_comics: list[str]) -> tuple[Path, ...]:
    bases = [Path('your_content')]
    for value in extra_comics:
        parts = value.split('/')
        if (not value or any(p in ('', '.', '..') or p.endswith(('.', ' ')) for p in parts)
                or '\\' in value or PureWindowsPath(value).drive
                or any(c in value for c in ':*?[]')
                or any(ord(c) < 32 for c in value)):
            raise ValueError(f'Invalid Extra Comic folder for selective copying: {value!r}')
        base = Path('your_content').joinpath(*parts)
        if any(base.resolve() == existing.resolve() for existing in bases):
            raise ValueError(f'Duplicate Extra Comic folder for selective copying: {value}')
        bases.append(base)
    roots = tuple(base / 'comics' for base in bases)
    for base in bases:
        if any(base == root or root in base.parents for root in roots):
            raise ValueError(f'Extra Comic folder is inside a managed comics directory: {base}')
        check_source_path(base)
    return roots


def validate_selective_output(output_dir: str) -> None:
    validate_hidden_path_policy(output_dir, '')
    output = Path(output_dir).resolve()
    # An external engine may be symlinked into the host; never clear its parent.
    for source in (Path('your_content').resolve(), Path('comic_git_engine').resolve(),
                   Path(__file__).resolve().parents[3]):
        if output == source or output in source.parents or source in output.parents:
            raise ValueError('Selective copying requires output separate from source and engine directories.')


def check_source_path(path: Path) -> None:
    """Reject link aliases before any read/copy/write through a selected path."""
    root = Path('your_content').absolute()
    absolute = path.absolute()
    if not absolute.is_relative_to(root) or '..' in path.parts:
        raise ValueError(f'Selective content path is outside your_content: {path}')
    for candidate in (root, *reversed(absolute.parents), absolute):
        if candidate.is_relative_to(root) and (candidate.is_symlink() or candidate.is_junction()):
            if not candidate.resolve().is_relative_to(root.resolve()):
                raise ValueError(f'Selective content link points outside your_content: {candidate}')
            raise ValueError(f'Selective copying does not support symlinks or junctions: {candidate}')


def check_source_tree(source: Path) -> None:
    check_source_path(source)
    if source.is_dir():
        for child in source.iterdir():
            if child.name != PYTHON_CACHE_DIR:
                check_source_tree(child)
    elif not source.is_file():
        raise ValueError(f'Unsupported selective content path: {source}')


def page_selection(pages: list[ComicPage], comic_folder: str) -> dict[str, str]:
    selected = {}
    root = Path('your_content') / comic_folder / 'comics'
    for page in pages:
        expected = root / page.page_name
        if (Path(page.page_dir) != expected or expected.parent != root
                or page.id in selected or page.page_name in ('', '.', '..')):
            raise ValueError(f'Invalid selected page identity or folder: {page.page_dir}')
        check_source_tree(expected)
        selected[page.id] = expected.as_posix()
    return selected


def validate_selected_pages(pages: list[ComicPage], selected: dict[str, str],
                            policy: ContentCopyPolicy) -> None:
    if len(pages) != len(selected) or {page.id for page in pages} != set(selected):
        raise ValueError('A hook changed the selected page identities during selective copying.')
    for page in pages:
        source = Path(selected[page.id])
        if Path(page.page_dir) != source or page.page_name != source.name:
            raise ValueError(f'A hook changed the selected page folder: {page.page_dir}')
        check_source_tree(source)
        for image in page.images:
            path = Path(image.source_path)
            if not path.resolve().is_relative_to(source.resolve()) or not path.is_file():
                raise ValueError(f'Comic image must remain in its selected page folder: {path}')
            if Path(image.web_path).resolve() != path.resolve():
                raise ValueError(f'Comic image source and public path disagree: {image.web_path}')
            if not policy.allows(image.web_path):
                raise ValueError(f'Comic image would be excluded by the hidden-path policy: {image.web_path}')
        for thumbnail in [page.thumbnail_path, *(image.thumbnail_path for image in page.images)]:
            if thumbnail is not None:
                if not Path(thumbnail).resolve().is_relative_to(source.resolve()):
                    raise ValueError(f'Thumbnail must remain in its selected page folder: {thumbnail}')
                if not policy.allows(thumbnail):
                    raise ValueError(f'Thumbnail would be excluded by the hidden-path policy: {thumbnail}')


def stage_page_assets(output_dir: str, selected: dict[str, str]) -> None:
    for relative in selected.values():
        source = Path(relative)
        check_source_tree(source)
        shutil.copytree(source, Path(output_dir) / source, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(PYTHON_CACHE_DIR))


def stage_remaining_content(output_dir: str, managed_roots: tuple[Path, ...]) -> None:
    """Traverse auxiliary content once, pruning every configured comics root."""
    def copy(source: Path) -> None:
        if source in managed_roots or source.name == PYTHON_CACHE_DIR:
            return
        check_source_path(source)
        destination = Path(output_dir) / source
        if source.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            for child in source.iterdir():
                copy(child)
        elif source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        else:
            raise ValueError(f'Unsupported selective content path: {source}')
    copy(Path('your_content'))
