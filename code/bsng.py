#!/usr/bin/env python
#coding=utf-8
#########################################################
# 							#
# This is BashStyle-NG  				#
#							#
# Licensed under GNU GENERAL PUBLIC LICENSE v3		#
#							#
# Copyright 2007 - 2010 Christopher Bratusek		#
#							#
#########################################################

MODULES = [ 'os', 'os.path', 'sys', 'gtk', 'locale', 'gettext', 'gconf',
            'shutil', 'vte', 'ctypes', 'optparse', 'subprocess', 'undobuffer',
            'commands', 'string' ]

FAILED = []

for module in MODULES:
	try:
		globals()[module] = __import__(module)
	except ImportError:
		FAILED.append(module)

if FAILED:
    print "The following modules failed to import: %s" % (" ".join(FAILED))
    sys.exit(1)

PREFIX = commands.getoutput('pkg-config --variable=prefix bashstyle-ng')

parser = optparse.OptionParser("bashstyle <option> [value]\
				\n\nBashStyle-NG © 2007 - 2010 Christopher Bratusek\
				\nLicensed under the GNU GENERAL PUBLIC LICENSE v3")

if sys.platform == 'linux2':
	try:
		libc = ctypes.CDLL('libc.so.6')
		libc.prctl(15, 'bashstyle', 0, 0, 0)
	except:
		pass

parser.add_option("-v", "--version", dest="version",
                  action="store_true", default=False, help="print version and exit")

parser.add_option("-p", "--prefix", dest="prefix",
                  action="store_true", default=False, help="print prefix and exit")

parser.add_option("-g", "--group", dest="group", default="style",
                  help="display a given group of options at startup, one of:\
                  \nstyle, alias, advanced, readline, extra, profile, vim, nano, ls or custom")

(options, args) = parser.parse_args()

if options.version:
		print "%s" % commands.getoutput('pkg-config --modversion bashstyle-ng')
		sys.exit(0)

if options.prefix:
		print "%s" % commands.getoutput('pkg-config --variable=prefix bashstyle-ng')
		sys.exit(0)

groups = {
	  "style" : "0",
	  "alias" : "1",
	  "advanced" : "2",
	  "readline" : "3",
	  "extra" : "4",
	  "profile" : "5",
	  "vim" : "6",
	  "nano" : "7",
	  "ls" : "8",
	  "custom" : "9",
	 }

initial_page = groups[options.group]

_ = gettext.gettext
APP_NAME = "bashstyle-ng"

icon_theme = gtk.icon_theme_get_default()

gtkbuilder = gtk.Builder()

gdb = gconf.client_get_default()
gdb.add_dir ("/apps/bashstyle", gconf.CLIENT_PRELOAD_RECURSIVE)
gbase = "/apps/bashstyle/"

blacklist = ['\'', '\"']

lockfile = os.path.expanduser("~/.bashstyle.lock")

def check_lockfile():
	####################### Check the lockfile ########################################
	if os.access(lockfile, os.F_OK):
		rlockfile = open(lockfile, "r")
		rlockfile.seek(0)
		oldpid = rlockfile.readline()
		if os.path.exists("/proc/%s" % oldpid):
			xpid = commands.getoutput("pgrep -l bashstyle")
			gpid = string.split(xpid)
			if not xpid == "" and gpid[1] == "bashstyle":
				print "Lockfile does exist and bashstyle-ng is already running."
				print "bashstyle-ng is running as process %s" % oldpid
				sys.exit(1)
			else:
				print "Lockfile does exist but the process with that pid is not"
				print "bashstyle-ng, removing lockfile of old process: %s" % oldpid
				os.remove(lockfile)
		else:
			print "Lockfile does exist but the process with that pid is no"
			print "longer running, removing lockfile of old process: %s" % oldpid
			os.remove(lockfile)

def write_lockfile():
	####################### Write the lockfile ########################################
	if not os.access(lockfile, os.F_OK):
		wlockfile = open(lockfile, "w")
		wlockfile.write("%s" % os.getpid())
		wlockfile.close

def remove_lockfile():
	####################### Remove the lockfile #######################################
	if os.access(lockfile, os.F_OK):
		os.remove(lockfile)

def swap_dic(original_dict):
	####################### Swap Keys and Values of a dictionary ######################
	return dict([(v, k) for (k, v) in original_dict.iteritems()])

