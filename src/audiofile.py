src/essentiaToWeka.py                                                                               000755  000771  000024  00000005715 12223077416 015770  0                                                                                                    ustar 00gkoduri                         staff                           000000  000000                                                                                                                                                                         import essentia.standard as es
from os import listdir
import numpy as np
import sys

def sortNumerical(s):
    return int(s[:-4])

def toWeka(pathGiven, label):
    print pathGiven
    parts = pathGiven.rstrip("/").split("/")
    parentDir = "/".join(parts[:-1])
    arffFilename = "/".join([parentDir, parts[-1]+".arff"])
    wekafile=file(arffFilename, "w+")
    relation_name = "segmentation"
    wekafile.write("@RELATION segmentation\n\n")

    all_labels = ['0.000000000000000000e+00', '1.000000000000000000e+00', '2.000000000000000000e+00']
    
    #write the descriptor details only once
    descriptor_flag = 0
    
    extension = ".sig"
    fnames = listdir(pathGiven)
    #fnames.sort(key=sortNumerical)
    for fname in fnames:
        if (fname.endswith(extension)):
            fname = pathGiven+"/"+fname
            #print fname
            yamlinput = es.YamlInput(filename=fname)
            pool = yamlinput()
            descriptorList = pool.descriptorNames()
            descriptorList.remove('metadata.version.essentia')
            
            #write descriptors details (once)
            if descriptor_flag == 0:
                attr_list = ""
                for i in descriptorList:
                    if isinstance(pool[i], float):
                        attr_list = attr_list + "@ATTRIBUTE "+i+" REAL\n"
                    elif isinstance(pool[i], np.ndarray):
                        shape = pool[i].shape
                        _len = shape[0]
                        if len(shape) > 1:
                            _len = shape[0]*shape[1]
                        for j in xrange(_len):
                            attr_list = attr_list + "@ATTRIBUTE "+i+str(j+1)+" REAL\n"
                attr_list = attr_list+"\n@ATTRIBUTE segment {"+", ".join(all_labels)+"}\n\n@DATA\n"
                wekafile.write(attr_list)
                descriptor_flag = 1
            
            #write the data points
            data_entry = ""
            for i in descriptorList:
                if isinstance(pool[i], float):
                    data_entry = data_entry+str(pool[i])+", "
                elif isinstance(pool[i], np.ndarray):
                    data = pool[i]
                    shape = data.shape
                    if len(shape) > 1:
                        data = data.reshape(shape[0]*shape[1])
                    data_entry = data_entry+", ".join(str(x) for x in data)+", "
            data_entry = data_entry+label
            wekafile.write(data_entry+"\n")

if __name__ == '__main__':
    #For building model
    #toWeka("../data/vocal/features-selfeats", "0.000000000000000000e+00")
    #toWeka("../data/violin/features-selfeats", "1.000000000000000000e+00")
    #toWeka("../data/tani/features-selfeats", "2.000000000000000000e+00")
    #toWeka("../data/test/", "2.000000000000000000e+00")
    
    #For using the built model
    #pathGiven = sys.argv[1]
    pathsGiven = sys.argv[1:]
    for pathGiven in pathsGiven:
        toWeka(pathGiven, "?")
    print "Done!"
                                                   src/extractFeatures.py                                                                              000755  000771  000024  00000015156 12223104745 016207  0                                                                                                    ustar 00gkoduri                         staff                           000000  000000                                                                                                                                                                         from os.path import exists, walk #is different from os.walk!
from essentia import Pool
from os import mkdir
import essentia.standard as es
import sys
import wave
from numpy import log10, square, sqrt

