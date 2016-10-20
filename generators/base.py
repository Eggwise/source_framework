import os, inspect
from .. import settings
from ..models.components import SourceFile, Folder

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








