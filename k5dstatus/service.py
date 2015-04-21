"""
Defines and manages d-bus services and objects.
"""
import dbus
import dbus.service
import threading
import xml.etree.ElementTree as etree
from aioevents import Event

DBUS_SERVICE = 'com.astro73.k5dstatus'
PATH_PREFIX = '/com/astro73/k5dstatus'


class BlockManager(dbus.service.Object):
    """
    Manages block objects.

    FIXME: Implement org.freedesktop.DBus.ObjectManager
    """
    INTERFACE = 'com.astro73.k5dstatus.Manager'

    blockchanged = Event("Fires when one of the managed blocks changes.")
    blockadded = Event("Fires when a new block is added.")
    blockremoved = Event("Fires when a block is removed.")

    def __init__(self, config):
        bus_name = dbus.service.BusName(DBUS_SERVICE, bus=dbus.SessionBus())
        super().__init__(bus_name, PATH_PREFIX)
        self.blocks = {}

        # cache the config
        self.config = config

        # Can't do this statically due to instances
        self.blockchanged.handler(self.BlockChanged)

    @dbus.service.signal(INTERFACE, signature="o")
    def BlockChanged(self, block):
        pass

    @dbus.service.method(INTERFACE, in_signature="a{sv}", out_signature="o")
    def CreateBlock(self, defaults):
        """
        Create a block with the given ID and return it.
        """

        if 'name' in defaults:
            bid = defaults['name'].replace('-', '')
        else:
            bid = "block"

        if bid in self.blocks:
            i = 1
            while bid+i in self.blocks:
                i += 1
            bid = bid+i

        self.blocks[bid] = blk = Block(bid, defaults)
        blk.changed.handler(lambda: self.blockchanged(blk))

        self.blockadded(blk)

        return blk

    @dbus.service.method(INTERFACE, in_signature="o")
    def RemoveBlock(self, blockpath):
        """
        Remove a block.
        """
        id = blockpath[len(PATH_PREFIX)+1:]
        block = self.blocks[id]
        # XXX: Will dbus hand us a real object or just a path?
        block.remove_from_connection()
        del self.blocks[id]
        self.blockremoved(block)

    def __iter__(self):
        """
        Yield the blocks in their defined order
        """
        for block in sorted(self.blocks.values(), key=lambda b: b.order):
            yield block

    @dbus.service.method(INTERFACE, in_signature='s', out_signature='v')
    def GetConfig(self, genname):
        """
        Get a generator's configuration block
        """
        if genname in self.config:
            return self.config[genname]
        else:
            return dbus.Dictionary(signature='sv')


