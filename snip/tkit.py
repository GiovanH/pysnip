import tkinter.font as tkFont
import tkinter as tk
from tkinter import ttk


def xstr(s, nonestr=str(None)):
    if s:
        # Strip invalid characters.
        return "".join([c for c in str(s) if ord(c) in range(65536)])
    else:
        return nonestr


def setListBox(listbox, values):
    listbox.delete(0, listbox.size())
    for val in values:
        listbox.insert(tk.END, xstr(val, nonestr=""))


class ToggleButton(ttk.Checkbutton):
    def __init__(self, parent, variable, command=(lambda x: x), text="Toggle", *args, **kwargs):
        super(ToggleButton, self).__init__(master=parent, variable=variable, command=self.toggle, text=text, *args, **kwargs)
        self.text = text
        self.callback = command
        self.variable = variable
        self.update()

    def toggle(self):
        # ttk.Checkbutton handles value toggling
        self.update()

    def update(self):
        self.callback(self.variable.get())

# class ToggleButton(tk.Button):
#     def __init__(self, parent, variable, command=(lambda x: x), text="Toggle", *args, **kwargs):
#         super(ToggleButton, self).__init__(master=parent, command=self.toggle, text=text, *args, **kwargs)
#         self.text = text
#         self.callback = command
#         self.variable = variable
#         self.update()

#     def toggle(self):
#         self.variable.set(not self.variable.get())
#         self.update()

#     def update(self):
#         if self.variable.get():
#             self.config(relief="sunken")
#         else:
#             self.config(relief="raised")
#         self.callback(self.variable.get())

        
class MultiColumnListbox(tk.Frame):
    """use a ttk.TreeView as a multicolumn ListBox"""

    def __init__(self, parent, headers, tabledata, multiselect=False, sortable=True, vscroll=True, hscroll=False, nonestr=str("None"), *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.tree = None
        self.sortable = sortable
        self.headers = headers  # This must remain static.
        self.nonestr = nonestr

        self.setup_widgets(headers, vscroll=vscroll, hscroll=hscroll)
        self.build_tree(headers, tabledata)


        if multiselect:
            self.tree.configure(selectmode=tk.NONE)
            self.bindSelectionAction("<Button-1>", self.tree.selection_toggle, useUID=True)
            # self.tree.bind("<Button-1>", self.handle_multiselect_click)

    def bindSelectionAction(self, binding, callback, useUID=False):
        def cb(event):
            if useUID:
                return callback(self.tree.identify('item', event.x, event.y))
            else:
                return callback(self.tree.item(self.tree.identify('item', event.x, event.y)))
        self.tree.bind(binding, cb)

    # def handle_multiselect_click(self, event):
    #     item = self.tree.identify('item', event.x, event.y)
    #     self.tree.selection_toggle(item)

    def setup_widgets(self, headers, vscroll=True, hscroll=True):
        container = self

        # Create a treeview with dual scrollbars
        self.tree = ttk.Treeview(self, columns=headers, selectmode=tk.EXTENDED, show="headings")
        self.tree.grid(column=0, row=0, sticky='nsew', in_=container)

        if vscroll:
            vsb = ttk.Scrollbar(orient="vertical", command=self.tree.yview)
            vsb.grid(column=1, row=0, sticky='ns', in_=container)
            self.tree.configure(yscrollcommand=vsb.set)
        if hscroll:
            hsb = ttk.Scrollbar(orient="horizontal", command=self.tree.xview)
            hsb.grid(column=0, row=1, sticky='ew', in_=container)
            self.tree.configure(xscrollcommand=hsb.set)

        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

    def sortby(self, tree, col, descending):
        """sort tree contents when a column header is clicked on"""

        data = [(tree.set(child, col), child) for child in tree.get_children('')]
        # if the data to be sorted is numeric change to float
        # data =  change_numeric(data)

        # now sort the data in place
        data.sort(reverse=descending)
        for index, item in enumerate(data):
            tree.move(item[1], '', index)

        # switch the heading so it will sort in the opposite direction
        tree.heading(col, command=lambda col=col: self.sortby(tree, col, int(not descending)))

    def insert_item(self, item):
        # Sanitize value strings
        if item.get("values"):
            item['values'] = [xstr(s, nonestr=self.nonestr) for s in item['values']]

        self.tree.insert('', tk.END, **item)

    def build_tree(self, headers, itemlist, resize=True):
        for col in headers:
            if self.sortable:
                self.tree.heading(col, text=col.title(), command=lambda c=col: self.sortby(self.tree, c, 0))
            else:
                self.tree.heading(col, text=col.title())
            if resize:
                # adjust the column's width to the header string
                self.tree.column(col, width=tkFont.Font().measure(col.title()))

        if resize:
            # Super dirty average
            avgs = [0] * len(headers)

            for item in itemlist:
                self.insert_item(item)

                # adjust column's width if necessary to fit each value
                for index, val in enumerate(item['values']):
                    if val and val != "":
                        col_w = tkFont.Font().measure(val)
                        avgs[index] = (col_w + avgs[index]) / 2

            for i in range(0, len(headers)):
                self.tree.column(headers[i], width=min(int(avgs[i]), 480))
        else:
            for item in itemlist:
                self.insert_item(item)

    def update_tree(self, itemlist, resize=True):
        self.tree.delete(*self.tree.get_children())
        for item in itemlist:
            self.insert_item(item)

    def modSelection(self, selectionNos):
        select_these_items = [
            child for child in self.tree.get_children('')
            if int(self.tree.set(child, "ID")) in selectionNos
        ]
        self.tree.selection_set(select_these_items)
        # self.tree.selection_set()

    def getSelections(self):
        return [int(self.tree.set(child, "ID")) for child in self.tree.selection()]


class JSONEditor(tk.Toplevel):
    def __init__(self, parent, jsonRoot, onExit=None, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)

        self.jsonRoot = jsonRoot

        def exit():
            if onExit:
                onExit()
            self.destroy()
        self.exit = exit
        self.protocol("WM_DELETE_WINDOW", self.exit)
        self.initWidgets()

    def initWidgets(self):
        self.title("JSON Editor")
        self.rootNotebook = self.NotebookPage(self, self, self.jsonRoot)
        self.rootNotebook.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)


