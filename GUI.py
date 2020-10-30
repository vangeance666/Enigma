import os, json, sys, time
from controller import *
sys.path.append(os.getcwd()+"\\python-3.8.2-embed-amd64")
sys.path.append(os.getcwd())
from selenium import webdriver
import subprocess
import ast
import tkinter as tk
from tkinter import filedialog
import controller


if 'pythonw' in sys.executable:
	f = open(os.devnull, 'w')
	sys.stdout = f
	sys.stderr = f


def returnImagePath(s):
	cwd_url = '/'.join(os.getcwd().split(os.sep))
	return str("file://" + cwd_url + "/" + s)

def saveDataStringIntoPath(s, rel_path):
	#The string returned from web will have twolines spacing 
	#This function will correct the format of the string and save as a temp csv file to be used.
	s.replace('\r\n', '\n')
	# cwd_url = '/'.join(os.getcwd().split(os.sep))
	# save_path = "file://" + cwd_url + "/" + rel_path
	with open(rel_path, 'wb') as f:
		f.write(s)
	return

class OutStream(object):

	def __init__(self, file_object=None):
		if 'pythonw' in sys.executable:
			self._f = None
		else:
			self._f = sys.__stdout__ if file_object is None else file_object

	def __lshift__(self, arg):
		if self._f is not None:
			self._f.write(str(arg))
		return self

def print_exc():
	if 'pythonw' not in sys.executable:
		traceback.print_exc()

cout = OutStream()


def BoolDict(d):
	from collections import defaultdict
	dd = defaultdict(lambda:False)
	dd.update(d if d else dict())
	return dd

#For make_browser_navless
def execute_chrome(browser, script=''):
	browser.command_executor._commands["SET_CONTEXT"] = ("POST", "/session/$sessionId/moz/context")
	browser.execute("SET_CONTEXT", {"context": "chrome"})
	browser.execute_script("""
		var h = function(id) { document.getElementById(id).style.display = 'none' };
		var b = function(k,v) { Services.prefs.setBoolPref(k,v) };
		var i = function(k,v) { Services.prefs.setIntPref(k,v) };%s;"""%(script))
	browser.execute("SET_CONTEXT", {"context": "content"})


#To make firefox browser not have navigation bar to improve UI experience
def make_browser_navless(browser, script=''):	
	execute_chrome(browser, """
	b('browser.tabs.drawInTitlebar', false);
	i('network.http.max-persistent-connections-per-server', 128); 
	h('nav-bar');
	h('TabsToolbar');
	b('reader.parse-on-load.enabled', false);
	b('browser.pocket.enabled', false);
	b('browser.tabs.forceHide', true);
	b('browser.helperApps.deleteTempFileOnExit', true);
	b('toolkit.cosmeticAnimations.enabled', false);
	i('browser.sessionhistory.max_total_viewers', 0);
	i('browser.sessionhistory.max_entries', 0);
	i('browser.sessionhistory.max_serialize_back', 0);
	i('browser.sessionstore.interval', 999999999);
	i('browser.sessionstore.interval.idle', 999999999);
	b('browser.sessionhistory.resume_from_crash', false);%s;"""%(script))

# Minor tweaks
def make_browser_fast(browser, script=''):
	make_browser_navless(browser, """
	i('browser.display.use_document_fonts', 0);
	b('browser.display.show_image_placeholders', false);
	i('layout.frame_rate', 10);%s;"""%(script))

# Personal Cout function to print text
class OutStream(object):
	def __init__(self, file_object=None):
		if 'pythonw' in sys.executable:
			self._f = None
		else:
			self._f = sys.__stdout__ if file_object is None else file_object

	def __lshift__(self, arg):
		if self._f is not None:
			self._f.write(str(arg))
		return self

def print_exc():
	if 'pythonw' not in sys.executable:
		traceback.print_exc()

cout = OutStream()


