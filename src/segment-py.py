# -*- coding: utf-8 -*-
from os.path import walk
from os import system
from sklearn import neighbors
import sys
import yaml
import numpy as np

annotationFile = "/homedtic/gkoduri/Workspace/annotations.yaml"
numFeats = 40
segmentLength = 1
modeRange = 5

def loadModel(trainDataFile):
	temp = file(trainDataFile, "r").readlines()
	numFeats = len(temp[-1].strip().split(","))-1
	data = np.loadtxt(trainDataFile, dtype='float', delimiter=',', comments='@', usecols=range(numFeats))
	labels = np.loadtxt(trainDataFile, dtype='float', delimiter=',', comments='@', usecols=[numFeats])
	
	global knn
	knn = neighbors.KNeighborsClassifier(n_neighbors=5, weights='distance')
	#p=1 uses manhattan distance, p=2 is eucl.
	knn.fit(data, labels)
	
def mode(values):
	uniq_v = np.unique(values)
	counts = []
	for i in uniq_v:
		counts.append(values.count(i))
	i = counts.index(max(counts))
	return uniq_v[i]

def modeFilter(prediction, l):
	"""
	Mode filter customized to be biased. It will turn vocal to violin/tani but not
	viceversa. This is intended for analyzing pitch of vocal regions, for which we
	want no false positives (violin/tani) even if that means losing out a few positives.
	"""
	prediction = list(prediction)
	newPrediction = []

	if len(prediction) < l:
		for i in prediction:
			newPrediction.append(mode(prediction))
		return newPrediction
	#else:
	newPrediction.extend(prediction)
	padding = (l-1)/2
	#print padding
	for i in xrange(padding):
		prediction.insert(0, prediction[0])
		prediction.insert(-1, prediction[-1])

	for i in xrange(padding, len(prediction)-padding):
		#if prediction[i] == "vocal":
		newPrediction[i-padding] = mode(prediction[i-padding:i+padding+1])

	prediction = prediction[padding:-1*padding]
	return newPrediction

def segment(arffFilePath):
	#NOTE: When run in bulk, make sure numFeats is pre-determined and not estimated for every file!!
	#temp = file(arffFilePath, "r").readlines()
	#numFeats = len(temp[-1].strip().split(","))-1
	data = np.loadtxt(arffFilePath, dtype='float', delimiter=',', comments='@', usecols=range(numFeats))
	prediction = knn.predict(data)
	
	prediction = modeFilter(prediction, modeRange)
	prev = prediction[0]
	start = -1
	end = -1
	if prev == 0: start = 0
	vocalPieces = []
	for i in xrange(1, len(prediction)):
		if start != -1 and prediction[i] != 0:
			end = i
			vocalPieces.append({'start':start*segmentLength, 'end':end*segmentLength})
			start = -1
			end = -1
		if start == -1 and prediction[i] == 0:
			start = i
	if start != -1 and start != i:
		if end == -1:
			end = i
		vocalPieces.append([start*segmentLength, end*segmentLength])
	return vocalPieces

if __name__ == '__main__':
	loadModel(sys.argv[1])
	arffFilePaths = sys.argv[2:]
	annotations = yaml.load(file(annotationFile))
	if not annotations:
		annotations = {}
	for arffFilePath in arffFilePaths:
		mbid = arffFilePath.split("/")[-1].split(".")[0]
		print mbid
		vocalPieces = segment(arffFilePath)
		if mbid in annotations.keys():
			if 'vocal' in annotations[mbid].keys():
				annotations[mbid].pop('vocal')
			annotations[mbid]['vocal'] = {'segments': vocalPieces, 'annotator':'gopal\'s script'}
		else:
			annotations[mbid] = {}
			annotations[mbid]['vocal'] = {'segments': vocalPieces, 'annotator':'gopal\'s script'}
	yaml.dump(annotations, file(annotationFile, "w"), default_flow_style=False)