def extractFeatures(arffDir, dirname, fnames, segment_length = 1):
	for fname in fnames:
		if ".wav" not in fname.lower(): continue

		wfile = wave.open(dirname+"/"+fname, "r")
		length = int((1.0 * wfile.getnframes()) / wfile.getframerate())
		print dirname+"/"+fname, length
	
		if length < segment_length: continue
	
		segmentArffDir = arffDir+"/"+fname[:-4]+"/"
		if not exists(segmentArffDir):
			mkdir(segmentArffDir)
		for start_time in xrange(0, length, segment_length):
			end_time = start_time+segment_length
			#print start_time, end_time, segment_length
			if end_time > length:
				break;
			
			loader = es.EasyLoader(filename = dirname+"/"+fname, 
								startTime=start_time, endTime=end_time)
			pool = Pool()
			lowLevelSpectralExtractor = \
			es.LowLevelSpectralExtractor(frameSize=2048, hopSize=1024, sampleRate=44100)
			
			audio = loader()
			#barkbands, barkbands_kurtosis, barkbands_skewness, barkbands_spread, hfc, mfcc, \
			#pitch, pitch_confidence, pitch_salience, sr_20, sr_30, sr_60, spectral_complexity,
			#spectral_crest, spectral_decrease, spectral_energy, spectral_energyband_low, 
			#spectral_energyband_middle_low, spectral_energyband_middle_high, spectral_energyband_high,
			#spectral_flatness_db, spectral_flux, spectral_rms, spectral_rolloff, spectral_strongpeak, 
			#zcr, inharmonicity, tristimulus, ote_her = lowLevelSpectralExtractor(audio)
			#All features except spectral contrast, mfcc and harmonic spectral features
			features = lowLevelSpectralExtractor(audio)
			
			#spectral contrast
			specContrast = es.SpectralContrast(frameSize=2048, lowFrequencyBound=40, sampleRate=44100)
			spectrum = es.Spectrum(size=2048) #size is frameSize
			
			#harmonic spectral features (TODO: Is the magnitude threshold ok?)
			spectralPeaks = es.SpectralPeaks(sampleRate=44100, minFrequency=40, maxFrequency=11000, maxPeaks=50, magnitudeThreshold=0.2)
			harmonicPeaks = es.HarmonicPeaks()
			pitch = es.PitchDetection()
			#using YIN instead of predominant pitch analysis as this frame-based analysis

			#mfcc
			mfcc = es.MFCC(lowFrequencyBound=40, sampleRate=44100)
			
			#Windowing
			window = es.Windowing(size=2048)
			for frame in es.FrameGenerator(audio, frameSize=2048, hopSize=1024):
				#spectral contrast
				s = spectrum(window(frame))
				contrast, valley = specContrast(s)
				pool.add('spectral_contrast', contrast)
				pool.add('spectral_valley', valley)

				#mfcc
				bands, mfccs = mfcc(s)
				pool.add('mfcc', mfccs[1:])

				#harmonic spectral features
				#denominator = max(s)-min(s)
				#if denominator != 0:
				#ns = (s-min(s))/denominator
				#print "In"
				#print s
				#ns = (s-min(s))/(max(s)-min(s))
				#else:
				#	ns = s
				#print ns
				freqs, mags = spectralPeaks(s)
				#print "Out"

				if len(freqs) > 0:
					p, conf = pitch(s)
					if freqs[0] == 0:
						freqs = freqs[1:]
						mags = mags[1:]
					freqs, mags = harmonicPeaks(freqs, mags, p)
					_sum = 0
					if len(freqs) == 1:
						specEnvelope_i = [freqs[0]] #for hsd
						_sum = freqs[0]*mags[0]
					elif len(freqs) == 2:
						specEnvelope_i = [(freqs[0]+freqs[1])/2.0] #for hsd
						_sum = freqs[0]*mags[0]+freqs[1]*mags[1]
					elif len(freqs) > 2:
						specEnvelope_i = [(freqs[0]+freqs[1])/2.0] #for hsd
						_sum = freqs[0]*mags[0]
						for i in xrange(1, len(freqs)-1):
							_sum += freqs[i]*mags[i] #for hsc_i
							specEnvelope_i.append((freqs[i-1]+freqs[i]+freqs[i+1])/3.0)
						specEnvelope_i.append((freqs[i]+freqs[i+1])/2.0)
						_sum += freqs[i+1]*mags[i+1]
					hsc_i = _sum/sum(mags)
					pool.add('harmonic_spectral_centroid', hsc_i)
					hsd_i = sum(abs(log10(mags)-log10(specEnvelope_i)))/sum(log10(mags))
					pool.add('harmonic_spectral_deviation', hsd_i)
					hss_i = sqrt(sum(square(freqs-hsc_i)*square(mags))/sum(square(mags)))/hsc_i
					pool.add('harmonic_spectral_spread', hss_i)
				else:
					pool.add('harmonic_spectral_centroid', 0)
					pool.add('harmonic_spectral_deviation', 0)
					pool.add('harmonic_spectral_spread', 0)


			for i in xrange(0, len(features[0])):
				#pool.add('mfcc', features[5][i])
				pool.add('pitch_confidence', features[7][i])
				pool.add('spectral_flatness_db', features[20][i])
				pool.add('spectral_flux', features[21][i])
				pool.add('spectral_rms', features[22][i])
				pool.add('spectral_rolloff', features[23][i])
				pool.add('spectral_strongpeak', features[24][i])
				pool.add('zero_crossing_rate', features[25][i])
				pool.add('inharmonicity',  features[26][i])
				pool.add('tristimulus',  features[27][i])
			
			#if sum(abs(pool['harmonic_spectral_centroid'])) == 0: continue
			onsetRate = es.OnsetRate()
			onsets, rate = onsetRate(audio)
			try:
				aggrPool = es.PoolAggregator(defaultStats = ['mean', 'var', 'skew', 'kurt', 'cov'])(pool)
			except:
				print start_time/segment_length, "failed"
				continue

