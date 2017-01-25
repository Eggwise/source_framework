import os, inspect
from ..models.components import SourceFile, Folder, SourceComponent
from ..models.indexer import Indexed
from ..utils.utils import LOG_CONSTANTS
from .. import framework_manager as fm
from ..models.components import Folder, Source
from .utils import parse_destination


def _ask_input(name, message=None, validation_func=None):
    if message is not None:
        print(message)
    user_input = input()

    valid_input = True
    if validation_func is not None:
        valid_input = validation_func(user_input)

    if not valid_input:
        print('Invalid input, try again.')
        return _ask_input(name, None, validation_func)

    return user_input


def _ask_index_name():
    message = 'enter name for the index'

    def validate(user_input):
        valid_input = True
        if ' ' in user_input:
            print('name may not contain spaces')
            valid_input = False
        if len(user_input.split()) > 1:
            print('name must be one word')
            valid_input = False
        return valid_input

    index_name = _ask_input('identifier', message, validate)
    return index_name

    pass


def _ask_file_index_identifier():
    message = 'enter the identifier.\nfiles with a filename ending with this identifier will get indexed by this index.'

    def validate(user_input):
        valid_input = True
        if ' ' in user_input:
            print('identifier may not contain spaces')
            valid_input = False
        if len(user_input.split()) > 1:
            print('identifier must be one word')
            valid_input = False
        return valid_input

    identifier = _ask_input('identifier', message, validate)
    return identifier


def file_index(output_path='HERE', output_folder=None, ):
    output_folder = parse_destination(inspect.currentframe(), output_path, output_folder)
    print('Generate new file index.')
    name = _ask_index_name()
    identifier = _ask_file_index_identifier()
    result = _generate_file_index(output_folder, name, identifier)


def _generate_file_index(output_folder, name, identifier):
    # config = fm.config  # type: Folder
    # file_index_template = config.templates.get_file('root.file.index.template')
    # TODO use template from config

    index_template = 'identifier: {identifier}'
    index_source = Source(index_template.format(identifier=identifier))
    file_name = name + '.file.index'
    index_file = index_source.to_file(folder=output_folder, filename=file_name)
    saved_index_file = index_file.do.save(backup=False)

    print('File index done created at: {0}'.format(index_file.path))

    return True


def item_index(output_path='HERE', output_folder=None):
    output_folder = parse_destination(inspect.currentframe(), output_path, output_folder)
    name = _ask_index_name()

    print('Enter the start identifier')
    start_identifier = input()

    print('Enter the end identifier, or press enter to use default (defined in the base item index config file)')
    end_identifier = input()

    identifier_config = {
        'start': start_identifier
    }

    if len(end_identifier) != 0:
        identifier_config['end'] = end_identifier

    file_name = name + '.item.index'
    index_config = dict(identifier=identifier_config)
    index_config_source = Source.from_yaml(index_config)

    index_file = index_config_source.to_file(folder=output_folder, filename=file_name)
    index_file.do.save()
    print('Item index file saved to: {0}'.format(index_file.path))
    return
