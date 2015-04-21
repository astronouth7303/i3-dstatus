"""
Utility functions for generators.
"""
import dbus
import collections.abc
from .service import DBUS_SERVICE, PATH_PREFIX, BlockManager, Block
__all__ = 'get_manager', 'get_block', 'get_config', 'make_block'


class BlockDict(collections.abc.MutableMapping):
    """
    dict-like wrapper around block objects
    """
    def __init__(self, obj):
        super().__init__()
        self._block = obj

        # Cache
        self._block_block = self.block(Block.INTERFACE)
        self._block_prop = self.block(Block.PROPINTERFACE)

    def block(self, interface=Block.INTERFACE):
        """
        Get the block object.
        """
        return dbus.Interface(self._block, interface)

    def __getitem__(self, key):
        return self._block_prop.Get(Block.INTERFACE, key)

    def __setitem__(self, key, value):
        return self._block_prop.Set(Block.INTERFACE, key, value)

    def __delitem__(self, key):
        raise TypeError("Can't delete keys on a BlockDict")

    def __iter__(self):
        for name in self._block_prop.GetAll(Block.INTERFACE).keys():
            yield name

    def __len__(self):
        return len(self._block_prop.GetAll(Block.INTERFACE))

    # Optional performance methods

    def update(self, other):
        self._block_block.Update(other)

    # TODO: Wrap items() so that it doesn't make repeated d-bus calls for values


def get_manager():
    return dbus.Interface(
        dbus.SessionBus().get_object(DBUS_SERVICE, PATH_PREFIX),
        BlockManager.INTERFACE
    )


def get_block(bpath):
    return BlockDict(dbus.SessionBus().get_object(DBUS_SERVICE, bpath))


def get_config(app):
    k5dstatus = get_manager()
    return k5dstatus.GetConfig(app)


class make_block:
    """
    Boilerplates the creation and cleanup of a block.

    >>> with make_block('spam', {}) as bgen:
    ...     block = bgen()
    ...     pass  # More code

    (We use the callable so that if the lookup fails, the finally triggers)
    """

    def __init__(self, **defaults):
        self.defaults = defaults or {}
        self.service = dbus.Interface(
            dbus.SessionBus().get_object(DBUS_SERVICE, PATH_PREFIX),
            BlockManager.INTERFACE
        )

    def __enter__(self):
        self.blockpath = bpath = self.service.CreateBlock(self.defaults)
        return lambda: get_block(bpath)

    def __exit__(self, *_):
        self.service.RemoveBlock(self.blockpath)
