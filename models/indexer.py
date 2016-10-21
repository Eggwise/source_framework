from typing import List
import logging, copy
from ..utils.utils import LOG_CONSTANTS



ROOT_IDENTIFIER = '.config'


class Unique():
    def __hash__(self):
        return '{0}-{1}-{2}'.format(self.__class__.__name__, self.name, self.path)



class Matchable():

    def match(self, query):

        if isinstance(self, Index):
            return self.name == query or self.index_type == query

        if isinstance(self, SourceComponent):
            return self.name == query or self.index.match(query)
        else:
            return self.name == query or self.index.match(query)


class Printable():

    def print(self):
        print(self._print)
        return self

    def log(self):
        logging.info(self._print)

    @property
    def _print(self):
        raise NotImplementedError



#TODO tidy this class
class Index(Matchable, Printable):


    def __init__(self, index_type: str, config_file, name=None):

        if name is None:
            name = config_file.name

        self.name = name

        self.index_type = index_type
        self.config_file = config_file
        self.config = config_file.yaml

        # assert isinstance(config_file, SourceFile)
        if name == 'root':
            self.identifier = ROOT_IDENTIFIER
            return

        if 'identifier' not in self.config:

            error_message =  'trying to create a {0} index named: {1}  without a identifier \n'.format(index_type, name)\
                + 'make sure your index config has a identifier\n' \
                + 'config file used {0}'.format(config_file._print)

            logging.error(error_message)
            raise Exception(error_message)

        self.identifier = self.config['identifier']

        if index_type == 'file' and not isinstance(self.identifier, str):
            error_message = '\n\ntrying to create the index: {0} index for files using a non file index config \n'.format(name) \
                            + 'are you sure the index config file is correct ?\n' \
                            + 'for files use a string identifying the end of the file\n' \
                              'so for indexing python script files with name xxNAMExx.script.py for example,use .script.py y\n' \
                            + 'look at the docs for how to format the identifier\n' \
                            + '\nconfig file used: {0}'.format(config_file._print)
            logging.error(error_message)
            raise Exception(error_message)


    def __eq__(self, other):
        return self.name == other.name and self.index_type == other.index_type


    def print_row(self):
        total = 30
        row_string = self.name + ''.join(map(lambda x: ' ', range(0, (total-len(self.name) -len(self.index_type))))) + self.index_type
        print(row_string)

    def __str__(self):
        return 'Index || >>> {0} ||| type  >>> {1}  || identifier >>> {2} '.format(self.name, self.index_type, self.identifier)

    @property
    def _print(self):
        return 'Index || >>> {0} ||| type  >>> {1}  || identifier >>> {2} '.format(self.name, self.index_type, self.identifier)






    #helper to acces source attributes
    def __getattr__(self, attr):
        logging.info('gettting attribute {0} from index, passing it to the index config source file'.format(attr))
        return getattr(self.config_file, attr)





class Indices(Printable):

    def __iter__(self):
        return iter(self.scoped)

    def __init__(self, indices: List[Index]):
        if not isinstance(indices, list):
            indices = [indices]
        self._indices = indices
        self.scoped = indices
        if len(indices) == 0:
            raise Exception('Trying to make indices for empty index list')
        self.current = 0

    def __len__(self):
        return len(self.scoped)

    def __next__(self):
        self.current += 1
        if self.current > len(self):
            raise StopIteration

        return self.scoped[self.current]

    def __getattr__(self, index_type):

        indices_of_type = [i for i in self if i.index_type == index_type]
        logging.info(LOG_CONSTANTS.REGION.format('GET INDICE {0}'.format(index_type)))
        logging.info('Filtering indices by type: {0}'.format(index_type))
        logging.info('Found {0} indices'.format(len(indices_of_type)))
        logging.info('Current indices: {0}'.format(self))

        if len(indices_of_type) == 0:
            error_message = 'Index error: no index found of the same type: {0}'.format(index_type)
            logging.error(error_message)

            logging.error('available indices: {0}'.format([i.index_type for i in self]))
            logging.debug('all indices: {0}'.format([(i.name, i.index_type) for i in self._indices]))
            raise AttributeError(error_message)
        self.scoped = indices_of_type
        logging.info('Indices found: {0}'.format(self))

        return self

    def __str__(self):
        return '{0}'.format([(i.index_type, i.name) for i in self.scoped])


    def has(self, index_type):
        return len([1 for i in self._indices if i.index_type == index_type]) > 0


    @property
    def _print(self):
        print_string = '\n\n'  \
        + LOG_CONSTANTS.REGION.format('INDICES') \
        + '\nTotal amount: {0}'.format(len(self._indices)) \
        + '\n---\n' \
        + '\n'.join([str(i) for i in self]) \
        + '\n' + LOG_CONSTANTS.REGION.format('INDICES END') \
        + '\n\n'

        return print_string

    @property
    def ok(self):
        #TODO check if copy is neccesary
        indices_copy = copy.copy(self.scoped)
        self_to_return = Indices(indices=indices_copy)
        self.refresh()
        return self_to_return


    @property
    def all(self):
        all_indices_copy = copy.copy(self._indices)
        return Indices(indices=all_indices_copy)

    def refresh(self):
        self.scoped = self._indices



    def types(self):

        # TODO make use of this
        return set([i.index_type for i in self])



