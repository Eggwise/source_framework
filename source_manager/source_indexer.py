import inspect
import logging
import os
import re
import pathlib

from ..models.indexer import Index, Indexed, Indices, Printable

from ..models.components import IndexedFile, SourceFile, IndexedItem, Source, SourceComponentContainer, Project, \
    IndexedSourceComponent
from ..utils.utils import find_dirs, merge, LOG_CONSTANTS
from ..utils import framework_manager


class SourceIndexerBase:
    CALLER_DIR = None

    @classmethod
    def prepare(cls, init_config):

        caller_path = init_config['caller_path']
        caller_dir = os.path.dirname(caller_path)
        logging.info('PREPARE SOURCE INDEXER')
        logging.info('-------------------------')
        logging.info('Source indexer initialized from script at: >> {0} <<'.format(caller_path))
        logging.info('The following dir will be used to search the root config from: >> {0} <<'.format(caller_dir))

        SourceIndexerBase.CALLER_DIR = caller_dir
        return cls

    _config = {
        # root config for identifying the root config file in the workspace
        'config': {
            'identifier': '.config$'
        },
        'root_config_name': 'root.config',
        'root_config_folder': '{home}/.source_framework'
    }

    @classmethod
    def _search_root_config(cls, start_path):
        config_identifier = cls._config['config']['identifier']
        root_config_name = 'root'
        root_config_identifier = root_config_name + config_identifier

        root_dir_search = find_dirs(start_path, root_config_identifier)
        if len(root_dir_search) == 0:
            error_message = '\n--------------\nNO ROOT CONFIG\nCould not find root config file\nSearched upwards from {0} \n'.format(
                start_path) + \
                            '--------------\nIf this is a new project, use the generator to generate the neccesary root and base config files' \
                            '\n\nsourceframework.generate.new_project()'
            logging.error(error_message)
            raise Exception(error_message)
        root_config_path = root_dir_search[0]

        logging.info('Root config found at: {0}'.format(root_config_path))
        return root_config_path

    @classmethod
    def _get_root_config_path(cls):
        logging.info('Searching for root config path..')
        logging.info('Walking up from the dir: {0}'.format(cls.CALLER_DIR))
        indexer_location = cls.CALLER_DIR

        root_config_path = cls._search_root_config(indexer_location)
        return root_config_path

    @classmethod
    def _get_root_dir(cls):
        return os.path.dirname(cls._get_root_config_path())

    @classmethod
    def _get_root_config(cls):
        logging.info('Getting the root config..')
        root_config_path = cls._get_root_config_path()
        # extract the name from the root config
        # using the hardcoded index described in the config attribute of the class

        root_config_name = SourceFile.extract_name(root_config_path, cls._config['config']['identifier'])

        # if ever this assertion fails... something is terribly wrong
        assert root_config_name == 'root'
        return SourceFile(root_config_name, root_config_path)

    @classmethod
    def _get_paths_by_identifiers(cls, identifiers: list):
        root_dir = cls._get_root_dir()

        logging.info('searching for matching paths using the following identifiers: {0}'.format(identifiers))

        if len(set(identifiers)) < len(identifiers):
            print('WARNING: CHECKING FOR MATCHES WITH SAME IDENTIFIER')
            print('YOU WILL LOSE YOUR INDEX')
            print('YOU PROBABLY NEED TO WRITE A NEW METHOD IF YOU NEED TO INDEX MULTIPLE INDICES WITH SAME IDENTIFIER')

        matches_by_identifier = {k: [] for k in identifiers}
        for path, dirs, files in os.walk(root_dir):
            for identifier in identifiers:
                matches = [os.path.join(path, i) for i in dirs + files if str(i).endswith(identifier)]
                matches_by_identifier[identifier].extend(matches)
        logging.info('found {0} matches.'.format(len(matches)))
        return matches_by_identifier

    @classmethod
    def _get_indices(cls):
        logging.info('Retrieving indices')
        # get identifiers

        logging.info('------------------')
        root_config_file = cls._get_root_config()

        base_config_file = cls._get_or_create_base_config()
        root_config = merge( base_config_file.yaml, root_config_file.yaml)



        if 'index' not in root_config:
            msg = 'Error: missing index configuration in root config.\ncheck the config at: {0}'.format(root_config_file.path) + '\nOr the base config at: {0}'.format(base_config_file.path)
            raise Exception(msg)

        root_index_config = root_config['index']

        if 'identifiers' not in root_index_config:
            msg = 'MISSING IDENTIFIERS FOR INDICES TYPES IN ROOT INDEX CONFIG\n turn on logging to see more..'
            logging.error(msg)
            raise AttributeError(msg)

        types_with_identifiers = root_index_config['identifiers'].items()
        # flip
        identifiers_with_types = {v: k for k, v in types_with_identifiers}

        # get identifier list
        identifiers = [v for k, v in root_index_config['identifiers'].items()]
        index_types = list(set(root_index_config['types']))

        if len(identifiers) > len(index_types):
            msg = 'NO INDEX TYPES DEFINED FOR THE IDENTIFIERS IN THE ROOT INDEX CONFIG\n\nthe following index types are defined\n' \
                  '{0}'.format(index_types) + \
                  '\nthe following identifiers are defined: {0}\n'.format(root_index_config['identifiers'].items()) + \
                  'Check your root config file at: {0}'.format(root_config_file.path)
            logging.error(msg)
            raise Exception(msg)

        if len(identifiers) < len(index_types):
            msg = 'NO IDENTIFIERS DEFINED FOR THE INDEX TYPES IN THE ROOT INDEX CONFIG\n\nthe following index types are defined\n' \
                  '{0}'.format(index_types) + \
                  '\nthe following identifiers are defined: {0}\n'.format(root_index_config['identifiers'].items()) + \
                  'Check your root config file at: {0}'.format(root_config_file.path)
            logging.error(msg)
            raise Exception(msg)

        logging.info('root config OK!')
        logging.info('------------------')
        logging.info('searching for index configuration files...')
        indices = []

        # get paths of index config files
        indexed_paths = cls._get_paths_by_identifiers(identifiers)

        # retrieve config files
        logging.info('------------------')
        for identifier, paths in indexed_paths.items():
            # order them by type
            # indices_by_type[identifiers_with_types[identifier]] = paths
            for p in paths:
                index_config_file = SourceFile.from_path(path=p, identifier=identifier)
                index = Index(identifiers_with_types[identifier], index_config_file)
                logging.info('found index: {0}'.format(index))
                indices.append(index)
        logging.info('------------------')
        # merge parent configs for indices
        # order root configs by type
        base_index_configs = {i.index_type: i for i in indices if i.name == 'root'}

        if len(base_index_configs) != len(index_types):
            msg = 'MISSING BASE CONFIG FILES FOR {0}\n'.format(
                [i for i in index_types if i not in base_index_configs]) + \
                  'Make sure you have a base index config named root somewhere in your workspace\n' \
                  'Root index config files are needed to inherit from in your custom index files\n' \
                  'You need the following root config files:\n{0}'.format(
                      '\n'.join(['root{0}'.format(i) for i in identifiers]))
            logging.error(msg)
            raise Exception(msg)

        child_indices = [i for i in indices if i.name != 'root']

        logging.info('Found the base index config files:\n{0}'.format(
            '\n'.join([i._print for i in indices if i.name == 'root'])))

        if len(child_indices) == 0:
            msg = 'NO INDEX CONFIG FILES FOUND!\n' \
                  'Have you created any?\nto create a new index use: source_framework.generate.file_index()\n' \
                  'To enable logging, use source_framework.enable_logging()'
            logging.error(msg)
            raise Exception(msg)

        logging.info('Found the child index config files:\n{0}'.format(
            '\n'.join([i._print for i in child_indices])))

        logging.info('Merging the configs..')
        logging.info('------------------')

        child_indices = [i for i in indices if i.name != 'root']
        merged_indices = []
        for index in child_indices:
            parent_config = base_index_configs[index.index_type]

            # TODO
            merged_config_dict = merge(parent_config.config, index.config)
            merged_index_config = SourceFile(name=index.name, path=index.config_file.path,
                                             source=Source.from_yaml(merged_config_dict))

            index = Index(name=index.name, index_type=index.index_type, config_file=merged_index_config)
            merged_indices.append(index)

        logging.info('\n--------------\nGET INDICES COMPLETE\n--------------')
        return Indices(merged_indices)

    @classmethod
    def _get_index_paths(cls, indices: Indices):

        ignore_indices = [i for i in indices if i.index_type == 'ignore']
        for i in ignore_indices:

            if not isinstance(i.identifier, str):
                error_message = 'trying to index files using non file indices \n' \
                                + 'are you sure the index config file is correct ?\n' \
                                + 'for files use a string as identifier\n' \
                                + 'Indices used: \n{0}'.format(indices._print)
                logging.error(error_message)
                raise Exception(error_message)

            if 'identifier' not in i.config:
                print('NO IDENTIFIER FOR INDEX: {0}'.format(i.name))
                raise Exception()
            ##TODO
            identifiers_with_indices[i.identifier] = i
        assert isinstance(indices, Indices)
        # indices = []
        indexed_paths = cls._get_paths_by_identifiers(list(identifiers_with_indices.keys()))

        # GET FILE PATHS

        identifiers_with_indices = {}
        assert all(list(map(lambda x: x.index_type == 'file', indices)))

        ## for now just do the file types and get the items from the files later
        file_indices = [i for i in indices if i.index_type == 'file']
        # file_indices = [i for i in indices]
        for i in file_indices:

            if not isinstance(i.identifier, str):
                error_message = 'trying to index files using non file indices \n' \
                                + 'are you sure the index config file is correct ?\n' \
                                + 'for files use a string as identifier\n' \
                                + 'Indices used: \n{0}'.format(indices._print)
                logging.error(error_message)
                raise Exception(error_message)

            if 'identifier' not in i.config:
                print('NO IDENTIFIER FOR INDEX: {0}'.format(i.name))
                raise Exception()
            ##TODO
            identifiers_with_indices[i.identifier] = i
        assert isinstance(indices, Indices)
        # indices = []
        indexed_paths = cls._get_paths_by_identifiers(list(identifiers_with_indices.keys()))

    @classmethod
    def index_all(cls, indexer) -> Indexed:
        raise NotImplemented


    @classmethod
    def _get_base_folder_path(cls):
        config_folder_args = {

        }
        logging.info('Project indexer: find root config')
        home_folder = pathlib.Path.home()
        config_folder_args['home'] = str(home_folder)

        root_config_folder = cls._config['root_config_folder']
        root_config_folder_path = root_config_folder.format(**config_folder_args)
        return root_config_folder_path

    @classmethod
    def _get_or_create_base_config(cls):

        root_config_folder_path = cls._get_base_folder_path()

        if not os.path.exists(root_config_folder_path):
            try:
                os.mkdir(root_config_folder_path)
            except Exception as e:

                logging.error('ERROR creating root config folder')
                raise e

                # place root config file in folder

        root_config_name = cls._config['root_config_name']
        root_config_file_path = os.path.join(root_config_folder_path, root_config_name)

        if not os.path.exists(root_config_file_path):
            logging.info('Root file not found at{0}'.format(root_config_file_path))
            root_config_source = cls._generate_base_config()
            logging.info('Root file generated')
            root_config_file = root_config_source.to_file(path=root_config_file_path)
            root_config_file.do.save()
        else:
            root_config_file = SourceFile.from_path(root_config_file_path)

        return root_config_file


    @staticmethod
    def _generate_base_config():

        base_config = framework_manager.config.base.get_file('base.config').yaml

        return Source.from_yaml(base_config)
