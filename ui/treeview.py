#!/usr/bin/env bashstyle --python
#coding=utf-8
#########################################################
# 							#
# This is BashStyle-NG  				#
#							#
# Licensed under GNU GENERAL PUBLIC LICENSE v3		#
#							#
# Copyright 2007 - 2014 Christopher Bratusek		#
#							#
#########################################################

MODULES = [ 'os', 'os.path', 'sys', 'widgethandler', 'subprocess' ]

FAILED = []

for module in MODULES:
	try:
		globals()[module] = __import__(module)
	except ImportError:
		FAILED.append(module)

try:
	from gi.repository import Gtk
except ImportError:
	FAILED.append("Gtk (from gi.repository)")

try:
	from gi.repository.GdkPixbuf import Pixbuf
except ImportError:
	FAILED.append("GdkPixbuf (from gi.repository)")

if FAILED:
    print("The following modules failed to import: %s" % (" ".join(FAILED)))
    sys.exit(1)

gtkbuilder = widgethandler.gtkbuilder

keybindings = {
	"undo",
	"upcase_word",
	"capitalize_word",
	"downcase_word",
	"transpose_words",
	"transpose_chars",
	"unix_word_rubout",
	"kill_word",
	"possible_filename_completions",
	"possible_hostname_completions",
	"possible_username_completions",
	"possible_variable_completions",
	"kill_line",
	"unix_line_discard",
	"beginning_of_line",
	"end_of_line",
	"clear_screen",
	"history_search_forward",
	"history_search_backward",
	"complete_path"
}

class Tree(object):

	def __init__(self, cfo, udc, fdc):
			self.config = cfo
			self.userdefault = udc
			self.factorydefault = fdc

	def InitTree(self):
		store = gtkbuilder.get_object("treeviewstore")
		tree = gtkbuilder.get_object("treeview")

		render_binding = Gtk.CellRendererText()
		column_binding = Gtk.TreeViewColumn("Binding", render_binding, text=0)
		tree.append_column(column_binding)

		render_alt = Gtk.CellRendererToggle()
		render_alt.set_property("radio", True)
		column_alt = Gtk.TreeViewColumn("Alt", render_alt, active=1)
		tree.append_column(column_alt)

		render_ctrl = Gtk.CellRendererToggle()
		render_ctrl.set_property("radio", True)
		column_ctrl = Gtk.TreeViewColumn("Ctrl", render_ctrl, active=2)
		tree.append_column(column_ctrl)

		def on_cell_toggled(widget, path, column, concurrent_column):
			store[path][column] = not store[path][column]
			store[path][concurrent_column] = not store[path][concurrent_column]

		render_ctrl.connect("toggled", on_cell_toggled, 2, 1)
		render_alt.connect("toggled", on_cell_toggled, 1, 2)

		render_key = Gtk.CellRendererText()
		render_key.set_property("editable", True)
		column_key = Gtk.TreeViewColumn("Key", render_key, text=3)
		tree.append_column(column_key)

		def text_edited(widget, path, text):
			store[path][3] = text
			self.change_setting(store[path][0].replace("-", "_"), store[path][1],
					store[path][2], store[path][3])

		render_key.connect("edited", text_edited)

		def on_changed(selection):
			(model, iter) = selection.get_selected()
			self.change_setting(model[iter][0].replace("-", "_"), model[iter][1],
					model[iter][2], model[iter][3])

		tree.get_selection().connect("changed", on_changed)

		for key in sorted(keybindings):
			modifier, boundkey, label = self.prepare(key)
			if modifier == "e":
				alt = True
				ctrl = False
			elif modifier == "C":
				alt = False
				ctrl = True
			else:
				alt = False
				ctrl = False
			store.append([label, alt, ctrl, boundkey])

	def prepare(self, setting):
		value = self.config["Keybindings"][setting]
		if value == "":
			modifier = ""
			boundkey = ""
		else:
			modifier = value.split(":")[0]
			boundkey = value.split(":")[1]
		label = setting.replace("_", "-")
		return modifier, boundkey, label

	def change_setting(self, setting, alt, ctrl, key):
		if key == "":
			self.config["Keybindings"][setting] = ""
		else:
			if alt == True:
				self.config["Keybindings"][setting] = "e:" + key
			elif ctrl == True:
				self.config["Keybindings"][setting] = "C:" + key
			else:
				self.config["Keybindings"][setting] = ""