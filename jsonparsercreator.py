#iterate through each folder
#if pom.xml is there in directory, then return a (build,filename.jar)
#if pom.xml is not there in directory, then get all directories in the folder, and recurse one step deeper
# and check if pom.xml is there and return (build,filename.jar)
# If it's gradle don't do anything for now
# 
import os
import xml.etree.ElementTree as ET
import json
import copy

def seeDirectory(dName, subModuleOf, repos):
    res = []
    subModuleOf = subModuleOf.replace("repos/", "")
    dirName = dName
    if not os.path.isfile(dirName):
        isMavenSingleModuleDir = os.path.exists(os.path.join(dirName, 'pom.xml'))
        if isMavenSingleModuleDir:
            toReturn = dict()
            toReturn['execDir'] = subModuleOf+dirName.split("/")[-1]
            retVals = getJarName(os.path.join(dirName, 'pom.xml'))
            toReturn['generatedJarName'], artifact, toReturn['build'] = retVals[0], retVals[1], 'maven'
            toReturn['rootDir'] = ""
            toReturn['javaVersion'] = 8
            tmpRepos = list()
            for repo in repos:
              if 'url' in repo.keys() and repo['url'].split("/")[-1] in toReturn['execDir']:
                if not 'artifact' in repo.keys():
                  repo['artifact'] = artifact
              else:
                  tmp = copy.deepcopy(repo)
                  tmp['artifact'] = artifact
                  if not tmp in tmpRepos and not tmp in repos:
                    tmpRepos.append(tmp)
              res.append(toReturn)
            repos.extend(tmpRepos)
        # handle the gradle stuff and multimodules here
        if (os.path.exists(dirName)):
            for file in os.listdir(dirName):
                if not os.path.isfile(os.path.join(dirName,file)):
                    #if its only directory
                    res.extend(seeDirectory(os.path.join(dirName,file), dName.split("/")[-1]+"/", repos))
    return [res, repos]


def getJarName(pomFile):
    tree = ET.parse(pomFile)
    ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")
    root = tree.getroot()
    ns = "http://maven.apache.org/POM/4.0.0"

    buildElems = root.findall('build')
    for buildElem in buildElems:
        finalName = buildElem.find('finalName')
        if finalName is not None: 
          return finalName.text

    group = artifact = version = ""
    p = tree.getroot().find("{%s}parent" % ns)

    if p is not None:
      if p.find("{%s}groupId" % ns) is not None:
        group = p.find("{%s}groupId" % ns).text

      if p.find("{%s}version" % ns) is not None:
        version = p.find("{%s}version" % ns).text

    if tree.getroot().find("{%s}groupId" % ns) is not None:
      group = tree.getroot().find("{%s}groupId" % ns).text

    if tree.getroot().find("{%s}artifactId" % ns) is not None:
      artifact = tree.getroot().find("{%s}artifactId" % ns).text

    if tree.getroot().find("{%s}version" % ns) is not None:
      version = tree.getroot().find("{%s}version" % ns).text
    return [artifact + '-'+ version, artifact]


def createJson(projectListDict):
    #will keep getting rewritten, make it 'a' if need it to be appended
    fileHandle = open(os.path.join(os.getcwd(),'repos','projects-list.json'),'w+')
    fileHandle.write(json.dumps(projectListDict,indent=4))
    fileHandle.write('\n')
    fileHandle.close()


#createJson(seeDirectory('./repos/webmagic', ""))