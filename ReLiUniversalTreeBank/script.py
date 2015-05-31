#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author: Pedro Balage (pedrobalage@gmail.com)
# Date: 25/05/2015
# Version: 1.0

# Python 3 compatibility
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement

# imports
from subprocess import Popen, PIPE
import tempfile
import fileinput
import codecs
import os
import re
import unicodedata

# variables
CORPUS_PATH = 'corpus/'
CORPUS_OUTPUT_PATH = 'corpus_UTB/'

# logfile
logfile = codecs.open('logfile.txt','w',encoding = 'utf-8')

def process_sentence(sentence):

    sentence_string = ' '.join([item['word'] for item in sentence])

    # MXPOST 
    p = Popen(['java', 
                '-mx30m', 
                '-cp', 
                'mxpost/mxpost.jar',
                'tagger.TestTagger',
                'pt-br-universal-tagger.project'], 
            stdin = PIPE, stdout=PIPE, stderr=PIPE)

    stdout, stderr = p.communicate(input=sentence_string.encode('utf8'))
    output = stdout.decode('utf8')

    tokens = [(w[:w.rfind('_')],w[w.rfind('_')+1:]) for w in output.split()]


    # MALT Parser
    input_file = tempfile.NamedTemporaryFile(prefix='malt_input.conll',
                                                    dir=tempfile.gettempdir(),
                                                    delete=False)
    output_file = tempfile.NamedTemporaryFile(prefix='malt_output.conll',
                                                    dir=tempfile.gettempdir(),
                                                    delete=False)

    for (i, (word, tag)) in enumerate(tokens, start=1):
        input_str = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' %\
            (i, word, '_', tag, tag, '_', '0', 'a', '_', '_')
        input_file.write(input_str.encode("utf8"))
    input_file.write(b'\n\n')
    input_file.close()

    cmd = ['java' ,
            '-jar', 'maltparser-1.8.1/maltparser-1.8.1.jar',
            '-c'  , 'uni-dep-tb-ptbr', 
            '-i'  , input_file.name,
            '-o'  , output_file.name, 
            '-m'  , 'parse']

    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    ret = p.wait()

    output = codecs.open(output_file.name,'r',encoding='utf8').read()

    input_file.close()
    os.remove(input_file.name)
    output_file.close()
    os.remove(output_file.name)

    # parser the output lines. Each line is a token
    lines = output.split('\n')

    output_string = ''
    i = -1   # token index

    while i < len(lines)-1:

        i += 1
        line = lines[i].strip()

        # ignore blank lines 
        if line == '':
            continue

        values = line.split('\t')
        if len(values) == 10:
            id,word,lemma,cpostag,postag,feats,head,deprel,phead,pdeprel = values
        else:
            logfile.write('Error processing, line doesnt have 10 values: \n{0}\n'.format(line))
            continue

        obj = sentence[i]['obj']
        if obj == 'O':
            obj = '_'
        opinion = sentence[i]['opinion']
        if opinion == 'O':
            opinion = '_'
        pol = sentence[i]['pol']
        if pol == 'O':
            pol = '_'

        # tokens match. OK!
        if word == sentence[i]['word']:
            output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
        else:
            # I dont know the problem
            logfile.write('Mismatch from word "{0}" with ReLi word "{1}" in the sentence:\n\t{2}\n\noutput:\n{3}'.format(word,sentence[i+j]['word'],sentence_string,output))            
            return ''

    return output_string

# List all the files under the directory
corpus_files = os.listdir(CORPUS_PATH)

discarted_sentences = 0
processed_sentences = 0

# Read each file and process
for filename in corpus_files:
    # Filname pattern
    if filename.startswith('ReLi') and filename.endswith('.txt'):
        input_file = codecs.open(CORPUS_PATH+filename,'r',encoding = 'utf-8')
        output_file = codecs.open(CORPUS_OUTPUT_PATH+filename,'w',encoding = 'utf-8')

        # reand and write the header
        input_file.next()
        output_file.write('[features = id, word, lemma, cpostag, postag, feats, obj, opinion, pol, head, deprel, phead, pdeprel]\n')

        sentence = []
        # loop to go through the text
        for line_num,line in enumerate(input_file):

            if line.startswith('#'):
                output_file.write(line)

            # Match the break line. Sentence boundary
            elif len(line.strip()) == 0:
                if len(sentence) != 0:
                    print('Processing {0}, linha {1}'.format(filename,line_num))
                    output = process_sentence(sentence)
                    if output == '':
                        logfile.write('Error processing, line {0} from {1}\n'.format(line_num,filename))
                        discarted_sentences += 1
                    else:
                        processed_sentences += 1
                        output_file.write(output)
                    sentence = []
                output_file.write('\n')

            # Find the elements in each line (word, pos, object, opinion, polarity, help).
            else:
                values = line.split('\t')
                if len(values) == 6:
                    word,pos,obj,opinion,pol,help = values
                    # store as a tuple of items
                    sentence.append( {'word':word,
                                    'pos':pos,
                                    'obj':obj,
                                    'opinion':opinion,
                                    'pol':pol,
                                    'help':help} )
                else:
                    logfile.write('Line {0} from {1} has not 6 features, values: {2}\n'.format(line_num,filename,line))
                    continue

        # Match the EOF, last sentence boundary
        if len(sentence) != 0:
            output = process_sentence(sentence)
            output_file.write(output)
            processed_sentences += 1

        logfile.write('\nSummary:\n\n')
        logfile.write('Processed Sentences: {0}\n'.format(processed_sentences))
        logfile.write('Discarted Sentences: {0}\n'.format(discarted_sentences))