class NotebookPage(tk.Frame):
    def __init__(self, master, top, jsonRoot, ownkey="", allow_saving=True, *args, **kwargs):
        tk.Frame.__init__(self, master=master, *args, **kwargs)

        self.controls = []
        self.pages = []
        self.notebook = ttk.Notebook(self)
        self.jsonRoot = jsonRoot
        self.top = top
        self.allow_saving = allow_saving

        row = 0
        for key in jsonRoot.keys():
            value = jsonRoot.get(key)
            if isinstance(value, dict):
                page = type(self)(self, top, value, ownkey=ownkey + "." + key, allow_saving=self.allow_saving, **kwargs)
                self.notebook.add(page, text=key)
                self.pages.append(page)
                # page.grid()

        looseItemFrame = ttk.Frame(self)
        looseItemFrame.columnconfigure(1, weight=1)

        for key in jsonRoot.keys():
            value = jsonRoot.get(key)
            if not isinstance(value, dict):
                row += 1
                self.makeLabel(looseItemFrame, jsonRoot, ".".join([ownkey, key]), value).grid(
                    row=row, column=0, sticky="nw", padx=(0, 6), pady=4)

                (var, control) = self.makeControl(value, key, parent=looseItemFrame)

                control.grid(row=row, column=1, sticky="new", pady=4)
                self.controls.append((key, var, control))

                row += 1
                ttk.Separator(looseItemFrame).grid(row=row, column=0, columnspan=2, sticky="ew")

        if len(self.controls) > 0:
            if len(self.pages) > 0:
                self.notebook.insert(0, looseItemFrame, text=self.getPrettyKey(ownkey))
                self.notebook.select(0)
            else:
                looseItemFrame.grid(sticky="nsew", padx=4, pady=4)

        if len(self.pages) > 0:
            self.notebook.grid(sticky="nsew", padx=4, pady=4)

        if len(self.controls) > 0:
            # Buttons, in a frame
            row += 1
            frame_buttons = tk.Frame(looseItemFrame)
            frame_buttons.grid(row=row, columnspan=2, sticky="es")
            frame_buttons.rowconfigure(0, weight=1)
            frame_buttons.columnconfigure(0, weight=1)
            looseItemFrame.rowconfigure(row, weight=1)
            # ttk.Button(frame_buttons, text="Close", command=top.exit).grid(
            #     row=0, column=0, sticky="ew", padx=2, pady=2)
            if self.allow_saving:
                ttk.Button(frame_buttons, text="Save", command=self.save).grid(
                    sticky="ew", padx=4, pady=4)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def makeLabel(self, parent, jsonRoot, key, value):
        return ttk.Label(parent, text=key)

    def getPrettyKey(self, key):
        return key.split(".")[-1]

    def makeControl(self, value, key=None, parent=None):
        if not parent:
            parent = self
        elif isinstance(value, list):
            var = control = ListFrame(parent, list_=value.copy())
        elif isinstance(value, bool):
            var = tk.BooleanVar(value=value)
            control = ToggleButton(parent, variable=var)
        elif isinstance(value, int):
            var = tk.IntVar(value=value)
            control = ttk.Entry(parent, textvariable=var)
        elif isinstance(value, float):
            var = tk.DoubleVar(value=value)
            control = ttk.Entry(parent, textvariable=var)
        elif isinstance(value, str):
            var = tk.StringVar(value=value)
            control = ttk.Entry(parent, textvariable=var)
        else:
            print("Bad variable type", value)
            control = ttk.Label(parent, text="Unknown Setting")
            var = None
        return (var, control)

    def save(self):
        print(self.jsonRoot)
        for (key, var, control) in self.controls:
            try:
                if var:
                    print(key, var.get())
                    self.jsonRoot[key] = var.get()
                else:
                    print("Skipping invalid", key)
            except tk.TclError as e:
                from tkinter import messagebox as mbox
                import traceback
                mbox.showerror("Error", "{}\n\n{}".format(
                    traceback.format_exc(limit=1).split("\n")[-2],
                    traceback.format_exc())
                )
                return