class FileIndexer(SourceIndexerBase):
    @classmethod
    def _index_files(cls, indices: Indices):
        identifiers_with_indices = {}
        assert all(list(map(lambda x: x.index_type == 'file', indices)))

        ## for now just do the file types and get the items from the files later
        file_indices = [i for i in indices if i.index_type == 'file']
        # file_indices = [i for i in indices]
        for i in file_indices:

            if not isinstance(i.identifier, str):
                error_message = 'trying to index files using non file indices \n' \
                                + 'are you sure the index config file is correct ?\n' \
                                + 'for files use a string as identifier\n' \
                                + 'Indices used: \n{0}'.format(indices._print)
                logging.error(error_message)
                raise Exception(error_message)

            if 'identifier' not in i.config:
                print('NO IDENTIFIER FOR INDEX: {0}'.format(i.name))
                raise Exception()
            ##TODO
            identifiers_with_indices[i.identifier] = i
        assert isinstance(indices, Indices)
        # indices = []
        indexed_paths = cls._get_paths_by_identifiers(list(identifiers_with_indices.keys()))

        files = []
        for identifier, paths in indexed_paths.items():

            # order them by type
            # indices_by_type[identifiers_with_types[identifier]] = paths
            for p in paths:
                index = identifiers_with_indices[identifier]
                assert isinstance(index, Index)
                indexed_index_file = IndexedFile.from_path(path=p, index=index)
                files.append(indexed_index_file)

        return Indexed(files)

    @property
    def files(self):
        def filter_func(comp):
            if isinstance(comp, IndexedSourceComponent):
                return comp.index.index_type == 'file'
            else:
                return False

        return self.filter(filter_func)

    @classmethod
    def index_all(cls, indexer):
        file_indices = indexer.indices.file.ok
        file_indices.log()

        all_indexed_files = indexer._index_files(file_indices)
        all_indexed_files.log()
        return all_indexed_files