class BashStyleNG(object):

	def __init__(self):

		####################### write the lockfile #########################################
		write_lockfile()

		####################### cd into $HOME ##############################################
		os.chdir(os.getenv("HOME"))

		####################### load gettext ###############################################
		langs = []
		lc, encoding = locale.getdefaultlocale()
		if (lc):
			langs = [lc]
		language = os.environ.get('LANGUAGE', None)
		if (language):
			langs += language.split(":")
		langs += ["C", "de", "it", "ru", "es"]

		gettext.bindtextdomain(APP_NAME)
		gettext.textdomain(APP_NAME)
		self.lang = gettext.translation(APP_NAME, languages=langs, fallback = True)
		global _
		_ = self.lang.gettext

		gtkbuilder.set_translation_domain(APP_NAME)
		gtkbuilder.add_from_file(PREFIX + "/share/bashstyle-ng/data/bashstyle7.ui")

		self.use_bashstyle = gtkbuilder.get_object("use_bashstyle")
		self.use_bashstyle.set_active(gdb.get_bool(gbase + "use_bashstyle"))

		def set_use_bashstyle(widget, data=None):
			gdb.set_bool(gbase + "use_bashstyle", widget.get_active())
			rc = open(os.path.expanduser("~/.bashrc"), "r")
			rc_new = open(os.path.expanduser("~/.bashrc.new"), "w")
			content = rc.readlines()
			for line in content:
				if line.find("bashstyle-ng/rc/nx-rc") == -1:
					rc_new.write(line)
			rc.close
			if widget.get_active() == True:
				rc_new.write("source /usr/share/bashstyle-ng/rc/nx-rc")
			rc_new.close
			shutil.move(os.path.expanduser("~/.bashrc.new"), os.path.expanduser("~/.bashrc"))

		self.use_bashstyle.connect("toggled", set_use_bashstyle)

		####################### Load the Colored Prompts Button ###########################

		self.colored_prompts = gtkbuilder.get_object("colored_prompts")
		self.colored_prompts.set_active(gdb.get_bool(gbase + "color/enable"))

		def set_colored_prompts(widget, data=None):
			gdb.set_bool(gbase + "color/enable", widget.get_active())

		self.colored_prompts.connect("toggled", set_colored_prompts)

		####################### Load the Colored ls Button ################################

		self.ls_color = gtkbuilder.get_object("ls_color")
		self.ls_color.set_active(gdb.get_bool(gbase + "colored_ls"))

		def set_colored_ls(widget, data=None):
			gdb.set_bool(gbase + "colored_ls", widget.get_active())

		self.ls_color.connect("toggled", set_colored_ls)

		####################### Lad the Colored Manpages Button ###########################

		self.manpage_color = gtkbuilder.get_object("manpage_color")
		self.manpage_color.set_active(gdb.get_bool(gbase + "colored_man"))

		def set_colored_man(widget, data=None):
			gdb.set_bool(gbase + "colored_man", widget.get_active())

		self.manpage_color.connect("toggled", set_colored_man)

		####################### Load the Colored Grep Button #############################

		self.grep_color = gtkbuilder.get_object("grep_color")
		self.grep_color.set_active(gdb.get_bool(gbase + "colored_grep"))

		def set_colored_grep(widget, data=None):
			gdb.set_bool(gbase + "colored_grep", widget.get_active())

		self.grep_color.connect("toggled", set_colored_grep)

		####################### Load the Random Style Button ##############################

		self.random_style = gtkbuilder.get_object("random_style")
		self.random_style.set_active(gdb.get_bool(gbase + "random_style"))

		def set_random_style(widget, data=None):
			gdb.set_bool(gbase + "random_style", widget.get_active())

		self.random_style.connect("toggled", set_random_style)

		####################### Load the Color Style Combobox #############################

		self.color_style = gtkbuilder.get_object("color_style")

		color_styles = {
				 0 : "normal",
				 1 : "bright",
				 2 : "dimmed",
				 3 : "inverted",
				 4 : "underlined",
			        }

		self.color_style.set_active(swap_dic(color_styles)[gdb.get_string(gbase + "color/style")])

		def set_color_style(widget, data=None):
			selection = widget.get_active()
			gdb.set_string(gbase + "color/style", color_styles[selection])

		self.color_style.connect("changed", set_color_style)

		####################### Load the Terminfo Combobox ################################

		self.terminfo = gtkbuilder.get_object("terminfo")

		man_styles = {
			      0 : "mostlike",
			      1 : "bold",
			      2 : "nebula",
			     }

		self.terminfo.set_active(swap_dic(man_styles)[gdb.get_string(gbase + "man_style")])

		def set_man_style(widget, data=None):
			selection = widget.get_active()
			gdb.set_string(gbase + "man_style", man_styles[selection])

		self.terminfo.connect("changed", set_man_style)

		####################### Load the Grep Color Combobox ##############################

		self.grep_colour = gtkbuilder.get_object("grep_colour")

		grep_colors = {
			        0 : "01;38;5;0",
			        1 : "01;38;5;1",
			        2 : "01;38;5;2",
			        3 : "01;38;5;3",
			        4 : "01;38;5;4",
			        5 : "01;38;5;5",
			        6 : "01;38;5;6",
			        7 : "01;38;5;7",
			        8 : "01;38;5;33",
			        9 : "01;38;5;111",
			       10 : "01;38;5;45",
			       11 : "01;38;5;60",
			       12 : "01;38;5;42",
			       13 : "01;38;5;637",
			       14 : "01;38;5;684",
			       15 : "01;38;5;761",
			       16 : "01;38;5;690",
			       17 : "01;38;5;714",
			       18 : "01;38;5;604",
			       19 : "01;38;5;213",
			       20 : "01;38;5;5344",
			      }

		self.grep_colour.set_active(swap_dic(grep_colors)[gdb.get_string(gbase + "color/grep")])

		def set_grep_color(widget, data=None):
			selection = widget.get_active()
			gdb.set_string(gbase + "color/grep", grep_colors[selection])

		self.grep_colour.connect("changed", set_grep_color)

		####################### Load the Color Changer Comboboxes #########################

		self.color_of = gtkbuilder.get_object("color_of")
		self.color_to = gtkbuilder.get_object("color_to")

		self.color_of.set_active(0)
		self.color_to.set_active(0)

		color_keys = {
			      1 : "color/user",
			      2 : "color/host",
			      3 : "color/date",
			      4 : "color/time",
			      5 : "color/wdir",
			      6 : "color/font",
			      7 : "color/separatorc",
			      8 : "color/uptime",
			      9 : "color/ps234c",
			     }

		colors = {
			   1 : "$black",
			   2 : "$red",
			   3 : "$green",
			   4 : "$yellow",
			   5 : "$blue",
			   6 : "$magenta",
			   7 : "$cyan",
			   8 : "$white",
			   9 : "$coldblue",
			  10 : "$smoothblue",
			  11 : "$iceblue",
			  12 : "$turqoise",
			  13 : "$smoothgreen",
			  14 : "$winered",
			  15 : "$brown",
			  16 : "$silver",
			  17 : "$ocher",
			  18 : "$orange",
			  19 : "$purple",
			  20 : "$pink",
			  21 : "$cream",
			 }

		def change_color(widget, data=None):
			color_set = self.color_of.get_active()
			color_is = self.color_to.get_active()
			if color_set != 0 and color_is != 0:
				gdb.set_string(gbase + color_keys[color_set], colors[color_is])
				self.color_to.set_active(0)
				self.color_of.set_active(0)

		self.color_of.connect("changed", change_color)
		self.color_to.connect("changed", change_color)

		####################### Load the Prompt Style Button ##############################

		self.prompt_style = gtkbuilder.get_object("prompt_style")

		prompt_styles = {
				  0 : "separator",
				  1 : "vector",
				  2 : "clock",
				  3 : "clock-ad",
				  4 : "elite",
				  5 : "poweruser",
				  6 : "dirks",
				  7 : "dot_prompt",
				  8 : "sepa_ng",
				  9 : "quirk",
				 10 : "sputnik",
				 11 : "ayoli",
				}

		self.prompt_style.set_active(swap_dic(prompt_styles)[gdb.get_string(gbase + "prompt_style")])

		def set_prompt_style(widget, data=None):
			selection = widget.get_active()
			gdb.set_string(gbase + "prompt_style", prompt_styles[selection])

		self.prompt_style.connect("changed", set_prompt_style)

		def emit_text(widget, text, *args):
			if text in blacklist:
				widget.emit_stop_by_name('insert-text')

		####################### Load the Alias #1 Entry ###################################

		self.alias1 = gtkbuilder.get_object("alias1")
		self.alias1.set_text("%s" % gdb.get_string(gbase + "alias/one"))

		def set_alias1(widget, data=None):
			gdb.set_string(gbase + "alias/one", widget.get_text())

		self.alias1.connect("insert-text", emit_text)
		self.alias1.connect("changed", set_alias1)

		####################### Load the Alias #2 Entry ###################################

		self.alias2 = gtkbuilder.get_object("alias2")
		self.alias2.set_text("%s" % gdb.get_string(gbase + "alias/two"))

		def set_alias2(widget, data=None):
			gdb.set_string(gbase + "alias/two", widget.get_text())

		self.alias2.connect("insert-text", emit_text)
		self.alias2.connect("changed", set_alias2)

		####################### Load the Alias #3 Entry ###################################

		self.alias3 = gtkbuilder.get_object("alias3")
		self.alias3.set_text("%s" % gdb.get_string(gbase + "alias/three"))

		def set_alias3(widget, data=None):
			gdb.set_string(gbase + "alias/three", widget.get_text())

		self.alias3.connect("insert-text", emit_text)
		self.alias3.connect("changed", set_alias3)

		####################### Load the Alias #4 Entry ###################################

		self.alias4 = gtkbuilder.get_object("alias4")
		self.alias4.set_text("%s" % gdb.get_string(gbase + "alias/four"))

		def set_alias4(widget, data=None):
			gdb.set_string(gbase + "alias/four", widget.get_text())

		self.alias4.connect("insert-text", emit_text)
		self.alias4.connect("changed", set_alias4)

		####################### Load the Alias #5 Entry ###################################

		self.alias5 = gtkbuilder.get_object("alias5")
		self.alias5.set_text("%s" % gdb.get_string(gbase + "alias/five"))

		def set_alias5(widget, data=None):
			gdb.set_string(gbase + "alias/five", widget.get_text())

		self.alias5.connect("insert-text", emit_text)
		self.alias5.connect("changed", set_alias5)

		####################### Load the Alias #6 Entry ###################################

		self.alias6 = gtkbuilder.get_object("alias6")
		self.alias6.set_text("%s" % gdb.get_string(gbase + "alias/six"))

		def set_alias6(widget, data=None):
			gdb.set_string(gbase + "alias/six", widget.get_text())

		self.alias6.connect("insert-text", emit_text)
		self.alias6.connect("changed", set_alias6)

		####################### Load the Alias #7 Entry ###################################

		self.alias7 = gtkbuilder.get_object("alias7")
		self.alias7.set_text("%s" % gdb.get_string(gbase + "alias/seven"))

		def set_alias7(widget, data=None):
			gdb.set_string(gbase + "alias/seven", widget.get_text())

		self.alias7.connect("insert-text", emit_text)
		self.alias7.connect("changed", set_alias7)

		####################### Load the Alias #8 Entry ###################################

		self.alias8 = gtkbuilder.get_object("alias8")
		self.alias8.set_text("%s" % gdb.get_string(gbase + "alias/eight"))

		def set_alias8(widget, data=None):
			gdb.set_string(gbase + "alias/eight", widget.get_text())

		self.alias8.connect("insert-text", emit_text)
		self.alias8.connect("changed", set_alias8)

		####################### Load the Alias #9 Entry ###################################

		self.alias9 = gtkbuilder.get_object("alias9")
		self.alias9.set_text("%s" % gdb.get_string(gbase + "alias/nine"))

		def set_alias9(widget, data=None):
			gdb.set_string(gbase + "alias/nine", widget.get_text())

		self.alias9.connect("insert-text", emit_text)
		self.alias9.connect("changed", set_alias9)

		def emit_text(widget, text, *args):
			if text in blacklist:
				widget.emit_stop_by_name('insert-text')

		####################### Load the Reset History Button #############################

		self.reset_history = gtkbuilder.get_object("reset_history")

		def do_reset_history(widget, data=None):
			os.remove(os.path.expanduser("~/.bash_history"))

		self.reset_history.connect("clicked", do_reset_history)

		####################### Load the History Control Combobox #########################

		self.history_control = gtkbuilder.get_object("history_control")

		history_types = {
				 0 : "erasedups",
				 1 : "ignoredups",
				 2 : "ignorespace",
				 3 : "ignoreboth",
				}

		self.history_control.set_active(swap_dic(history_types)[gdb.get_string(gbase + "hist_control")])

		def set_history_control(widget, data=None):
			selection = widget.get_active()
			gdb.set_string(gbase + "hist_control", history_types[selection])

		self.history_control.connect("changed", set_history_control)

		####################### Load the History Blacklist Entry ##########################

		self.history_blacklist = gtkbuilder.get_object("history_blacklist")
		self.history_blacklist.set_text(gdb.get_string(gbase + "hist_ignore"))

		def set_history_blacklist(widget, data=None):
			gdb.set_string(gbase + "hist_ignore", widget.get_text())

		self.history_blacklist.connect("insert-text", emit_text)
		self.history_blacklist.connect("changed", set_history_blacklist)

		####################### Load the History Size Entry ###############################

		self.history_size = gtkbuilder.get_object("history_size")
		self.history_size.set_value(gdb.get_int(gbase + "history_size"))

		def set_history_size(widget, data=None):
			gdb.set_int(gbase + "history_size", widget.get_value_as_int())

		self.history_size.connect("value-changed", set_history_size)

		####################### Load the Separator Entry ##################################

		self.separator = gtkbuilder.get_object("separator")
		self.separator.set_text(gdb.get_string(gbase + "separator/separator"))

		def set_separator(widget, data=None):
			gdb.set_string(gbase + "separator/separator", widget.get_text())

		self.separator.connect("insert-text", emit_text)
		self.separator.connect("changed", set_separator)

		####################### Load the PS234 Char Entry #################################

		self.ps234 = gtkbuilder.get_object("ps234")
		self.ps234.set_text(gdb.get_string(gbase + "ps234"))

		def set_ps234(widget, data=None):
			gdb.set_string(gbase + "ps234", widget.get_text())

		self.ps234.connect("insert-text", emit_text)
		self.ps234.connect("changed", set_ps234)

		####################### Load the PWD Cutter Entry #################################

		self.pwd_cutter = gtkbuilder.get_object("pwd_cutter")
		self.pwd_cutter.set_text(gdb.get_string(gbase + "pwdchar"))

		def set_pwd_cutter(widget, data=None):
			gdb.set_string(gbase + "pwd_char", widget.get_text())

		self.pwd_cutter.connect("insert-text", emit_text)
		self.pwd_cutter.connect("changed", set_pwd_cutter)

		####################### Load the PWD Length Entry #################################

		self.pwd_len = gtkbuilder.get_object("pwd_len")
		self.pwd_len.set_value(gdb.get_int(gbase + "pwdmaxlength"))

		def set_pwd_len(widget, data=None):
			gdb.set_int(gbase + "pwdmaxlength", widget.get_value_as_int())

		self.pwd_len.connect("value-changed", set_pwd_len)

		####################### Load the CDPATH Entry #####################################

		self.cdpath = gtkbuilder.get_object("cdpath")
		self.cdpath.set_text(gdb.get_string(gbase + "cdpath"))

		def set_cdpath(widget, data=None):
			gdb.set_string(gbase + "cdpath", widget.get_text())

		self.cdpath.connect("insert-text", emit_text)
		self.cdpath.connect("changed", set_cdpath)

		####################### Load the Completion Blacklist Entry #######################

		self.completion_blacklist = gtkbuilder.get_object("completion_blacklist")
		self.completion_blacklist.set_text(gdb.get_string(gbase + "fignore"))

		def set_completion_blacklist(widget, data=None):
			gdb.set_string(gbase + "fignore", widget.get_text())

		self.completion_blacklist.connect("insert-text", emit_text)
		self.completion_blacklist.connect("changed", set_completion_blacklist)

		####################### Load the Timeout Entry ####################################

		self.timeout = gtkbuilder.get_object("timeout")
		self.timeout.set_value(gdb.get_int(gbase + "timeout"))

		def set_timeout(widget, data=None):
			gdb.set_int(gbase + "timeout", widget.get_value_as_int())

		self.timeout.connect("value-changed", set_timeout)

		####################### Load the FCEDITOR Entry ###################################

		self.fcedit = gtkbuilder.get_object("fcedit")
		self.fcedit.set_text(gdb.get_string(gbase + "fcedit"))

		def set_fcedit(widget, data=None):
			gdb.set_string(gbase + "fcedit", widget.get_text())

		self.fcedit.connect("insert-text", emit_text)
		self.fcedit.connect("changed", set_fcedit)

		####################### Load the Welcome Message Entry ############################

		self.welcome = gtkbuilder.get_object("welcome")
		self.welcome.set_text(gdb.get_string(gbase + "welcome_message"))

		def set_welcome(widget, data=None):
			gdb.set_string(gbase + "welcome_message", widget.get_text())

		self.welcome.connect("insert-text", emit_text)
		self.welcome.connect("changed", set_welcome)

		####################### Load the PATH Entry #######################################

		self.path = gtkbuilder.get_object("path")
		self.path.set_text(gdb.get_string(gbase + "path"))

		def set_path(widget, data=None):
			gdb.set_string(gbase + "path", widget.get_text())

		self.path.connect("insert-text", emit_text)
		self.path.connect("changed", set_path)

		####################### Connect the Use Readlinecfg Button ########################

		self.readline = gtkbuilder.get_object("readline")
		self.readline.set_active(gdb.get_bool(gbase + "readline/use_readlinecfg"))

		def set_readline(widget, data=None):
			gdb.set_bool(gbase + "readline/use_readlinecfg", widget.get_active())

		self.readline.connect("clicked", set_readline)

		####################### Connect the Completion Button #############################

		self.completion = gtkbuilder.get_object("completion")
		self.completion.set_active(gdb.get_bool(gbase + "readline/completion"))

		def set_completion(widget, data=None):
			gdb.set_bool(gbase + "readline/completion", widget.get_active())

		self.completion.connect("clicked", set_completion)

		####################### Connect the Bellstyle Combobox ############################

		self.bellstyle = gtkbuilder.get_object("bellstyle")

		bell_styles = {
				0 : "audible",
				1 : "visible",
				2 : "none",
			      }

		self.bellstyle.set_active(swap_dic(bell_styles)[gdb.get_string(gbase + "readline/bellstyle")])

		def set_bellstyle(widget, data=None):
			selection = widget.get_active()
			gdb.set_string(gbase + "readline/bellstyle", bell_styles[selection])

		self.bellstyle.connect("changed", set_bellstyle)

		####################### Connect the Editing Mode Combobox #########################

		self.editmode = gtkbuilder.get_object("editmode")

		edit_modes = {
			      0 : "emacs",
			      1 : "vi",
			     }

		self.editmode.set_active(swap_dic(edit_modes)[gdb.get_string(gbase + "readline/editing_mode")])

		def set_editmode(widget, data=None):
			selection = widget.get_active()
			gdb.set_string(gbase + "readline/editing_mode", edit_modes[selection])

		self.editmode.connect("changed", set_editmode)

		####################### Connect the Ambiguous Button ##################################

		self.ambiguous = gtkbuilder.get_object("ambiguous")
		self.ambiguous.set_active(gdb.get_bool(gbase + "readline/ambiguous"))

		def set_ambiguous(widget, data=None):
			gdb.set_bool(gbase + "readline/ambiguous", widget.get_active())

		self.ambiguous.connect("clicked", set_ambiguous)

		####################### Connect the Match Hidden Button ###########################

		self.match_hidden = gtkbuilder.get_object("match_hidden")
		self.match_hidden.set_active(gdb.get_bool(gbase + "readline/hidden"))

		def set_match_hidden(widget, data=None):
			gdb.set_bool(gbase + "readline/hidden", widget.get_active())

		self.match_hidden.connect("clicked", set_match_hidden)

		####################### Connect the Ignore Case Button ############################

		self.ignore_case = gtkbuilder.get_object("ignore_case")
		self.ignore_case.set_active(gdb.get_bool(gbase + "readline/ignorecase"))

		def set_ignore_case(widget, data=None):
			gdb.set_bool(gbase + "readline/ignorecase", widget.get_active())

		self.ignore_case.connect("clicked", set_ignore_case)

		####################### Connect the Query Items Button ############################

		self.query_items = gtkbuilder.get_object("query_items")
		self.query_items.set_value(gdb.get_int(gbase + "readline/query_item"))

		def set_query_items(widget, data=None):
			gdb.set_int(gbase + "readline/query_item", widget.get_value_as_int())

		self.query_items.connect("value-changed", set_query_items)

		####################### Connect the Horizontal Completion Button ##################

		self.completion_hz = gtkbuilder.get_object("completion_hz")
		self.completion_hz.set_active(gdb.get_bool(gbase + "readline/completion_hz"))

		def set_completion_hz(widget, data=None):
			gdb.set_bool(gbase + "readline/completionhz", widget.get_active())

		self.completion_hz.connect("clicked", set_completion_hz)

		####################### Connect the Mark Directories Button #######################

		self.mark_dirs = gtkbuilder.get_object("mark_dirs")
		self.mark_dirs.set_active(gdb.get_bool(gbase + "readline/mark_dirs"))

		def set_mark_dirs(widget, data=None):
			gdb.set_bool(gbase + "readline/mark_dirs", widget.get_active())

		self.mark_dirs.connect("clicked", set_mark_dirs)

		####################### Connect the Mark Symbolic Directories Button ##############

		self.mark_symdirs = gtkbuilder.get_object("mark_symdirs")
		self.mark_symdirs.set_active(gdb.get_bool(gbase + "readline/mark_sym_dirs"))

		def set_mark_symdirs(widget, data=None):
			gdb.set_bool(gbase + "readline/mark_sym_dirs", widget.get_active())

		self.mark_symdirs.connect("clicked", set_mark_symdirs)

		####################### Connect the Visible Stats Button ##########################

		self.vstats = gtkbuilder.get_object("vstats")
		self.vstats.set_active(gdb.get_bool(gbase + "readline/vstats"))

		def set_vstats(widgets, data=None):
			gdb.set_bool(gbase + "readline/vstats", widgets.get_active())

		self.vstats.connect("clicked", set_vstats)

		####################### Connect the Horizontal Scroll Button ######################

		self.scroll_hz = gtkbuilder.get_object("scroll_hz")
		self.scroll_hz.set_active(gdb.get_bool(gbase + "readline/scroll_hz"))

		def set_scroll_hz(widget, data=None):
			gdb.set_bool(gbase + "readline/scroll_hz", widget.get_active())

		self.scroll_hz.connect("clicked", set_scroll_hz)

		####################### Connect the Mark Modified Lines Button ####################

		self.modlines = gtkbuilder.get_object("modlines")
		self.modlines.set_active(gdb.get_bool(gbase + "readline/mark_modlines"))

		def set_modlines(widget, data=None):
			gdb.set_bool(gbase + "readline/mark_modlines", widget.get_active())

		self.modlines.connect("clicked", set_modlines)

		####################### Connect the Show Files Amount Button ######################

		self.show_files_amount = gtkbuilder.get_object("show_files_amount")
		self.show_files_amount.set_active(gdb.get_bool(gbase + "separator/files_amount"))

		def set_show_files_amount(widget, data=None):
			gdb.set_bool(gbase + "separator/files_amount", widget.get_active())

		self.show_files_amount.connect("clicked", set_show_files_amount)

		####################### Connect the Show Uptime Button ############################

		self.show_uptime = gtkbuilder.get_object("show_uptime")
		self.show_uptime.set_active(gdb.get_bool(gbase + "separator/uptime"))

		def set_show_uptime(widget, data=None):
			gdb.set_bool(gbase + "separator/show_uptime", widget.get_active())

		self.show_uptime.connect("clicked", set_show_uptime)

		####################### Connect the Show Files Size Button ########################

		self.show_file_size = gtkbuilder.get_object("show_file_size")
		self.show_file_size.set_active(gdb.get_bool(gbase + "separator/file_size"))

		def set_show_file_size(widget, data=None):
			gdb.set_bool(gbase + "separator/file_size", widget.get_active())

		self.show_file_size.connect("clicked", set_show_file_size)

		####################### Connect the Show TTY Button ##############################

		self.show_tty = gtkbuilder.get_object("show_tty")
		self.show_tty.set_active(gdb.get_bool(gbase + "separator/tty"))

		def set_show_tty(widget, data=None):
			gdb.set_bool(gbase + "separator/tty", widget.get_active())

		self.show_tty.connect("clicked", set_show_tty)

		####################### Connect the Show Running Processes Button #################

		self.show_processes = gtkbuilder.get_object("show_processes")
		self.show_processes.set_active(gdb.get_bool(gbase + "separator/show_processes"))

		def set_show_processes(widget, data=None):
			gdb.set_bool(gbase + "separator/processes", widget.get_active())

		self.show_processes.connect("clicked", set_show_processes)

		####################### Connect the Show Systemload Button ########################

		self.show_load = gtkbuilder.get_object("show_load")
		self.show_load.set_active(gdb.get_bool(gbase + "separator/load"))

		def set_show_load(widget, data=None):
			gdb.set_bool(gbase + "separator/load", widget.get_active())

		self.show_processes.connect("clicked", set_show_load)

		####################### Connect the Show Batteryload Button #######################

		self.show_battery = gtkbuilder.get_object("show_battery")
		self.show_battery.set_active(gdb.get_bool(gbase + "separator/battery_load"))

		def set_show_battery(widget, data=None):
			gdb.set_bool(gbase + "separator/battery_load", widget.get_active())

		self.show_battery.connect("clicked", set_show_battery)

		####################### Connect the Show Memory Combobox ##########################

		self.show_mem = gtkbuilder.get_object("show_mem")

		memory_types = {
				0 : "free",
				1 : "used",
				2 : "both",
				3 : "none",
			       }

		self.show_mem.set_active(swap_dic(memory_types)[gdb.get_string(gbase + "separator/mem")])

		def set_show_mem(widget, data=None):
			selection = widget.get_active()
			gdb.set_string(gbase + "separator/mem", memory_types[selection])

		self.show_mem.connect("changed", set_show_mem)

		def emit_text(widget, text, *args):
			if text in blacklist:
				widget.emit_stop_by_name('insert-text')

		####################### Connect the Dirchar Entry #################################

		self.dirchar = gtkbuilder.get_object("dirchar")
		self.dirchar.set_text(gdb.get_string(gbase + "dirchar"))

		def set_dirchar(widget, data=None):
			gdb.set_string(gbase + "dirchar", widget.get_text())

		self.dirchar.connect("insert-text", emit_text)
		self.dirchar.connect("changed", set_dirchar)

		####################### Connect the Tab Rotation Button ###########################

		self.tabrotate = gtkbuilder.get_object("tabrotate")
		self.tabrotate.set_active(gdb.get_bool(gbase + "tabrotate"))

		def set_tabrotate(widget, data=None):
			gdb.set_bool(gbase + "tabrotate", widget.get_active())

		self.tabrotate.connect("clicked", set_tabrotate)

		####################### Connect the histappend Button ###########################

		self.histappend = gtkbuilder.get_object("histappend")
		self.histappend.set_active(gdb.get_bool(gbase + "shopt/histappend"))

		def set_histappend(widget, data=None):
			gdb.set_bool(gbase + "shopt/histappend", widget.get_active())

		self.histappend.connect("clicked", set_histappend)

		####################### Connect the cdspell Button ###########################

		self.cdspell = gtkbuilder.get_object("cdspell")
		self.cdspell.set_active(gdb.get_bool(gbase + "shopt/cdspell"))

		def set_cdspell(widget, data=None):
			gdb.set_bool(gbase + "shopt/cdspell", widget.get_active())

		self.cdspell.connect("clicked", set_cdspell)

		####################### Connect the cdable_vars Button ###########################

		self.cdable_vars = gtkbuilder.get_object("cdable_vars")
		self.cdable_vars.set_active(gdb.get_bool(gbase + "shopt/cdable_vars"))

		def set_cdable_vars(widget, data=None):
			gdb.set_bool(gbase + "shopt/cdable_vars", widget.get_active())

		self.cdable_vars.connect("clicked", set_cdable_vars)

		####################### Connect the checkhash Button ###########################

		self.checkhash = gtkbuilder.get_object("checkhash")
		self.checkhash.set_active(gdb.get_bool(gbase + "shopt/checkhash"))

		def set_checkhash(widget, data=None):
			gdb.set_bool(gbase + "shopt/checkhash", widget.get_active())

		self.checkhash.connect("clicked", set_checkhash)

		####################### Connect the cmdhist Button ###########################

		self.cmdhist = gtkbuilder.get_object("cmdhist")
		self.cmdhist.set_active(gdb.get_bool(gbase + "shopt/cmdhist"))

		def set_cmdhist(widget, data=None):
			gdb.set_bool(gbase + "shopt/cmdhist", widget.get_active())

		self.cmdhist.connect("clicked", set_cmdhist)

		####################### Connect the force_fignore Button ###########################

		self.force_fignore = gtkbuilder.get_object("force_fignore")
		self.force_fignore.set_active(gdb.get_bool(gbase + "shopt/force_fignore"))

		def set_force_fignore(widget, data=None):
			gdb.set_bool(gbase + "shopt/force_fignore", widget.get_active())

		self.force_fignore.connect("clicked", set_force_fignore)

		####################### Connect the histreedit Button ###########################

		self.histreedit = gtkbuilder.get_object("histreedit")
		self.histreedit.set_active(gdb.get_bool(gbase + "shopt/histreedit"))

		def set_histreedit(widget, data=None):
			gdb.set_bool(gbase + "shopt/histreedit", widget.get_active())

		self.histreedit.connect("clicked", set_histreedit)

		####################### Connect the no_empty_cmd Button ###########################

		self.no_empty_cmd = gtkbuilder.get_object("no_empty_cmd")
		self.no_empty_cmd.set_active(gdb.get_bool(gbase + "shopt/no_empty_cmd_completion"))

		def set_no_empty_cmd(widget, data=None):
			gdb.set_bool(gbase + "shopt/no_empty_cmd_completion", widget.get_active())

		self.no_empty_cmd.connect("clicked", set_no_empty_cmd)

		####################### Connect the autocd Button ###########################

		self.autocd = gtkbuilder.get_object("autocd")
		self.autocd.set_active(gdb.get_bool(gbase + "shopt/autocd"))

		def set_autocd(widget, data=None):
			gdb.set_bool(gbase + "shopt/autocd", widget.get_active())

		self.autocd.connect("clicked", set_autocd)

		####################### Connect the checkjobs Button ###########################

		self.checkjobs = gtkbuilder.get_object("checkjobs")
		self.checkjobs.set_active(gdb.get_bool(gbase + "shopt/checkjobs"))

		def set_checkjobs(widget, data=None):
			gdb.set_bool(gbase + "shopt/checkjobs", widget.get_active())

		self.checkjobs.connect("clicked", set_checkjobs)

		####################### Connect the globstar Button ###########################

		self.globstar = gtkbuilder.get_object("globstar")
		self.globstar.set_active(gdb.get_bool(gbase + "shopt/globstar"))

		def set_globstar(widget, data=None):
			gdb.set_bool(gbase + "shopt/globstar", widget.get_active())

		self.globstar.connect("clicked", set_globstar)

		####################### Connect the dirspell Button ###########################

		self.dirspell = gtkbuilder.get_object("dirspell")
		self.dirspell.set_active(gdb.get_bool(gbase + "shopt/dirspell"))

		def set_dirspell(widget, data=None):
			gdb.set_bool(gbase + "shopt/dirspell", widget.get_active())

		self.dirspell.connect("clicked", set_dirspell)

		####################### Connect the Export Profile Button #########################

		self.export_profile = gtkbuilder.get_object("export_profile")

		def do_export_profile(widget, data=None):
			subprocess.Popen("bs-ng-profiler --export", shell=True)

		self.export_profile.connect("clicked", do_export_profile)

		####################### Connect the Import Profile Button #########################

		self.import_profile = gtkbuilder.get_object("import_profile")

		def do_import_profile(widget, data=None):
			subprocess.Popen("bs-ng-profiler --import " + widget.get_filename(), shell=True)

		self.import_profile.connect("file-set", do_import_profile)

		####################### Connect the Bashrc Button #################################

		self.make_bashrc = gtkbuilder.get_object("make_bashrc")

		def do_make_bashrc(widget, data=None):
			subprocess.Popen("rcgenerator --bash", shell=True)

		self.make_bashrc.connect("clicked", do_make_bashrc)

		####################### Connect the Inputrc Button ################################

		self.make_inputrc = gtkbuilder.get_object("make_inputrc")

		def do_make_inputrc(widget, data=None):
			subprocess.Popen("rcgenerator --readline", shell=True)

		self.make_inputrc.connect("clicked", do_make_inputrc)

		####################### Connect the Vimrc Button ##################################

		self.make_vimrc = gtkbuilder.get_object("make_vimrc")

		def do_make_vimrc(widget, data=None):
			subprocess.Popen("rcgenerator --vim", shell=True)

		self.make_vimrc.connect("clicked", do_make_vimrc)

		####################### Connect the Nanorc Button #################################

		self.make_nanorc = gtkbuilder.get_object("make_nanorc")

		def do_make_nanorc(widget, data=None):
			subprocess.Popen("rcgenerator --nano", shell=True)

		self.make_nanorc.connect("clicked", do_make_nanorc)

		####################### Connect the All RC Button ##################################

		self.make_allrc = gtkbuilder.get_object("make_allrc")

		def do_make_allrc(widget, data=None):
			subprocess.Popen("rcgenerator --all", shell=True)

		self.make_allrc.connect("clicked", do_make_allrc)

		def emit_text(widget, text, *args):
			if text in blacklist:
				widget.emit_stop_by_name('insert-text')

		####################### Connect the Use VimCFG Button #############################

		self.use_vimcfg = gtkbuilder.get_object("use_vimcfg")
		self.use_vimcfg.set_active(gdb.get_bool(gbase + "vim/use_vimcfg"))

		def set_use_vimcfg(widget, data=None):
			gdb.set_bool(gbase + "vim/use_vimcfg", widget.get_active())

		self.use_vimcfg.connect("clicked", set_use_vimcfg)

		####################### Connect the Vim/Backup files Button #######################

		self.vim_backup = gtkbuilder.get_object("vim_backup")
		self.vim_backup.set_active(gdb.get_bool(gbase + "vim/backup"))

		def set_vim_backup(widget, data=None):
			gdb.set_bool(gbase + "vim/backup", widget.get_active())

		self.vim_backup.connect("clicked", set_vim_backup)

		####################### Connect the Vim/Jump Back Button ##########################

		self.vim_jump = gtkbuilder.get_object("vim_jump")
		self.vim_jump.set_active(gdb.get_bool(gbase + "vim/jump_back"))

		def set_vim_jump(widget, data=None):
			gdb.set_bool(gbase + "vim/jump_back", widget.get_active())

		self.vim_jump.connect("clicked", set_vim_jump)

		###################### Connect the Vim/Jump to start of line Button ##############

		self.vim_sline = gtkbuilder.get_object("vim_sline")
		self.vim_sline.set_active(gdb.get_bool(gbase + "vim/startofline"))

		def set_vim_sline(widget, data=None):
			gdb.set_bool(gbase + "vim/startofline", widget.get_active())

		self.vim_sline.connect("clicked", set_vim_sline)

		##################### Connect the Vim/Tabstop Button ##############################

		self.vim_tabstop = gtkbuilder.get_object("vim_tabstop")
		self.vim_tabstop.set_value(gdb.get_int(gbase + "vim/tabstop"))

		def set_vim_tabstop(widget, data=None):
			gdb.set_int(gbase + "vim/tabstop", widget.get_value_as_int())

		self.vim_tabstop.connect("value-changed", set_vim_tabstop)

		####################### Connect the Vim/Autowrap Entry ############################

		self.vim_autowrap = gtkbuilder.get_object("vim_autowrap")
		self.vim_autowrap.set_value(gdb.get_int(gbase + "vim/wrap_length"))

		def set_vim_autowrap(widget, data=None):
			gdb.set_int(gbase + "vim/wrap_length", widget.get_value_as_int())

		self.vim_autowrap.connect("value-changed", set_vim_autowrap)

		####################### Connect the Vim/Wrap line Button ##########################

		self.vim_wrap = gtkbuilder.get_object("vim_wrap")
		self.vim_wrap.set_active(gdb.get_bool(gbase + "vim/wrap"))

		def set_vim_wrap(widget, data=None):
			gdb.set_bool(gbase + "vim/wrap", widget.get_active())

		self.vim_wrap.connect("clicked", set_vim_wrap)

		###################### Connect the Vim/Autochdir Button ##########################

		self.vim_cd = gtkbuilder.get_object("vim_cd")
		self.vim_cd.set_active(gdb.get_bool(gbase + "vim/chdir"))

		def set_vim_cd(widget, data=None):
			gdb.set_bool(gbase + "vim/chdir", widget.get_active())

		self.vim_cd.connect("clicked", set_vim_cd)

		####################### Connect the Vim/Indention Button ##########################

		self.vim_indent = gtkbuilder.get_object("vim_indent")
		self.vim_indent.set_active(gdb.get_bool(gbase + "vim/filetype_indent"))

		def set_vim_indent(widget, data=None):
			gdb.set_bool(gbase + "vim/filetype_indent", widget.get_active())

		self.vim_indent.connect("clicked", set_vim_indent)

		####################### Connect the Vim/Show (partial) command Button #############

		self.vim_cmd = gtkbuilder.get_object("vim_cmd")
		self.vim_cmd.set_active(gdb.get_bool(gbase + "vim/show_cmd"))

		def set_vim_cmd(widget, data=None):
			gdb.set_bool(gbase + "vim/show_cmd", widget.get_active())

		self.vim_cmd.connect("clicked", set_vim_cmd)

		####################### Connect the Vim/Match Brackets Button #####################

		self.vim_match = gtkbuilder.get_object("vim_match")
		self.vim_match.set_active(gdb.get_bool(gbase + "vim/show_match"))

		def set_vim_match(widget, data=None):
			gdb.set_bool(gbase + "vim/show_match", widget.get_active())

		self.vim_match.connect("clicked", set_vim_match)

		####################### Connect the Vim/Syntax Highlight Button ###################

		self.vim_syntax = gtkbuilder.get_object("vim_syntax")
		self.vim_syntax.set_active(gdb.get_bool(gbase + "vim/syntax_hilight"))

		def set_vim_syntax(widget, data=None):
			gdb.set_bool(gbase + "vim/syntax_hilight", widget.get_active())

		self.vim_syntax.connect("clicked", set_vim_syntax)

		####################### Connect the Vim/Background Button #########################

		self.vim_bg = gtkbuilder.get_object("vim_bg")
		self.vim_bg.set_active(gdb.get_bool(gbase + "vim/dark_background"))

		def set_vim_bg(widget, data=None):
			gdb.set_bool(gbase + "vim/dark_background", widget.get_active())

		self.vim_bg.connect("clicked", set_vim_bg)

		####################### Connect the Vim/Case-Insensitive Button ###################

		self.vim_icase = gtkbuilder.get_object("vim_icase")
		self.vim_icase.set_active(gdb.get_bool(gbase + "vim/ignore_case"))

		def set_vim_icase(widget, data=None):
			gdb.set_bool(gbase + "vim/ignore_case", widget.get_active())

		self.vim_icase.connect("clicked", set_vim_icase)

		####################### Connect the Vim/Smart-Case Button #########################

		self.vim_scase = gtkbuilder.get_object("vim_scase")
		self.vim_scase.set_active(gdb.get_bool(gbase + "vim/smart_case"))

		def set_vim_scase(widget, data=None):
			gdb.set_bool(gbase + "vim/smart_case", widget.get_active())

		self.vim_scase.connect("clicked", set_vim_scase)

		####################### Connect the Vim/Incremental Search Button #################

		self.vim_isearch = gtkbuilder.get_object("vim_isearch")
		self.vim_isearch.set_active(gdb.get_bool(gbase + "vim/inc_search"))

		def set_vim_isearch(widget, data=None):
			gdb.set_bool(gbase + "vim/inc_search", widget.get_active())

		self.vim_isearch.connect("clicked", set_vim_isearch)

		####################### Connect the Vim/Hilight Matches Button ####################

		self.vim_hilight = gtkbuilder.get_object("vim_hilight")
		self.vim_hilight.set_active(gdb.get_bool(gbase + "vim/highlight"))

		def set_vim_hilight(widget, data=None):
			gdb.set_bool(gbase + "vim/highlight", widget.get_active())

		self.vim_hilight.connect("clicked", set_vim_hilight)

		####################### Connect the Vim/Linenumber Button #########################

		self.vim_number = gtkbuilder.get_object("vim_number")
		self.vim_number.set_active(gdb.get_bool(gbase + "vim/number"))

		def set_vim_number(widget, data=None):
			gdb.set_bool(gbase + "vim/number", widget.get_active())

		self.vim_number.connect("clicked", set_vim_number)

		####################### Connect the Vim/Autosave Button ###########################

		self.vim_save = gtkbuilder.get_object("vim_save")
		self.vim_save.set_active(gdb.get_bool(gbase + "vim/autosave"))

		def set_vim_save(widget, data=None):
			gdb.set_bool(gbase + "vim/autosave", widget.get_active())

		self.vim_save.connect("clicked", set_vim_save)

		####################### Connect the Vim/Highlight Line Button #####################

		self.vim_hiline = gtkbuilder.get_object("vim_hiline")
		self.vim_hiline.set_active(gdb.get_bool(gbase + "vim/hl_cursor"))

		def set_vim_hiline(widget, data=None):
			gdb.set_bool(gbase + "vim/hl_cursor", widget.get_active())

		self.vim_hiline.connect("clicked", set_vim_hiline)

		####################### Connect the Vim/Highlight Column Button ###################

		self.vim_hicol = gtkbuilder.get_object("vim_hicol")
		self.vim_hicol.set_active(gdb.get_bool(gbase + "vim/hl_column"))

		def set_vim_hicol(widget, data=None):
			gdb.set_bool(gbase + "vim/hl_column", widget.get_active())

		self.vim_hicol.connect("clicked", set_vim_hicol)

		####################### Connect the Vim/Show Ruler Button #########################

		self.vim_ruler = gtkbuilder.get_object("vim_ruler")
		self.vim_ruler.set_active(gdb.get_bool(gbase + "vim/ruler"))

		def set_vim_ruler(widget, data=None):
			gdb.set_bool(gbase + "vim/ruler", widget.get_active())

		self.vim_ruler.connect("clicked", set_vim_ruler)

		####################### Connect the Vim/Colorscheme Combobox ######################

		self.vim_colorscheme = gtkbuilder.get_object("vim_colorscheme")

		vim_colors = {
			       0 : "default",
			       1 : "adaryn",
			       2 : "advantage",
			       3 : "desert",
			       4 : "gobo",
			       5 : "impact",
			       6 : "nightshade",
			       7 : "nightwish",
			       8 : "wombat",
			       9 : "asu1dark",
			      10 : "candycode",
			      11 : "dw_orange",
			      12 : "fruit",
			      13 : "relaxedgreen",
			      14 : "tango",
			     }

		self.vim_colorscheme.set_active(swap_dic(vim_colors)[gdb.get_string(gbase + "vim/vim_colorscheme")])

		def set_vim_colorscheme(widget, data=None):
			selection = widget.get_active()
			gdb.set_string(gbase + "vim/vim_colorscheme", vim_colors[selection])

		self.vim_colorscheme.connect("changed", set_vim_colorscheme)

		####################### Connect the Rulerformat Entry #############################

		self.vim_rulerformat = gtkbuilder.get_object("vim_rulerformat")
		self.vim_rulerformat.set_text(gdb.get_string(gbase + "vim/rulerformat"))

		def set_vim_rulerformat(widget, data=None):
			gdb.set_string(gbase + "vim/rulerformat", widget.get_text())

		self.vim_rulerformat.connect("insert-text", emit_text)
		self.vim_rulerformat.connect("changed", set_vim_rulerformat)

		####################### Connect the Use Nanocfg Button ############################

		self.use_nanocfg = gtkbuilder.get_object("use_nanocfg")
		self.use_nanocfg.set_active(gdb.get_bool(gbase + "nano/use_nanocfg"))

		def set_use_nanocfg(widget, data=None):
			gdb.set_bool(gbase + "nano/use_nanocfg", widget.get_active())

		self.use_nanocfg.connect("clicked", set_use_nanocfg)

		####################### Connect the Nano/Backup Button ############################

		self.nano_backup = gtkbuilder.get_object("nano_backup")
		self.nano_backup.set_active(gdb.get_bool(gbase + "nano/backup"))

		def set_nano_backup(widget, data=None):
			gdb.set_bool(gbase + "nano/backup", widget.get_active())

		self.nano_backup.connect("clicked", set_nano_backup)

		####################### Connect the Nano/Display Cursor Position Button ###########

		self.nano_const = gtkbuilder.get_object("nano_const")
		self.nano_const.set_active(gdb.get_bool(gbase + "nano/const"))

		def set_nano_const(widget, data=None):
			gdb.set_bool(gbase + "nano/const", widget.get_active())

		self.nano_const.connect("clicked", set_nano_const)

		####################### Connect the Nano/Indention Button #########################

		self.nano_indent = gtkbuilder.get_object("nano_indent")
		self.nano_indent.set_active(gdb.get_bool(gbase + "nano/auto_indent"))

		def set_nano_indent(widget, data=None):
			gdb.set_bool(gbase + "nano/auto_indent", widget.get_active())

		self.nano_indent.connect("clicked", set_nano_indent)

		####################### Connect the Nano/Syntax Button ############################

		self.nano_colors = gtkbuilder.get_object("nano_colors")
		self.nano_colors.set_active(gdb.get_bool(gbase + "nano/use_colors"))

		def set_nano_colors(widget, data=None):
			gdb.set_bool(gbase + "nano/use_colors", widget.get_active())

		self.nano_colors.connect("clicked", set_nano_colors)

		####################### Connect the Nano/No Help Button ###########################

		self.nano_nohelp = gtkbuilder.get_object("nano_nohelp")
		self.nano_nohelp.set_active(gdb.get_bool(gbase + "nano/nohelp"))

		def set_nano_nohelp(widget, data=None):
			gdb.set_bool(gbase + "nano/nohelp", widget.get_active())

		self.nano_nohelp.connect("clicked", set_nano_nohelp)

		####################### Connect the Nano/Case-Sensitive Button ####################

		self.nano_case = gtkbuilder.get_object("nano_case")
		self.nano_case.set_active(gdb.get_bool(gbase + "nano/case_sensitive"))

		def set_nano_case(widget, data=None):
			gdb.set_bool(gbase + "nano/case_sensitive", widget.get_active())

		self.nano_case.connect("clicked", set_nano_case)

		####################### Connect the Nano/Bold Text Button #########################

		self.nano_boldtext = gtkbuilder.get_object("nano_boldtext")
		self.nano_boldtext.set_active(gdb.get_bool(gbase + "nano/bold_text"))

		def set_nano_boldtext(widget, data=None):
			gdb.set_bool(gbase + "nano/bold_text", widget.get_active())

		self.nano_boldtext.connect("clicked", set_nano_boldtext)

		####################### Connect the Nano/More Space Button ########################

		self.nano_morespace = gtkbuilder.get_object("nano_morespace")
		self.nano_morespace.set_active(gdb.get_bool(gbase + "nano/more_space"))

		def set_nano_morespace(widget, data=None):
			gdb.set_bool(gbase + "nano/more_space", widget.get_active())

		self.nano_morespace.connect("clicked", set_nano_morespace)

		####################### Connect the Nano/History Button ############################

		self.nano_history = gtkbuilder.get_object("nano_history")
		self.nano_history.set_active(gdb.get_bool(gbase + "nano/history"))

		def set_nano_history(widget, data=None):
			gdb.set_bool(gbase + "nano/history", widget.get_active())

		self.nano_history.connect("clicked", set_nano_history)

		####################### Connect the Nano/Rebind delete Button ######################

		self.nano_rbdel = gtkbuilder.get_object("nano_rbdel")
		self.nano_rbdel.set_active(gdb.get_bool(gbase + "nano/rebind_del"))

		def set_nano_rbdel(widget, data=None):
			gdb.set_bool(gbase + "nano/rebind_del", widget.get_active())

		self.nano_rbdel.connect("clicked", set_nano_rbdel)

		####################### Connect the Nano/Rebind Keypad Button ######################

		self.nano_rbkp = gtkbuilder.get_object("nano_rbkp")
		self.nano_rbkp.set_active(gdb.get_bool(gbase + "nano/rebind_kp"))

		def set_nano_rbkp(widget, data=None):
			gdb.set_bool(gbase + "nano/rebind_kp", widget.get_active())

		self.nano_rbkp.connect("clicked", set_nano_rbkp)

		def emit_text(widget, text, *args):
			if text in blacklist:
				widget.emit_stop_by_name('insert-text')

		####################### Set the ls color for given filetype #######################

		ls_colors = {
			      0 : "$lblack",
			      1 : "$lred",
			      2 : "$lgreen",
			      3 : "$lyellow",
			      4 : "$lblue",
			      5 : "$lmagenta",
			      6 : "$lcyan",
			      7 : "$lwhite",
			      8 : "$lcoldblue",
			      9 : "$lsmoothblue",
			     10 : "$liceblue",
			     11 : "$lturqoise",
			     12 : "$lsmoothgreen",
			     13 : "$lwinered",
			     14 : "$lbrown",
			     15 : "$lsilver",
			     16 : "$locher",
			     17 : "$lorange",
			     18 : "$lpurple",
			     19 : "$lpink",
			     20 : "$lcream",
			    }

		ls_colors_inv = swap_dic(ls_colors)

		def set_ls_color(self, type, selection):
			gdb.set_string(gbase + "dircolors/%s" % type, ls_colors[selection])

		####################### Connect the use LS-COLORS Button ##########################

		self.use_lscolors = gtkbuilder.get_object("use_lscolors")
		self.use_lscolors.set_active(gdb.get_bool(gbase + "dircolors/enable"))

		def set_use_lscolors(widget, data=None):
			gdb.set_bool(gbase + "dircolors/enable", widget.get_active())

		self.use_lscolors.connect("clicked", set_use_lscolors)

		####################### Connect the Executable Files Combobox #####################

		self.ls_exec = gtkbuilder.get_object("ls_exec")
		self.ls_exec.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/exec")])

		def set_ls_exec(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "exec", selection)

		self.ls_exec.connect("changed", set_ls_exec)

		####################### Connect the Generic Files Combobox ########################

		self.ls_gen = gtkbuilder.get_object("ls_gen")
		self.ls_gen.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/generic")])

		def set_ls_gen(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "generic", selection)

		self.ls_gen.connect("changed", set_ls_gen)

		####################### Connect the Log Files Combobox ############################

		self.ls_log = gtkbuilder.get_object("ls_log")
		self.ls_log.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/logs")])

		def set_ls_log(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "logs", selection)

		self.ls_log.connect("changed", set_ls_log)

		####################### Connect the Deb Files Combobox ############################

		self.ls_deb = gtkbuilder.get_object("ls_deb")
		self.ls_deb.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/deb")])

		def set_ls_deb(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "deb", selection)

		self.ls_deb.connect("changed", set_ls_deb)

		####################### Connect the RPM Files Combobox ############################

		self.ls_rpm = gtkbuilder.get_object("ls_rpm")
		self.ls_rpm.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/rpm")])

		def set_ls_rpm(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "rpm", selection)

		self.ls_rpm.connect("changed", set_ls_rpm)

		####################### Connect the Desktop Files Combobox ########################

		self.ls_dirs = gtkbuilder.get_object("ls_dirs")
		self.ls_dirs.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/dirs")])

		def set_ls_dirs(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "dirs", selection)

		self.ls_dirs.connect("changed", set_ls_dirs)

		####################### Connect the JPEG Files Combobox ###########################

		self.ls_jpeg = gtkbuilder.get_object("ls_jpeg")
		self.ls_jpeg.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/jpeg")])

		def set_ls_jpeg(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "jpeg", selection)

		self.ls_jpeg.connect("changed", set_ls_jpeg)

		####################### Connect the PNG Files Combobox ############################

		self.ls_png = gtkbuilder.get_object("ls_png")
		self.ls_png.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/png")])

		def set_ls_png(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "png", selection)

		self.ls_png.connect("changed", set_ls_png)

		####################### Connect the GIF Files Combobox ############################

		self.ls_gif = gtkbuilder.get_object("ls_gif")
		self.ls_gif.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/gif")])

		def set_ls_gif(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "gif", selection)

		self.ls_gif.connect("changed", set_ls_gif)

		####################### Connect the MP3 Files Combobox ############################

		self.ls_mp3 = gtkbuilder.get_object("ls_mp3")
		self.ls_mp3.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/mp3")])

		def set_ls_mp3(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "mp3", selection)

		self.ls_mp3.connect("changed", set_ls_mp3)

		####################### Connect the OGG Files Combobox ############################

		self.ls_ogg = gtkbuilder.get_object("ls_ogg")
		self.ls_ogg.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/ogg")])

		def set_ls_ogg(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "ogg", selection)

		self.ls_ogg.connect("changed", set_ls_ogg)

		####################### Connect the FLAC Files Combobox ###########################

		self.ls_flac = gtkbuilder.get_object("ls_flac")
		self.ls_flac.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/flac")])

		def set_ls_flac(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "flac", selection)

		self.ls_flac.connect("changed", set_ls_flac)

		####################### Connect the TAR Files Combobox ############################

		self.ls_tar = gtkbuilder.get_object("ls_tar")
		self.ls_tar.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/tar")])

		def set_ls_tar(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "tar", selection)

		self.ls_tar.connect("changed", set_ls_tar)

		####################### Connect the TARGZ Files Combobox ##########################

		self.ls_targz = gtkbuilder.get_object("ls_targz")
		self.ls_targz.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/targz")])

		def set_ls_targz(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "targz", selection)

		self.ls_targz.connect("changed", set_ls_targz)

		####################### Connect the TARBZ2 Files Combobox #########################

		self.ls_tarbz2 = gtkbuilder.get_object("ls_tarbz2")
		self.ls_tarbz2.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/tarbz2")])

		def set_ls_tarbz2(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "tarbz2", selection)

		self.ls_tarbz2.connect("changed", set_ls_tarbz2)

		####################### Connect the ZIP Files Combobox ############################

		self.ls_zip = gtkbuilder.get_object("ls_zip")
		self.ls_zip.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/zip")])

		def set_ls_zip(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "zip", selection)

		self.ls_zip.connect("changed", set_ls_zip)

		####################### Connect the RAR Files Combobox ############################

		self.ls_rar = gtkbuilder.get_object("ls_rar")
		self.ls_rar.set_active(ls_colors_inv[gdb.get_string(gbase + "dircolors/rar")])

		def set_ls_rar(widget, data=None):
			selection = widget.get_active()
			set_ls_color(self, "rar", selection)

		self.ls_rar.connect("changed", set_ls_rar)

		####################### Connect the Custom-LS-COLORS Entry ########################

		self.ls_custom = gtkbuilder.get_object("ls_custom")
		self.ls_custom.set_text(gdb.get_string(gbase + "dircolors/custom"))

		def set_ls_custom(widget, data=None):
			gdb.set_string(gbase + "dircolors/custom", widget.get_text())

		self.ls_custom.connect("insert-text", emit_text)
		self.ls_custom.connect("changed", set_ls_custom)

		####################### Connect the PROMPT_COMMAND TextView ########################

		self.prompt_command = gtkbuilder.get_object("prompt_command")

		self.prompt_command_buffer = undobuffer.UndoableBuffer()
		self.prompt_command.set_buffer(self.prompt_command_buffer)
		self.prompt_command_buffer.set_text("%s" % gdb.get_string(gbase + "custom_command"))

		def set_prompt_command(widget, data=None):
			start = widget.get_start_iter()
			end = widget.get_end_iter()
			gdb.set_string(gbase + "custom_command", widget.get_text(start, end))

		self.prompt_command_buffer.connect("changed", set_prompt_command)

		self.active_buffer = "P_C"

		####################### Connect the PS1 TextView ##################################

		self.custom_prompt = gtkbuilder.get_object("custom_prompt")

		self.custom_prompt_buffer = undobuffer.UndoableBuffer()
		self.custom_prompt.set_buffer(self.custom_prompt_buffer)
		self.custom_prompt_buffer.set_text("%s" % gdb.get_string(gbase + "custom_prompt"))

		def set_custom_prompt(widget, data=None):
			start = widget.get_start_iter()
			end = widget.get_end_iter()
			gdb.set_string(gbase + "custom_prompt", widget.get_text(start, end))

		self.custom_prompt_buffer.connect("changed", set_custom_prompt)

		##

		self.place_p_c = gtkbuilder.get_object("place_p_c")

		def do_place_p_c(widget, data=None):
			self.prompt_command.set_sensitive(1)
			self.custom_prompt.set_sensitive(0)
			self.active_buffer = "P_C"

		self.place_p_c.connect("clicked", do_place_p_c)

		##

		self.place_ps1 = gtkbuilder.get_object("place_ps1")

		def do_place_ps1(widget, data=None):
			self.prompt_command.set_sensitive(0)
			self.custom_prompt.set_sensitive(1)
			self.active_buffer = "PS1"

		self.place_ps1.connect("clicked", do_place_ps1)

		##

		def prompt_add(text):
			if self.active_buffer == "P_C":
				self.prompt_command_buffer.insert_at_cursor(text)
			elif self.active_buffer == "PS1":
				self.custom_prompt_buffer.insert_at_cursor(text)

		##

		def prompt_set(text):
			if self.active_buffer == "P_C":
				self.prompt_command_buffer.set_text(text)
			elif self.active_buffer == "PS1":
				self.custom_prompt_buffer.set_text(text)

		####################### Connect the Use Custom Prompt Button #######################

		self.use_custom_prompt = gtkbuilder.get_object("use_custom_prompt")
		self.use_custom_prompt.set_active(gdb.get_bool(gbase + "use_custom_prompt"))

		def set_use_custom_prompt(widget, data=None):
			gdb.set_bool(gbase + "use_custom_prompt", widget.get_active())

		self.use_custom_prompt.connect("clicked", set_use_custom_prompt)

		####################### Connect the Show Toolbox Button ###########################

		self.toolbox = gtkbuilder.get_object("Toolbox")
		self.show_toolbox = gtkbuilder.get_object("show_toolbox")

		def do_show_toolbox(widget, data=None):
			self.toolbox.show_all()

		self.show_toolbox.connect("clicked", do_show_toolbox)

		####################### Connect the Show Help Button ##############################

		self.show_cpb_help = gtkbuilder.get_object("show_cpb_help")

		def do_show_cpb_help(widget, data=None):
			subprocess.Popen("x-www-browser " + PREFIX + "/share/doc/bashstyle-ng/chapter07.html", shell=True)

		self.show_cpb_help.connect("clicked", do_show_cpb_help)

		####################### Connect the Username Button ###############################

		self.username = gtkbuilder.get_object("username")

		def set_username(widget, data=None):
			prompt_add("\\u")

		self.username.connect("clicked", set_username)

		####################### Connect the Hostname Button ###############################

		self.hostname = gtkbuilder.get_object("hostname")

		def set_hostname(widget, data=None):
			prompt_add("\\h")

		self.hostname.connect("clicked", set_hostname)

		####################### Connect the Fullhostname Button ###########################

		self.fhostname = gtkbuilder.get_object("fhostname")

		def set_fhostname(widget, data=None):
			prompt_add("\\H")

		self.fhostname.connect("clicked", set_fhostname)

		####################### Connect the Time Button ###################################

		self.time = gtkbuilder.get_object("time")

		def set_time(widget, data=None):
			prompt_add("\\t")

		self.time.connect("clicked", set_time)

		####################### Connect the Date Button ###################################

		self.date = gtkbuilder.get_object("date")

		def set_date(widget, data=None):
			prompt_add("\\d")

		self.date.connect("clicked", set_date)

		####################### Connect the Sign Button ###################################

		self.sign = gtkbuilder.get_object("sign")

		def set_sign(widget, data=None):
			prompt_add("\\$")

		self.sign.connect("clicked", set_sign)

		####################### Connect the Full Workdir Button ###########################

		self.fworkdir = gtkbuilder.get_object("fworkdir")

		def set_fworkdir(widget, data=None):
			prompt_add("\\w")

		self.fworkdir.connect("clicked", set_fworkdir)

		####################### Connect the Base Workdir Button ############################

		self.workdir = gtkbuilder.get_object("workdir")

		def set_workdir(widget, data=None):
			prompt_add("\\W")

		self.workdir.connect("clicked", set_workdir)

		####################### Connect the EUID Button ###################################

		self.euid = gtkbuilder.get_object("euid")

		def set_euid(widget, data=None):
			prompt_add("\\$EUID")

		self.euid.connect("clicked", set_euid)

		####################### Connect the Jobs Button ###################################

		self.jobs = gtkbuilder.get_object("jobs")

		def set_jobs(widget, data=None):
			prompt_add("\\j")

		self.jobs.connect("clicked", set_jobs)

		####################### Connect the History Number Button #########################

		self.bang = gtkbuilder.get_object("bang")

		def set_bang(widget, data=None):
			prompt_add("\\!")

		self.bang.connect("clicked", set_bang)

		####################### Connect the Session Number Button #########################

		self.number = gtkbuilder.get_object("number")

		def set_number(widget, data=None):
			prompt_add("\\#")

		self.number.connect("clicked", set_number)

		####################### Connect the Bash PID Button ###############################

		self.pid = gtkbuilder.get_object("pid")

		def set_pid(widget, data=None):
			prompt_add("$BASHPID")

		self.pid.connect("clicked", set_pid)

		####################### Connect the Shelllevel Button #############################

		self.shlvl = gtkbuilder.get_object("shlvl")

		def set_shlvl(widget, data=None):
			prompt_add("$SHLVL")

		self.shlvl.connect("clicked", set_shlvl)

		####################### Connect the TruncPWD Button ###############################

		self.truncpwd = gtkbuilder.get_object("truncpwd")

		def set_truncpwd(widget, data=None):
			prompt_add("\\$(trunc_pwd)")

		self.truncpwd.connect("clicked", set_truncpwd)

		####################### Connect the Showsize Button #############################

		self.showsize = gtkbuilder.get_object("showsize")

		def set_showsize(widget, data=None):
			prompt_add("\\$(show_size)")

		self.showsize.connect("clicked", set_showsize)

		####################### Connect the Countfiles Combobox ###########################

		self.countfiles = gtkbuilder.get_object("countfiles")
		self.countfiles.set_active(0)

		counters = {
			    1 : "\\$(count_files +f)",
			    2 : "\\$(count_files -f)",
			   }

		def set_countfiles(widget, data=None):
			selection = widget.get_active()
			if selection != 0:
				prompt_add(counters[selection])

		self.countfiles.connect("changed", set_countfiles)

		####################### Connect the Countprocesses Button #########################

		self.countprocesses = gtkbuilder.get_object("countprocesses")

		def set_countprocesses(widget, data=None):
			prompt_add("\\$(count_processes)")

		self.countprocesses.connect("clicked", set_countprocesses)

		####################### Connect the Showuptime Button #############################

		self.showuptime = gtkbuilder.get_object("showuptime")

		def set_showuptime(widget, data=None):
			prompt_add("\\$(show_uptime)")

		self.showuptime.connect("clicked", set_showuptime)

		####################### Connect the Showload Button ###############################

		self.showload = gtkbuilder.get_object("showload")
		self.showload.set_active(0)

		load_getters = {
				1 : "\\$(show_system_load 1)",
				2 : "\\$(show_system_load 10)",
				3 : "\\$(show_system_load 15)",
			       }

		def set_showload(widget, data=None):
			selection = widget.get_active()
			if selection != 0:
				prompt_add(load_getters[selection])

		self.showload.connect("changed", set_showload)

		####################### Connect the ShowTTY Button ################################

		self.showtty = gtkbuilder.get_object("showtty")

		def set_showtty(widget, data=None):
			prompt_add("\\$(showtty)")

		self.showtty.connect("clicked", set_showtty)

		####################### Connect the Showmem Combobox ##############################

		self.showmem = gtkbuilder.get_object("showmem")
		self.showmem.set_active(0)

		memory_getters = {
				  1 : "\\$(show_mem --used)",
				  2 : "\\$(show_mem --free)",
				  3 : "\\$(show_mem --used-percent)",
				  4 : "\\$(show_mem --free-percent)",
				 }

		def set_showmem(widget, data=None):
			selection = widget.get_active()
			if selection != 0:
				prompt_add(memory_getters[selection])

		self.showmem.connect("changed", set_showmem)

		####################### Connect the Showcpuload Button #############################

		self.showcpuload = gtkbuilder.get_object("showcpuload")

		def set_showcpuload(widget, data=None):
			prompt_add("\\$(show_cpu_load)")

		self.showcpuload.connect("clicked", set_showcpuload)

		####################### Connect the Showbatteryload Combobox ######################

		self.showbatteryload = gtkbuilder.get_object("showbatteryload")
		self.showbatteryload.set_active(0)

		battery_getters = {
				   1 : "\\$(show_battery_load --acpi)",
				   2 : "\\$(show_battery_load --apm)",
				  }

		def set_showbatteryload(widget, data=None):
			selection = widget.get_active()
			if selection != 0:
				prompt_add(battery_getters[selection])

		self.showbatteryload.connect("changed", set_showbatteryload)

		####################### Connect the Showspace Combobox #############################

		self.showspace = gtkbuilder.get_object("showspace")
		self.showspace.set_active(0)

		space_getters = {
				  1 : "\\$(show_space --used <device>)",
				  2 : "\\$(show_space --free <device>)",
				  3 : "\\$(show_space --used-percent <device>)",
				  4 : "\\$(show_space --free-percent <device>)",
				 }

		def set_showspace(widget, data=None):
			selection = widget.get_active()
			if selection != 0:
				prompt_add(space_getters[selection])

		self.showspace.connect("changed", set_showspace)

		####################### Connect the bash seconds Button ###########################

		self.showseconds = gtkbuilder.get_object("showseconds")

		def set_showseconds(widget, data=None):
			prompt_add("${SECONDS}")

		self.showseconds.connect("clicked", set_showseconds)

		####################### Connect the empty PROMPT_COMMAND Button ###################

		self.empty_pc = gtkbuilder.get_object("empty_pc")

		def do_empty_pc(widget, data=None):
			self.prompt_command_buffer.set_text("")

		self.empty_pc.connect("clicked", do_empty_pc)

		####################### Connect the undo PROMPT_COMMAND Button ####################

		self.undo_pc = gtkbuilder.get_object("undo_pc")

		def do_undo_pc(widget, data=None):
			self.prompt_command_buffer.undo()

		self.undo_pc.connect("clicked", do_undo_pc)

		####################### Connect the undo PROMPT_COMMAND Button ####################

		self.redo_pc = gtkbuilder.get_object("redo_pc")

		def do_redo_pc(widget, data=None):
			self.prompt_command_buffer.redo()

		self.redo_pc.connect("clicked", do_redo_pc)

		####################### Connect the emtpy PS1 Button ##############################

		self.empty_ps1 = gtkbuilder.get_object("empty_ps1")

		def do_empty_ps1(widget, data=None):
			self.custom_prompt_buffer.set_text("")

		self.empty_ps1.connect("clicked", do_empty_ps1)

		####################### Connect the undo PS1 Button ####################

		self.undo_ps1 = gtkbuilder.get_object("undo_ps1")

		def do_undo_ps1(widget, data=None):
			self.custom_prompt_buffer.undo()

		self.undo_ps1.connect("clicked", do_undo_ps1)

		####################### Connect the redo PS1 Button ####################

		self.redo_ps1 = gtkbuilder.get_object("redo_ps1")

		def do_redo_ps1(widget, data=None):
			self.custom_prompt_buffer.redo()

		self.redo_ps1.connect("clicked", do_redo_ps1)

		####################### Connect the Insert Symbolic Color Combobox ################

		self.insert_color = gtkbuilder.get_object("insert_color")
		self.insert_color.set_active(0)

		symbolic_colors = {
				   1 : "$usercolor",
				   2 : "$hostcolor",
				   3 : "$datecolor",
				   4 : "$timecolor",
				   5 : "$wdircolor",
				   6 : "$fontcolor",
				   7 : "$sepacolor",
				   8 : "$upcolor",
				   9 : "$pscolor",
				  }

		def do_insert_color(widget, data=None):
			selection = widget.get_active()
			if selection != 0:
				prompt_add(symbolic_colors[selection])

		self.insert_color.connect("changed", do_insert_color)

				####################### Connect the Insert Style Combobox #########################

		self.insert_prompt = gtkbuilder.get_object("insert_prompt")
		self.insert_prompt.set_active(0)

		styles_pc = {
			      1 : "",
			      2 : "",
			      3 : "let prompt_x=$(tput cols)-29\
\ntput sc\
\ntput cup 0 ${prompt_x}\
\necho -n \"[ $(date '+%a, %d %b %y') :: $(date +%T) ]\"\
\ntput rc",
			      4 : "user=\"whoami\"\
\nhost=$(echo -n $HOSTNAME | sed -e \"s/[\.].*//\")\
\ndirchar=$(get_key dirchar)\
\ntrunc_symbol=$(get_key pwdchar)\
\ntrunc_length=$(($(echo $trunc_symbol | wc -m)-1))\
\n\
\nj=4 k=6 l=8 m=10 newPWD=\"${PWD}\" fill=\"\"\
\n\
\nlet promptsize=$(echo -n \"--($user @ $host)---(${PWD})-------\" | wc -c | tr -d \" \")\
\nlet fillsize=${COLUMNS}-${promptsize}\
\n\
\nwhile [ \"$fillsize\" -gt \"0\" ]; do\
\n	fill=\"${fill}─\"; let fillsize=${fillsize}-1\
\ndone\
\n\
\nif [ \"$fillsize\" -lt \"0\" ]; then\
\n	let cutt=${trunc_length}-${fillsize}\
\n	xPWD=\"${trunc_symbol}$(echo -n $PWD | sed -e \"s/\(^.\{$cutt\}\)\(.*\)/\\2/\")\"\
\n	newPWD=\"${xPWD//\//$dirchar}\"\
\nelse	newPWD=\"${PWD//\//$dirchar}\"\
\nfi\
\n\
\n_newPWD () {\
\n	echo -e $newPWD \
\n}\
\n\
\necho -en \"\\033[2;$((${COLUMNS}-29))H\"\
\necho -en \"( $(date +%H:%M) : $(date '+%a, %d %b %y') )────┐\"\
\necho -en \"\\033[2;${COLUMNS}H\"\
\ni=${LINES}\
\n\
\nwhile [ $i -ge 4 ]; do\
\n   if [[ $i == $j ]]; then\
\n	echo -en \"\\033[$j;$((${COLUMNS}-29))H\"\
\n	echo -en \"( system-load: $(show_system_load 1) )────────\"\
\n   fi\
\n   if [[ $i == $k ]]; then\
\n	echo -en \"\\033[$k;$((${COLUMNS}-29))H\"\
\n	echo -en \"( cpu-load: $(show_cpu_load) )────────────\"\
\n   fi\
\n   if [[ $i == $l ]]; then\
\n	echo -en \"\\033[$l;$((${COLUMNS}-29))H\"\
\n	echo -en \"( ram: $(show_mem --used)mb / $(show_mem --free)mb )─────\"\
\n   fi\
\n   if [[ $i == $m ]]; then\
\n	echo -en \"\\033[$m;$((${COLUMNS}-29))H\"\
\n	echo -en \"( processes: $(count_processes) )──────────\"\
\n   fi\
\n   echo -en \"\\033[$(($i-1));${COLUMNS}H│\"\
\n   let i=$i-1\
\ndone\
\nlet prompt_line=${LINES}-1",
			      5 : "",
			      6 : "\
\nlocal one=$(uptime | sed -e \"s/.*load average: \(.*\...\), \(.*\...\), \(.*\...\)/\\1/\" -e \"s/ //g\")\
\nlocal five=$(uptime | sed -e \"s/.*load average: \(.*\...\), \(.*\...\), \(.*\...\).*/\\2/\" -e \"s/ //g\")\
\nlocal diff1_5=$(echo -e \"scale = scale ($one) \\nx=$one - $five\\n if (x>0) {print \\\"up\\\"} else {print \\\"down\\\"}\\n print x \\nquit \\n\" | bc)\
\nloaddiff=\"$(echo -n \"${one}${diff1_5}\" | sed -e 's/down\-/down/g')\"\
\
\nlet files=$(ls -l | grep \"^-\" | wc -l | tr -d \" \")\
\nlet hiddenfiles=$(ls -l -d .* | grep \"^-\" | wc -l | tr -d \" \")\
\nlet executables=$(ls -l | grep ^-..x | wc -l | tr -d \" \")\
\nlet directories=$(ls -l | grep \"^d\" | wc -l | tr -d \" \")\
\nlet hiddendirectories=$(ls -l -d .* | grep \"^d\" | wc -l | tr -d \" \")-2\
\nlet linktemp=$(ls -l | grep \"^l\" | wc -l | tr -d \" \")\
\
\nif [ \"$linktemp\" -eq \"0\" ]\
\nthen\
\nlinks=\"\"\
\nelse\
\nlinks=\" ${linktemp}l\"\
\nfi\
\nunset linktemp\
\nlet devicetemp=$(ls -l | grep \"^[bc]\" | wc -l | tr -d \" \")\
\
\nif [ \"$devicetemp\" -eq \"0\" ]\
\nthen\
\ndevices=\"\"\
\nelse\
\ndevices=\" ${devicetemp}bc\"\
\nfi\
\nunset devicetemp",
			      7 : "",
			      8 : "",
			      9 : "",
			     10 : "",
			     11 : "",
			     12 : "newPWD=\"${PWD}\"\
\nuser=\"whoami\"\
\nhost=$(echo -n $HOSTNAME | sed -e \"s/[\.].*//\")\
\ndatenow=$(date \"+%a, %d %b %y\")\
\nlet promptsize=$(echo -n \"┌( $user @ $host ddd., DD mmm YY)( ${PWD} )┐\" | wc -c | tr -d \" \")\
\n\
\nlet fillsize=${COLUMNS}-${promptsize}\
\n\
\nfill=\"\"\
\nwhile [ \"$fillsize\" -gt \"0\" ]\
\ndo\
\n    fill=\"${fill}─\"\
\n	let fillsize=${fillsize}-1\
\ndone\
\nif [ \"$fillsize\" -lt \"0\" ]\
\nthen\
\n    let cutt=3-${fillsize}\
\n    newPWD=\"...$(echo -n $PWD | sed -e \"s/\(^.\{$cutt\}\)\(.*\)/\2/\")\"\
\nfi",
			    }

		styles_ps1 = {
			       1 : "\\n\u @ \h | \d | \\t | \\$(trunc_pwd)\n$ -> ",
			       2 : "\\n┌( \u @ \h )─( \$(date +%I:%M%P) -:- \$(date +%m)/\$(date +%d) )\\n└( \$(trunc_pwd) )·> ",
			       3 : "[ \u @ \h : \$(trunc_pwd) ] ",
			       4 : "\[\\033[\${prompt_line};0H\]\\n┌─( \u @ \h )─\${fill}─( \$(_newPWD) )────┘\\n└─( uptime: \$(show_uptime) : $ )·> ",
			       5 : "\\n┌─[ \u @ \h ]─[ job #\# ]─[ \$(show_tty) ]─[ \$(date +%H:%M:%S): \$(date +%m/%d/%y) : \$(show_uptime) ]\\n└─[ $ : \$(trunc_pwd) ]·> ",
			       6 : "\\n[ \$(date +%T) - \$(date +%D) ]\
[ \u @ \h ]\ [ \${files}.\${hiddenfiles}-\${executables}x \$(show_size) \
\${directories}.\${hiddendirectories}d\${links}\${devices} ][ \${loaddiff} ][ \
\$(ps ax | wc -l | sed -e \\\"s: ::g\\\")proc ]\\n[ \$(trunc_pwd) ] $ ",
			       7 : "\\n[ \\t ] \u \$(trunc_pwd) $ ",
			       8 : "\\n.:[ \u @ \h ]:. .:[ \$(trunc_pwd) ]:.\n.:[·> ",
			      10 : "\\n⊏⁅ \u ⁑ \h ⁆⁅ \d ⁑ \\t ⁑ \$(show_uptime) ⁆⊐\\n⊏⁅ \$(trunc_pwd) ⁆⊐≻ ",
			      11 : "\\n -( \u / \h )-( \$(show_tty) )-( uptime: \$(show_uptime) )-( \$(date +%H:%M) \
\$(date +%d-%b-%y ) )-( files: \$(count_files +f) / folders: \$(count_files -d) )-\\n -< \$(trunc_pwd) >- ",
			      12 : "\\n♦♦( \u @ \h : Space on /: \$(show_space --used /) used of \$(show_space --total /) )♦♦( \$(trunc_pwd) )♦♦\\n♦♦( \$(date +%H:%M) → \$(date \\\"+%a, %d %b %y\\\") : uptime : \$(show_uptime) \$ )♦♦ ",
			      13 : "┌─( \u @ \h \$(date \"+%a, %d %b %y\") )─\${fill}─( \$newPWD \
)─<\n└─( \$(date \"+%H:%M\") \$ )─> ",
			     }

		def do_insert_prompt(widget, data=None):
			selection = widget.get_active()
			if selection != 0:
				self.prompt_command_buffer.set_text(styles_pc[selection])
				self.custom_prompt_buffer.set_text(styles_ps1[selection])

		self.insert_prompt.connect("changed", do_insert_prompt)


		####################### Load the Main-Window #######################################
		self.bashstyle = gtkbuilder.get_object("bashstyle")

		def destroy(self, widget):
			remove_lockfile()
			gtk.main_quit()

		self.bashstyle.connect("destroy", destroy, None)

		####################### load the AboutDialog/NoteBook/TreeView #####################
		aboutdialog = gtkbuilder.get_object("aboutdialog")

		def about_destroy(widget, extra, data=None):
			widget.hide()

		####################### Load the Notebook ##########################################
		notebook = gtkbuilder.get_object("notebook")
		notebook.set_current_page(int(initial_page))
		notebook.set_show_tabs(0)

		####################### Load the TreeView ##########################################
		liststore = gtk.ListStore(gtk.gdk.Pixbuf, str)
		treeview = gtkbuilder.get_object("treeview")
		treeview.set_model(liststore)

		imagecell = gtk.CellRendererPixbuf()
		imagecolumn = gtk.TreeViewColumn("")
		imagecolumn.pack_start(imagecell, True)
		imagecolumn.add_attribute(imagecell, "pixbuf", 0)
		treeview.append_column(imagecolumn)

		textcell = gtk.CellRendererText()
		textcolumn = gtk.TreeViewColumn("")
		textcolumn.pack_start(textcell, True)
		textcolumn.add_attribute(textcell, "text", 1)
		textcolumn.set_attributes(textcell, markup=1)
		treeview.append_column(textcolumn)

		image_style=icon_theme.load_icon( "bs-ng-style", 32, 0 )
		liststore.append([image_style, _("<b>Style</b>")])

		image_alias=icon_theme.load_icon( "bs-ng-alias", 32, 0 )
		liststore.append([image_alias, _("<b>Aliases</b>")])

		image_advanced=icon_theme.load_icon( "bs-ng-advanced", 32, 0 )
		liststore.append([image_advanced, _("<b>Advanced</b>")])

		image_readline=icon_theme.load_icon( "bs-ng-readline", 32, 0 )
		liststore.append([image_readline, _("<b>Readline</b>")])

		image_extra=icon_theme.load_icon( "bs-ng-extra", 32, 0 )
		liststore.append([image_extra, _("<b>Extras</b>")])

		image_profile=icon_theme.load_icon( "bs-ng-profile", 32, 0 )
		liststore.append([image_profile, _("<b>Profiles</b>")])

		image_vim=icon_theme.load_icon( "bs-ng-vim", 32, 0 )
		liststore.append([image_vim, _("<b>VIM</b>")])

		image_nano=icon_theme.load_icon( "bs-ng-nano", 32, 0 )
		liststore.append([image_nano, _("<b>Nano</b>")])

		image_ls=icon_theme.load_icon( "bs-ng-ls", 32, 0 )
		liststore.append([image_ls, _("<b>LS Colors</b>")])

		image_custom=icon_theme.load_icon( "bs-ng-custom", 32, 0 )
		liststore.append([image_custom, _("<b>Custom</b>")])

		image_help=icon_theme.load_icon( "bs-ng-help", 32, 0 )
		liststore.append([image_help, _("<b>Help</b>")])

		image_info=icon_theme.load_icon( "bs-ng-info", 32, 0 )
		liststore.append([image_info, _("<b>Info</b>")])

		tree_selection = treeview.get_selection()
		treeview.set_cursor(int(initial_page))

		def treeview_action(widget, extra, data=None):
			selection = treeview.get_selection()
			position = int(selection.get_selected_rows()[1][0][0])
			if position <= 9:
				notebook.set_current_page(position)
			elif position == 10:
				subprocess.Popen("x-www-browser " + PREFIX + "/share/doc/bashstyle-ng/index.html", shell=True)
			elif position == 11:
				aboutdialog.show_all()
				aboutdialog.connect("response", about_destroy, None)

		treeview.connect("cursor-changed", treeview_action, None)

		self.bashstyle.show

if __name__ == "__main__":
	check_lockfile()
	hwg = BashStyleNG()
	gtk.main()