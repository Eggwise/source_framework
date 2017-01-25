import sys, io, re
from ...models.components import IndexedItem, Source, SourceComponent, SourceComponentContainer, SourceFile
from ...models.indexer import Indexed
import inspect


class InjectImport():
    from ...models.components import IndexedItem, Source, SourceComponent, SourceComponentContainer

    __import_source_code_execution_template = '''import inspect
{import_statement}
module_file = inspect.getsourcefile({import_name})
import_source_code = inspect.getsource({import_name})
print(module_file)
print(import_source_code)
    '''


    def inject_imports(cls, source):
        default_import_name = 'palla'
        new_lines = []
        for index, line in enumerate(source):
            if 'import' in line:
                if 'as' in line:
                    import_name = line.split('as')[-1]
                else:
                    line = line.strip()
                    line += ' as {0}'.format(default_import_name)
                    import_name = default_import_name

                injected_source_code = cls._get_import_sourcecode(line, import_name)
                new_lines.extend(injected_source_code.splitlines(keepends=True))

        return ''.join(new_lines)



    @classmethod
    def _extract_imports(cls, import_statement):
        import_statement = import_statement.strip()

        if 'import ' not in import_statement:
            # raise Exception('Not an import statement: {0}'.format(import_statement))
            return []

        if len(re.findall('=|#|if|[0-9]|\(\)', import_statement)) > 0:
            return []

        #one import with custom name
        if 'as' in import_statement:

            import_name = import_statement.split('as')[-1]
            get_source_import_statement = import_statement

            return [(import_name, get_source_import_statement)]



        import_statement = import_statement.strip()
        import_names = import_statement.split('import ')[1]

        #multiple imports in one line
        if ',' in import_names:
            import_names = import_names.split(',')[1:]
            import_names = list(map(lambda x: x.strip(), import_names))
            imports = []
            for import_name in import_names:
                get_source_import_statement = import_statement.split('import')[0].strip() + ' import ' + import_name
                get_source_import_statement = get_source_import_statement.strip()
                imports.append((import_name, get_source_import_statement))

            return imports

        #one import
        import_name = import_statement.split('import ')[1].strip()
        get_source_import_statement = import_statement.strip()
        return [(import_name, get_source_import_statement)]



    @classmethod
    def _get_import(cls, import_name, import_statement):

        template_args = dict(import_statement=import_statement, import_name=import_name)
        execution_source = cls.__import_source_code_execution_template.format(**template_args)

        print('EXECUTING IMPORT STATEMENT {0}'.format(import_statement))

        execution_output = cls._capture_execution(execution_source)
        execution_output = Source(execution_output)

        module_path = execution_output[0]
        import_source = execution_output[1:]

        return Source(import_source), module_path


    @classmethod
    def get_imports(cls, source_components):

        if isinstance(source_components, Source) or isinstance(source_components, SourceFile):
            source_components = [source_components]
        extracted_imports = []
        for sc in source_components:
            try:
                if isinstance(sc, Source):
                    source = sc
                elif isinstance(sc, SourceComponent):
                    source = sc.source
                elif isinstance(sc, str):
                    source = sc
                else:
                    continue

                for line in source:
                    imports_from_line = cls._extract_imports(line)
                    extracted_imports.extend(imports_from_line)

            except Exception as e:
                raise(e)

        unique_imports = list(set(extracted_imports))
        all_imports = []
        for i_name, i_statement in unique_imports:
            import_source, module_path = cls._get_import(i_name, i_statement)
            all_imports.append(import_source)
        return all_imports



    @staticmethod
    def _capture_execution(source_code):
        # capture output
        original_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()
        exec(source_code)
        sys.stdout = original_stdout

        captured_output = redirected_output.getvalue()
        return captured_output



