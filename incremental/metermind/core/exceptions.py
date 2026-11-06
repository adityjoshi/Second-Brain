class MeterMindError(Exception):
    pass
class UnsupportedCategoryError(MeterMindError):
    pass
class ReadingStorageError(MeterMindError):
    pass
class InvalidReadingError(MeterMindError):
    pass
class ToolError(MeterMindError):
    pass
