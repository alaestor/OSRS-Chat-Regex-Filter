import os
import sys
import logging
import inspect

import tkinter as tk
import tkinter.ttk as ttk
from ttkwidgets import CheckboxTreeview
import ttkwidgets as ttkw
from typing import List

import json

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

	def __init__(self, parent):
		logging.debug("initializing EditableTreeview")
		tk.Frame.__init__(self, parent)
		self.tree = ttk.Treeview(self, show="tree")
		self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
		self.tree.configure(yscrollcommand=self.vsb.set)
		self.vsb.pack(side="right", fill="y")
		self.tree.pack(side="top", fill="both", expand=True)
		self.export_menu = ExportMenu(self)
		self.state= {
			"dragging item": False
		}

		tree_event_bindings = {
			# edit and item menu
			"<Double-1>": self.event_item_edit,
			"<Button-3>": self.event_item_menu,
			# leftclick
			"<ButtonPress-1>": self.event_leftclick_press,
			"<ButtonRelease-1>": self.event_leftclick_release,
			#"<B1-Motion>": self.event_leftclick_drag,
			# selection hotkeys
			"<Escape>": self.event_deselect,
			"<Control-a>": self.event_select_all,
			# cut, copy, paste
			"<Control-c>": self.event_copy,
			"<Control-x>": self.event_cut,
			"<Control-v>": self.event_paste,
		}
		for trigger, event in tree_event_bindings.items():
			self.tree.bind(trigger, event)

	def open_parents(self, node):
		parent = self.tree.parent(node)
		if parent != "":
			self.tree.item(parent, open=True)
			self.open_parents(parent)

	def open_children(self, node):
		for child in self.tree.children(node):
			self.tree.item(child, open=True)
			self.open_children(child)

	def list_all_nodes(self, node=""):
		l = [] if node == None else [node]
		for child in self.tree.get_children(node):
			l.extend(self.list_all_nodes(child))
		return l

	def item_exists(self, text, parent=None):
		#for child in self.tree.get_children(parent):
		#	if self.tree.item(child)["text"] == text or self.item_exists(text, child):
		#		return True
		for child in self.list_all_nodes():
			if self.tree.item(child)["text"] == text:
				return True
		return False

	def insert(self, text, index: int or None = None, parent: str or None = None):
		if self.item_exists(text):
			raise ValueError(f"Could not insert {text} because it already exists")
		self.tree.insert(parent=parent or "", index=index or "end", iid=text, text=text)

	def delete(self, items: str or list):
		if type(items) is str:
			self.tree.delete(items)
		if type(items) is list:
			for item in items:
				self.tree.delete(item)

	def text(self, item):
		return self.tree.item(item)["text"]

	def rename(self, item, text):
		if self.item_exists(text):
			raise ValueError(f"Could not rename '{self.text(item)}' to '{text}' because it already exists")
		i = self.tree.index(item)
		p = self.tree.parent(item)
		self.tree.delete(item)
		self.insert(text, index=i, parent=p)

	def add(self, node: str or list(str) or dict, parent=""):
		print(node)
		def recurse(d, p):
			for k,v in d.items():
				self.tree.insert(parent=p, index="end", iid=k, text=k)
				if type(v) is dict:
					recurse(v, k)
			if p != "":
				self.tree.item(p, open=True)
		self.event_deselect()
		if type(node) is dict:
			recurse(node, parent)
			self.tree.selection_add([key for key in node.keys()])
		elif type(node) is str:
			self.tree.insert(parent=parent, index="end", iid=node, text=node)
			self.tree.selection_add(node)
		elif type(node) is list:
			for n in node:
				self.add(n)
		else:
			raise ValueError("'node' must be dict, str, or list of dict or str")

	def export_json(self, parent_nodes):
		def recurse(n):
			ns = {}
			for child in self.tree.get_children(n):
				ns[self.tree.item(child)["text"]] = recurse(child) or ""
			return ns
		d = {}
		for node in parent_nodes:
			d[self.tree.item(node)["text"]] = recurse(node)
		return json.dumps(d, indent = 4)

	def import_json(self, json_string, parent=""):
		self.add(json.loads(json_string), parent)

	def event_copy(self, event=None):
		logging.debug(f"{inspect.currentframe().f_code.co_name} {self.tree.selection()}")
		self.clipboard_clear()
		self.clipboard_append(self.export_json(self.tree.selection()))

	def event_cut(self, event):
		logging.debug(f"{inspect.currentframe().f_code.co_name} {self.tree.selection()}")
		self.event_copy()
		self.tree.delete(*self.tree.selection())

	## TODO no selection should be top-level
	def event_paste(self, event):
		logging.debug(f"{inspect.currentframe().f_code.co_name} {self.tree.selection()}")
		try:
			self.import_json(
				self.clipboard_get(),
				self.tree.selection()[0]
			)
		except ValueError as e:
			tk.messagebox.showerror(
				title="error",
				message="Clipboard didn't contain a valid JSON string."
			)

	def event_leftclick_press(self, event):
		#logging.debug(f"{inspect.currentframe().f_code.co_name} {self.tree.selection()}")
		return

	def event_leftclick_release(self, event):
		#logging.debug(f"{inspect.currentframe().f_code.co_name} {self.tree.selection()}")
		return

	def event_item_menu(self, click_event):
		logging.debug(f"{inspect.currentframe().f_code.co_name} {self.tree.selection()}")
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

	def event_deselect(self, event=None):
		logging.debug(f"{inspect.currentframe().f_code.co_name} {self.tree.selection()}")
		self.tree.selection_remove(self.tree.selection())

	def event_select_all(self, event=None):
		logging.debug(f"{inspect.currentframe().f_code.co_name} {self.tree.selection()}")
		self.tree.selection_add(self.list_all_nodes())

	def event_item_edit(self, event=None):
		logging.debug(f"{inspect.currentframe().f_code.co_name} {self.tree.selection()} ")
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
				#self.tree.item(item, text=input_string,)
				self.rename(item, input_string)
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