class ItemIndexer(FileIndexer):



    @staticmethod
    def parse_identifier_arguments(identifier_arguments, identifier_string, start=True):
        # get the tags from the identifier string,
        # some of the tags are named with the following format->  {tag:name}

        identifier_tags = re.findall('{([a-z:_.A-Z]*)}', identifier_string)

        named_regex_template = '(?P<{name}>{regex})'
        format_arg_dict = {}

        for an in identifier_tags:
            arg, *arg_name = an.split(':')

            if arg not in identifier_arguments:
                if start:
                    raise KeyError('MISSING ARGS FOR {0}'.format(arg))
                else:
                    # if this is the end tag, then the named tags in the start identifier
                    # will be injected after extracting the item from the source
                    # so for now keep keep the {name} in the string
                    identifier_arguments[arg] = '{' + str(arg) + '}'

            if arg_name:
                arg_name = arg_name[0]
                # replace the named arg so the string can be formatted
                identifier_string = identifier_string.replace(':{0}'.format(arg_name), '')
                arg_value = named_regex_template.format(name=arg_name, regex=identifier_arguments[arg])
            else:
                arg_value = identifier_arguments[arg]

            format_arg_dict[arg] = arg_value

        # return identifier_string, format_arg_dict
        identifier = identifier_string.format(**format_arg_dict)
        return identifier

    @classmethod
    def _extract_items(cls, indexed_file: IndexedFile, indices: Indices):
        logging.info('Extracting items from:')
        # logging.info(LOG_CONSTANTS.REGION.format('EXTRACT ITEMS'))
        indexed_file.log()
        all_extracted_items = []
        # TODO VALIDATE ?
        for i in indices:
            if i.index_type != 'item':
                logging.error('Trying to extract items from non item index: {0}'.format((i.name, i.index_type)))
            assert i.index_type == 'item'
            config = i.config
            parse_tags = config['parse_tags']
            identifier_start_config = i.identifier['start']

            # TODO does this work???
            if 'end' in config['identifier']:
                identifier_end_config = i.identifier['end']
            else:
                logging.info('NO END TAG PROVIDED')
                logging.info('getting default end identifier tag from root.item.index')
                if 'end_default' not in parse_tags:
                    error_message = 'Could not find default end identifier tag'
                    logging.error(error_message)
                    raise Exception(error_message)
                identifier_end_config = parse_tags['end_default']

            format_arg_values = merge(config, parse_tags)

            start_identifier = cls.parse_identifier_arguments(format_arg_values, identifier_start_config)
            # NOT SURE IF THE SAME END IDENTIFIER AS START_IDENTIFIER WORKS
            end_identifier = cls.parse_identifier_arguments(format_arg_values, identifier_end_config, False)

            extracted_items = cls._extract_items_from_source(start_identifier, end_identifier, indexed_file, i)
            all_extracted_items.extend(extracted_items)
        logging.info('found {0} items'.format(len(all_extracted_items)))
        logging.info('\n')
        return all_extracted_items

    @staticmethod
    def _extract_items_from_source(start_match_regex, end_match_regex, indexed_file: IndexedFile, item_index: Index):
        source = indexed_file.source

        def get_line_number(the_match):
            return source.count("\n", 0, the_match.start()) + 1

        # loop over start matches and get the corresponding end match
        # then create item
        items = []

        start_matches = re.finditer(start_match_regex, source)

        for start_match in start_matches:
            line_start = get_line_number(start_match)
            match_props = start_match.groupdict()
            # print(end_match_regex)

            try:
                end_regex = end_match_regex.format(**match_props)
            except Exception:
                error_message = 'could not format the end tag using the named tags in the start identifier\n' \
                                'Tried to format the string: {0} using the available arguments: {1}\n'.format(
                    end_match_regex, match_props) \
                                + 'If you dont want to use a end identifier leave the end attribute empty in ' \
                                  'the identifier options in your index config \nthe standard end identifier in the ' \
                                  'root item index config will be used.. normally matching 1 or more whitespaces ( {ws}+ )'

                logging.error(error_message)
                raise Exception(error_message)
            # check for end of item matches
            assert isinstance(source, Source)

            source_from_start_match = source[line_start:]

            line_end = None
            for index, line in enumerate(source_from_start_match):
                if re.match(end_regex, line):
                    line_end = line_start + index
                    break
            if line_end is None:
                # No end tag found for dependency section
                error_message = 'Could not find end of item with match props: {0}\nstart regex: {1}\nend regex: {2}'.format(
                    match_props, start_match_regex, end_regex)
                logging.error(error_message)

                raise Exception(error_message)

            # TODO cleanup
            if 'name' not in match_props:
                # error_message = 'a name must be defined for an item index\n' \
                #                 'include the name tag {name} somewhere in the start identifier string for matching' \
                #                 'available variables {0}'.format(match_props) + \
                #                 'NOTE: the tags in the start identifier are available in the end identifier'
                # logging.error(error_message)
                match_props['name'] = '_'
                # raise AttributeError(error_message)

            name = match_props['name']
            del (match_props['name'])

            item = IndexedItem(name, indexed_file, line_start, line_end, item_index, properties=match_props)
            items.append(item)

        return items


