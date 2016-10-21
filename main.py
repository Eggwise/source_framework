import inspect
import logging, os
from .source_manager.source_indexer import SourceIndexer
from . import generators

_init_config = {

    'caller_path' : None
}

_source_indexer = None

def init():
    global _init_config
    global _source_indexer

    if _init_config['caller_path'] is not None:
        error_message = 'initialize for the second time, why?'
        logging.error(error_message)

    (frame, script_path, line_number,
     function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]




    _init_config['caller_path'] = os.path.realpath(script_path)

    SourceIndexer.prepare(_init_config)
    _source_indexer = SourceIndexer()





def _check_initialized():
    global _init_config
    global _source_indexer
    if _init_config['caller_path'] is None:
        error_message = 'source manager is not initialized. call init() first'
        logging.error(error_message)
        raise Exception(error_message)

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

    indexer = _source_indexer
    return indexer.at_path(script_path)



generate = generators