#					aggrPool = es.PoolAggregator(defaultStats = ['mean'], exceptions = \
#												{'pitch_confidence' : ['mean', 'var', 'skew'],\
#												'spectral_flux' : ['mean', 'skew'],\
#												'spectral_strongpeak' : ['mean', 'var'],\
#												'mfcc' : ['mean', 'var', 'cov'],\
#												'harmonic_spectral_centroid' : ['mean', 'var'], \
#												'harmonic_spectral_deviation' : ['mean', 'var'], \
#												'harmonic_spectral_spread' : ['mean', 'var'], \
#												'spectral_contrast' : ['mean', 'var'], \
#												'spectral_valley' : ['mean', 'var'], \
#												'tristimulus' : ['mean', 'var']})(pool)
			aggrPool.add('onset_rate', rate)
			
#			#remove the first coefficient. (why?)
#			if aggrPool.containsKey('mfcc.mean'):
#				for feat in ['mean', 'var','skew','kurt', 'cov']:
#					temp = aggrPool['mfcc.'+feat][1:]
#					aggrPool.remove('mfcc.'+feat)
#					for i in temp: aggrPool.add('mfcc.'+feat, i)
				
			#print start_time, segment_length, start_time/segment_length
			fileout = segmentArffDir+fname[:-4]+"_%003d%s"%(start_time/segment_length, ".sig")
			output = es.YamlOutput(filename = fileout)
			output(aggrPool)

def main(wavDir, arffDir):
	"""
	main(wavDir, arffDir)
	wavDir: The complete path to the folder with set of wav files of 
	which the features are to be calculated. This folder can have several 
	levels of sub folders.
	arffDir: The complete path to the folder where the features have to be
	saved. For each wav file, a folder is created by its name in this folder.
	"""
	walk(wavDir, extractFeatures, arffDir)

if __name__ == '__main__':
	wavDirs = sys.argv[1:-1]
	arffDir = sys.argv[-1]
	for wavDir in wavDirs:
		main(wavDir, arffDir)
	print "Done!"
                                                                                                                                                                                                                                                                                                                                                                                                                  src/normalize.py                                                                                    000755  000771  000024  00000010024 12077722602 015030  0                                                                                                    ustar 00gkoduri                         staff                           000000  000000                                                                                                                                                                         # -*- coding: utf-8 -*-

