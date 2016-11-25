import os, inspect
from ..models.components import Folder
import logging


def parse_destination(current_frame, output_path='HERE', output_folder=None):
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