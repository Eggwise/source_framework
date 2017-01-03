import sys, io


class InjectImport():


    __import_source_code_execution_template = '''import inspect
{import_statement}
import_source_code = inspect.getsource({import_name})
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
    def _get_import_sourcecode(cls, import_statement, import_name):

        template_args = dict(import_statement=import_statement, import_name=import_name)
        execution_source = cls.__import_source_code_execution_template.format(**template_args)


        print('EXECUTING IMPORT STATEMENT {0}'.format(import_statement))

        # capture output
        original_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()
        exec(execution_source)
        sys.stdout = original_stdout

        import_source_code = redirected_output.getvalue()

        return import_source_code


