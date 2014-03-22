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

iconview_icons = ["bs-ng-style", "bs-ng-separator", "bs-ng-alias",
		  "bs-ng-advanced", "bs-ng-shopts", "bs-ng-git",
		  "bs-ng-readline", "bs-ng-vim", "bs-ng-nano",
		  "bs-ng-ls", "bs-ng-keys", "bs-ng-custom",
		  "bs-ng-help", "bs-ng-info" ]

iconview_labels = {
	"bs-ng-style" : "General Style",
	"bs-ng-alias" : "Aliases",
	"bs-ng-advanced" : "Advanced",
	"bs-ng-readline" : "Readline",
	"bs-ng-vim" : "Vi IMproved",
	"bs-ng-nano" : "GNU Nano",
	"bs-ng-ls" : "LS colors",
	"bs-ng-custom" : "Custom Prompt Builder",
	"bs-ng-separator" : "Separator Style",
	"bs-ng-shopts" : "Shell Options",
	"bs-ng-git" : "GIT",
	"bs-ng-help" : "Documentation",
	"bs-ng-info" : "About BashStyle-NG",
	"bs-ng-keys" : "Keybindings"
}

notebook_pages = {

	"General Style" : 1,
	"Aliases" : 2,
	"Advanced" : 3,
	"Readline" : 4,
	"Vi IMproved" : 5,
	"GNU Nano" : 6,
	"LS colors" : 7,
	"Custom Prompt Builder" : 8,
	"Separator Style" : 9,
	"Shell Options" : 11,
	"GIT" : 10,
	"Documentation" : 0,
	"About BashStyle-NG" : 0,
	"Keybindings" : 12
}

gtkbuilder = widgethandler.gtkbuilder
DOCDIR = os.getenv('BSNG_DOCDIR')

class IconBook(object):

	def ShowDocumentation(self):
		subprocess.Popen("x-www-browser " + DOCDIR + "/bashstyle-ng/index.html", shell=True)

	def ShowAboutDialog(self):
		aboutdialog = gtkbuilder.get_object("aboutdialog")
		aboutdialog.show_all()
		aboutdialog.connect("response", lambda w, e: w.hide() or True)
		aboutdialog.connect("delete-event", lambda w, e: w.hide() or True)

	def InitIconBook(self):

		liststore = gtkbuilder.get_object("iconviewstore")
		iconview = gtkbuilder.get_object("iconview")
		iconview.set_model(liststore)
		iconview.set_pixbuf_column(0)
		iconview.set_text_column(1)
		iconview.set_activate_on_single_click(True)

		notebook = gtkbuilder.get_object("notebook")
		notebook.set_current_page(0)

		def back_clicked(data):
			notebook.set_current_page(0)

		back = gtkbuilder.get_object("back")
		back.connect("clicked", back_clicked)

		for icon in iconview_icons:
			pixbuf = Gtk.IconTheme.get_default().load_icon(icon, 32, 0)
			liststore.append([pixbuf, iconview_labels[icon]])

		def iconview_activated(widget, item):
				model = widget.get_model()
				notebook.set_current_page(notebook_pages[model[item][1]])
				print(model[item][1])
				if model[item][1] == "Documentation" :
					self.ShowDocumentation()
				elif model[item][1] == "About BashStyle-NG" :
					self.ShowAboutDialog()

		iconview.connect("item-activated", iconview_activated)
