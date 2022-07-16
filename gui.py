import os
import sys
import logging

import tkinter as tk
import tkinter.ttk as ttk
from ttkwidgets import CheckboxTreeview
import ttkwidgets as ttkw
from typing import List

def init_logging():
	basename = os.path.basename(__file__)
	scriptname = os.path.splitext(basename)[0]
	logging.basicConfig(
		level=logging.DEBUG,
		format="[%(levelname)s] %(message)s",
		handlers=[
			#logging.FileHandler(os.path.join(".", scriptname) + ".log", encoding="UTF-8", mode="w"),
			logging.StreamHandler(sys.stdout)
		]
	)

"""
DATA = {
	"filename":"file.txt",
	"filesize":"500kb",
	"maxcolwidth": {
		"col1":"300",
		"col2":"2",
		"col3":"3"
		},
	"numberofcolumns":"3",
	"datatypes": {
		"col1":"string",
		"col2":"int",
		"col3":"int"
		},
	"rowcount":"400"
}
"""

DATA = {
	"Generic Spam":{
		"Begging":[["regex"],["sample"]],
		"Websites":[["regex"],["sample"]],
		"White Knight":[["regex"],["sample"]]
	},
	"Scams":{
		"Games of Chance":[["regex"],["sample"]],
		"Social Phishing":[["regex"],["sample"]],
		"Trade Scams":[["regex"],["sample"]],
		"Example":{
			"Deeper": {
				"Even Deeper":None
			}
		}
	}
}

class ExportMenu(tk.Menu):
	def __init__(self, parent, things=None):
		tk.Menu.__init__(self, parent, tearoff=0)
		self.add_command(label="Clipboard")
		self.add_command(label="Text file")
		self.add_command(label="JSON file")

class EditableTreeview(tk.Frame):
	class item_menu(tk.Menu):
		def __init__(self, parent, multi_select):
			tk.Menu.__init__(self, parent, tearoff=0)
			edit_state = "normal" if not multi_select else "disabled"
			self.add_command(label="Edit", state=edit_state, command=parent.event_item_edit)
			self.add_command(label="Create", state=edit_state)
			self.add_separator()
			self.add_cascade(label="Export Regex", menu=parent.export_menu)
			self.add_separator()
			self.add_command(label="Remove")

	def event_item_menu(self, click_event):
		try:
			menu = None
			iid = self.tree.identify_row(click_event.y)
			if iid:
				if iid not in self.tree.selection():
					self.event_deselect(None)
					self.tree.selection_set(iid)
				menu = self.item_menu(self, len(self.tree.selection()) > 1)
				menu.tk_popup(click_event.x_root, click_event.y_root, 0)
		finally:
			if menu:
				menu.grab_release()

	def __init__(self, parent):
		tk.Frame.__init__(self, parent)
		self.tree = ttk.Treeview(self, show="tree")
		self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
		self.tree.configure(yscrollcommand=self.vsb.set)
		self.vsb.pack(side="right", fill="y")
		self.tree.pack(side="top", fill="both", expand=True)
		self.export_menu = ExportMenu(self)

		tree_event_bindings = {
			"<Double-1>": self.event_item_edit,
			"<Button-3>": self.event_item_menu,
			"<Button-1>": self.event_update_selection,
			"<Escape>": self.event_deselect,
			"<Control-a>": self.event_select_all
		}
		for trigger, event in tree_event_bindings.items():
			self.tree.bind(trigger, event)

	def event_update_selection(self, event):
		logging.debug(f"{event} {self.tree.selection()} {self.tree.focus()}")

	def event_deselect(self, event=None):
		logging.debug("treeview selection cleared")
		self.tree.selection_remove(self.tree.selection())

	def event_select_all(self, event=None):
		def recurse(node=None):
			l = [] if node == None else [node]
			for child in self.tree.get_children(node):
				l.extend(recurse(child))
			return l
		self.tree.selection_add(recurse())

	def event_item_edit(self, event=None):
		item = self.tree.selection()[0] # now you got the item on that tree
		item_text = self.tree.item(item,"text")
		logging.debug(f"editing tree item '{item_text}'")

		def edit_item_text(
				cb_accept,
				cb_cancel=None,
				x=0, relx=0,
				y=0, rely=0
			):
			inputbox = tk.Entry(self, borderwidth=0, highlightthickness=1)
			inputbox.insert(0, item_text)
			inputbox.selection_from(0)
			inputbox.selection_to("end")
			inputbox.place(x=x, relx=relx, rely=rely, y=y, relwidth=0.9, width=-1)
			inputbox.focus_set()
			inputbox.grab_set()

			def accept_edit(e):
				if cb_accept is not None:
					cb_accept(e.widget.get())
				e.widget.destroy()

			def cancel_edit(e):
				if cb_cancel is not None:
					cb_cancel()
				e.widget.destroy()

			inputbox.bind("<Return>", accept_edit)
			inputbox.bind("<Escape>", cancel_edit)

		def user_input(input_string):
			if input_string == "":
				logging.debug(f"deleted item '{item_text}' (blank input)")
				self.tree.delete(item)
			else:
				logging.debug(f"changed item '{item_text}' to '{input_string}'")
				self.tree.item(item, text=input_string)

		edit_item_text(user_input, y=self.tree.bbox(item)[1])

"""
list of valid strings which shouldn't match any patterns

map of hierarchal categories to maps of regex patterns to list of samples that it should match

toggle buttons in GUI categories to enable/disable regex? space bar to toggle selection?
"""


def addNode(eh, value:dict, parentNode:str="", key:str or None = None):
	id = "" if key is None else eh.tree.insert(parentNode, "end", text=key)
	if isinstance(value, dict):
		eh.tree.item(id, open=True)
		for (k, v) in value.items():
			addNode(eh, v, id, k)
	else:
		eh.tree.item(id)

def init_tk():
	root = tk.Tk()
	e = EditableTreeview(root)
	e.pack(fill="both", expand=True)
	addNode(e, DATA)
	root.mainloop()

if __name__ == "__main__":
	init_logging()
	try:
		logging.debug("Hello, World!")
		init_tk()
	except Exception as e:
		logging.critical(str(e))
