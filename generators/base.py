import os, inspect
from ..models.components import SourceFile, Folder, SourceComponent
from ..models.indexer import Indexed
from ..utils.utils import LOG_CONSTANTS

from .. import framework_manager as fm
import logging


def _parse_destination(current_frame, output_path='HERE', output_folder=None):
    if output_folder is not None and output_path != 'HERE':
        logging.info(
            'Generator ->\ngot an output path AND folder parameter.\nThe output path overides the folder parameter.\nusing the folder at path: {0}\n<<======'.format(
                output_path))

    if output_folder is None:
        if output_path == 'HERE':
            caller_frame = inspect.getouterframes(current_frame)[1]
            output_folder = Folder.from_frame(caller_frame)
        else:
            output_folder = Folder.from_path(output_path)
    return output_folder

def root_config(output_path='HERE', output_folder=None):
    output_folder = _parse_destination(inspect.currentframe(), output_path, output_folder)
    config = fm.config
    root_config_file = config.base.get_file('root.config') # type: SourceFile

    return root_config_file.do.write_to(folder=output_folder, name='root.config')


def base_indices(output_path = 'HERE', output_folder=None):
    output_folder = _parse_destination(inspect.currentframe(), output_path, output_folder)

    config = fm.config # type: Folder
    indice_configs = Indexed(config.indices.files)

    return indice_configs.do.write_to(folder=output_folder, name=lambda manager: manager.file.name)





def new_project(output_path='HERE', output_folder=None):

    output_folder = _parse_destination(inspect.currentframe(), output_path, output_folder)

    print(LOG_CONSTANTS.REGION.format('GENERATE NEW PROJECT'))
    print('Generating root config')
    root_config_path = root_config(output_folder=output_folder)
    print('Root config written to path: {0}'.format(root_config_path))
    print('Generating neccesary indice config files')
    base_indices(output_folder= output_folder)
    print('Success!')
    print('Dont forget to init the framework before using it')
    print('\n\nsource_framework.init()')
    print(LOG_CONSTANTS.REGION.format('GENERATE NEW PROJECT DONE'))









