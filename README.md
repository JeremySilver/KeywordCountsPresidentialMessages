# Python scripts to perform word-counts for US Presidential speeches and budgetary messages

The scripts contained here can be used to perform basic word-search
and counting for particular themes or keywords from US Presidential
messages: orally-delivered State of the Union (SoU) addresses and
Presidential Budgetary Messages (PBMs).

## Contents
1. `retrieveStats_SoU.py`: Script to perform word-counts for the SoU addresses; this will read the HTML source code from file if it has been saved, or save it to file if it has not.
2. `retrieveStats_PBM.py`: Script to perform word-counts for the PBMs; as with `retrieveStats_SoU.py`, read from file if available or download if not.
3. `grepFile.py`: Script to preform word-counts for particular speeches or messages that are not saved in a standard format. It assumes that the files contain plain-text (i.e., no HTML artifacts)
4. `target_PIDs_SoU.txt`: A list of SoU PIDs or file-names to read and process. The term "PID" refers to an indexing for messages appearing in the [The American Presidency Project](http://www.presidency.ucsb.edu) URLs and page sources, and is used here to reference the individual presidential messages. Note that more recent speeches have a different referencing system (not numerical), but speeches indexed in this way are still listed in this file.
5. `target_PIDs_PBM.txt`: A list of the PBM PIDs to read and process. Some of these are excluded (these lines begin with the comment character `#`) as they were deemed to be of a different message type (Economic Reports of the President). This file contains a list of files containing PBM texts that were not available through [The American Presidency Project](http://www.presidency.ucsb.edu), to the best of our knowledge; these files are listed below.
6. `annual-budget-messages.txt`: This file contains metadata for PBMs (e.g., the date delivered, the President, the title of the PBM)

## Data sources

Most of the source files used here are made available through the
website of the [The American Presidency
Project](http://www.presidency.ucsb.edu)
([UCSB](http://www.ucsb.edu)), with some exceptions listed below. We
are grateful to the [UCSB](http://www.ucsb.edu) and [The American
Presidency Project](http://www.presidency.ucsb.edu) for making this
data available to the public for reference and study. 
Please note that this repository does not contain the original data.

The following files are referred to in `target_PIDs_PBM.txt`, but are
not supplied with this repository. 

- `BUDGET_MESSAGE_1988.txt`: PBM delivered by Ronald Reagan on January 5 1987
- `BUDGET_MESSAGE_1990.txt`: PBM delivered by Ronald Reagan on January 9 1989
- `bus_1991_sec1.txt`: PBM delivered by George Bush on January 29 1990
- `bus_1993_sec2.txt`: PBM delivered by George Bush on January 29 1992
- `bus_1994_sec1.txt`: PBM delivered by William J. Clinton on 1993,April 8  1993
- `bus_1995.txt`: PBM delivered by William J. Clinton on February 7 1994
- `budget-fy2020.txt`: PBM delivered by Donald J. Trump on March 11 2019
- `budget-fy2019_TRUMP_PBMonly.txt`: PBM delivered by Donald J. Trump on February 15 2018

The older texts were extracted from the US Federal Budget documents
archived on [FRASER](https://fraser.stlouisfed.org/), a digital
library of U.S. economic, financial, and banking history. The more
recent documents were extracted from US Federal Budget documents
downloaded from the website of the [White
House](https://www.whitehouse.gov). 

## Authors

This is code from Jeremy Silver (School of Earth Sciences, University
of Melbourne, Australia), with input from Mark Quigley (same
affiliation).

## Disclaimer

The scripts were mainly written in 2018, with some updates in early 2019. The URLs, formats and content will likely change over time. These scripts will most likely not be updated over time to adapt to these changes, and users are encouraged to check the work-flow carefully to ensure that the results match with expected. These scripts will not be updated as they were part of a research project, rather than an ongoing service. 
