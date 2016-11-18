import jinja2, yaml, os, re, json
import logging, copy
from ..utils.utils import LOG_CONSTANTS
import inspect
from .indexer import Printable, Matchable, Unique


# import sample
# from ..indexer import  Printable, Matchable, Unique, Index
# from source_framework.models.indexer import Printable, Matchable, Unique, Index
# indexer.Printable




class Container():

    @property
    def components(self):
        raise NotImplementedError

    @property
    def copy(self):
        raise NotImplementedError


class SourceComponent(Printable, Matchable, Unique):

    # @property
    # def indexer(self):
    #     return source_manager._source_indexer.at(self)
    # pass

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def is_at(self, other_component):
        #folder must overide this
        return self.path == other_component.path


    @staticmethod
    def extract_name(path, identifier):
        path = os.path.realpath(path)
        extract_regex = '(?P<name>.*){0}'.format(identifier)
        parent, filename = os.path.split(path)
        name_match = re.match(extract_regex, filename)

        assert name_match is not None
        assert 'name' in name_match.groupdict()
        assert name_match.groupdict()['name']

        return name_match.groupdict()['name']



    @classmethod
    def from_path(cls, path, index = None, identifier=None):

        path = os.path.realpath(path)

        if identifier is not None and index is not None:
            logging.info('Source component -> from_path -> provided both an index and a identifier..\n now using the given identifier instead of the index identifier')

        if identifier is None and index is not None:
            identifier = index.identifier

        if identifier is not None:
            name = cls.extract_name(path, identifier)
        else:
            name = os.path.basename(path)

        if cls is Folder:
            return Folder(name, path, True)
        elif cls is SourceFile:
            return SourceFile(name, path)
        elif os.path.isfile(path):
            return SourceFile(name, path)
        else:
            return Folder(name, path)


    @classmethod
    def from_here(cls):
        caller_frame = inspect.getouterframes(inspect.currentframe())[1]
        return cls.from_frame(caller_frame)

    @classmethod
    def from_frame(cls, frame):
        (frame, script_path, line_number,
         function_name, lines, index) = frame

        return cls.from_path(script_path)

    @property
    def exists(self):
        return os.path.exists(self.path)

class SourceComponentContainer():

    @property
    def components(self):
        raise NotImplementedError

    @property
    def copy(self):
        raise NotImplementedError

    @property
    def ok(self):
        return self.scoped

    @property
    def one(self):
        if len(self.scoped) == 0:
            err_message = 'Trying to get indexed component from empty index'
            logging.error(err_message)
            raise Exception(err_message)

        if len(self.scoped) != 1:
            err_message = 'Trying to get one indexed component from index with multiple components'
            logging.error(err_message)
            logging.error('If you whish to merge the components use merge')
            logging.error('Or if you really want a list of components set the one parameter to False')
            logging.error('Current items in scope: \n{0}'.format(self._print()))
            raise Exception(err_message)
        return self.scoped[0]

    @property
    def get(self):
        if len(self.scoped) == 0:
            err_message = 'Trying to get indexed component from empty index'
            logging.error(err_message)
            raise Exception(err_message)
        return self.scoped

    @property
    def scoped(self):
        return self._scoped

    @scoped.setter
    def scoped(self, value):
        self._scoped = value


    def filter(self, filter_func, mutable=False):
        if mutable:
            return_val = self
        else:
            return_val = self.copy

        #for indexed inside source indexer
        if isinstance(return_val.scoped, SourceComponentContainer):
            return_val.scoped.filter(filter_func=filter_func, mutable=True)
        else:
            return_val.scoped = list(filter(filter_func, return_val.scoped))

        return return_val

    def map(self, map_func, mutable=False):
        if mutable:
            return_val = self
        else:
            return_val = self.copy

        if isinstance(return_val.scoped, SourceComponentContainer):
            return_val.scoped.map(map_func=map_func, mutable=mutable)
        else:
            return_val.scoped = list(map(map_func, return_val.scoped))

        return return_val



