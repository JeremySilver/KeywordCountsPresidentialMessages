from urllib2 import urlopen
import os
import itertools
import time
import re
import numpy
import json
import datetime
import subprocess

## This script downloads and processes Presidential Budget Messages
## from The American Presidency Project (UCSB)'s website or from files
## (if the relevant message was not available from the UCSB website).

## open a list of the PBMs and the PIDs
f = open('annual-budget-messages.txt','rt')
lines = f.readlines()
f.close()
## lines beginning with # are removed
lines = [l.strip() for l in lines if not l.startswith('#')]
## extract the PIDs
PIDs = [elt for l in lines for elt in l.split('\t') if elt.startswith('pid')]
PIDs = [pid.split('=')[1] for pid in PIDs]

## get a list of the PIDs for the SoUs - some messages are indexed by
## PID and some messages are indexed by filename (if they don't have a
## PID). 
f = open('target_PIDs_PBM.txt')
targetPIDs = f.readlines()
f.close()
## lines beginning with # are removed
targetPIDs = [pid.strip() for pid in targetPIDs if not pid.startswith('#')]
## separate into those indexed by PID and those indexed by filename
targetPIDsByUrl = [pid for pid in targetPIDs if pid.find(',') == -1]
## those indexed by file have extra information (date, president, filename)
targetPIDsByFile = [pid for pid in targetPIDs if pid.find(',') != -1]

## holder for the results
results = {}

## loop through the individual messages - process only those indexed by PID
for PID in PIDs:
    ## exlude those indexed by file
    if PID not in targetPIDsByUrl:
        print 'PID {} was not in the list of targets - skipping...'.format(PID)
        continue
    ## check if we have downloaded this file already
    PIDfile = os.path.join('PIDfiles','{}.html'.format(PID))
    ## if so, read from file
    if os.path.exists(PIDfile):
        f = open(PIDfile)
        speechLines = f.readlines()
        f.close()
    else:
        ## otherwise, download from the UCSB website
        url='http://www.presidency.ucsb.edu/ws/index.php?pid={}'.format(PID)
        con = urlopen(url)
        speechLines = con.readlines()
        con.close()
        ## then save to file
        f = open(PIDfile,'w')
        f.writelines(speechLines)
        f.close()
    ##
    ## remove leading/trailing whitespace
    speechLines = [l.strip() for l in speechLines]
    ## find the title
    titleLine = [l for l in speechLines if l.find('title') > 0]
    if titleLine[0].find('Economic Report') > 0:
        print 'maybe an ERP??'
    ## find the name of the speaker
    name = [l for l in speechLines if l.find('title') > 0][0].replace('<title>','').split(':')[0]
    ## find the date of the speech
    date = [l for l in speechLines if l.find('title') > 0][1].split(' - ')[1].split('"')[0].replace(',','')
    ## find the start of the speech text in the HTML
    istart = [i for i,l in enumerate(speechLines) if l.find('</div></div><span class="displaytext">') >= 0]
    if len(istart) != 1:
        raise RuntimeError('istart problem')
    ## find the year
    year = int(date[-4:])
    print PID,year,name,date
    ##
    istart = istart[0]
    ## find the end of the speech text in the HTML
    iend = [i for i,l in enumerate(speechLines) if l.find('</span>') >= 0 and i >= istart]
    iend = iend[0]
    ## get the speech text
    SpeechLines = [element.strip().rstrip().replace('_','') for i in range(istart,iend+1) for element in speechLines[i].split('<p>') ]
    ## Work towards breaking everything up into sentences, removing any HTML formatting
    SpeechLines = [element.strip().rstrip() for l in SpeechLines for element in re.split('([\.:?!])',l) ]
    SpeechLines = [l for l in SpeechLines if len(l) > 0]
    Sentences = []
    ## break the speech into sentences or phrases
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
    Sentences = [l.replace("'",'').strip().rstrip() for l in Sentences]
    ## remove any empty 'phrases' after the above replacemenents
    Sentences = [l for l in Sentences if len(l) > 0]
    ## find the last sentence
    iend = [i for i,l in enumerate(Sentences) if l.find('</span>') >= 0][0]
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
    filename = 'budget-regexes_{}_{}_{}.txt'.format(year,name.replace(' ','').replace('.',''),PID)
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
    results[PID] = {'name':name,
                    'year':year,
                    'date':date,
                    'totalWordCount':count,
                    'counts':counts}

## process those messages saved as files
for targetPIDByFile in targetPIDsByFile:
    parts = targetPIDByFile.split(',')
    filename = parts[0]
    name = parts[1]
    year = parts[2]
    date = parts[3]
    print year,name,date
    ## run an external script (grepFile.py) on the file
    cmd = ['python','grepFile.py',filename]
    out,err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    ## check that there were no errors
    assert len(err) == 0, 'Could not parse {} properly...'.format(filename)
    ## read the output as a dictionary of counts (same as above)
    counts = eval(out)
    ## remove one of the entries
    count = counts['totalCount']
    del counts['totalCount']
    results[filename] = {'name':name,
                         'year':year,
                         'date':date,
                         'totalWordCount':count,
                         'counts':counts}

## process the dates
allDates = [ datetime.datetime.strptime(results[k]['date'], '%B %d %Y') for k in results.keys()]
## sort by dates
indDate = numpy.argsort(numpy.array(allDates))
    
## save the combined counts to a JSON format file
with open('results_budget.json', 'w') as outfile:
    json.dump(results, outfile)

## ## save the combined counts to a comma-delimited text file
## define the headings
countKeys = counts.keys()
## extra headings present the keyword counts as a percentage of the total keywords
countKeysWithExtraHeadings = list(itertools.chain(*[[key, key+'_pct_of_keywords',key+'_pct_of_all_words'] for key in countKeys]))
with open('results_budget.txt', 'w') as outfile:
    ## print the heading line
    outStr = '{}, {}, {}, {}, {}, {}, {}'.format('pid','year','date','name','count_of_all_words','count_of_keywords',', '.join(countKeysWithExtraHeadings))
    outfile.write(outStr + '\n')
    ## print the results, one row per message
    for k in [results.keys()[i] for i in indDate]:
        ## get the total keyword counts
        totalKeywordCount = numpy.array([results[k]['counts'][ck] for ck in countKeys]).sum()
        outStr = '{}, {}, {}, {}, {}, {}'.format(k,results[k]['year'],results[k]['date'],results[k]['name'],results[k]['totalWordCount'],totalKeywordCount)
        ## present the results as the raw counts and as a percentage (take care of the case of division by zero)
        for ck in countKeys:
            if totalKeywordCount == 0:
                pctOfKeywords = numpy.nan
            else:
                pctOfKeywords = 100.0*float(results[k]['counts'][ck])/float(totalKeywordCount)
            outStr += ', %d, %.5g, %.5g' % (results[k]['counts'][ck], pctOfKeywords, 100.0*float(results[k]['counts'][ck])/float(results[k]['totalWordCount']))
        outfile.write(outStr + '\n')
    
