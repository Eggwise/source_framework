import inspect
import logging, os

from source_framework.models.components import Project
from source_framework.models.indexer import Indexed
from .source_manager.source_indexer import SourceIndexer
from . import generators
from contextlib import contextmanager

_init_config = {

    'caller_path': None
}

_source_indexer = None


def init(path=None):
    global _init_config
    global _source_indexer

    if _init_config['caller_path'] is not None:
        error_message = 'initialize for the second time, why?'
        logging.error(error_message)

    (frame, script_path, line_number,
     function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]

    if path is not None:
        _init_config['caller_path'] = os.path.realpath(path)
    else:
        _init_config['caller_path'] = os.path.realpath(script_path)

    SourceIndexer.prepare(_init_config)
    _source_indexer = SourceIndexer()


def _check_initialized():
    global _init_config
    global _source_indexer

    if _source_indexer is None:
        error_message = 'something went wrong when initializing the source manager. did you call init()?'
        logging.error(error_message)
        raise Exception(error_message)


def find():
    _check_initialized()
    global _source_indexer
    return _source_indexer


def from_this():
    (frame, script_path, line_number,
     function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]
    _check_initialized()
    indexer = _source_indexer

    return indexer.at_path(script_path)


def current_project() -> Project:
    source_indexer = find()
    root_config = _source_indexer._get_root_config()

    return source_indexer.projects.by_path(root_config.path).one


def enable_logging():
    logging.basicConfig(level=1)


def indexer():
    _check_initialized()
    global _source_indexer
    return _source_indexer


@contextmanager
def edit(file, indexed = None):
    from .source_manager.source_editor import FileEditor
    if indexed is None:
        indexed = indexer()

    yield FileEditor(file, indexed)

generate = generators
