#!/usr/bin/env python
# -*- coding: utf-8 -*-

#### Translate from ReLi column format to Html format
#### Author: Pedro Paulo Balage Filho
#### Version: 1.0
#### Date: 08/11/12

import re
import codecs
import os

# Function to convert the lines present in the txt file into an html representation
def convert2html(text):
	html = '''
	<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
	<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
	    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	</head>
	'''
	livro = 'NaN'
	for line in text:

		# Match the line specifying the book
		m = re.match(r"#Livro_(.+)$",line)
		if m:
			if m.group(1) != livro:
				html = html + '<h3>Livro:' + m.group(1) + '</h3>'
			else:
				livro = m.group(1)
			livro = m.group(1)

		# Match the review
		m = re.match(r"#Resenha_([0-9]+)",line)
		if m:
			html = html + '<br/><b>Resenha:' + m.group(1) + '</b><br/>'

		# Match the score
		m = re.match(r"#Nota_([0-9.]+)",line)
		if m:
			html = html + '<b>Nota:' + m.group(1) + '</b><br/>'

		# Match the score
		m = re.match(r"#Título_(.+)$",line)
		if m:
			html = html + '<b>Título:' + m.group(1) + '</b><br/>'

		# An empty line is a break line
		if len(line.strip()) == 0:
			html = html + '<br/>'

		# Find the elements in each line (word, pos, object, opinion, polarity, help)
		m = re.match(r"([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t\[]+)[\n\[]",line)
		if m:
			word = unicode(m.group(1))
			pos = m.group(2)
			obj = m.group(3)
			opinion = m.group(4)
			pol = m.group(5)
			whelp = m.group(6)

			if obj != 'O':
				html = html + '<b><a title="'+obj+'">' + word + '</a></b> '
			elif opinion != 'O':
				if opinion.endswith('-'):
					html = html + '<font color="red"><a title="' + opinion + '">' + word + '</a></font> '
				else:
					html = html + '<font color="blue"><a title="' + opinion + '">' + word + '</a></font> '
			else:
				html = html + word + ' '
	html = html + '</html>'
	return html


## Main Program ##
corpus_files = os.listdir('../ReLi/corpus/')
if not os.path.exists('ReLiWeb'):
	os.mkdir('ReLiWeb')

for filename in corpus_files:
	if filename.startswith('ReLi') and filename.endswith('.txt'):
		handle = codecs.open('../ReLi/corpus/'+filename,'r','utf-8')
		text = handle.readlines()
		handle.close()

		html = convert2html(text)

		handle = codecs.open('ReLiWeb/'+filename[:-3]+'html','w','utf-8')
		handle.write(html)
		print 'Processed: ', filename
