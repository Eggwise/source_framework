import os, inspect
from .. import settings



def root_config(output_path='HERE'):

    if output_path == 'HERE':
        (frame, script_path, line_number,
         function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]

        output_path = script_path



