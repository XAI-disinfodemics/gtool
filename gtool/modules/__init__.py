import pkgutil
import importlib

__all__ = []

def _import_modules():
    """Import all modules automatically (to allow things like BaseEngine.__subclasses__()
    without explicitly importing each subclass)
    """
    prefix_len = len(__name__) + 1
    for _, module_name, is_pkg in pkgutil.iter_modules(__path__, prefix=f'{__name__}.'):
        assert not is_pkg
        module_name_without_prefix = module_name[prefix_len:]
        __all__.append(module_name_without_prefix)

        # Use importlib to import the module
        module = importlib.import_module(module_name)
        globals()[module_name_without_prefix] = module

_import_modules()
