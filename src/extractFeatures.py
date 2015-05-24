from os.path import exists, walk #is different from os.walk!
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
