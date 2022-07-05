import fileinput
import json
import os
import subprocess
import pandas as pd
import numpy as np
from jupyterlab_server import add_handlers
from itertools import groupby
from random import randrange
import networkx as nx
import collections
import colourmap as cm
import functools as ft
from community import community_louvain

# using local, modified version of d3graph, hope PRs will be accepted soon - can then change to pip version
import sys
sys.path.insert(0, './d3graph')
from d3graph import d3graph, vec2adjmat
from d3graph.d3graph import adjmat2dict
###

from jsonparsercreator import *
from Project import Project

# get method name
def getMethodName(x):
	if " " in x:
		x = x.split(" ")[-1]
	if pd.isnull(x):
		return ''
	if not "::" in x:
		x = x+"::"+x
	return x.split("::")[1]

# get class name
def getClassName(x):
	if " " in x:
		x = x.split(" ")[-1]
	if pd.isnull(x):
		return ''
	if not "::" in x:
		x = x+"::"+x
	return x.split("::")[0]

# get pkg name
def getPkgName(x):
	if " " in x:
		x = x.split(" ")[-1]
	if pd.isnull(x):
		return ''
	if not "::" in x:
		x = x+"::"+x
	return ".".join(x.split("::")[0].split(".")[:-1])

# get lib name without version
def getVersionlessLibName(x):
	if pd.isnull(x):
		return ''
	if ":" in x:
		return ":".join(x.split(":")[0:2])
	return x

# get a dict of pks to classes
def getPackagesToClassesMapping(fileName):
	tmpDf = pd.read_csv(fileName, sep='\t', on_bad_lines='skip')
	for i, row in tmpDf.iterrows():
		for clsName in row['Classes'].split(':'):
			pkg = '.'.join(clsName.split('.')[:-1])
			sourceColToJars[pkg] = getVersionlessLibName(row['Library Name'])

	packageToClassesMap = collections.defaultdict(list)
	[packageToClassesMap['.'.join(eachClass.split('.')[:-1])].append(eachClass.split('.')[-1]) for classNames in list(tmpDf['Classes']) for eachClass in classNames.split(":") if isinstance(eachClass, str)]
	return packageToClassesMap

# get list of clients and library from input JSON
def getRepos():
	datasetFile = open('./input.json','r')
	datasetMetadata = json.load(datasetFile)

	try:
		os.mkdir('./repos')
	except OSError as error:
		print('Directory "repos" exists.')   

	for repo in datasetMetadata:
		if 'url' in repo.keys():
			project = Project(repo['url'])
			try:
				res=project.clone('./repos')
				project.checkout_commit(repo['commit'])
			except CalledProcessError as error:
				print('Directory exists.')   
		
	return datasetMetadata