class Source(str, Printable):

    def __init__(self, source):
        self._source = source
        self._current_line = 0

        if isinstance(source, list):
            source = ''.join(source)

        self.lines = source.splitlines(keepends=True)

        #TODO check if super call causes errors
        super(str).__init__()


    def __iter__(self):
        return iter(self.lines)

    def __next__(self):
        self._current_line += 1
        if self._current_line > len(self.lines):
            raise StopIteration

        return self.lines[self._current_line]

    # PROPERTIES (maybe split this up in source loaders module
    @property
    def source(self):
        return ''.join(self.lines)

    @property
    def json(self):
        return json.loads(self.source)

    @property
    def yaml(self):
        return yaml.load(self.source)

    @property
    def template(self):
        return jinja2.Template(self.source)

    # BUILTINS
    def _slice(self, start, stop):
        return Source(self.lines[start: stop])

    def __str__(self):
        return self.source

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self._slice(item.start, item.stop)
        return self.lines[item]

    def __setitem__(self, key, value):

        #todo
        if isinstance(key, int):
            self.lines[key] = value

    #HELPERS
    @property
    def _print(self):
        return LOG_CONSTANTS.REGION_IDENTIFIER \
                + LOG_CONSTANTS.REGION.format('SOURCE COMPONENT') \
                + self.source \
                + LOG_CONSTANTS.REGION_IDENTIFIER

    @classmethod
    def from_json(cls, json_object):
        json_dump = json.dumps(json_object, indent=4)
        return cls(json_dump.splitlines())

    @classmethod
    def from_yaml(cls, yaml_object):
        return cls(yaml.dump(yaml_object, default_flow_style=True))

    #TODO TEST
    def to_file(self, path=None, name=None, folder=None, filename=None, source_file=None):

        if path is None and (folder is None or filename is None) and source_file is None:
            err_msg = 'Must provide a path, a folder with filename, or a sourcefile to create path with.'
            logging.error(err_msg)
            raise Exception(err_msg)
        elif folder is not None and source_file is not None:
            err_msg = 'Provided both a folder and a source file, choose either one'
            logging.error(err_msg)
            raise Exception
        elif source_file is not None:
            if filename is None:
                filename = source_file.filename

            path = os.path.join(source_file.path, filename)

        if name is None:
            #create name from extension
            name = ''.join(filename.split('.')[:-1])

        return SourceFile(name, path, source=self)


#TODO WIP
class Folder(SourceComponent):

    def __init__(self, name: str, path: str, get_dir_name = False):
        self.name = name

        if os.path.isfile(path):
            if not get_dir_name:
                raise Exception('trying to create folder folder using file path: {0}'.format(self.path))
            else:
                path = os.path.dirname(path)
        self.path = os.path.realpath(path)
    @property
    def items(self):
        return [SourceComponent.from_path(os.path.join(self.path, i)) for i in os.listdir(self.path) if not i.startswith('.')]

    @property
    def files(self):
        return list(filter(lambda x: not os.path.isdir(x.path), self.items))

    @property
    def dirs(self):
        return list(filter(lambda x: os.path.isdir(x.path), self.items))

    def __getattr__(self, name):
        items_starting_with = [i for i in self.items if i.name.startswith(name)]

        if len(items_starting_with) > 1:
            raise Exception('multiple items with same name')
        if len(items_starting_with) == 0:
            raise AttributeError('no items with found with name {0} at path: {1}'.format(name, self.path))

        match_item = items_starting_with[0]
        logging.info('get item: {0}'.format(match_item))

        return match_item

    def join(self, *path):
        new_folder = Folder.from_path(os.path.join(self.path, *path))
        return new_folder

    def get_folder(self, name):
        items_starting_with = [i for i in self.dirs if i.name.startswith(name)]
        if len(items_starting_with) > 1:
            raise Exception('Error getting folder, multiple items with same name')
        if len(items_starting_with) == 0:
            raise AttributeError('no items with found with name {0}'.format(name))

        match_item = items_starting_with[0]
        return match_item

    def get_file(self, name):
        items_starting_with = [i for i in self.files if i.filename.startswith(name)]

        if len(items_starting_with) > 1:
            raise Exception('multiple items with same name')
        if len(items_starting_with) == 0:
            raise AttributeError('no items with found with name {0}\nAt path: {1}\nFiles available: {2}'.format(name, self.path, [i.filename for i in self.files]))

        match_item = items_starting_with[0]
        return match_item

    @property
    def children(self):
        return [Folder.from_path(i[1]) for i in self.dirs]

    @property
    def parent(self):
        parent_path, current = os.path.split(self.path)
        return Folder.from_path(parent_path)




    def has_dir(self, name):
        try:
            self.get_folder(name)
            return True
        except AttributeError:
            return False

    def has_file(self, name):
        try:
            self.get_file(name)
            return True
        except AttributeError:
            return False

    def __repr__(self):
        try:
            return '[Folder: >> {0} <<, {1} items]'.format(os.path.basename(self.name), len(self.items))
        except FileNotFoundError:
            return '[Virtual folder >> {0} << at {1}]'.format(os.path.basename(self.name), self.path)



