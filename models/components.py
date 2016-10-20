import jinja2, yaml, os, re, json
import logging, copy
from ..utils.utils import LOG_CONSTANTS

from .indexer import Printable, Matchable, Unique


# import sample
# from ..indexer import  Printable, Matchable, Unique, Index
# from source_framework.models.indexer import Printable, Matchable, Unique, Index
# indexer.Printable

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

    def is_at(self, other_component):
        #folder must overide this
        return self.path == other_component.path




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
            self.lines = source
        else:
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


    #HELPERS
    @property
    def _print(self):
        return LOG_CONSTANTS.REGION_IDENTIFIER \
                + LOG_CONSTANTS.REGION.format('SOURCE COMPONENT') \
                + self.source \
                + LOG_CONSTANTS.REGION_IDENTIFIER

    @classmethod
    def from_json(cls, json_object):
        return cls(json.dumps(json_object))

    @classmethod
    def from_yaml(cls, yaml_object):
        return cls(yaml.dump(yaml_object, default_flow_style=True))



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
        with open(path) as f:
            source = f.read()
            return source

    @property
    def folder(self):
        #TODO TEST
        return os.path.realpath(self.dirname)

    @property
    def extension(self):
        #TODO TEST
        return self.filename.split('.')[-1]

    @property
    def dirname(self):
        return os.path.dirname(self.path)

    @property
    def filename(self):
        return os.path.basename(self.path)

    @property
    def source(self):
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




#TODO WIP
class Folder():
    def __init__(self, path):
        self.path = os.path.realpath(path)
        if os.path.isfile(path):
            raise Exception('trying to get folder using filename')
        self.items = [(i, os.path.join(path, i)) for i in os.listdir(path) if not i.startswith('.')]


    @property
    def files(self):
        return list(filter(lambda x: not os.path.isdir(x[1]), self.items))

    @property
    def dirs(self):
        return list(filter(lambda x: os.path.isdir(x[1]), self.items))

    def __getattr__(self, name):
        items_starting_with = [i for i in self.items if i[0].startswith(name)]

        if len(items_starting_with) > 1:
            raise Exception('multiple items with same name')
        if len(items_starting_with) == 0:
            raise AttributeError('no items with found with name {0} at path: {1}'.format(name, self.path))

        match_item = items_starting_with[0]
        logging.info('get item: {0}'.format(match_item))

        if os.path.isfile(match_item[1]):
            return SourceFile.from_path(match_item[1])
        else:
            return Folder(match_item[1])


    def get_folder(self, name):
        items_starting_with = [i for i in self.dirs if i[0].startswith(name)]
        if len(items_starting_with) > 1:
            raise Exception('multiple items with same name')
        if len(items_starting_with) == 0:
            raise AttributeError('no items with found with name {0}'.format(name))

        match_item = items_starting_with[0]
        return Folder(match_item[1])

    def get_file(self, name):
        items_starting_with = [i for i in self.files if i[0].startswith(name)]

        if len(items_starting_with) > 1:
            raise Exception('multiple items with same name')
        if len(items_starting_with) == 0:
            raise AttributeError('no items with found with name {0}'.format(name))

        match_item = items_starting_with[0]
        return SourceFile.from_path(match_item[1])

    @property
    def children(self):
        return [Folder(i[1]) for i in self.dirs]

    @property
    def parent(self):
        parent_path, current = os.path.split(self.path)
        return Folder(parent_path)


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
        return '[dir: >> {0} <<, {1} items]'.format(os.path.basename(self.path), len(self.items))


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


    #pass down to the filemanager
    def __getattr__(self, item):
        manager = self.MANAGER(self)
        return getattr(manager, item)

    @property
    def _print(self):
        return 'indexed file: {2} >>> {0} <<< \t{1}'.format(self.name, self.path, self.index.name)





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