# create dataframe in the shape we want
def getInteractionsDF(arrayTsvFiles):
	global pkgToCls
	global pkgToClsLength
	global sourceColToJars
	df = pd.DataFrame({'SourceMethod': [], 'SourceClass': [], 'SourcePackage': [], 'SourceJar': [], 'TargetMethod': [], 'TargetClass': [], 'TargetPackage': [], 'TargetJar': [], 'Type': [], 'Static': [], 'Count': []})
	for file in arrayTsvFiles:
		print(file)
		if file.endswith("libsInfo.tsv"):
			pkgToCls = getPackagesToClassesMapping(file)
			for pkg in pkgToCls.keys():
				pkgToClsLength[pkg] = len(pkgToCls[pkg])

		if file.endswith("dynamic-invocations.tsv"):
			tmpDf = pd.read_csv(file, sep='\t', on_bad_lines='skip')
			checkDf = tmpDf.applymap(lambda x : type(x).__name__).eq({'Declared Callee Method': 'str', 'Declared Callee Library': 'str', 'Actual Callee Method': 'str', 'Actual Callee Library': 'str', 'Caller Method': 'str', 'Caller Library': 'str', 'Count': 'int', 'Callee Visibility': 'str','Reflective': 'bool','DynamicProxy': 'bool','Label': 'str'})
			tmpDf = tmpDf.drop(list(checkDf[checkDf.isin([False]).any(axis=1)].index))
			for index, row in tmpDf.iterrows():
				checkDf.iloc[index]
				stat = 'both' if row['Declared Callee Method'] == row['Actual Callee Method'] else 'dynamic'
				method1, klass1, pkg1, lib1 = getMethodName(row['Caller Method']), getClassName(row['Caller Method']), getPkgName(row['Caller Method']), getVersionlessLibName(row['Caller Library'])
				method2, klass2, pkg2, lib2 = getMethodName(row['Actual Callee Method']), getClassName(row['Actual Callee Method']), getPkgName(row['Actual Callee Method']), getVersionlessLibName(row['Actual Callee Library'])
				sourceColToJars[method1], sourceColToJars[klass1], sourceColToJars[pkg1] = lib1, lib1, lib1
				sourceColToJars[method2], sourceColToJars[klass2], sourceColToJars[pkg2] = lib2, lib2, lib2
				newRow = {'SourceMethod': method1, 'SourceClass': klass1, 'SourcePackage': pkg1, 'SourceJar': lib1, 'TargetMethod': method2, 'TargetClass': klass2, 'TargetPackage': pkg2, 'TargetJar': lib2, 'Type': 'invocation', 'Static': stat, 'Count': row['Count']}
				df = df.append(newRow, ignore_index = True)
				if stat == 'dynamic':
					method2, klass2, pkg2, lib2 = getMethodName(row['Declared Callee Method']), getClassName(row['Declared Callee Method']), getPkgName(row['Declared Callee Method']), getVersionlessLibName(row['Declared Callee Library'])
					sourceColToJars[method2], sourceColToJars[klass2], sourceColToJars[pkg2] = lib2, lib2, lib2
					newRow = {'SourceMethod': method1, 'SourceClass': klass1, 'SourcePackage': pkg1, 'SourceJar': lib1, 'TargetMethod': method2, 'TargetClass': klass2, 'TargetPackage': pkg2, 'TargetJar': lib2, 'Type': 'invocation', 'Static': 'static', 'Count': row['Count']}
					df = df.append(newRow, ignore_index = True)
		elif file.endswith("static-invocations.tsv"):
			tmpDf = pd.read_csv(file, sep='\t', on_bad_lines='skip')
			checkDf = tmpDf.applymap(lambda x : type(x).__name__).eq({'Declared Callee Method': 'str', 'Declared Callee Library': 'str', 'Caller Method': 'str', 'Caller Library': 'str', 'Count': 'int', 'Callee Visibility': 'str', 'Label': 'str'})
			tmpDf = tmpDf.drop(list(checkDf[checkDf.isin([False]).any(axis=1)].index))
			for index, row in tmpDf.iterrows():
				method1, klass1, pkg1, lib1 = getMethodName(row['Caller Method']), getClassName(row['Caller Method']), getPkgName(row['Caller Method']), getVersionlessLibName(row['Caller Library'])
				method2, klass2, pkg2, lib2 = getMethodName(row['Declared Callee Method']), getClassName(row['Declared Callee Method']), getPkgName(row['Declared Callee Method']), getVersionlessLibName(row['Declared Callee Library'])
				sourceColToJars[method1], sourceColToJars[klass1], sourceColToJars[pkg1] = lib1, lib1, lib1
				sourceColToJars[method2], sourceColToJars[klass2], sourceColToJars[pkg2] = lib2, lib2, lib2
				newRow = {'SourceMethod': method1, 'SourceClass': klass1, 'SourcePackage': pkg1, 'SourceJar': lib1, 'TargetMethod': method2, 'TargetClass': klass2, 'TargetPackage': pkg2, 'TargetJar': lib2, 'Type': 'invocation', 'Static': 'static', 'Count': row['Count']}
				df = df.append(newRow, ignore_index = True)
		elif file.endswith("classesUsageInfo.tsv"):
			pass
		elif file.endswith("annotations.tsv"):
			tmpDf = pd.read_csv(file, sep='\t', on_bad_lines='skip')
			checkDf = tmpDf.applymap(lambda x : type(x).__name__).eq({'Class': 'str', 'Method': 'str', 'Field Name:Field Signature': 'str', 'Annotation': 'str', 'Annotated In Library': 'str', 'Annotation Visibility': 'str', 'Count': 'int', 'Annotation Library': 'str'})
			tmpDf = tmpDf.drop(list(checkDf[checkDf.isin([False]).any(axis=1)].index))
			for index, row in tmpDf.iterrows():
				annotated = row['Class'] if not row['Class'] == '-' else (row['Method'] if not row['Method'] == '-' else row['Field Name:Field Signature'])
				method1, klass1, pkg1, lib1 = getMethodName(annotated), getClassName(annotated), getPkgName(annotated), getVersionlessLibName(row['Annotated In Library'])
				method2, klass2, pkg2, lib2 = getMethodName(row['Annotation']), getClassName(row['Annotation']), getPkgName(row['Annotation']), getVersionlessLibName(row['Annotation Library'])
				sourceColToJars[method1], sourceColToJars[klass1], sourceColToJars[pkg1] = lib1, lib1, lib1
				sourceColToJars[method2], sourceColToJars[klass2], sourceColToJars[pkg2] = lib2, lib2, lib2
				newRow = {'SourceMethod': method1, 'SourceClass': klass1, 'SourcePackage': pkg1, 'SourceJar': lib1, 'TargetMethod': method2, 'TargetClass': klass2, 'TargetPackage': pkg2, 'TargetJar': lib2, 'Type': 'annotation', 'Static': 'static', 'Count': row['Count']}
				df = df.append(newRow, ignore_index = True)
		elif file.endswith("subtyping.tsv"):
			tmpDf = pd.read_csv(file, sep='\t', on_bad_lines='skip')
			checkDf = tmpDf.applymap(lambda x : type(x).__name__).eq({'SubClass': 'str', 'Sub Library': 'str', 'Super Class/Interface': 'str', 'Super Class/Interface Visibility': 'str', 'Super Library': 'str', 'Count': 'int'})
			tmpDf = tmpDf.drop(list(checkDf[checkDf.isin([False]).any(axis=1)].index))
			for index, row in tmpDf.iterrows():
				method1, klass1, pkg1, lib1 = getMethodName(row['SubClass']), getClassName(row['SubClass']), getPkgName(row['SubClass']), getVersionlessLibName(row['Sub Library'])
				method2, klass2, pkg2, lib2 = getMethodName(row['Super Class/Interface']), getClassName(row['Super Class/Interface']), getPkgName(row['Super Class/Interface']), getVersionlessLibName(row['Super Library'])
				sourceColToJars[method1], sourceColToJars[klass1], sourceColToJars[pkg1] = lib1, lib1, lib1
				sourceColToJars[method2], sourceColToJars[klass2], sourceColToJars[pkg2] = lib2, lib2, lib2
				newRow = {'SourceMethod': method1, 'SourceClass': klass1, 'SourcePackage': pkg1, 'SourceJar': lib1, 'TargetMethod': method2, 'TargetClass': klass2, 'TargetPackage': pkg2, 'TargetJar': lib2, 'Type': 'subtyping', 'Static': 'static', 'Count': row['Count']}
				df = df.append(newRow, ignore_index = True)
		elif file.endswith("fields.tsv"):
			tmpDf = pd.read_csv(file, sep='\t', on_bad_lines='skip')
			checkDf = tmpDf.applymap(lambda x : type(x).__name__).eq({'Caller Class': 'str', 'Caller Library': 'str', 'Field Name': 'str', 'Declared Class': 'str', 'Actual Class': 'str', 'Field Signature': 'str', 'Count': 'int', 'Visibility': 'str','Reflective': 'bool','Static': 'bool','Field Library': 'str'})
			tmpDf = tmpDf.drop(list(checkDf[checkDf.isin([False]).any(axis=1)].index))
			for index, row in tmpDf.iterrows():
				method1, klass1, pkg1, lib1 = getMethodName(row['Caller Class']), getClassName(row['Caller Class']), getPkgName(row['Caller Class']), getVersionlessLibName(row['Caller Library'])
				sourceColToJars[method1], sourceColToJars[klass1], sourceColToJars[pkg1] = lib1, lib1, lib1
				if row['Declared Class'] == row['Actual Class']:
					method2, klass2, pkg2, lib2 = getMethodName(row['Field Name']), getClassName(row['Field Name']), getPkgName(row['Field Name']), getVersionlessLibName(row['Field Library'])
					sourceColToJars[method2], sourceColToJars[klass2], sourceColToJars[pkg2] = lib2, lib2, lib2
					newRow = {'SourceMethod': method1, 'SourceClass': klass1, 'SourcePackage': pkg1, 'SourceJar': lib1, 'TargetMethod': method2, 'TargetClass': klass2, 'TargetPackage': pkg2, 'TargetJar': lib2, 'Type': 'field', 'Static': 'both', 'Count': row['Count']}
					df = df.append(newRow, ignore_index = True)
				else:
					stat = 'static' if row['Declared Class'] == 'static' else 'dynamic'
					method2, klass2, pkg2, lib2 = getMethodName(row['Field Name']), getClassName(row['Field Name']), getPkgName(row['Field Name']), getVersionlessLibName(row['Field Library'])
					sourceColToJars[method2], sourceColToJars[klass2], sourceColToJars[pkg2] = lib2, lib2, lib2
					newRow = {'SourceMethod': method1, 'SourceClass': klass1, 'SourcePackage': pkg1, 'SourceJar': lib1, 'TargetMethod': method2, 'TargetClass': klass2, 'TargetPackage': pkg2, 'TargetJar': lib2, 'Type': 'field', 'Static': stat, 'Count': row['Count']}
					df = df.append(newRow, ignore_index = True)
					if stat == 'dynamic':
						method2, klass2, pkg2, lib2 = getMethodName(row['Declared Class']), getClassName(row['Declared Class']), getPkgName(row['Declared Class']), getVersionlessLibName(row['Field Library'])
						sourceColToJars[method2], sourceColToJars[klass2], sourceColToJars[pkg2] = lib2, lib2, lib2
						newRow = {'SourceMethod': method1, 'SourceClass': klass1, 'SourcePackage': pkg1, 'SourceJar': lib1, 'TargetMethod': method2, 'TargetClass': klass2, 'TargetPackage': pkg2, 'TargetJar': lib2, 'Type': 'field', 'Static': stat, 'Count': row['Count']}
						df = df.append(newRow, ignore_index = True)
		
	return df

