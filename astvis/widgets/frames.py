import gtk

class FrameBox(object):
    "Class deals with notbooks and frames implemented with gtk panes."

    def __init__(self, root, groupId=-1):
        self.root = root

        otherEventBox = gtk.EventBox()
        otherEventBox.props.can_focus = True
        otherEventBox.add_events(gtk.gdk.FOCUS_CHANGE_MASK&gtk.gdk.BUTTON_PRESS_MASK)
        otherNotebook = gtk.Notebook()
        otherNotebook.set_group_id(groupId)

        otherEventBox.set_data('framebox', self)

        otherEventBox.connect('focus', self._focus)
        otherEventBox.connect('notify::has-focus', self._notify)
        otherNotebook.connect('set-focus-child', self._focus_child)
        otherEventBox.connect('button-press-event', self._button_press)

        otherEventBox.add(otherNotebook)
        otherEventBox.show_all()

        self.eventBox = otherEventBox
        self.notebook = otherNotebook

    def _focus(self, widget, direction):
        "Focus event handler for event box with a notebook in it."
        notebook = widget.get_child()
        if notebook.get_n_pages()>0:
            # forward focus to notebook if there are any pages
            res = notebook.child_focus(direction)
            if not res:
                widget.grab_focus()
            return res

        # with no pages
        if widget.is_focus():
            # release focus
            return False
        # grab focus
        widget.grab_focus()
        return True

    def _notify(self, widget, prop):
        "focus-in-event handler for event box with a notebook in it."
        if widget.props.has_focus:
            self.root.focusedFrame = self
        elif self.root.focusedFrame==self:
            self.root.focusedFrame = None            

    def _focus_child(self, container, widget):
        "'set-child-focus' event handler for event box with a notebook in it."
        notebook = self.notebook
        if widget!=None:
            self.root.focusedFrame = self
        elif self.root.focusedFrame==self:
            self.root.focusedFrame = None            
        return True

    def _button_press(self, widget, event):
        "'button-press-event' handler for event box with a notebook in it."
        notebook = self.notebook
        if notebook.get_n_pages()==0:
            widget.grab_focus()
        return True

    def split(self, paned):
        notebook = self.notebook
        eventBox = self.eventBox
        parent = eventBox.get_parent()
        parent.remove(eventBox)
        hp = paned

        newFrame = FrameBox(self.root, self.notebook.get_group_id())
        self.splitFrame = newFrame # otherwise python deallocate the object
        newFrame.splitFrame = self
        hp.add1(eventBox)
        hp.add2(newFrame.eventBox)

        hp.show_all()
        parent.add(hp)
        
    def unsplit(self):
        # remove paned widget
        paned = self.eventBox.get_parent()
        parent = paned.get_parent()
        parent.remove(paned)
        paned.remove(self.eventBox)
        self.splitFrame.splitFrame = None

        # get all views from split frame
        otherFrame = self.splitFrame
        otherNotebook = otherFrame.notebook
        self.splitFrame = None
        while otherNotebook.get_n_pages()>0:
            page = otherNotebook.get_nth_page(0)
            label = otherNotebook.get_tab_label(page)
            otherNotebook.remove_page(0)
            self.notebook.insert_page(page, label, -1)
            self.notebook.set_tab_detachable(page, True)

        # add
        # TODO: setup splitFrames
        otherEventBox = parent.get_child1()
        print otherEventBox
        if isinstance(otherEventBox, gtk.EventBox):
            otherFrame = otherEventBox.get_data('framebox')
            otherFrame.splitFrame = self
            self.splitFrame = otherFrame
        parent.add(self.eventBox)
        
