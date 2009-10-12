import gtk
import os

_icon_factory = gtk.IconFactory()
_icon_factory.add_default()

icon_dir = 'data/icons'
_files = [('pointer', 'pointer24.png'),
          ('flow', 'flow24.png'),
          ('use', 'use24.png'),
          ('split-vertical','split-vertical.png'),
          ('split-horizontal','split-horizontal.png')
          ]

for iconId, filename in _files:
    set = gtk.IconSet()
    pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(icon_dir, filename))
    source = gtk.IconSource()
    source.set_pixbuf(pixbuf)
    #source.set_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
    set.add_source(source)
    _icon_factory.add(iconId, set)