# helper for checking equivalent nodes for coascelence
def checkIfInEdgesEqual(G, key, otherKey):
	if G.in_degree(key)==0 and G.in_degree(otherKey)==0:
		return True
	keyInEdgeSources = set()
	otherKeyInEdgeSources = set()
	for e in G.edges():
		if e[1]==key:
			keyInEdgeSources.add(e[0])
		elif e[1]==otherKey:
			otherKeyInEdgeSources.add(e[0])
	if (keyInEdgeSources==otherKeyInEdgeSources):
		return True
	return False

# checking equivalent nodes for coascelence
def getEquivalentNodes(G):
	adjList = list(nx.generate_adjlist(G))
	actualAdjList = {}
	for eachEntry in adjList:
		splits = eachEntry.split(' ')
		if len(splits) > 1:
			actualAdjList[splits[0]] = splits[1].split(' ')
		else:
			actualAdjList[splits[0]] = list()

	finalResultList = []
	listKeysRead = list()
	for key in actualAdjList.keys():
		if key not in listKeysRead:
			setToCreate = set()
			setToCreate.add(key)
			for otherKey in actualAdjList.keys():
				if otherKey != key:
					if collections.Counter(actualAdjList[key]) == collections.Counter(actualAdjList[otherKey]) and G.in_degree(key)==G.in_degree(otherKey) and checkIfInEdgesEqual(G, key, otherKey):
						setToCreate.add(otherKey)
						listKeysRead.append(otherKey)
			finalResultList.append(list(setToCreate))
			listKeysRead.append(key)

	return finalResultList