class Block(dbus.service.Object):
    """
    A single block in i3bar.

    Doc strings blatently ripped from http://i3wm.org/docs/i3bar-protocol.html

    FIXME: Implement org.freedesktop.DBus.Properties
    """
    INTERFACE = 'com.astro73.k5dstatus.Block'
    PROPINTERFACE = 'org.freedesktop.DBus.Properties'
    __properties__ = {
        'full_text' : ('s', lambda v: isinstance(v, str)),
        'short_text': ('s', lambda v: isinstance(v, str)),
        'color'     : ('s', lambda v: isinstance(v, str)),
        'min_width' : ('v', lambda v: isinstance(v, (int, str)) and (v >= 0 if isinstance(v, int) else True)),
        'align'     : ('s', lambda v: v in ('left', 'center', 'right')),
        'name'      : ('s', lambda v: isinstance(v, str)),
        'instance'  : ('s', lambda v: isinstance(v, str)),
        'urgent'    : ('b', lambda v: isinstance(v, bool)),
        'separator' : ('b', lambda v: isinstance(v, bool)),
        'separator_block_width': ('u', lambda v: isinstance(v, int) and v >= 0),
        'markup'    : ('s', lambda v: v in ('pango', 'none')),
        # Not in the spec; used for our purposes
        'order'     : ('i', lambda v: isinstance(v, int)),
        }

    full_text = ""
    short_text = ""
    color = ""
    min_width = 0
    align = "left"
    name = ""
    instance = ""
    urgent = False
    separator = True
    separator_block_width = 9
    markup = 'none'
    order = 0

    changed = Event("Raised when a property is set")

    def __init__(self, id, props):
        bus_name = dbus.service.BusName(DBUS_SERVICE, bus=dbus.SessionBus())
        super().__init__(bus_name, '{}/{}'.format(PATH_PREFIX, id))

        self.id = id

        # Slight misnomer. Only locks out changed events. Doesn't actually prevent other changes.
        self._change_lock = threading.Lock()  # XXX: Use asyncio.Lock? Only if .update() is a coroutine

        self._props = {}

        # We can safely ignore the events this generates, because nobody's had the chance to attach to our events yet.
        self.Update(props)

    @dbus.service.signal(INTERFACE, signature="iiu")
    def Click(self, x, y, button):
        pass

    # @dbus.service.method(INTERFACE, in_signature='s', out_signature='v')
    # def Get(self, name):
    #     """
    #     Gets a property.
    #     """
    #     return getattr(self, name)

    # @dbus.service.method(INTERFACE, in_signature='sv')
    # def Set(self, name, value):
    #     """
    #     Sets a property.
    #     """
    #     setattr(self, name, value)

    @dbus.service.method(INTERFACE, in_signature='a{sv}')
    def Update(self, values):
        """
        Performs a bulk update of properties. Issues only one changed event for
        the entire update.
        """
        # XXX: Rewrite to validate without fragile locks
        with self._change_lock:
            for prop, value in values.items():
                if prop in self.__properties__:
                    setattr(self, prop, value)
                else:
                    self._props[prop] = value
        self.changed()
        self.PropertiesChanged(self.INTERFACE, values, [])

    def _changed(self, name, value):
        """
        Raise a changed event, unless it's been locked out by update()
        """
        have_lock = self._change_lock.acquire(blocking=False)
        if have_lock:
            self._change_lock.release()
            self.changed()
            if not name.startswith('_'):
                self.PropertiesChanged(self.INTERFACE, {name: value}, [])

    def __setattr__(self, name, value):
        if name in self.__properties__:
            _, validate = self.__properties__[name]
            if not validate(value):
                raise ValueError("Validation failed")
            self._changed(name, value)
        super().__setattr__(name, value)

    @dbus.service.method(INTERFACE, in_signature='s', out_signature='v')
    def GetProp(self, name):
        """
        Gets a user-defined property.
        """
        return self._props.get(name)

    @dbus.service.method(INTERFACE, in_signature='sv')
    def SetProp(self, name, value):
        """
        Sets a user-defined property.
        """
        self._props[name] = value
        self._changed(name, value)

    def json(self):
        """
        Convert this object to built-in types only.
        """
        rv = {
            prop: getattr(self, prop)
            for prop in self.__properties__
            if prop in vars(self)
        }
        rv.update(self._props)
        return rv

    # I have to do this because dbus-python doesn't support properties.
    # Maybe gio's version does?

    @dbus.service.method(PROPINTERFACE, in_signature='ss', out_signature='v')
    def Get(self, interface_name, property_name):
        if interface_name in (self.INTERFACE, ''):
            return getattr(self, property_name)
        else:
            raise TypeError("Unknown interface {}".format(interface_name))

    @dbus.service.method(PROPINTERFACE, in_signature='ssv')
    def Set(self, interface_name, property_name, value):
        if interface_name in (self.INTERFACE, ''):
            return setattr(self, property_name, value)
        else:
            raise TypeError("Unknown interface {}".format(interface_name))

    @dbus.service.method(PROPINTERFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface_name):
        if interface_name in (self.INTERFACE, ''):
            return {
                name: getattr(self, name)
                for name in self.__properties__
            }
        else:
            raise TypeError("Unknown interface {}".format(interface_name))

    @dbus.service.signal(PROPINTERFACE, signature="sa{sv}a{sv}")
    def PropertiesChanged(
        self, interface_name, changed_properties, invalidated_properties
    ):
        pass

    # This exists doubly because dbus-python is lame
    @dbus.service.method(
        "org.freedesktop.DBus.Introspectable",
        in_signature='', out_signature='s',
        path_keyword='object_path', connection_keyword='connection')
    def Introspect(self, object_path, connection):
        intro = etree.fromstring(
            super().Introspect(object_path, connection)
        )
        iface = intro.find("interface[@name='{}']".format(self.INTERFACE))
        for name, (sig, _) in self.__properties__.items():
            etree.SubElement(
                iface, 'pProperty',
                name=name, type=sig, access="readwrite"
            )
        return etree.tostring(intro)