# Class to set 
class Browser(object):

	def __init__(self, headless=False, gen_iid=False, msg_box_title=None, msg_box_text=None, msg_box_timeout=60*60*1000):
		self._headless = headless
		show_msg_box = (msg_box_title is not None or msg_box_text is not None)
		if show_msg_box:
			gen_iid = True
		if gen_iid:
			try:
				iid_chars = string.ascii_uppercase+string.ascii_lowercase+string.digits
				self._iid = ''.join(random.choice(iid_chars) for x in xrange(16))
				if not os.path.exists('iids'):
					os.mkdir('iids')
				elif not os.path.isdir('iids'):
					os.unlink('iids')
					os.mkdir('iids')
				with open(os.path.join('iids', self._iid), 'w') as iid_f:
					iid_f.write('')
			except e:
				pass
		else:
			self._iid = None
		if show_msg_box and self._iid is not None:
			if msg_box_title is None:
				msg_box_title = ''
			if msg_box_text is None:
				msg_box_text = ''
			prog = '\n'.join(("""title="%s";text="%s";delay=%d;iid="%s";"""%(msg_box_title, msg_box_text, msg_box_timeout, self._iid),
				"""import os""",
				"""try:\n\timport Tkinter as tk\nexcept:\n\timport tkinter as tk""",
				"""r = tk.Tk()\nr.title(title)\ntk.Label(r, text=text).pack()""",
				"""def cf():\n\tif os.path.isfile(os.path.join('iids',iid)):r.after(3000, cf)\n\telse:r.destroy()""",
				"""r.after(3000, cf);r.after(delay, lambda: r.destroy())\nr.mainloop()"""))
			try:
				pkwargs = dict()
				pkwargs['startupinfo'] = subprocess.STARTUPINFO()
				pkwargs['startupinfo'].dwFlags |= subprocess.STARTF_USESHOWWINDOW
				pkwargs['creationflags'] = 0x00000008
				subprocess.Popen(['pythonw', '-c', prog], close_fds=platform.system() != 'Windows', **pkwargs)
			except:
				subprocess.Popen(['python', '-c', prog], close_fds=platform.system() != 'Windows')

	def __enter__(self):
		MH = 'MOZ_HEADLESS'
		h = os.environ[MH] if MH in os.environ else None
		if self._headless:
			os.environ[MH] = '1'
		self._browser = webdriver.Firefox()
		if h is None and MH in os.environ: 
			del os.environ[MH]
		elif h is not None: 
			os.environ[MH] = h
		self._browser.iid = self._iid
		self._open = True
		return self._browser

	def _quit(self):
		if self._iid is not None:
			try:
				os.unlink(os.path.join('iids', self._iid))
			except Exception as e:
				pass
		if self._open:
			pid = self._browser.service.process.pid
			self._browser.quit()
			try:
				os.kill(pid, signal.SIGTERM)
			except Exception as e:
				pass
			self._open = False

	def __exit__(self, type, value, traceback):
		self._quit()

	def __del__(self):
		self._quit()

def tk_ask_input(mode="file"):

	root = tk.Tk()
	root.withdraw()

	# Make it almost invisible - no decorations, 0 size, top left corner.
	root.overrideredirect(True)
	root.geometry('0x0+0+0')
	root.wm_attributes('-topmost', 1)
	root.deiconify()
	root.lift()
	root.focus_force()

	if mode == "file":
		ret = filedialog.askopenfilenames(parent=root) # Or some other dialog
	elif mode == "folder":
		ret = str(filedialog.askdirectory(parent=root)) # Or some other dialog

	root.destroy()
	return ret

