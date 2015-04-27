#!/usr/bin/python
# -*- coding: utf-8 -*-

#### Script to produce the ReLi Corpus with PALAVRAS parser dependency output
#### Used PALAVRAS revision 10586, compiled on 2015-03-08
####
#### Corpus reference:
####          Freitas, C., Motta, E., Milidiú, R., & Cesar, J. (2012).
####          Vampiro que brilha... rá! Desafios na anotação de opinião em um corpus
####          de resenhas de livros. Proceedings do XI Encontro de Linguística de Corpus (XI ELC). São Carlos - SP.
####          http://www.linguateca.pt/Repositorio/ReLi/
####
#### Parser reference:
####          Bick, Eckhard (2000), The Parsing System "Palavras" - Automatic Grammatical Analysis of Portuguese in a Constraint Grammar Framework
####          Aarhus: Aarhus University Press -- dr.phil. thesis
####          http://beta.visl.sdu.dk/constraint_grammar.html

# Author: Pedro Balage (pedrobalage@gmail.com)
# Date: 23/04/2015
# Version: 1.0

# Python 3 compatibility
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement

# imports
import os
import re
from subprocess import Popen, PIPE
import codecs
import unicodedata

# variables
CORPUS_PATH = 'corpus/'
CORPUS_OUTPUT_PATH = 'corpus_PALAVRAS/'
PALAVRAS_CMD = ['/opt/palavras/por.pl']
PALAVRAS_POS_CMD = ['/opt/palavras/bin/visldep2conll']

# logfile
logfile = codecs.open('logfile.txt','w',encoding = 'utf-8')