#This is to be run after essentiaToWeka.py
#Handling nans and infs:
#infs: negative inf is set to min of the range of feature values and viceversa
#nans: set to 0

import sys
import numpy as np
from os import unlink
from os.path import basename

topLimit=100000

#arguments:
if len(sys.argv) < 2:
	print """
	Usage:
	------
	python normalize.py 'train' trainFile normalizedTrainFile (OR)
	python normalize.py 'test' trainFile testFiles destDirectory
	"""
	exit()

#[train] [trainFile] [normalizedTrainFile]
#[test] [trainFile] [testFile] [normalizedTestFile]

if sys.argv[1] == "train":
	#look all the values for each feature and find max and min, and normalize to (0-1)
	temp = file(sys.argv[2], "r").readlines()
	prologue = ""
	for line in temp:
		prologue += line
		if line.strip() == "@DATA":
			break
	numFeats = len(temp[-1].strip().split(","))-1
	del temp
	data = np.loadtxt(sys.argv[2], dtype='float', delimiter=',', comments='@', usecols=range(numFeats))
	for i in xrange(numFeats):
		temp = data[:, i]
		infAlert = 0
		if max(temp) == np.inf:
			infAlert = 1
			temp = temp[temp < np.inf]
		if min(temp) == -np.inf:
			infAlert = 1
			temp = temp[temp > -np.inf]
		_max = max(temp)
		_min = min(temp)
		data[:, i] = (data[:, i]-_min)/(_max-_min)
		#TODO: Is there a better way to handle inf & nan values?
		_min = min(abs(data[:, i])) 
		#The following is because weka complains if the numbers are too small (I guess 1.0e-8)
		if infAlert:
			data[:, i][data[:, i] == np.inf] = topLimit
			data[:, i][data[:, i] == -np.inf] = 0
		data[:, i] = np.nan_to_num(data[:, i])
		data[:, i] = data[:, i]*topLimit
#	for i in xrange(numFeats):
#		print i, max(data[:, i]), min(data[:, i])
	outfile = file(sys.argv[3], 'w')
	outfile.write(prologue)
	labels = np.loadtxt(sys.argv[2], dtype='float', comments='@', usecols=[numFeats])
	data = np.column_stack([data, labels])
	np.savetxt('dataTMP.txt', data, delimiter=',')
	#Weird. Python does not seem to have a nice way to 'append' array data to a file. 
	#It can only create a new file and write.
	temp = file('dataTMP.txt', 'r').read()
	unlink('dataTMP.txt')
	outfile.write(temp)
	outfile.close()