# draw graph
def createGraph(sourceColumn, targetColumn, sourceClubColumn, targetClubColumn, df):
	# check if club is smaller than base, and if none
	G = nx.from_pandas_edgelist(df, source=sourceClubColumn, target=targetClubColumn, edge_attr=list(['Count', 'Static', 'Type']),create_using=nx.DiGraph())
	# add unused pkgs
	for pkg in pkgToCls.keys():
		if not pkg in G.nodes:
			G.add_node(pkg)
			G.add_edge(pkg, list(pkgToCls.keys())[randrange(len(pkgToCls)-1)], Count=1, Static='none', Type='none')
	
	# coalesce nodes
	eqvNodes = getEquivalentNodes(G)
	for initNodesToMerge in eqvNodes:
		try:
			grouped = [list(g) for k, g in groupby(initNodesToMerge, lambda s: sourceColToJars[s])]
			for nodesToMerge in grouped:
				for n in nodesToMerge[1:]:
					G = nx.contracted_nodes(G, nodesToMerge[0], n)
				if len(nodesToMerge)>1:
					nx.set_node_attributes(G, {nodesToMerge[0]:sum([pkgToClsLength[a] for a in nodesToMerge])}, 'number')
					nx.set_node_attributes(G, {nodesToMerge[0]:sourceColToJars[nodesToMerge[0]]+" : "+" ".join(nodesToMerge)}, 'lbl')
		except KeyError:
			pass

	# add invisible nodes to fix downstream and upstream positions
	G.add_node('imagClient', lbl='', number=1)
	sourceColToJars['imagClient'] = ''
	G.add_node('imagLib', lbl='', number=1)
	sourceColToJars['imagLib'] = ''
	for repo in repos:
		try:
			if repo['type']=='client':
				clientRows = df.loc[(df['SourceJar'].apply(lambda x: x.split(":")[-1]) == repo['artifact']) | (df['TargetJar'].apply(lambda x: x.split(":")[-1]) == repo['artifact'])]
				for index, row in clientRows.iterrows():
					nod = row[sourceClubColumn]
					G.add_edge('imagClient', nod, Count=10, Static='none', Type='none')
			elif repo['type']=='library':
				libRows = df.loc[(df['SourceJar'].apply(lambda x: x.split(":")[-1]) == repo['artifact']) | (df['TargetJar'].apply(lambda x: x.split(":")[-1]) == repo['artifact'])]
				for index, row in libRows.iterrows():
					nod = row[sourceClubColumn]
					G.add_edge('imagLib', nod, Count=10, Static='none', Type='none')
		except KeyError:
			pass
	# set node attribute labels
	numMax, numMin = 0, 0
	for node in G.nodes:
		try:
			node_dict = G.nodes[node]
			if 'lbl' not in node_dict or node_dict['lbl'] is None:
				node_dict['lbl'] = sourceColToJars[node]+" : "+node
			if 'number' not in node_dict or node_dict['number'] is None:
				node_dict['number'] = pkgToClsLength[node]
			if node_dict['number']> numMax:
				numMax = node_dict['number']
			elif node_dict['number']< numMin:
				numMin = node_dict['number']
		except KeyError:
			pass

	if '' in G.nodes:
		G.remove_node('')

	# draw graph using d3
	d3 = d3graph(charge=500)
	adjmat = nx.to_pandas_adjacency(G, multigraph_weight=max, weight='Count')
	# clustering
	cluster_labels = community_louvain.best_partition(G.to_undirected())
	# Extract clusterlabels
	y = list(map(lambda x: cluster_labels.get(x), cluster_labels.keys()))
	hex_colors, _ = cm.fromlist(y, cmap='Paired', scheme='hex')
	labx = {}
	# Use the order of node_names
	for i, key in enumerate(cluster_labels.keys()):
		labx[key] = {}
		labx[key]['name'] = key
		if key=='imagClient' or key=='imagLib':
			labx[key]['color'] = '#FFFFFF'
		else:
			labx[key]['color'] = hex_colors[i]
		labx[key]['cluster_label'] = cluster_labels.get(key)

	# return
	node_names = adjmat.columns.astype(str)
	color = np.array(list(map(lambda x: labx.get(x)['color'], node_names)))

	d3.graph(adjmat)
	for node in G.nodes:
			node_dict = G.nodes[node]
			if 'number' not in node_dict.keys() or node_dict['number'] is None:
				node_dict['number'] = 1
	
		
	sizes = [2*int((G.nodes[node]['number'] - numMin)*(6 - 4)/(numMax-numMin) + 4) for node in G.nodes]

	# fix downstream clusters to the left, project to the middle, upstream to the right
	fixedPos = list()
	nodeColors, nodeEdgeColors, nodeEdgeSizes = list(), list(), list()
	for i, node in enumerate(G.nodes):
		repoTypeList = [repo for repo in repos if repo['artifact'] == sourceColToJars[node].split(':')[-1]]
		if repoTypeList:
			repoType = repoTypeList[0]['type']
			if repoType == 'client':
				nodeColors.append('#FFFFFF')
				nodeEdgeColors.append(color[i])
				nodeEdgeSizes.append(4)
			elif repoType == 'library':
				nodeColors.append(color[i])
				nodeEdgeColors.append('#000000')
				nodeEdgeSizes.append(3)
		else:
			if not node=='imagClient' and not node=='imagLib':
				nodeColors.append(color[i])
				nodeEdgeColors.append('#000000')
				nodeEdgeSizes.append(0.1)

		if node=='imagClient':
			fixedPos.append(json.dumps({'isFixed':'true', 'x':50, 'y':350}))
			nodeColors.append('#FFFFFF')
			nodeEdgeColors.append('#FFFFFF')
			nodeEdgeSizes.append(0.1)
		elif node=='imagLib':
			fixedPos.append(json.dumps({'isFixed':'true', 'x':800, 'y':200}))
			nodeColors.append('#FFFFFF')
			nodeEdgeColors.append('#FFFFFF')
			nodeEdgeSizes.append(0.1)
		else:
			fixedPos.append(json.dumps({'isFixed':'false'}))
		

	d3.set_node_properties(hover=[G.nodes[node]['lbl'] for node in G.nodes], label=['' for node in G.nodes], color=nodeColors, size=sizes, fixedPos=fixedPos, edge_color=nodeEdgeColors, edge_size=nodeEdgeSizes)
	d3.set_edge_properties(directed=True)
	for edge in G.edges:
		if edge in d3.edge_properties.keys():
			d3.edge_properties[edge]['hover'] = nx.get_edge_attributes(G,'Type')[edge]
			staticAttr = G.get_edge_data(*edge)['Static']
			if staticAttr == 'static':
				d3.edge_properties[edge]['color']='#A91F01'
			elif staticAttr == 'dynamic':
				d3.edge_properties[edge]['color']='#625fad'
			elif staticAttr == 'both':
				d3.edge_properties[edge]['color']='#000000'
			elif staticAttr == 'none':
				d3.edge_properties[edge]['style']='none'	
			typeAttr = G.get_edge_data(*edge)['Type']
			if typeAttr == 'invocation':
				d3.edge_properties[edge]['style']='link'
			elif typeAttr == 'field':
				d3.edge_properties[edge]['style']='field-link'
			elif typeAttr == 'subtyping':
				d3.edge_properties[edge]['style']='subtyping-link'
			elif typeAttr == 'annotation':
				d3.edge_properties[edge]['style']='annotation-link'
			
	d3.show(filepath='./api-dataproc-fastjson.html', title='VizAPI', graphLbl="VizAPI - API Usage : "+"-".join([repo['artifact'] for repo in repos]))