# Read from this point onwards only
# ####################################
def launch():
	
	# Hide Tkinter
	# root = tk.Tk()
	# root.withdraw()

	# M = ModulesControler()

	# root = tk.Tk()
	# root.withdraw()

	# Make it almost invisible - no decorations, 0 size, top left corner.
	# root.overrideredirect(True)
	# root.geometry('0x0+0+0')

	# Show window again and lift it to top so it can get focus,
	# otherwise dialogs will end up behind the terminal.
	# root.deiconify()
	# root.lift()
	
	control = controller.ModulesControler()
	

	with Browser(headless=False) as browser:
		make_browser_navless(browser)
		browser.get("file://"+os.getcwd()+"/GUI/index.html")
		browser.set_script_timeout(2147483647)

		# Constantly loop and check if any of the javascript variables are set to true. 
		# If 
		while 1:
			try:
				needs_update = BoolDict(browser.execute_async_script("""
					var callback = arguments[0];
					(function fn() {
						if (!(typeof needsUpdate === 'undefined')) {
							var t = false;
							for (var k in needsUpdate) if (needsUpdate[k]) t = true; 
							if (t) {
								var u = {};
								for (var k in needsUpdate) {
									u[k] = needsUpdate[k];
									needsUpdate[k] = false;
								}
								return callback(u);
							}
						}
						setTimeout(fn, 60);
					})();
				"""))
				if needs_update is None:
					break





				if needs_update['volRamDumpInput']:
					# Just to ask for ram dump file 
					cout << "Ram Dump Mode\n"
					ram_image_file_path = tk_ask_input("file")
					browser.execute_script("")

					cout << "Update Triage Case Folder Path\n"
					if ram_image_file_path != "":
						browser.execute_script("window.inputFilePaths['ramImage'] = \"%s\"; window.volRamDumpInputed();" %ram_image_file_path)



				if needs_update['volExecuteDump']:
					# Uses controller to call volatility to dump case details
					cout << "Volatlity Execute mode\n"
					case_name = browser.execute_script("return volFields['caseName'];")					
					
					
					browser.execute_script("showLoader('Conducting Volatility Dump...');")
					# check if already have case first
					# if dont have then success can start dumping to a fixed name folder with dateetc..

					# Put ur code within here kevin
					# 
					# 
					# 
					browser.execute_script("showSuccess('Finished dumping case details!');")




				if needs_update['triageCaseFolderInput']:
					cout << "Update Triage Case Folder Path\n"

					triage_case_path = tk_ask_input('folder')
					# Get folder using tkinter




					if triage_case_path != "":
						browser.execute_script("window.inputFilePaths['triageFolderPath'] = \"%s\"; window.triageFolderInputed();" %triage_case_path)





				if needs_update['triageExecuteAnalysis']:
					cout << "Triage Results Mode\n"



					
					case_folder = browser.execute_script("return triageFields['caseFolderPath'];")

					browser.execute_script("showLoader('Conducting Triage Analysis...');")
					cout << "Case folder : " << case_folder
					results = control.start_triage_analysis(case_folder)

					cout << "Received controller results: " << results << "\n"



					browser.execute_script("modesResultsData['triage'] = JSON.parse('%s'); window.execTriageDumpRun(); window.triageFinishedAnalysis(); hideLoader(); showSuccess('Finished Triage Analysis!');"  % json.dumps(results))
					# browser.execute_async_script("")
					cout << "Done\n"
					
					# M.start_triage_analysis("C:\\Users\\User\\Desktop\\2202-WELTPEIOC-Suite\\ram_output")




				# Procedure for analyzing graphs
				# if needs_update['graph']:
				# 	cout << "graph Mode" << "\n"
				# 	mode = browser.execute_script("return graphs['mode'];")
				# 	csv_text = browser.execute_script("return updates['graph_csv'];")
				# 	saveDataStringIntoPath(csv_text, 'tmp/tmp_graph_csv.csv')

				# 	browser.execute_script("resetGraphAnalysisImg();")
				# 	browser.execute_script("showLoader('Generating graph...');")

				# 	res_d = {}
				# 	# Call different file depending on mode
				# 	if mode == 'timeseries':
				# 		res_d = ast.literal_eval(subprocess.check_output(["python", "timeseries.py", 'tmp/tmp_graph_csv.csv']))
				# 		if (int(res_d['no']) == 1):
				# 			browser.execute_script("hideLoader('');")
				# 			browser.execute_script("showSuccess('Successfully generated graph")
				# 			browser.execute_script("setGraphAnalysisImg('%s');" %(res_d['file_path']))
				# 	else: 
				# 		cout << "not timeseries" << "\n"


				# 	browser.execute_script("hideLoader('');")

				# if needs_update['plot_map']:	
				# 	cout << "Plotting map" << "\n"

				# 	start_location = browser.execute_script("return mapLocation['from'];")
				# 	end_location = browser.execute_script("return mapLocation['to'];")
				# 	travel_method = browser.execute_script("return method['type'];")
				# 	algorithm_plot = browser.execute_script("return algorithm['algo'];")

				# 	cout << start_location << " " << end_location << " " << travel_method <<  " " << algorithm_plot << "\n"
					
				# 	# Start loc and end loc can be in string
				# 	if start_location != end_location:
				# 		browser.execute_script("showLoader('Generating path...');")

				# 		# Find path will return a list of each run time algorithm
				# 		algoruntime = routeObj.find_path(int(start_location),int(end_location),travel_method)

				# 		if(algoruntime == -1):
				# 			print("Graph does not have this node")
				# 		elif(algoruntime == -2):
				# 			print("There is no Path from start point to end point.")
				# 		else:

				# 			if algorithm_plot == "Dijk": 
				# 				browser.execute_script("document.getElementById('mainframe').src = 'tmp/Dijkstra.html';")
				# 			elif algorithm_plot == "A":
				# 				browser.execute_script("document.getElementById('mainframe').src = 'tmp/A_Star.html';")
				# 			elif algorithm_plot == "Fast-Belman":
				# 				browser.execute_script("document.getElementById('mainframe').src = 'tmp/Fast_Bellmon.html';")
						
				# 			browser.execute_script("hideLoader('');")
				# 			# browser.execute_script("document.getElementById('content-displaygraph').style.display = 'block';")
				# 			browser.execute_script("toastr.success('Shortest path shown', 'Graph Updated');")
				# 			# browser.execute_script("")
				# 			browser.execute_script("document.getElementById('dijk-frame').src = 'tmp/Dijkstra.html';")
				# 			browser.execute_script("document.getElementById('a-star-frame').src = 'tmp/A_Star.html';")
				# 			browser.execute_script("document.getElementById('fast-bellmon-frame').src = 'tmp/Fast_Bellmon.html';")
							
				# 			browser.execute_script("runtime['dijkstra'] = %s;" %algoruntime[0] )
				# 			browser.execute_script("runtime['astar'] = %s;" %algoruntime[1])
				# 			browser.execute_script("runtime['fastBellman'] = %s;" %algoruntime[2])

				# 			cout << "Completed" << "\n"
				# 	else:
				# 		cout << "Same start and end" << "\n"

					# Launch pythons subprocess to generate new folium html element? 
			except Exception as e:
				print("hehehe")
				print(e)
				# raise e
				break


launch()