def process_sentence(sentence):

    sentence_string = ' '.join([item['word'] for item in sentence])

    # Run PALAVRAS with the sentence string

    # first PALAVRAS parser
    p = Popen(PALAVRAS_CMD, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = p.communicate(input=sentence_string.encode('utf8'))

    # second the script to convert from visl format to conll format
    p = Popen(PALAVRAS_POS_CMD, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = p.communicate(input=stdout)

    output= stdout.decode('utf8')

    # some normalizations
    output = output.replace('&quot;','"')
    output = output.replace('--','-')

    output_string = ''
    i = -1   # token index
    j = 0   # index correction while read the tokens

    # parser the output lines. Each line is a token
    lines = output.split('\n')

    while i < len(lines)-1:

        i += 1
        line = lines[i].strip()

        # blank lines is a signal for sentence splitting
        if line == '':
            output_string += '\n'
            j -=1
            continue

        # long urls are not parsed
        if line.startswith('<long:'):
            j +=1
            continue

        values = line.split('\t')
        if len(values) == 10:
            id,word,lemma,cpostag,postag,feats,head,deprel,phead,pdeprel = values
        elif len(values) == 11:
            id,word,lemma,cpostag,postag,feats,head,deprel,extrasem,phead,pdeprel = values
        else:
            logfile.write('Error processing PALAVRAS, line doesnt have 10 values: \n{0}\n'.format(line))
            continue


        # some semantic tags come with the word
        if '<' in word:
            word = re.sub(r' <\w+>','',word)

        # tokens created by PALAVRAS in the end of the sentence, Ex. full stop.
        if i+j >= len(sentence):
            obj = '_'
            opinion = '_'
            pol = '_'
            output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
            continue

        obj = sentence[i+j]['obj']
        if obj == 'O':
            obj = '_'
        opinion = sentence[i+j]['opinion']
        if opinion == 'O':
            opinion = '_'
        pol = sentence[i+j]['pol']
        if pol == 'O':
            pol = '_'

        #########################################################################
        ######## map tokenization between the input and the output       ########
        #########################################################################

        # tokens match. OK!
        if word == sentence[i+j]['word']:
            output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
            continue


        # tokens dont match due a collocation: hoje_em_dia
        if '_' in word:
            shift = word.count('_')
            collocation = '_'.join([item['word'] for item in sentence[i+j:i+j+shift+1]])
            if word == collocation:
                j += shift
                output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
                continue

        # PALAVRAS concatenated two or three tokens
        if word.startswith(sentence[i+j]['word']):
            # 2 tokens
            shift = 1
            collocation = ''.join([item['word'] for item in sentence[i+j:i+j+shift+1]])
            if word == collocation:
                j += shift
                output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
                continue
            else:
                # 3 tokens
                shift = 2
                collocation = ''.join([item['word'] for item in sentence[i+j:i+j+shift+1]])
                if word == collocation:
                    j += shift
                    output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
                    continue

        # PALAVRAS split a token in two and contractions
        if i+1 < len(lines):
            next_line = lines[i+1].strip()
            if next_line != '':
                next_word = lines[i+1].strip().split('\t')
                if len(next_word) >= 2:
                    collocation = word + next_word[1]
                    if collocation == 'dea':
                        collocation = 'da'
                    if collocation == 'deo':
                        collocation = 'do'
                    if collocation == 'emaquela':
                        collocation = 'naquela'
                    if collocation == 'emaquele':
                        collocation = 'naquele'
                    if collocation == 'emos':
                        collocation = 'nos'
                    if collocation == 'emas':
                        collocation = 'nas'
                    if sentence[i+j]['word'] == collocation:
                        shift = -1
                        j += shift
                        i+=1
                        output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
                        continue
            else:
                # in case there is a blank line between the tokens
                if i+2 < len(lines):
                    next_line = lines[i+2].strip()
                    if next_line != '':
                        next_word = lines[i+2].strip().split('\t')
                        if len(next_word) >= 2:
                            collocation = word + next_word[1]
                            if sentence[i+j]['word'] == collocation:
                                shift = -2
                                j += shift
                                i+=2
                                output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
                                continue

        # PALAVRAS split a token in three
        if sentence[i+j]['word'].startswith(word):
            if i+1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line != '':
                    next_word = lines[i+1].strip().split('\t')
                    if len(next_word) >= 2:
                        collocation = word + next_word[1]
                        if i+2 < len(lines):
                            next_line = lines[i+2].strip()
                            if next_line != '':
                                next_word = lines[i+2].strip().split('\t')
                                if len(next_word) >= 2:
                                    collocation += collocation + next_word[1]
                                    if sentence[i+j]['word'] == collocation:
                                        shift = -2
                                        j += shift
                                        i+=2
                                        output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
                                        continue

        # PALAVRAS change symbom ' to `
        if word == sentence[i+j]['word'].replace('\'','`'):
            output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
            continue

        # PALAVRAS remove dialog introduction symbol '-'
        if word == sentence[i+j]['word'].replace('-',''):
            output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
            continue

        # PALAVRAS symbol ' from the word:
        if word == sentence[i+j]['word'].replace('\'',''):
            output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
            continue

        # PALAVRAS sometimes put accents in the words
        w1 = unicodedata.normalize('NFD', word).encode('ascii', 'ignore').lower()
        w2 = unicodedata.normalize('NFD', sentence[i+j]['word']).encode('ascii', 'ignore').lower()
        if w1 == w2:
            output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
            continue

        # Unknown match, but next words match, so continue...
        if i+1 < len(lines) :
            next_line = lines[i+1].strip()
            if next_line != '':
                next_word = lines[i+1].strip().split('\t')
                if len(next_word) >= 2:
                    next_word = next_word[1]
                    if i+j+1 < len(sentence):
                        next_word_ReLi = sentence[i+j+1]
                        if next_word == next_word_ReLi:
                            output_string += '\t'.join([id,word,lemma,cpostag,postag,feats,obj,opinion,pol,head,deprel,phead,pdeprel]) + '\n'
                            continue

        # I dont know the problem
        logfile.write('Mismatch from PALAVRAS word "{0}" with ReLi word "{1}" in the sentence:\n\t{2}\n\noutput:\n{3}'.format(word,sentence[i+j]['word'],sentence_string,output))
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
                    output = process_sentence(sentence)
                    if output == '':
                        logfile.write('Error processing PALAVRAS, line {0} from {1}\n'.format(line_num,filename))
                        discarted_sentences += 1
                    else:
                        processed_sentences += 1
                        output_file.write(output)
                    sentence = []

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
