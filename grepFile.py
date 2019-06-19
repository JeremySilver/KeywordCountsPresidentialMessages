#!/usr/bin/python
import os
import itertools
import time
import re
import numpy
import json
import sys

## This script performs keyword counts on a plain-text document, for
## which the filename is given as a command-lint argument.

## get the filename
filename = sys.argv[1]

## open the file and read the contents
f = open(filename,'rt')
speechLines = f.readlines()
f.close()


## remove leading/trailing whitespace
speechLines = [l.strip() for l in speechLines]
## remove any '_', and remove any leading/trailing whitespace adjacent
## to sentence delimiters
SpeechLines = [element.strip().rstrip().replace('_','') for element in speechLines ]
SpeechLines = [element.strip().rstrip() for l in SpeechLines for element in re.split('([\.:?!])',l) ]
## remove any empty 'phrases' after the above replacemenents
SpeechLines = [l for l in SpeechLines if len(l) > 0]
Sentences = []
for l in SpeechLines:
    if l in ['.',':','?','!','"',"'"]:
        Sentences[-1] = Sentences[-1] + l
    else:
        Sentences.append(l)
##
## Remove any HTML artefacts
Sentences = [l.replace('</div></div><span class="displaytext">','') for l in Sentences]
p = re.compile('(\[<i>\w+<\/i>\])')
Sentences = [p.sub('',l) for l in Sentences]
Sentences = [l.replace('&mdash;','') for l in Sentences]
Sentences = [l.replace('"','') for l in Sentences]
Sentences = [l.replace("'",'').strip().rstrip() for l in Sentences]
## remove any empty 'phrases' after the above replacemenents
Sentences = [l for l in Sentences if len(l) > 0]
## get the total word count
count = numpy.array([len(re.findall(r"([\w\-\'\.]+)", l.lower())) for l in Sentences]).sum()
##
## Define the regular expressions
## For the first group, we just get the counts
regexsSimple = {
    'science':[r'\b(science)([\w]*)', r'\b(scientist)([\w]*)', r'\b(scientific)([\w]*)'],
    'tech':[r'([\w]*)(technolog)([\w]*)', r'\btechnical\b'],
    'environment':[r'([\w]*)(environment)([\w]*)'],
    'economy':[r'([\w]*)(economy)([\w]*)', r'([\w]*)(economic)([\w]*)'],
    'energy':['energy'],
    'naturalResources':[r'(natural resource)([\w]*)'],
    'employment':[r'([\w]*)(employ)([\w]*)'],
    'jobs':['jobs'],
    'housing':['housing'],
    'inflation':['inflation'],
    'education':['education'],
    'tax':[r'\bnontaxable\b', r'\bovertax\b', r'\bovertaxed\b', r'\bovertaxes\b', r'\bovertaxing\b', r'\btaxing\b', r'\bsurtax\b', r'\bsurtaxed\b', r'\bsurtaxes\b', r'\bsurtaxing\b', r'\bsurtaxs\b', r'\btax\b', r'\btaxable\b', r'\btaxation\b', r'\btaxations\b', r'\btaxed\b', r'\btaxes\b', r'\btaxpayer\b', r'\btaxpayers\b', r'\btaxs\b'],
    'health':[r'([\w]*)(health)([\w]*)'],
    'business':[r'([\w]*)(business)([\w]*)'],
    'crime':[r'\bcrime\b', r'\bcrimes\b',r'([\w]*)(criminal)([\w]*)'],
    'terror':[r'([\w]*)(terror)([\w]*)'],
    'gun':[r'\bgun\b',r'\bguns\b','handgun','gunfire','gunman','rifle','shotgun'],
    'drugs':['drugs','narcotics'],
    'religion':[r'\bgod\b',r"\bgod's\b", 'religion', 'prayer', 'faith'],
    'shooting':['shooting'],
    'military':['military'],
    'research':[r'(research)([\w]*)']}
## For the second group, we do not save matches to a file (as with
## retrieveStats_PBM.py and retrieveStats_SoU.py)
regexsDetailed = {
    'security'  :      ['security'],        
    'climate'   :      ['climate'],         
    'space'     :      [r'\bspace\b'],
    'defense'   :      ['defense', 'defence', 'defend'], 
    'nuclear'   :      ['nuclear'],
    'war'       :      [r'\bwar\b',r'\bwars\b', r'([\w]*)(warrior)([\w]*)'],
    'racism'    :      ['civil rights', 'racism'],
    'pollution' :      ['pollution']}

## save the total word count
counts = {'totalCount':count}
matches = {}
## ## perform the counts for the first group
for k in regexsSimple.keys():
    thisCount = 0
    matches[k] = []
    for r in regexsSimple[k]:
        p = re.compile(r)
        for l in Sentences:
            ans = p.findall(l.lower())
            thisCount += len(ans)
            if len(ans) > 0:
                matches[k].append( ''.join(ans[0]) )
    ##
    matches[k] = list(set(matches[k]))
    matches[k].sort()
    counts[k] = len(matches[k])
        
## perform the counts for the second group
for k in regexsDetailed.keys():
    thisCount = 0
    counts[k] = 0
    matches[k] = []
    for r in regexsDetailed[k]:
        p = re.compile(r)
        for l in Sentences:
            ans = p.findall(l.lower())
            thisCount += len(ans)
            counts[k] += len(ans)
            if len(ans) > 0:
                matches[k].append( ''.join(ans[0]) )
    matches[k] = list(set(matches[k]))
    matches[k].sort()
    counts[k] = len(matches[k])

## print the results to the console's standard output
print counts