class ProjectIndexer(SourceIndexerBase):


    @classmethod
    def _index_projects(cls):
        base_config_file = cls._get_or_create_base_config()

        base_config = Project.from_path(base_config_file.path)
        project_config = Project(cls._get_root_config())

        project_paths = []
        unique_projects = []
        all_projects = [*project_config.with_dependencies(), *base_config.with_dependencies()]

        while len(all_projects) != 0:
            p = all_projects.pop()
            if p.path in project_paths:
                continue
            project_paths.append(p.path)
            unique_projects.append(p)
        return Indexed(unique_projects)

    @classmethod
    def index_all(cls, indexer):
        return cls._index_projects()


# @pretty_print
class SourceIndexer(ItemIndexer, ProjectIndexer, Printable, SourceComponentContainer):
    TIMES_INDEXED = 0

    _all_indexed = None

    def __init__(self, indices: Indices = None, scoped: Indexed = None, index_all=True):
        self.indices = indices or self._get_indices()
        if index_all:
            SourceIndexer._all_indexed = self._index_all()

        self.scoped = scoped or SourceIndexer._all_indexed
        self.current = 0



    def __getattr__(self, name):
        return self.filter(lambda x: x.match(name))

    def __getitem__(self, item):
        if isinstance(item, slice):
            self.scoped = Indexed(self.scoped[item.start, item.stop])
            return self

        logging.debug('get item {0} from source indexer, passing it to the scoped indexed components'.format(item))
        return self.scoped[item]

    def __add__(self, other):

        if isinstance(other, SourceFile):
            extracted_items = self._extract_items(other, indices=self.indices.item)
            self.components.extend(extracted_items)

        return self

    @property
    def file(self):
        #NEW API
        return self.files.one

    @property
    def copy(self):
        return SourceIndexer(indices=Indices(self.indices.scoped), scoped=Indexed(self.scoped), index_all=False)


    def _index_all(self):

        def check_second_time():
            SourceIndexer.TIMES_INDEXED += 1
            if SourceIndexer.TIMES_INDEXED > 1:
                error_message = 'indexing all the source for the second time, why???'
                logging.error(error_message)
                raise Exception(error_message)

        logging.info(LOG_CONSTANTS.REGION.format('INDEXING ALL SOURCE'))
        # self.indices.refresh()
        try:
            item_indices = self.indices.item.ok
        except AttributeError as e:
            logging.info('Tried retrieving item indices but none where available.')
            logging.info('Exception, thrown: {0}'.format(e))
            logging.info('------\nskip item indexing.')
            item_indices = None

        all_indexed_files = FileIndexer.index_all(self)

        # TODO
        all_indexed_items = []
        if item_indices is not None:
            for file in all_indexed_files:

                logging.info('Extracting items from: {0}'.format(file))

                indexed_items = self._extract_items(file, item_indices)
                all_indexed_items.extend(indexed_items)

        # index projects
        indexed_projects = ProjectIndexer.index_all(self)

        all_indexed = Indexed(all_indexed_items, all_indexed_files, indexed_projects)
        logging.info(LOG_CONSTANTS.REGION.format('INDEXING END'))
        logging.info(
            'indexed {0} source components using {1} indices'.format(len(all_indexed), len(self.indices)))

        return all_indexed

    @property
    def _print(self):
        return LOG_CONSTANTS.REGION_IDENTIFIER \
               + LOG_CONSTANTS.REGION.format('SOUCE_INDEXER') \
               + LOG_CONSTANTS.LINE.format('Amount of indices: {0}'.format(len(self.indices))) \
               + LOG_CONSTANTS.LINE.format(
            'Total amount of indexed source components: {0}'.format(len(self.all_indexed))) \
               + LOG_CONSTANTS.LINE.format('source components in scope: {0}'.format(len(self.scoped))) \
               + LOG_CONSTANTS.LINE.format(LOG_CONSTANTS.REGION.format('SOUCE_INDEXER END')) \
               + LOG_CONSTANTS.REGION_IDENTIFIER

    def refresh(self):
        self.indices.refresh()
        self.scoped = self.all_indexed
        return self

    @property
    def count(self):
        return len(self.scoped)

    def __len__(self):
        return len(self.scoped)

    def list(self):
        print(LOG_CONSTANTS.REGION.format('LIST INDEXED COMPONENTS'))
        for i in self:
            if hasattr(i, '_print'):
                i.print()
            else:
                print(i)

        print(LOG_CONSTANTS.REGION.format('LIST INDEXED COMPONENTS END'))
        pass

    def at_path(self, path, temp_index=False, mutable=False):

        if temp_index:
            # create index
            # create indexed file
            # index the items in this file
            # add to scope
            raise NotImplementedError
            pass

        if mutable:
            return_val = self
        else:
            return_val = self.copy

        return_val = return_val.filter(lambda x: x.path == path, mutable)
        # print(return_val.ok)
        if len(return_val) == 0:
            error_message = 'Trying to get indexed components with path: {0}\n' \
                            'But no indexed components could be found with the current indices\n' \
                            'Are you sure you are calling from_this() from within an indexed file?\n' \
                            'Available indices: \n{1}'.format(path, self.indices._print)
            logging.error(error_message)
            raise Exception(error_message)

        return return_val

    def by_path(self, path):
        return self.filter(lambda x: x.path == path)

    @property
    def items(self):
        def filter_func(comp):
            if isinstance(comp, IndexedSourceComponent):
                return comp.index.index_type == 'item'
            else:
                return False

        return self.filter(filter_func)

    @property
    def projects(self):
        return self.filter(lambda x: isinstance(x, Project))

    @property
    def components(self):
        return self.scoped.components

    @property
    def here(self):
        (frame, script_path, line_number,
         function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]
        # print(script_path)
        return self.at_path(script_path)

    def at(self, *source_components):
        # TODO file indexer at DIR

        source_components = Indexed(*source_components)
        source_components_with_paths = []
        for c in source_components:

            # for now compare with path, later check folder too
            for s in self.scoped:
                if s.is_at(c):
                    if s not in source_components_with_paths:
                        source_components_with_paths.append(s)

        instance = SourceIndexer(scoped=Indexed(*source_components_with_paths), index_all=False)
        return instance

    def extract_items(self, keep_scope=True):
        # TODO TEST
        files = self.files.get(one=False)
        indices = self.indices.item.ok

        extracted_items = [self._extract_items(f, indices) for f in files]
        self.scoped = Indexed(extracted_items)
        return self

    @staticmethod
    def from_project(project: Project):
        SourceIndexer.all_indexed = None
        root_dir = project.config.folder.path
        SourceIndexerBase.CALLER_DIR = root_dir
        return SourceIndexer()

    @staticmethod
    def from_components(source_components):
        indexer = SourceIndexer(scoped=source_components, index_all=False)
        return indexer