def getDataTsvs(dir, repos):
	tsvs = list()
	repoArtifacts = [repo['artifact'] for repo in repos]
	for file in os.listdir(dir):
		d = os.path.join(dir, file)
		if os.path.isfile(d):
			if ':' in file and file.split(':')[1] in repoArtifacts:
				tsvs.append(d)
		else:
			tsvs.extend(getDataTsvs(d, repos))
	return tsvs

def dataExists(dir, repos):
	repoArtifacts = [repo['artifact'] for repo in repos]
	for file in os.listdir(dir):
		if ':' in file and (file.split(':')[1] in repoArtifacts):
				return True
	return False


if __name__ == "__main__":
	sourceColToJars = dict()
	pkgToCls = dict()
	pkgToClsLength = dict()
	repos = list()
	
	# get clients and library and run instrumentation on it - output tsvs
	repos = getRepos()
	retVals = seeDirectory('./repos', "", repos)
	projList, repos = retVals[0], retVals[1]
	createJson(projList)
	if not dataExists('./repos/api-surface-data', repos):
		subprocess.call(['java', '-jar', './dependencies/libs-info-project-runner-1.0-SNAPSHOT-jar-with-dependencies.jar'])
	tsvs = getDataTsvs('./repos/api-surface-data', repos)
	interactionsDf = getInteractionsDF(tsvs)
	createGraph("SourceJar","TargetJar","SourcePackage","TargetPackage", interactionsDf)
	