from .source_indexer import SourceIndexer
from ..models.components import IndexedItem
from ..models.indexer import Index
from ..main import indexer

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

    def split(self):

        items_positions = list(sorted([(i.line_start, i.line_end) for i in self.items], key=lambda x: x[0]))
        if len(items_positions) ==0:
            return None

        last_item = (0, 0)
        items_in_between = []
        for i in items_positions:
            new_item = (last_item[1], i[0])
            items_in_between.append(new_item)
            last_item = i
        new_item = (last_item[1], len(self.file))
        items_in_between.append(new_item)



        items_in_between = [IndexedItem('_', self.file, start, end, None) for start, end in items_in_between]

        all_items = [*self.items, *items_in_between]

        return list(sorted(all_items, key=lambda x: x.line_start))


    def __getattr__(self, item):
        self.items.filter(item)


