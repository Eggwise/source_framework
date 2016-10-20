import os, inspect
from . import settings
# from .settings import CONFIG_DIR
from .models.components import Folder




def root_config(output_path='HERE'):

    if output_path == 'HERE':
        (frame, script_path, line_number,
         function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]

        output_path = script_path



class Config():

    ROOT = CONFIG_DIR

    @property
    def base(self):
        return Folder(self.ROOT)




print(Config().base.root.yaml)