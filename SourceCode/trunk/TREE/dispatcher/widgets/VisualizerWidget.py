try:
  import networkx as nx
  NetworkX = True
except:
  print "[debug] No Networkx library support"
  pass
from PySide import QtGui, QtCore
from PySide.QtGui import QIcon
from idaapi import *
from idautils import *
from idc import *
from ..core.structures.Graph.PySideGraph import *
import os

class VisualizerWidget(QtGui.QMainWindow):
    """
    This widget is the front-end for the trace generations.
    """
    def __init__(self,parent):
        QtGui.QMainWindow.__init__(self)
        print "[|] loading VisualizerWidget"
        # Access to shared modules
        self.parent = parent
        self.name = "Visualizer"
        path = os.path.join(self.parent.iconPath,"trace.png")
        self.icon = QIcon(path)
        
        #References to qt-specific modules
        self.QtGui = QtGui
        self.QtCore = QtCore
        self.central_widget = self.QtGui.QWidget()
        self.setCentralWidget(self.central_widget)
        self._definePropEnum()
        self._createGui()
        self.t_graph = nx.MultiDiGraph()
        
    def _createGui(self):
        """
        Create the main GUI with its components
        """
        # Create buttons
        self.taint_nodes_label = QtGui.QLabel("Taint Nodes(0/0)")
        
        self._createToolbar()
        
        self._createTaintTable()
        #Layout information
        self.graphView = QtGui.QGraphicsView()
        visualizer_layout = QtGui.QVBoxLayout()
        upper_table_widget = QtGui.QWidget()
        upper_table_layout = QtGui.QHBoxLayout()
        
        self.layoutPolicy = QtGui.QGroupBox("Graph Layout Policy")
        vbox2 = QtGui.QVBoxLayout()
        self.radioGroup2 = QtGui.QButtonGroup()
        self.radioGroup2.setExclusive(True)
        bIsFirst = True
        for i,row in enumerate(self.layout_prop):
            radio = QtGui.QRadioButton(row)
            self.radioGroup2.addButton(radio, i)
            if bIsFirst:
                radio.setChecked(True)
                bIsFirst = False
            vbox2.addWidget(radio)
        
        self.layoutPolicy.setLayout(vbox2)
        upper_table_layout.addWidget(self.taint_table)
        upper_table_layout.addWidget(self.layoutPolicy)
        upper_table_widget.setLayout(upper_table_layout)
        
        lower_tables_widget = QtGui.QWidget()
        lower_tables_layout = QtGui.QVBoxLayout()
        
        #lower_tables_layout.addWidget(QtGui.QGraphicsView(QtGui.QGraphicsScene()))
        lower_tables_layout.addWidget(self.graphView)
        lower_tables_widget.setLayout(lower_tables_layout)
        
        splitter = self.QtGui.QSplitter(self.QtCore.Qt.Vertical)
        q_clean_style = QtGui.QStyleFactory.create('Plastique')
        splitter.setStyle(q_clean_style)
        splitter.addWidget(upper_table_widget)
        splitter.addWidget(lower_tables_widget)
        visualizer_layout.addWidget(splitter)
        
        self.central_widget.setLayout(visualizer_layout)
        #self.populateTaintTable()
        
    def _createToolbar(self):
        """
        Create the toolbar
        """
        self._createRefreshAction()
        self._createImportTraceAction()
        self._createImportIndexAction()
        self._createIDAGraphAction()
        
        self.toolbar = self.addToolBar('Trace Generation Toolbar')
        self.toolbar.addAction(self.refreshAction)
        #self.toolbar.addAction(self.importTraceAction)
        self.toolbar.addAction(self.importIDAGraphAction)
        
    def _definePropEnum(self):
        """
        Generate the taint propagation policies
        """
        self.layout_prop = []
        self.layout_prop.append("Spring")
        self.layout_prop.append("Circular")
        self.layout_prop.append("Shell")
        self.layout_prop.append("Spectral")
        self.layout_prop.append("Standard")
        
    def _createRefreshAction(self):
        """
        Create the refresh action for the oolbar. triggers a scan of virtualmachines and updates the GUI.
        """
        path = os.path.join(self.parent.iconPath,"refresh.png")
        self.refreshAction = QtGui.QAction(QIcon(path), "Refresh the " \
            + "view", self)
        self.refreshAction.triggered.connect(self._onRefreshButtonClicked)
        
        
    def _createImportTraceAction(self):
        """
        Create the import trace action
        """
        path = os.path.join(self.parent.iconPath,"import.png")
        self.importTraceAction = QtGui.QAction(QIcon(path), "Import the trace file", self)
        self.importTraceAction.triggered.connect(self.onImportTraceButtonClicked)
        
    def _createIDAGraphAction(self):
        """
        Create the import trace action
        """
        path = os.path.join(self.parent.iconPath,"online.png")
        self.importIDAGraphAction = QtGui.QAction(QIcon(path),"Generate IDA Graph", self)
        self.importIDAGraphAction.triggered.connect(self.onIDAGraphClicked)
        
    def _createImportIndexAction(self):
        """
        Create an import button that calls QFileDialog
        """
        self.pin_trace_cb = QtGui.QCheckBox("PIN Trace")
        self.indexFileIn = QtGui.QPushButton()
        #self.indexFileIn.setGeometry(QtCore.QRect(0,0,25,19))
        self.indexFileIn.setToolTip("Import index file for PIN.")
        self.indexFileIn.setText("Import Index File")
        self.indexFileStr = QtGui.QLabel("Import Index File")
        self.indexFileIn.clicked.connect(self.onImportIndexButtonClicked)
        
    def _createTaintTable(self):
        """
        Create the top table used for showing all
        """
        self.taint_table = QtGui.QTableWidget()
        self.taint_table.clicked.connect(self.onTaintClicked)
        #self.taint_table.doubleClicked.connect(self.onProcessDoubleClicked)
        
    def populateTaintTable(self):
        """
        Populate the VM table with information about the virtual machines
        """
        #If no config then connect to virtualbox in config
        self.taint_table.setSortingEnabled(False)
        if self.policy == "TAINT_BRANCH":
            self.taints_header_labels = ["UUID", "Type", "Name", "StartInd", "EndInd", "Edge Anno"]
        else:
            self.taints_header_labels = ["UUID", "Type", "Name", "StartInd", "EndInd", "Edge Anno", "Child C", "Child D"]
        self.taint_table.clear()
        self.taint_table.setColumnCount(len(self.taints_header_labels))
        self.taint_table.setHorizontalHeaderLabels(self.taints_header_labels)
        self.taint_table.setSelectionMode(self.QtGui.QAbstractItemView.SingleSelection)
        self.taint_table.resizeColumnsToContents()
        self.taint_table.setSortingEnabled(True)
        
    def _onRefreshButtonClicked(self):
        """
        Action for refreshing the window data by checking each process
        """
        self._createGraphView()
        
    def updateTaintsLabel(self,n1, n2):
        """
        Action for updating the TaintsLabel
        """
        self.taint_nodes_label.setText("Taint Nodes(%d/%d)" %
            (n1, n2))
            
    def insert_node(self, s):
        from ..core.structures.Parse.TaintNode import TaintNode
        tempNode = None
        uuid = self.extract_uuid(s)
        if self.t_graph.has_node(uuid):
            tempNode = self.t_graph.node[uuid]['inode']
            tempNode.ExtractData(s)
        else:
            tempNode = TaintNode()
            tempNode.ExtractData(s)
            self.t_graph.add_node(uuid, inode = tempNode)
        self.child_edges(tempNode)

    def child_edges(self, node):
        from dispatcher.core.structures.Parse.TaintNode import TaintNode
        for attr, value in node.__dict__.iteritems():
            if(attr.startswith('child')):
                x = getattr(node, attr)
                if x is not None:
                    for child in x.split():
                        if self.t_graph.has_node(child):
                            self.t_graph.add_edge(str(node), child, anno=node.edgeann, edgetype=attr.split('_')[1])
                            tempNode = self.t_graph.node[child]['inode']
                            tempNode.SetNodeAttr(attr.split('_')[1])
                        else:
                            newNode = TaintNode(child)
                            newNode.SetNodeAttr(attr.split('_')[1])
                            self.t_graph.add_node(child, inode = newNode)
                            self.t_graph.add_edge(str(node), child, anno=node.edgeann, edgetype=attr.split('_')[1])
    def extract_uuid(self, s):
        import re
        pattern = re.compile(r"""
                            \[(?P<uuid>\d+)\].*
                            """, re.VERBOSE)
        m = pattern.search(s)
        return str(m.group('uuid'))
            
    def onImportTraceButtonClicked(self):
        """ 
        Action for importing an XML file containing VM information
        """
        #from ..core.structures.Parse import TrNode
        fname, _ = self.QtGui.QFileDialog.getOpenFileName(self, 'Import Trace')
        self.trace_fname = fname
        #self.populateTraceTable()
        
    def onIDAGraphClicked(self):
        """ 
        Action for generating the IDA Graph
        """
        #self.populateTraceTable()
        from ..core.structures.Graph.TaintGraph import TaintGraph
        from ..core.structures.Graph.BCTaintGraph import BCTaintGraph
        if self.policy == "TAINT_BRANCH":
            tv = BCTaintGraph(self.t_graph, self.node_ea)
        else:
            tv = TaintGraph(self.t_graph, self.node_ea, self.node_lib)
        tv.Show()
    
    def onImportIndexButtonClicked(self):
        """
        Action for importing an XML file containing VM information
        """
        fname, _ = self.QtGui.QFileDialog.getOpenFileName(self, 'Import Index')
        self.index_fname = fname
        self.indexFileStr.setText(fname)
        
    def _createTaintsTable(self):
        """
        Create the bottom left table
        """
        self.taints_table = QtGui.QTableWidget()
        #self.taints_table.doubleClicked.connect(self._onDetailsDoubleClicked)
    
    def _createTraceTable2(self):
        """
        Create the bottom right table
        """
        self.taint_table2 = QtGui.QTextEdit()
        #self.taint_table.doubleClicked.connect(self._onTraceDoubleClicked)
        
    def onTaintClicked(self, mi):
        """
        If a process is clicked, the view of the process and details are updated
        """
        self.clicked_trace = self.taint_table.item(mi.row(), 1).text()
        #self.populateTaintsTable(self.clicked_process)
        
    def traceTableWriter(self, text):
        """
        Writer method to append text to the trace table
        """
        self.taint_table2.append(text)
        
    def setTaintGraph(self, t, p):
        """
        Method to set taint graph
        """
        self.t_graph = t
        self.policy = p
        self.populateTaintTable()
        self.populateTaintsTableImported()
        self._createGraphView() 
        
    def _createGraphView(self):
        from ..core.structures.Graph.PySideGraph import *
        import networkx as nx
        self.graphScene = self.QtGui.QGraphicsScene()
        self.graphScene.setSceneRect(0,0,800,600)
        #pos = nx.shell_layout(self.t_graph, scale=800)
        pos = nx.circular_layout(self.t_graph, scale=800)
        if (self.radioGroup2.checkedButton().text() == "Spring"):
            pos = nx.spring_layout(self.t_graph, scale=800)
        elif (self.radioGroup2.checkedButton().text() == "Circular"):
            pos = nx.circular_layout(self.t_graph, scale=800)
        elif (self.radioGroup2.checkedButton().text() == "Shell"):
            pos = nx.shell_layout(self.t_graph, scale=800)
        elif (self.radioGroup2.checkedButton().text() == "Spectral"):
            pos = nx.spectral_layout(self.t_graph, scale=800)
        else:
            #standard
            #pos = nx.circular_layout(self.t_graph, scale=800)
            if self.policy == "TAINT_BRANCH":
                pos = self.genStandardLayoutBranch(self.t_graph, scale=800)
            else:
                pos = self.genStandardLayout(self.t_graph, scale=800)
        #Select node connection and its decorator types
        nc = CenterCalc()
        cd = LineArrowOnStart()      
        node_dict = dict() #must contain the textnode object for parent lookup
        for x,y in self.t_graph.nodes(data=True):
            node = None
            node_p = None
            #Current Logic:
            #Create a node 
            #Create the children of the node
            #there will be conflicts
            #Must check if the child already exists and link it to parent
            if not str(x) in node_dict:
                cur_x = int(float(pos[str(x)][0]))
                cur_y = int(float(pos[str(x)][1]))
                node_p = TextNode(nc, cd, None, str(x), y['inode'].label(), cur_x, cur_y, 200, 30)
                #self.graphScene.addItem(node_p)
                node_dict[str(x)] = node_p
            for attr, value in y['inode'].__dict__.iteritems():
                if(attr.startswith('child')):
                    a = getattr(y['inode'], attr)
                    if a is not None:
                        for child in a.split():
                            child_x = int(float(pos[child][0]))
                            child_y = int(float(pos[child][1]))
                            node = TextNode(nc, cd, node_dict[str(x)], child, self.t_graph.node[child]['inode'].label(), child_x, child_y, 200, 30)
                            #self.graphScene.addItem(node)
                            node_dict[child] = node
        for x,y in node_dict.iteritems():
            self.graphScene.addItem(y)
        self.graphView.setScene(self.graphScene)
        self.graphView.update()
        self.graphView.repaint()
        
    def genStandardLayout(self, t_graph, scale):
        import networkx as nx
        roots = [n for n,d in t_graph.in_degree().items() if d == 0]
        topo = nx.topological_sort(t_graph)
        std_layout = dict()
        x_counter = 0
        y_counter = 0
        y_chain_length = 20
        for i in topo:
            if i in roots:
                x_counter = x_counter + 1
                y_counter = 0
            cur_x = x_counter*(800/len(roots))
            cur_y = (600/y_chain_length)*y_counter
            y_counter = y_counter + 1
            A = []
            A.append(cur_x)
            A.append(cur_y)
            std_layout[i] = A
            #print std_layout[i][0]
            #print std_layout[i][1]
        return std_layout
            
    def genStandardLayout2(self, t_graph, scale):
        from networkx.algorithms.traversal.depth_first_search import dfs_tree
        numChains = 0
        roots = [n for n,d in t_graph.out_degree().items() if d == 0]
        #print roots
        for i in roots:
            #print t_graph.node[i]['inode'].child_d
            #print type(t_graph.node[i])
            print self.getTreeDepth(dfs_tree(t_graph,i), 1)
            #children = [n for n,d in 
            
    def crawlTreeStd(self, t_graph, num):
        from networkx.algorithms.traversal.depth_first_search import dfs_tree
        root = t_graph.root()
        print type(root)
        #self.std_layout[
        if root.hasNoChildren(): return
        #for child in root.children():
        if not t_graph.size() <= 1:
            for attr, value in t_graph.node[i]['inode']:
                if(attr.startswith('child')):
                    a = getattr(t_graph.node[i]['inode'], attr)
        else:
            print "else"
            
            
    def getTreeDepth(self, t_graph, num):
        from networkx.algorithms.traversal.depth_first_search import dfs_tree
        if not t_graph.size() <= 1:
            for attr, value in t_graph.node[i]['inode']:
                if(attr.startswith('child')):
                    a = getattr(t_graph.node[i]['inode'], attr)
                    if a is not None:
                        curChildMax = 0
                        for child in a.split():
                            a = self.getTreeDepth(dfs_tree(t_graph,child), num+1)
                            if a > curChildMax:
                                curChildMax = a
                        return curChildMax + num
                    else:
                        return num
        else:
            return num
            
    def genStandardLayoutBranch(self, t_graph, scale):
        #
        # Branch depth-based layout, columns are chain sequences
        # Rows are depth levels
        #
        numChains = 0
        roots = [n for n,d in t_graph.in_degree().items() if d == 0]
        self.cur_chain = dict()
        self.std_layout = dict()
        x_counter = 0
        y_counter = 0
        y_chain_length = 20
        for i in roots:
            self.cur_chain[i] = 0
            root = t_graph.node[i]['inode']
            cur_x = x_counter*(scale/len(roots))
            cur_y = 0
            A = []
            A.append(cur_x)
            A.append(cur_y)
            self.std_layout[i] = A
            self.cur_chain[i] = cur_chain[i] + 1
            #
            #Supposedly recurse through an entire chain and the other chains should be unaffected
            #Property that exists on the taint branch policy
            #
            print root
            if root.child_c:
                self.stdLayoutBrancRec(t_graph, scale, root.child_c, i, len(roots))
            elif root.child_d:
                self.stdLayoutBrancRec(t_graph, scale, root.child_d, i, len(roots))
            else:
                print root.child_c
            x_counter = x_counter + 1
            #for x in xrange(2**i)):
            #    #cur_x = x_counter*(800/len(roots))
            #    #cur_y = (600/y_chain_length)*y_counter
            #    #A = []
            #    #A.append(cur_x)
            #    #A.append(cur_y)
            #    #std_layout[i] = A
            #    #cur_chain[i] = cur_chain[i] + 1
            #print i
            #print t_graph.node[i]['inode'].depth
        #for i in t_graph:
        
    def stdLayoutBrancRec(self, t_graph, scale, node, chain, x_inc):
        node_f = t_graph.node[node]['inode']
        print node_f
        root = t_graph.node[node]['inode']
        cur_x = x_counter*(scale/x_inc)
        cur_y = cur_chain[chain]*60
        A = []
        A.append(cur_x)
        A.append(cur_y)
        self.std_layout[i] = A
        self.cur_chain[chain] = cur_chain[chain] + 1
        if node_f.child_c:
            self.stdLayoutBrancRec(t_graph, scale, node_f.child_c, i, x_inc)
        elif node_f.child_d:
            self.stdLayoutBrancRec(t_graph, scale, node_f.child_d, i, x_inc)
        else:
            print "end"
            
    def genStandardLayoutBranch2(self, t_graph, scale):
        #
        # Branch depth-based layout, columns are chain sequences
        # Rows are depth levels
        #
        numChains = 0
        roots = [n for n,d in t_graph.in_degree().items() if d == 0]
        cur_chain = dict()
        std_layout = dict()
        print roots
        for i in roots:
            cur_chain[i] = 0
            #for x in xrange(2**i)):
            #    cur_x = x_counter*(scale/len(roots))
            #    cur_y = (600/y_chain_length)*y_counter
            #    A = []
            #    A.append(cur_x)
            #    A.append(cur_y)
            #    std_layout[i] = A
            #    cur_chain[i] = cur_chain[i] + 1
            print i
            print t_graph.node[i]['inode'].depth
        #for i in t_graph
        
    def _createGraphView2(self, A):
        from ..core.structures.Graph.PySideGraph import *
        self.graphScene = self.QtGui.QGraphicsScene()
        self.graphScene.setSceneRect(0,0,800,600)

        #Select node connection and its decorator types
        nc = CenterCalc()
        cd = LineArrowOnStart()          

        cur_thread = [[]*(self.thread_count+1) for x in xrange(self.thread_count+1)]
        cur_num = 0
        for x in A.nodes_iter():
            node = None
            cur_x = int(thread.t1)*(800/self.thread_count)
            cur_y = (600/len(self.thread_list))*cur_num
            print thread.label()
            if not cur_thread[int(thread.t1)]:
                node = TextNode(nc, cd, None, thread.e, thread.label(), cur_x, cur_y, 200, 30)
                cur_thread[int(thread.t1)].append(node)
            else:
                node = TextNode(nc, cd, cur_thread[int(thread.t1)][-1], thread.e, thread.label(), cur_x, cur_y, 200, 30)
                cur_thread[int(thread.t1)].append(node)
            self.graphScene.addItem(node)
            cur_num = cur_num + 1

        self.graphView.setScene(self.graphScene)
        self.graphView.update()
        self.graphView.repaint()
        
    def setTraceFile(self, t):
        """
        Method to set taint graph
        """
        self.node_ea = dict()
        self.node_lib = dict()
        f=open(t, 'r')
        # read input file line by line
        tempNode = None
        for line in f:
            #Hard implementation of 'E' search
            if line.startswith('E'):
                splitted = line.split(' ')
                self.node_ea[splitted[5]] = splitted[1]
            #Hard implementation of 'L' search
            elif line.startswith('L'):
                splitted = line.split(' ')
                self.node_lib[splitted[1]] = (str(splitted[2]) + " " + str(splitted[3]))
        print "[debug] trace imported from file into dictionary"
        f.close()
        
    def populateTaintsTableImported(self):
        """
        Method for populating the taints table
        """
        self.taint_table.setRowCount(len(self.t_graph))
        self.taint_table.setContextMenuPolicy(self.QtCore.Qt.CustomContextMenu)
        self.taint_table.customContextMenuRequested.connect(self.handleTaintMenu)
        if self.policy == "TAINT_BRANCH":
            for row, ynode in enumerate(self.t_graph.nodes(data=True)):
                for column, column_name in enumerate(self.taints_header_labels):
                    tmp_item = None
                    if column == 0:
                        tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].uuid)
                    elif column == 1:
                        tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].typ)
                    elif column == 2:
                        tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].name)
                    elif column == 3:
                        tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].startind)
                    elif column == 4:
                        tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].endind)
                    elif column == 5:
                        tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].edgeann)
                    tmp_item.setFlags(tmp_item.flags() & ~self.QtCore.Qt.ItemIsEditable)
                    self.taint_table.setItem(row, column, tmp_item)
                self.taint_table.resizeRowToContents(row)
        else:
            for row, ynode in enumerate(self.t_graph.nodes(data=True)):
                for column, column_name in enumerate(self.taints_header_labels):
                    ##@self.process_header_labels = ["UUID", "Type", "Name", "StartInd", "EndInd", "Edge Anno", "Child C", "Child D"]
                    if column == 0:
                        tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].uuid)
                    elif column == 1:
                        tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].typ)
                    elif column == 2:
                        tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].name)
                    elif column == 3:
                        tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].startind)
                    elif column == 4:
                        tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].endind)
                    elif column == 5:
                        tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].edgeann)
                    elif column == 6:
                        if hasattr(ynode[1]['inode'], 'child_c'):
                            tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].child_c)
                        else:
                            tmp_item = self.QtGui.QTableWidgetItem(" ")
                    elif column == 7:
                        if hasattr(ynode[1]['inode'], 'child_d'):
                            tmp_item = self.QtGui.QTableWidgetItem(ynode[1]['inode'].child_d)
                        else:
                            tmp_item = self.QtGui.QTableWidgetItem(" ")
                    tmp_item.setFlags(tmp_item.flags() & ~self.QtCore.Qt.ItemIsEditable)
                    self.taint_table.setItem(row, column, tmp_item)
                self.taint_table.resizeRowToContents(row)
            self.taint_table.setSelectionMode(self.QtGui.QAbstractItemView.SingleSelection)
            self.taint_table.resizeColumnsToContents()
            self.taint_table.setSortingEnabled(True)
            
    def handleTaintMenu(self, pos):
        menu = self.QtGui.QMenu()
        addr = self.QtGui.QAction("Go to address", menu)
        addr.setStatusTip("Go to address within IDA")
        self.connect(addr, self.QtCore.SIGNAL('triggered()'), self.addrGo)
        menu.addAction(addr)
        menu.exec_(self.QtGui.QCursor.pos())
        
    def addrGo(self):
        from idc import *
        uuid = self.taint_table.item(self.taint_table.currentItem().row(), 0).text()
        int_addr = self.t_graph.node[uuid]['inode'].ea
        bLoaded = isLoaded(int_addr)
        if bLoaded:
          print "Found addr: 0x%x" % int_addr
          idc.Jump(int_addr)
        #self.filters_filename_table.insertRow(self.filters_filename_table.rowCount())
        #self.filters_filename_table.setItem(self.filters_filename_table.rowCount()-1, 0, self.QtGui.QTableWidgetItem(" "))