class ListFrame(tk.Frame):
    def __init__(self, parent, list_, *args, **kwargs):
        super(ListFrame, self).__init__(master=parent, *args, **kwargs)
        # self.config(relief=tk.RIDGE, bd=2, padx=2)

        self.columnconfigure(0, weight=1)
        self.vars = []
        row = 0
        list_.append("")
        for value in list_:
            row += 1
            if isinstance(value, int):
                var = tk.IntVar(value=value)
                control = ttk.Entry(self, textvariable=var)
            elif isinstance(value, float):
                var = tk.DoubleVar(value=value)
                control = ttk.Entry(self, textvariable=var)
            elif isinstance(value, str):
                var = tk.StringVar(value=value)
                control = ttk.Entry(self, textvariable=var)
            else:
                print("Bad variable type", value)
            control.grid(row=row, column=1, sticky="ew")
            self.vars.append(var)
        row += 1
        ttk.Separator(self).grid(row=row, column=0, columnspan=2, sticky="ew")

    def get(self):
        r = []
        for var in self.vars:
            print(r)
            val = var.get()
            if val is "":
                continue
            if isinstance(val, str):
                if val.isnumeric():
                    val = int(val)
            r.append(val)
        return r


imageCache = []


def makePhotoImage(filename, maxwidth, maxheight, ALWAYS_RESIZE=True):
    """Make a resized photoimage given a filepath
    
    Args:
        filename (str): Path to an image file
        maxwidth (TYPE): Maximum width of canvas
        maxheight (TYPE): Maximum height of canvas
    
    Returns:
        ImageTk.PhotoImage
    """

    from PIL import ImageTk, Image
    from math import floor
    pilimg = Image.open(filename)
    curimg = ImageTk.PhotoImage(pilimg)

    width = curimg.width()
    height = curimg.height()
    imageIsTooBig = width > maxwidth or height > maxheight
    if (imageIsTooBig or ALWAYS_RESIZE):
        ratio = min(maxwidth / width, maxheight / height)
        method = Image.ANTIALIAS
        if ratio > 1:
            ratio = floor(ratio)
            method = Image.LINEAR
        pilimg = Image.open(filename).resize(
            (int(width * ratio), int(height * ratio)), method)

    r = ImageTk.PhotoImage(pilimg)
    return r
