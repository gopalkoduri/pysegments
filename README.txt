Files and their functionality:
------------------------------

--> extractFeatures.py: This file takes any number of arguments, all except the last being audio directories, and the last is the path to directory where yaml/sig & arff (output) files are put.

--> essentiaToWeka.py: This file converts all the sig files of an audio file to a single arff file compatible with weka tool. The input is path to sig files. If the given path is /home/gopal/segments/515ad72f-2f0c-473c-9feb-da701c7ce1d5/features/, It places the arff file in /home/gopal/segments/515ad72f-2f0c-473c-9feb-da701c7ce1d5/. For training, look at the __main__ function.

--> normalize.py: Normalizes the train and test files appropriately using proper bounds from train data.

--> selectFeats.py: We keep only a few of the features extracted. This file will take as input the yaml/sig filename. Any number of them can be passed as arguments. (I use linux regular expression on command line to pass all of them at once: */*.sig)


--> segment.py: This file uses a built model (../SMO-10-Min.model) to classify the segments of a given audio file. The input arguments are paths to arff files. Several of them can be passed at once. (I use linux regular expression on command line: */*.arff). Make sure the variables cmdPrefix and annotationFile are correct!!

--> zeropad.py: --Discontinued--


Example usage:

Audio directory: /media/Data/segment-example/audio/
Output directory: /media/Data/segment-example/arff/

Steps:

python extractFeatures.py /media/Data/segment-example/audio/ /media/Data/segment-example/arff/
python essentiaToWeka.py /media/gkoduri/Dump/segment-test/arff/*/10/
python normalize.py train train-data.arff train-data-norm.arff

python selectFeats.py /media/Data/segment-example/arff/*/*/*.sig
python segment.py /media/gkoduri/Dump/segment-test/arff/*/*.arff

Your annotations are stored in the file referred in the annotationFile in segment.py! It is YAML format.
