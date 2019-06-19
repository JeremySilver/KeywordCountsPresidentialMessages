from urllib2 import urlopen
import os
import itertools
import time
import re
import numpy
import json
import datetime

## This script downloads and processes orally-delivered presidential
## State of the Union addresses from The American Presidency Project
## (UCSB)'s website.

## years of the speeches considered
years = range(1947,2019+1)

## Download the HTML from the front-page of the The American
## Presidency Project (UCSB)'s State of the Union page
url = 'http://www.presidency.ucsb.edu/sou.php'
print url
con = urlopen(url)
lines = con.readlines()
con.close()

## remove starting/trailing whitespace
lines = [l.strip() for l in lines]

## get a list of the PIDs for the SoUs
f = open('target_PIDs_SoU.txt')
targetPIDs = f.readlines()
f.close()
targetPIDs = [pid.strip() for pid in targetPIDs]

## holder for the results
results = {}

## Some of the messages were written (not oral) - note which
## ones. These will be excluded from the analysis.
writtenMessagePids = [30867, 32735, 33062, 44541, 4328, 3407, 12074, 10593, 14379, 12467]
writtenMessagePids = [str(pid) for pid in writtenMessagePids]

## one PID needed to be added manually
PIDsToAdd = ['3996']
YEARsToAdd = [1973]

## Find the years for each of the PIDs we want to process
PIDs = []
YEARs = []
## work through the list year by year
for year in years:
    ## find the relevant lines in the USBC APP SoU page
    ## pidLines = [l for l in lines if l.find('pid') > 0 and l.find(">{}<".format(year)) > 0]
    pidLines = [l for l in lines if l.find(">{}<".format(year)) > 0]
    if len(pidLines) > 0:
        pidLines = [elt for l in pidLines for elt in l.split('a><a')]
        for pidLine in pidLines:
            ## extract the PID
            if pidLine.find('pid') > 0:
                pid = pidLine.split('pid')[1].split('=')[1].split('"')[0]
            else:
                pid = pidLine.split('href')[1].split('"')[1].split('/')[-1]
            ## make sure it is not a duplicate
            if pid in PIDs:
                ## we have already added this one - do not duplicate...
                continue
            ## skip the messages that were written only
            if pid in writtenMessagePids:
                print "PID {} was not included, as it was a written message - skipping...".format(pid)
                continue
            ## make sure it is in the list that we were aiming to get
            if pid not in targetPIDs:
                print "PID {} was not in the list of target PIDs - skipping...".format(pid)
                continue
            ## record the PID and the associated year
            PIDs.append(pid)
            YEARs.append(year)
            ## check that the formatting is as expected
            if pidLine.count('href') != 1:
                raise RuntimeError('multiple hrefs')

## One PID needed to be appended manually
PIDs  = PIDs  + PIDsToAdd
YEARs = YEARs + YEARsToAdd

## a directory to put the save PID files
if not os.path.exists('PIDfiles'):
    os.mkdir('PIDfiles')