from .components import SourceComponentContainer, SourceComponent

class Indexed(Printable, SourceComponentContainer):

    def __iter__(self):
        self.current = 0
        return iter(self.scoped)


    @classmethod
    def _unpack(cls, items, unpacked=None):
        if unpacked is None:
            unpacked = []
        if isinstance(items, SourceComponent):
            unpacked.append(items)
            return unpacked

        if isinstance(items, SourceComponentContainer):
            unpacked = cls._unpack(items.components, unpacked)


        for s in items:
            if isinstance(s, list):
                unpacked = cls._unpack(s, unpacked)
                continue

            if isinstance(s, SourceComponent):
                unpacked.append(s)
                continue

            if isinstance(s, SourceComponentContainer):
                unpacked = cls._unpack(s.components, unpacked)
                continue

            error_message = 'Indexed tried to unpack non source component {0}'.format(s)
            logging.error(error_message)
            raise Exception(error_message)

        return unpacked

    def __init__(self, *source_components):
        self._components = self._unpack(source_components)
        self.scoped = self._components

        for i in self._components:
            if not isinstance(i, SourceComponent):
                print(i)
            assert  isinstance(i, SourceComponent)

        if len(source_components) == 0:
            raise Exception('Trying to use 0 components')
        self.current = -1


    def __getitem__(self, item):
        if isinstance(item, slice):
            return self.scoped[item.start: item.stop]

        if isinstance(item, str):
            components_with_name = [i for i in self.scoped if i.name == item]
            if len(components_with_name) > 1:
                error_message = 'trying to get unique source component by name : {0} but there where multiple components found with the same name. '.format(item) \
                + 'source components found: {0} '.format(components_with_name)
                logging.error(error_message)
                raise AttributeError(error_message)

            if len(components_with_name) == 0:
                error_message = 'trying to get unique source component by name : {0} but there were no components found. '.format(
                    item) \
                    + 'source components in scope: {0} '.format(self.scoped)
                logging.error(error_message)
                raise AttributeError(error_message)

            return components_with_name[0]

        if isinstance(item, int):
            return self.scoped[item]

        raise AttributeError


    def __getattr__(self, item):
        logging.debug('get attribute from indexed items, applying get attr {0} to all scoped components'.format(item))
        return_val = self.map(mutable=True, map_func=lambda x: getattr(x, item))
        # self.map(lambda x: getattr(x, item))
        return return_val


    def __call__(self, *args, **kwargs):
        return self.map(mutable=True, map_func=lambda x: x.__call__(*args, **kwargs))


    def __len__(self):
        return len(self.scoped)

    def __next__(self):
        self.current += 1
        if self.current > len(self):
            raise StopIteration
        return self.scoped[self.current]



    @property
    def copy(self):
        return Indexed(self.scoped)

    def refresh(self):
        self.scoped = self._components
        return self

    #gets the result

    @property
    def ok(self):
        components = copy.copy(self.scoped)
        # self_to_return = Indexed(components)
        # self.refresh()
        return components

    @property
    def components(self):
        return self.scoped

    def get(self, one=True):
        if len(self) == 0:
            err_message = 'Trying to get indexed component from empty index'
            logging.error(err_message)
            raise Exception(err_message)
        if one:
            if len(self) != 1:
                err_message = 'Trying to get one indexed component from index with multiple components'
                logging.error(err_message)
                logging.error('If you whish to merge the components use merge')
                logging.error('Or if you really want a list of components set the one parameter to False')
                logging.error('Current items in scope: \n{0}'.format(self._print()))
                raise Exception(err_message)
            return self[0]

        return self.scoped







    @property
    def _print(self):
        children_prints = '\n'.join([i._print for i in self])

        print_string = '\n\n' \
                        + LOG_CONSTANTS.REGION.format('INDEXED COMPONENTS') \
                        + '\nAmount: {0}'.format(len(self))  \
                        + '\nScoped: {0}\n-----\n'.format(len(self.scoped)) \
                        + children_prints \
                        + '\n-----\n' \
                        + LOG_CONSTANTS.REGION.format('INDEXED COMPONENTS END') \
                        + '\n\n'
        return print_string







