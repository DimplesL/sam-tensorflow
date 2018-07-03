import numpy as np
import os
import re
import h5py
import math
import json
from collections import Counter


def create_vocabulary_word2vec(file, capl=None, v2i={'': 0, 'UNK':1, 'BOS':2, 'EOS':3}):
	'''
	v2i = {'': 0, 'UNK':1}  # vocabulary to index
	'''
	vocab_file = file+'/vocabulary.txt'
	train_file = file+'/sents_train_lc_nopunc.txt'
	val_file = file+'/sents_val_lc_nopunc.txt'
	test_file = file+'/sents_test_lc_nopunc.txt'
	
	with open(vocab_file, 'r') as voc_f:
		for line in voc_f:
			word = line.strip()
			v2i[word]=len(v2i)

	train_data = []
	val_data = []
	test_data = []
	def parse_file_2_dict(temp_file):
		captions = []
		with open(temp_file, 'r') as voc_f:
			for line in voc_f:
				cap = {}
				temp = line.strip().split('\t')
				words = temp[1].split(' ')
				if len(words)<capl:# and len(words)>=8: 
				# if len(words)<16:
					cap[temp[0]] = words
					captions.append(cap)
		return captions
	def generate_test_data():
		captions = []
		
		for idx in xrange(1301,1971):
			cap = {}
			cap['vid'+str(idx)] = ['']
			captions.append(cap)
		return captions

	train_data = parse_file_2_dict(train_file)
	val_data = parse_file_2_dict(val_file)
	test_data = generate_test_data()

	# v2i = generate_vocab(train_data, v2i={'': 0, 'UNK':1, 'BOS':2, 'EOS':3})
	print('len v2i:',len(v2i))
	return v2i, train_data, val_data, test_data



	

def getCategoriesInfo(file):
	'''
	v2i = {'': 0, 'UNK':1}  # vocabulary to index
	limit_sen: the number sentence for training per video
	'''
	json_file = file+'/videodatainfo_2017.json'
	train_info = json.load(open(json_file,'r'))
	videos = train_info['videos']
	cate_info = {}
	for idx,video in enumerate(videos):
		cate_info[video['video_id']]=video['category']

	return cate_info

def getBatchVideoCategoriesInfo(batch_caption, cate_info, feature_shape):
	batch_size = len(batch_caption)
	input_categories = np.zeros((batch_size,1),dtype='float32')

	for idx, caption in enumerate(batch_caption):
		for k,v in caption.items():
			input_categories[idx,0] = cate_info[k]
	return input_categories

def getBatchVideoAudioInfo(batch_caption, audio_info):
	batch_size = len(batch_caption)
	input_audio = np.zeros((batch_size,34,2),dtype='float32')

	for idx, caption in enumerate(batch_caption):
		for k,v in caption.items():
			vid = int(k[5:])
			input_audio[idx,:,:] = audio_info[vid]
	return input_audio

def generate_vocab(train_data, v2i={'': 0, 'UNK':1, 'BOS':2, 'EOS':3}):


	for caption_info in train_data:
		for k,v in caption_info.items():
			for w in v:
				if not v2i.has_key(w):
					v2i[w] = len(v2i)


	print('vocab size %d' %(len(v2i)))
	return v2i
	


def getBatchVideoFeature(batch_caption, hf, feature_shape):
	batch_size = len(batch_caption)
	input_video = np.zeros((batch_size,)+tuple(feature_shape),dtype='float32')

	for idx, caption in enumerate(batch_caption):
		for k,v in caption.items():
			feature = hf[k]
			input_video[idx] = np.reshape(feature,feature_shape)
	return input_video

def getBatchC3DVideoFeature(batch_caption, hf, feature_shape):
	batch_size = len(batch_caption)
	input_video = np.zeros((batch_size,)+tuple(feature_shape),dtype='float32')

	for idx, caption in enumerate(batch_caption):
		for k,v in caption.items():
			vid = int(k[5:])
			feature = hf[vid]
			input_video[idx] = np.reshape(feature[0:40,:],feature_shape)
	return input_video

def getBatchStepVideoFeature(batch_caption, hf, feature_shape):
	batch_size = len(batch_caption)
	feature_shape = (40,1024)
	step = np.random.randint(1,5)
	# print(step)
	input_video = np.zeros((batch_size,)+tuple((10,1024)),dtype='float32')

	for idx, caption in enumerate(batch_caption):
		for k,v in caption.items():
			vid = int(k[5:])
			feature = hf[vid]
			input_video[idx] = np.reshape(feature,feature_shape)[0::step][0:10]
	return input_video



def getBatchTrainCaption(batch_caption, v2i, capl=16):
	batch_size = len(batch_caption)

	labels = np.zeros((batch_size,capl,len(v2i)),dtype='int32')

	input_captions = np.zeros((batch_size,capl),dtype='int32')
	input_captions[:,0] = v2i['BOS']

	for idx, caption in enumerate(batch_caption):
		for vid, sen in caption.items():

			for k, w in enumerate(sen):
				
				if w in v2i.keys():
					labels[idx][k][v2i[w]] = 1
					input_captions[idx][k+1] = v2i[w]
				else:
					labels[idx][k][v2i['UNK']] = 1
					input_captions[idx][k+1] = v2i['UNK']
			labels[idx][len(sen)][v2i['EOS']] = 1
			if len(sen)+1<capl:
				input_captions[idx][len(sen)+1] = v2i['EOS']
	return input_captions, labels



def getBatchTestCaption(batch_caption, v2i, capl=16):
	batch_size = len(batch_caption)
	labels = np.zeros((batch_size,capl,len(v2i)),dtype='int32')
	input_captions = np.zeros((batch_size,capl),dtype='int32')
	input_captions[:,0] = v2i['BOS']


	return input_captions, labels

def getBatchTrainCaptionWithSparseLabel(batch_caption, v2i, capl=16):
	batch_size = len(batch_caption)

	labels = np.zeros((batch_size,capl),dtype='int32')

	input_captions = np.zeros((batch_size,capl),dtype='int32')
	input_captions[:,0] = v2i['BOS']

	for idx, caption in enumerate(batch_caption):
		for vid, sen in caption.items():

			for k, w in enumerate(sen):
				
				if w in v2i.keys():
					labels[idx][k]=v2i[w] 
					input_captions[idx][k+1] = v2i[w]
				else:
					labels[idx][k]= v2i['UNK']
					input_captions[idx][k+1] = v2i['UNK']
			labels[idx][len(sen)]= v2i['EOS']
			if len(sen)+1<capl:
				input_captions[idx][len(sen)+1] = v2i['EOS']
	return input_captions, labels




def getBatchTestCaptionWithSparseLabel(batch_caption, v2i, capl=16):
	batch_size = len(batch_caption)
	labels = np.zeros((batch_size,capl),dtype='int32')
	input_captions = np.zeros((batch_size,capl),dtype='int32')
	input_captions[:,0] = v2i['BOS']


	return input_captions, labels
def convertCaptionI2V(batch_caption, generated_captions,i2v):
	captions = []
	for idx, sen in enumerate(generated_captions):
		caption = ''
		for word in sen:
			if i2v[word]=='EOS' or i2v[word]=='':
				break
			caption+=i2v[word]+' '
		captions.append(caption)
	return captions


if __name__=='__main__':
	main()