## loop through the speaches, tracking the PID and year
for year,pid in zip(YEARs,PIDs):
    PIDfile = os.path.join('PIDfiles','{}.html'.format(pid))
    ## do we have it on file already?
    if os.path.exists(PIDfile):
        ## if it exists on file, read the local copy
        f = open(PIDfile)
        speechLines = f.readlines()
        f.close()
    else:
        ## if no local copy is found, read from the internet...
        ## check if the PID is only digits
        if len(re.findall(r'[a-zA-Z]',pid)) == 0:
            ## one URL format for digits
            url = 'http://www.presidency.ucsb.edu/ws/index.php?pid={}'.format(pid)
        else:
            ## one URL format for other data
            url = 'http://www.presidency.ucsb.edu/documents/{}'.format(pid)
        ##
        con = urlopen(url)
        speechLines = con.readlines()
        con.close()
        ## ... and save to file
        f = open(PIDfile,'w')
        f.writelines(speechLines)
        f.close()
    ##
    ## remove leading/trailing whitespace
    speechLines = [l.strip() for l in speechLines]
    ## find the title
    titleLine = [l for l in speechLines if l.find('title') > 0]
    ## find the name of the speaker
    dietTitle = [l for l in speechLines if l.find('diet-title') > 0]
    ## there are two possible speech formats
    if len(dietTitle) > 0:
        name = dietTitle[0].split('>')[2].split('<')[0]
        ## find the date of the speech
        date = [l for l in speechLines if l.find('dateTime') > 0][0].split('>')[1].split('<')[0]
        ## find the start of the speech text in the HTML
        istart = [i+1 for i,l in enumerate(speechLines) if l.find('field-docs-content') >= 0]
        if len(istart) != 1:
            raise RuntimeError('istart problem')
        istart = istart[0]
        ## find the end of the speech text in the HTML
        iend = [i for i,l in enumerate(speechLines) if l.find('</div>') >= 0 and i >= istart]
        if len(iend) == 0:
            raise RuntimeError('iend problem')
        iend = iend[0]
    else:
        name = [l for l in speechLines if l.find('title') > 0][0].replace('<title>','').split(':')[0]
        ## find the date of the speech
        date = [l for l in speechLines if l.find('title') > 0][1].split(' - ')[1].split('"')[0].replace(',','')
        ## find the start of the speech text in the HTML
        istart = [i for i,l in enumerate(speechLines) if l.find('</div></div><span class="displaytext">') >= 0]
        if len(istart) != 1:
            raise RuntimeError('istart problem')
        istart = istart[0]
        ## find the end of the speech text in the HTML
        iend = [i for i,l in enumerate(speechLines) if l.find('</span>') >= 0 and i >= istart]
        if len(iend) == 0:
            raise RuntimeError('iend problem')
        iend = iend[0]
    ##
    print year,name,date
    ##    
    ## get the speech text
    SpeechLines = [element.strip().rstrip() for i in range(istart,iend+1) for element in speechLines[i].split('<p>') ]
    ## Work towards breaking everything up into sentences, removing any HTML formatting
    SpeechLines = [element.strip().rstrip() for l in SpeechLines for element in re.split('([\.:?!])',l) ]
    SpeechLines = [l for l in SpeechLines if len(l) > 0]
    ## break the speech into sentences or phrases
    Sentences = []
    for l in SpeechLines:
        if l in ['.',':','?','!']:
            Sentences[-1] = Sentences[-1] + l
        else:
            Sentences.append(l)
    ## Remove any HTML artefacts
    Sentences = [l.replace('</div></div><span class="displaytext">','') for l in Sentences]
    p = re.compile('(\[<i>\w+<\/i>\])')
    Sentences = [p.sub('',l) for l in Sentences]
    Sentences = [l.replace('&mdash;','') for l in Sentences]
    Sentences = [l.replace('"','') for l in Sentences]
    Sentences = [l.replace('</p>','') for l in Sentences]
    Sentences = [l.replace("'",'').strip().rstrip() for l in Sentences]
    ## remove any empty 'phrases' after the above replacemenents
    Sentences = [l for l in Sentences if len(l) > 0]
    ## find the last sentence
    iend = [i for i,l in enumerate(Sentences) if l.find('</span>') >= 0 or l.find('</div>') >= 0][0]
    ## restrict the sentences to those deemed to be within the speech body
    Sentences = Sentences[0:iend]
    ## remove any remaining HTML tags
    p = re.compile('<.*?>')
    Sentences = [p.sub('',l) for l in Sentences]
    ## remove any empty 'phrases' after the above replacemenents
    Sentences = [l for l in Sentences if len(l) > 0]
    ## get the total word count
    count = numpy.array([len(re.findall(r"([\w\-\'\.]+)", l.lower())) for l in Sentences]).sum()
    ## Define the regular expressions
    ## For the first group, we just get the counts
    regexssimple = {
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
    ## For the second group, we get matches printed to a file
    regexsDetailed = {
        'security'  :      ['security'],        
        'climate'   :      ['climate'],         
        'space'     :      [r'\bspace\b'],
        'defense'   :      ['defense', 'defence', 'defend'], 
        'nuclear'   :      ['nuclear'],
        'war'       :      [r'\bwar\b',r'\bwars\b', r'([\w]*)(warrior)([\w]*)'],
        'racism'    :      ['civil rights', 'racism'],
        'pollution' :      ['pollution']}
    ## perform the counts for the first group
    counts = {}
    for k in regexsSimple.keys():
        thisCount = 0
        for r in regexsSimple[k]:
            p = re.compile(r)
            for l in Sentences:
                ans = p.findall(l.lower())
                thisCount += len(ans)
        ##
        counts[k] = thisCount
    ## matches from the second group get saved to this file
    filename = 'speech-regexes_{}_{}_{}.txt'.format(year,name.replace(' ','').replace('.',''),pid)
    ## perform the counts for the second group and write the matches to file
    f = open(filename,'wt')
    for k in regexsDetailed.keys():
        thisCount = 0
        f.write('topic = '+k+'\n')
        for r in regexsDetailed[k]:
            f.write('\tregex = ' + r+'\n')
            p = re.compile(r)
            for l in Sentences:
                ans = p.findall(l.lower())
                thisCount += len(ans)
                if len(ans) > 0:
                    f.write('\t\t{} : {}\n'.format(len(ans),l))
        ##
        counts[k] = thisCount
    ##
    f.write('\n\n\n\n')
    ##
    for k in regexsSimple.keys():
        f.write('topic = {} : matches = {}\n'.format(k,counts[k]))
    ##
    for k in regexsDetailed.keys():
        f.write('topic = {} : matches = {}\n'.format(k,counts[k]))
    ##
    f.close()
    ##
    results[pid] = {'name':name,
                    'year':year,
                    'date':date.replace(',',''),
                    'totalWordCount':count,
                    'counts':counts}

## process the dates
allDates = [ datetime.datetime.strptime(results[k]['date'], '%B %d %Y') for k in results.keys()]
## sort by dates
indDate = numpy.argsort(numpy.array(allDates))

## save the combined counts to a JSON format file
with open('results_SoU.json', 'w') as outfile:
    json.dump(results, outfile)

## ## save the combined counts to a comma-delimited text file
## define the headings
countKeys = counts.keys()
## extra headings present the keyword counts as a percentage of the total keywords
countKeysWithExtraHeadings = list(itertools.chain(*[[key, key+'_pct_of_keywords',key+'_pct_of_all_words'] for key in countKeys]))
## write the results to file
with open('results_SoU.txt', 'w') as outfile:
    ## print the heading line
    outStr = '{},{},{},{},{},{},{}'.format('pid','year','date','name','count_of_all_words','count_of_keywords',','.join(countKeysWithExtraHeadings))
    outfile.write(outStr + '\n')
    ## print the results, one row per message
    for k in [results.keys()[i] for i in indDate]:
        ## get the total keyword counts
        totalKeywordCount = numpy.array([results[k]['counts'][ck] for ck in countKeys]).sum()
        outStr = '{},{},{},{},{},{}'.format(k,results[k]['year'],results[k]['date'],results[k]['name'],results[k]['totalWordCount'],totalKeywordCount)
        ## present the results as the raw counts and as a percentage (take care of the case of division by zero)
        for ck in countKeys:
            if totalKeywordCount == 0:
                pctOfKeywords = numpy.nan
            else:
                pctOfKeywords = 100.0*float(results[k]['counts'][ck])/float(totalKeywordCount)
            outStr += ',%d,%.5g,%.5g' % (results[k]['counts'][ck], pctOfKeywords, 100.0*float(results[k]['counts'][ck])/float(results[k]['totalWordCount']))
        outfile.write(outStr + '\n')
    
