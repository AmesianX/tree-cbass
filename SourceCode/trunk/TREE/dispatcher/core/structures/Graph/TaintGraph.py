import re
from idaapi import *
from idautils import *
from idc import *
from dispatcher.core.structures.Graph.CallGraph2 import CallGraph2
try:
  import networkx as nx
  NetworkX = True
except:
  print "[debug] No Networkx library support"
  pass
##################################################################
#Pass in NetworkX Graph
class TaintGraph(GraphViewer):
  def __init__(self, graph):
    GraphViewer.__init__(self, "Taint Graph")
    self.graph = graph
    self.selectedNode = None
    
  def __init__(self, graph, node_ea, node_lib):
    GraphViewer.__init__(self, "Taint Graph")
    self.graph = graph
    self.node_ea = node_ea
    self.node_lib = node_lib
    self.selectedNode = None

  def OnRefresh(self):
    '''
    @TODO 
    '''
    self.Clear()
    #Add nodes
    print "Generating graph"
    idNode = dict()
    for x,y in self.graph.nodes(data=True):
        node_ea = y['inode'].uuid
        try:
            idNode[node_ea] = self.AddNode(y['inode'])
        except:
            print "screwed"
    for x,y,d in self.graph.edges(data=True):
        print x
        print y
        print d
        try:
            print idNode[x]
            print idNode[y]
            self.AddEdge(idNode[x],idNode[y])
        except:
            continue
    # Generate a reverse dictionary { node_id: node_ea}
    self.AddrNode = dict()
    for ea,id in idNode.iteritems():
        self.AddrNode[id] = ea
    return True
    
  def OnDblClick(self, node_id):
    print "[debug] dbl clicked %d\n" % node_id
    uuid = self.AddrNode[node_id]
    addr = 0
    ind = ''
    ind = self.graph.node[uuid]['inode'].startind.split(':')[0]
    print ind
    if self.graph.node[uuid]['inode'].endind is not None:
        ind = self.graph.node[uuid]['inode'].endind.split(':')[0]
        print "endi"
    print ind
    #prefer endind if exists
    try:
        addr = self.node_ea[ind]
    except KeyError:
        addr = 0
    print "[debug] %s" % ind
    print "Found addr: %s" % addr
    if addr != 0:
        print int(addr, 16)
        idc.Jump(int(addr,16))
    return True
    
  def OnHint(self, node_id):
    uuid = self.AddrNode[node_id]
    tempNode = self.graph.node[uuid]['inode']
    return tempNode.label()
    
  def OnClick(self, node_id):
    return True
    
  def OnGetText(self, node_id):
    uuid = self.AddrNode[node_id]
    print uuid
    a = self.graph.node[uuid]['inode']
    if a.nodeattr == 'c':
        uuid = "[c] " + str(uuid)
    if not a.nodeattr:
        return (uuid, 0x0000ff) #Was Green 0x7fff00, Change to red 0x0000ff to display the sink (XL)
    if a.child_c is None and a.child_d is None:
        print "[debug] sink: %s" % uuid
        return (uuid, 0x7fff00) #Was Red 0x0000ff, Change to Grace 0x7fff00 to display the source (XL)
    #reg
    elif a.typ == 'reg':
        return (uuid, 0xff88ff) #pink
    #mem
    else:
        #return (self.AddrNode[node_id], 0xff00f0)
        return (uuid, 0xffffff) #white
  
  def OnSelect(self, node_id):
    print "[debug] %sd selected" % self.AddrNode[node_id]
    self.selectedNode = node_id
    return True
    
  def OnCommand(self, cmd_id):
    '''
    Triggered when a menu command is selected through the menu of hotkey
    @return: None
    '''
    if cmd_id == self.cmd_close:
        self.Close()
        return
    elif cmd_id == self.cmd_callgraph:
        #callgraph stuff
        print "callgraph"
        self.OnGenCallGraph()
    else:
        print "[debug] Unknown command:", cmd_id
    return True
    
  def Show(self):
    if not GraphViewer.Show(self):
        return False
    # Add some handy commands to the graph view
    self.cmd_close =  self.AddCommand("Close", "F2")
    if self.cmd_close == 0:
        print "[debug] Failed to add popup menu item for GraphView"
    self.cmd_callgraph = self.AddCommand("Call Graph", "F3")
    if self.cmd_callgraph == 0:
        print "[debug] Failed to add popup menu item for GraphView"
    return True
    
  def OnGenCallGraph(self):
    print "callgraph called"
    print self.selectedNode
    uuid = self.AddrNode[self.selectedNode]
    addr = 0
    #
    # Really bad implementation, searches every node on dbl click
    #
    ind = self.graph.node[uuid]['inode'].startind.split(':')[0]
    if self.graph.node[uuid]['inode'].endind is not None:
        ind = self.graph.node[uuid]['inode'].endind.split(':')[0]
        print "endi"
    print ind
    #prefer endind if exists
    addr = self.node_ea[ind]
    print "[debug] %s" % ind
    print "Found addr: %s" % addr
    print int(addr, 16)
    print GetFunctionName(int(addr,16))
    #Iterate through all function instructions and take only call instructions
    result = {}
    for x in [x for x in FuncItems(int(addr, 16)) if idaapi.is_call_insn(x)]:
        for xref in XrefsFrom(x, idaapi.XREF_FAR):
            if not xref.iscode: continue
            t = GetFunctionName(xref.to)
            if not t:
                t = hex(xref.to)
            result[t] = True
    g = CallGraph2(GetFunctionName(int(addr,16)), result)
    if g.Show():
        return g
    else:
        return None