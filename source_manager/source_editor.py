from .source_indexer import SourceIndexer

class EditorBase():
    pass

class FileEditor(EditorBase):

    def __init__(self, file, indexed):
        if isinstance(indexed, SourceIndexer):
            self.indexer = indexed
        else:
            self.indexer = SourceIndexer.from_components(indexed)

        self.file = file

    @property
    def items(self):
        return self.indexer.items.at(self.file)


    def __getattr__(self, item):
        self.items.filter(item)