class SourceFile(SourceComponent):


    def __init__(self, name: str, path: str, source : str= None):
        self.name = name
        self.path = os.path.realpath(path)
        if source is None:
            self._source = self._load_source(self.path)
        else:
            self._source = source


    @classmethod
    def _load_source(cls, path: str):
        with open(path, encoding='utf8') as f:

            try:
                source = f.read()
            except UnicodeDecodeError:
                logging.error('Failed to read: {0}'.format(path))
                raise
            return source

    @property
    def folder(self) -> Folder:
        return Folder.from_path(os.path.realpath(os.path.dirname(self.path)))

    @property
    def do(self) :
        from ..source_manager.source_manager import FileManager
        return FileManager(self) # type: FileManager

    @property
    def extension(self) -> str:
        #TODO TEST
        return self.filename.split('.')[-1]


    @property
    def filename(self) -> str:
        return os.path.basename(self.path)

    @property
    def source(self) -> Source:
        return Source(self._source)


    # @property
    # def compile(self):
    #     return source_manager.compiler(self)

    #helper to acces source attributes
    def __getattr__(self, attr):
        logging.debug('gettting attribute {0} from source file, passing it to the child source object'.format(attr))
        return getattr(self.source, attr)

    def __len__(self):
        return len(self.source)

    @property
    def _print(self):
        return LOG_CONSTANTS.REGION_IDENTIFIER \
               + LOG_CONSTANTS.REGION.format('SOURCE FILE') \
                +LOG_CONSTANTS.LINE.format('name: {0}'.format(self.name)) \
                +LOG_CONSTANTS.LINE.format('path: {0}'.format(self.path)) \
                +LOG_CONSTANTS.LINE.format('') \
               + LOG_CONSTANTS.LINE.format('') \
               +LOG_CONSTANTS.REGION.format('SOURCE') \
                +LOG_CONSTANTS.LINE.format(self.source._source) \
                + LOG_CONSTANTS.REGION.format('SOURCE FILE END')




from .indexer import Index
class IndexedFile(SourceFile, SourceComponent):

    # MANAGER = FileManager

    def __init__(self, name: str, path: str, index: Index, source=None):
        self.index = index
        super().__init__(name, path, source=source)

    def __eq__(self, other):
        return self.name == other.name and self.index == other.index

    def __str__(self):
        return 'Indexed file: {0} at {1}'.format(self.name, self.path)


    #pass down to the sourcefile
    def __getattr__(self, item):
        return getattr(self.source, item)
        # manager = self.MANAGER(self)
        # return getattr(manager, item)

    @property
    def _print(self):
        return 'indexed file: {2} >>> {0} <<< \t{1}'.format(self.name, self.path, self.index.name)


    @classmethod
    def from_path(cls, path, index = None, identifier=None):
        assert index is not None
        file = super().from_path(path=path, index=index, identifier=identifier)
        return cls.from_source_file(file, index)


    @classmethod
    def from_source_file(cls, file: SourceFile, index):
        return cls(file.name, file.path, index)


class IndexedItem(SourceComponent):

    def __init__(self, name: str, indexed_file: IndexedFile, line_start: int, line_end: int, index, properties: dict = None):
        self.line_start = line_start
        self.line_end = line_end
        self.name = name
        self.indexed_file = indexed_file
        self._source = None
        if properties is not None:
            for k, v in properties.items():
                setattr(self, k, v)
        self.index = index

    def __eq__(self, other):
        return self.name == other.name and self.index == other.index

    #helper to acces indexed file attributes
    def __getattr__(self, item):
        return getattr(self.indexed_file, item)

    @property
    def _print(self):
        return 'Indexed item: {0} between lines {1} and {2} in file: {3}'.format(self.name, self.line_start, self.line_end, self.filename)


    @property
    def file(self):
        return self.indexed_file

    @property
    def source(self):
        if self._source is None:
            file_source = self.indexed_file.source
            self._source = file_source[self.line_start: self.line_end]
        return self._source

    @property
    def dirname(self):
        return os.path.dirname(self.indexed_file.path)

    @property
    def filename(self):
        return os.path.basename(self.indexed_file.path)


class IndexedProject(SourceComponent):


    def __init__(self, config_file):
        self.config = config_file


    def register_project(self, project):

        config = self.config.yaml

        if 'dependencies' not in config:
            config['dependencies'] = []

        project_identifier = {
            'name': project.name,
            'path': project.path
        }
        config['dependencies'].append(project_identifier)

        new_config = Source.from_yaml(config).to_file(source_file=self.config)
        new_config.do.save(backup=True)




    @classmethod
    def from_path(cls, path, index = None, identifier=None):
        assert index is None
        assert identifier is None
        file = super().from_path(path=path, index=index, identifier=identifier)
        return cls(file)