elif sys.argv[1] == "test":
	#read limits obtained from train data and do normalization accordingly
	#temp = file(sys.argv[2], "r").readlines()
	#numFeats = len(temp[-1].strip().split(","))-1
	#del temp
	numFeats = 40 #NOTE: Hardcoded to reduce i/o, uncomment the above lines and delete this if necessary
	data = np.loadtxt(sys.argv[2], dtype='float', delimiter=',', comments='@', usecols=range(numFeats))
	trainLimits = []
	for i in xrange(numFeats):
		temp = data[:, i]
		infAlert = 0
		temp = temp[temp < np.inf]
		temp = temp[temp > -np.inf]
		_max = max(temp)
		_min = min(temp)
		trainLimits.append([_min, _max])

	#prologue is same for every file. read for one, and write for all.
	temp = file(sys.argv[3], "r").readlines()
	prologue = ""
	for line in temp:
		prologue += line
		if line.strip() == "@DATA":
			break
	#numFeats = len(temp[-1].strip().split(","))-1
	del temp
	for f in sys.argv[3:-1]:
		print f
		data = np.loadtxt(f, dtype='float', delimiter=',', comments='@', usecols=range(numFeats))
		for i in xrange(numFeats):
			temp = data[:, i]
			_min = trainLimits[i][0]
			_max = trainLimits[i][1]
			data[:, i] = (data[:, i]-_min)/(_max-_min)
			#TODO: Is there a better way to handle inf & nan values?
			_min = min(abs(data[:, i])) 
			data[:, i][data[:, i] == np.inf] = topLimit
			data[:, i][data[:, i] == -np.inf] = 0
			data[:, i] = np.nan_to_num(data[:, i])
			#The following is because weka complains if the numbers are too small (I guess 1.0e-8)
			data[:, i] = data[:, i]*topLimit
		
		outfile = file(sys.argv[-1]+"/"+basename(f), 'w')
		outfile.write(prologue)
		np.savetxt('dataTMP.txt', data, delimiter=',')
		#Weird. Python does not seem to have a nice way to 'append' array data to a file. 
		#It can only create a new file and write.
		temp = file('dataTMP.txt', 'r').readlines()
		unlink('dataTMP.txt')
		for line in temp:
			line = line.strip()
			line = line+",?\n"
			outfile.write(line)
		outfile.close()
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            src/scripts/                                                                                        000755  000771  000024  00000000000 12223076267 014147  5                                                                                                    ustar 00gkoduri                         staff                           000000  000000                                                                                                                                                                         src/scripts/moveTrainSigFiles.sh                                                                    000755  000771  000024  00000000126 12017655000 020064  0                                                                                                    ustar 00gkoduri                         staff                           000000  000000                                                                                                                                                                         for i in *; do for j in "$i"/10/*; do mv "$j" "`echo $j|sed 's/\//\_/g'`"; done; done
                                                                                                                                                                                                                                                                                                                                                                                                                                          src/segment-py.py                                                                                   000755  000771  000024  00000006413 12223076513 015123  0                                                                                                    ustar 00gkoduri                         staff                           000000  000000                                                                                                                                                                         # -*- coding: utf-8 -*-
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
                                                                                                                                                                                                                                                     src/segment.py                                                                                      000755  000771  000024  00000006453 12223076527 014506  0                                                                                                    ustar 00gkoduri                         staff                           000000  000000                                                                                                                                                                         from os.path import walk
from os import system
from numpy import unique
import sys
import yaml

annotationFile = "annotations.yaml"

def mode(values):
	uniq_v = unique(values)
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
	tmpFile =  "tmp.out"
	cmdPrefix = 'java -classpath "/homedtic/gkoduri/Workspace/tools/weka-3-6-8/weka.jar" weka.classifiers.lazy.IBk -l "/homedtic/gkoduri/Workspace/segmentation/data/weka experiments/weka-knn.model" -p 0 -T '
	#cmdPrefix = 'java -classpath "C:/Program Files/Weka-3-6/weka.jar" weka.classifiers.functions.SMO -l "SMO-10-Min.model" -p 0 -T '
	cmd = cmdPrefix+'"'+arffFilePath+'" > '+tmpFile
	#print cmd
	system(cmd)
	output = file(tmpFile).readlines()
	output = output[5:-1] #wondering why? open tmpFile and look.
	timeframe = []
	prediction = []
	for i in output:
		parts = i.split()
		timeframe.append(int(parts[0]))
		temp = parts[2].split(":")
		prediction.append(temp[1])
	#print prediction
	prediction = modeFilter(prediction, modeRange)
	print prediction
	exit()
	#print len(timeframe), len(prediction)
	prev = prediction[0]
	start = -1
	end = -1
	if prev == "vocal": start = 0
	vocalPieces = []
	for i in xrange(1, len(timeframe)):
		if start != -1 and prediction[i] != "vocal":
			end = i
			vocalPieces.append({'start':start*segmentLength, 'end':end*segmentLength})
			start = -1
			end = -1
		if start == -1 and prediction[i] == "vocal":
			start = i
	if start != -1 and start != i:
		if end == -1:
			end = i
		vocalPieces.append({'start':start*segmentLength, 'end':end*segmentLength})
	return vocalPieces

if __name__ == '__main__':
	segmentLength = 1
	modeRange = 5
	arffFilePaths = sys.argv[1:]
	annotations = yaml.load(file(annotationFile))
	if not annotations:
		annotations = {}
	for arffFilePath in arffFilePaths:
		mbid = arffFilePath.split("/")[-1].split("_")[0]
		print mbid, "being processed ..."
		vocalPieces = segment(arffFilePath)
		print vocalPieces
		print "---------------"		
		if mbid in annotations.keys():
			if 'vocal' in annotations[mbid].keys():
				annotations[mbid].pop('vocal')
			annotations[mbid]['vocal'] = {'segments': vocalPieces, 'annotator':'gopal\'s script'}
		else:
			annotations[mbid] = {}
			annotations[mbid]['vocal'] = {'segments': vocalPieces, 'annotator':'gopal\'s script'}
	yaml.dump(annotations, file(annotationFile, "w"), default_flow_style=False)

                                                                                                                                                                                                                     src/selectFeats.py                                                                                  000755  000771  000024  00000003553 12077713767 015317  0                                                                                                    ustar 00gkoduri                         staff                           000000  000000                                                                                                                                                                         from essentia.standard import YamlInput, YamlOutput
import sys

#This file does an in-place selection of features. Meaning selected features
#from a file are written to the same file.

fnames = sys.argv[1:]

#non-array type values in wanted features
wantedFeats = ["harmonic_spectral_centroid.mean","harmonic_spectral_centroid.skew","harmonic_spectral_centroid.var","harmonic_spectral_spread.mean","harmonic_spectral_spread.skew","mfcc.cov","mfcc.kurt","mfcc.mean","mfcc.skew","pitch_confidence.mean","pitch_confidence.skew","spectral_contrast.cov","spectral_contrast.mean","spectral_flatness_db.mean","spectral_rms.mean","spectral_rms.skew","spectral_strongpeak.kurt","spectral_strongpeak.mean","spectral_strongpeak.skew","spectral_valley.cov","spectral_valley.mean","spectral_valley.var","tristimulus.mean","tristimulus.skew"]

#array type values in wanted features
wantedIndices = {"mfcc.cov": [2, 15, 26], "mfcc.kurt":[1], "mfcc.mean":[2, 4, 5, 7, 8, 12], \
				"mfcc.skew": [1, 2], "spectral_contrast.cov": [9, 11, 14, 26], "spectral_contrast.mean": [2, 3, 5], \
				"spectral_valley.cov": [16, 21, 22], "spectral_valley.mean": [6], "spectral_valley.var": [4], \
				"tristimulus.mean": [1, 2], "tristimulus.skew": [2]}

#Do!
for fname in fnames:
	print fname
	fileIn = YamlInput(filename=fname)
	pool = fileIn()
	
	for descriptor in pool.descriptorNames():
		if descriptor not in wantedFeats:
			pool.remove(descriptor)
						
	for descriptor in wantedIndices.keys():
		temp = pool[descriptor]
		shape = temp.shape
		if len(shape) > 1:
			temp = temp.reshape(shape[0]*shape[1])
		pool.remove(descriptor)
		for index in wantedIndices[descriptor]:
			pool.add(descriptor, temp[index-1])
			#In essentiaToWeka, we make index 0 as element 1. (eg: mfcc.mean1). 
			#remember the wanted features are known from weka experiment! Hence index-1 !!
		
	output = YamlOutput(filename=fname)
	output(pool)
                                                                                                                                                     src/zeropad.py                                                                                      000755  000771  000024  00000000517 12052417577 014507  0                                                                                                    ustar 00gkoduri                         staff                           000000  000000                                                                                                                                                                         #!/usr/bin/env python
#NOT USED ANYMORE!

from os import listdir, rename
import sys


folder = sys.argv[1]+"/"

for oldName in listdir(folder):
	if oldName[-4:] == ".sig":
		parts = oldName.strip(".sig").split("_")
		newName = folder+"%s%003d%s" %(parts[0]+"_", int(parts[1]), ".sig")
		print newName
		rename(folder+oldName, newName)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 