import os, inspect
from .. import settings
from ..models.components import SourceFile, Folder, SourceComponent
from ..models.indexer import Indexed

from .. import framework_manager as fm


def root_config(output_path='HERE'):

    if output_path == 'HERE':
        (frame, script_path, line_number,
         function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]

        output_folder = Folder.from_path(os.path.dirname(script_path))
        output_folder.join(True, 'root.config')

        output_path = output_folder.path


    config = fm.config
    root_config_file = config.base.get_file('root.config') # type: SourceFile
    root_config_file.do.write_to(path=output_path)


def base_indices(output_folder = 'HERE', item=True, file=True):
    if output_folder == 'HERE':
        (frame, script_path, line_number,
         function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]

        output_folder = SourceComponent.from_path(script_path).folder # type: Folder

    config = fm.config # type: Folder
    indice_configs = Indexed(config.indices.files)

    indice_configs.do.write_to(folder=output_folder, name=lambda manager: manager.file.name)












