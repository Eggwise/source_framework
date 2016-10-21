import os, inspect
from .. import settings
from ..models.components import SourceFile, Folder, SourceComponent
from ..models.indexer import Indexed

from .. import framework_manager as fm
import logging

def root_config(output_path='HERE', output_folder=None):
    if output_folder is not None and output_path != 'HERE':
        logging.info(
            'Generate base indice\n====>>\nprovided an output path AND folder.\nThe output path overides the folder parameter.\nusing the folder at path: {0}\n<<======'.format(
                output_path))

        output_folder = Folder.from_path(output_path)


    if output_folder is None:
        if output_path == 'HERE':
            caller_frame = inspect.getouterframes(inspect.currentframe())[1]
            output_folder = SourceComponent.from_frame(caller_frame).folder # type: Folder
        else:
            output_folder = Folder.from_path(output_path)

    config = fm.config
    root_config_file = config.base.get_file('root.config') # type: SourceFile

    root_config_file.do.write_to(folder=output_folder, name='root.config')


def base_indices(output_path = 'HERE', output_folder=None):

    if output_folder is not None and output_path != 'HERE':
        logging.info(
            'Generate base indice\n====>>\nprovided an output path AND folder.\nThe output path overides the folder parameter.\nusing the folder at path: {0}\n<<======'.format(
                output_path))

        output_folder = Folder.from_path(output_path)

    if output_folder is None:
        if output_path == 'HERE':
            caller_frame = inspect.getouterframes(inspect.currentframe())[1]
            output_folder = SourceComponent.from_frame(caller_frame).folder # type: Folder
        else:
            output_folder = Folder.from_path(output_path)




    config = fm.config # type: Folder
    indice_configs = Indexed(config.indices.files)

    indice_configs.do.write_to(folder=output_folder, name=lambda manager: manager.file.name)












