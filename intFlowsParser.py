import urllib.request
import xml.etree.ElementTree as ET
from graphviz import Digraph
import tempfile

'''
GraphViz Installation
   For Windows:

       Install windows package from: https://graphviz.gitlab.io/_pages/Download/Download_windows.html
       Install python graphviz package : sudo pip install graphviz
       Add C:\Program Files (x86)\Graphviz2.38\bin to User path
       Add C:\Program Files (x86)\Graphviz2.38\bin\dot.exe to System Path

'''

def isInOrOutMessageFlow(mflow):
   for node in mflow:
      #print(node.attrib['app-name'], ' - ', node.attrib['type'])
      if 'refid' not in node.attrib and node.attrib['app-name'] == 'rib-rms' and node.attrib['type'] == 'JmsToDb':
         return 'in'
         break
      elif 'refid' not in node.attrib and node.attrib['app-name'] == 'rib-rms' and node.attrib['type'] == 'DbToJms':
         return'out'
         break
         
   result = '?'


link = "http://dev1ribapp01.or.tata.com.uy:7777/rib-func-artifact/integration/rib-integration-flows.xml"

with urllib.request.urlopen(link) as response:
   html = response.read().decode('utf-8')

root = ET.fromstring(html)

rotate = 0
engine = 'dot'
contraint = 'false'

# Initialization
appList = []
adapterList = []
topicList = []
inoutSubGraph = {}   # In/Outbound
subSubFlow = {}      # Message Family
momSubGraph = {}
appSubGraph = {}

#chartAttribs = [engine = engine, overlap = 'false']

flows = Digraph(comment='Integration Flows', engine = engine)
flows.attr(rankdir='LR',  newrank="true")

inoutSubGraph['in'] = Digraph(name = 'cluster_inbound', engine = engine)
inoutSubGraph['in'].attr(rankdir='LR')

inoutSubGraph['out'] = Digraph(name = 'cluster_outbound', engine = engine)
inoutSubGraph['out'].attr(rankdir='LR')

momSubGraph['in'] = Digraph(name = 'cluster_mom_inbound', engine = engine)
momSubGraph['in'].attr(rankdir='LR' , rank = 'min')

momSubGraph['out'] = Digraph(name = 'cluster_mom_outbound', engine = engine)
momSubGraph['out'].attr(rankdir='LR', rank = 'max')

appSubGraph['in'] = Digraph(name = 'cluster_app_inbound', engine = engine)
appSubGraph['in'].attr(rankdir='LR', rank = 'min')

appSubGraph['out'] = Digraph(name = 'cluster_app_outbound', engine = engine)
appSubGraph['out'].attr(rankdir='LR', rank = 'max')

i=0

for messageflow in root:
   inout = isInOrOutMessageFlow(messageflow)
   #if not int(messageflow.attrib['id']) < 10:
   #   break
   
   #if inout not in ['in', 'out']:
   if inout not in ['in', 'out']:
      print('Couldn\'t determine if message-flow is (In/Out)bound !! message-flow id =', messageflow.attrib['id'])
      continue
   
   subSubFlow[i] = Digraph(name = 'cluster_' +  messageflow.attrib['id'], engine = engine)
   
   if inout == 'out':
      subSubFlow[i].attr(rankdir='LR')
   elif inout == 'in':
      subSubFlow[i].attr(rankdir='RL')
      
   for node in messageflow:
      
      if 'refid' in node.attrib:
         continue
      
      app_name = str(node.attrib['app-name']) + '_' + inout
      app_label = str(node.attrib['app-name'])
      adapter = str(node.attrib['id'])   
      
      if app_name not in appList: 
         if 'rib-rms' in app_name:
            momSubGraph[inout].node(app_name, label = app_label, shape='box')
         else:
            appSubGraph[inout].node(app_name, shape='box')
            
         appList.append(app_name)
         
      if adapter not in adapterList: 
         subSubFlow[i].node(adapter, shape ='ellipse')
         adapterList.append(adapter)
         
      for edge in node:
         tagName = edge.tag.split("}")[1][0:]
         
         if tagName == 'in-db':
            inoutSubGraph[inout].edge(app_name, adapter)
            
         elif tagName == 'out-db':
            inoutSubGraph[inout].edge(adapter, app_name)
            
         elif tagName == 'in-topic':
            topicName = edge.text
            if topicName not in topicList: 
               subSubFlow[i].node(topicName, shape ='hexagon')
               topicList.append(topicName)
               
            subSubFlow[i].edge(topicName, adapter)
            
         elif tagName == 'out-topic':
            topicName = edge.text
            if topicName not in topicList: 
               subSubFlow[i].node(topicName, shape ='hexagon')
               topicList.append(topicName)
            subSubFlow[i].edge(adapter, topicName)
   
   inoutSubGraph[inout].subgraph(subSubFlow[i])


inoutSubGraph['in'].subgraph(appSubGraph['in'])
inoutSubGraph['out'].subgraph(appSubGraph['out'])
inoutSubGraph['in'].subgraph(momSubGraph['in'])
inoutSubGraph['out'].subgraph(momSubGraph['out'])

flows.subgraph(inoutSubGraph['in'])
flows.subgraph(inoutSubGraph['out'])

print(flows.source)
flows.render(tempfile.mktemp('.gv'), view=True)  # doctest: +SKIP
