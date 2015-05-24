from essentia.standard import YamlInput, YamlOutput
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
