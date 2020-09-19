# Introduction
A tweet scraper for *#fratl* times for the *#couchpeloton* during the Tour de France watching *#sbstdf.* These hashtags mean:
- **#FRATL**: First Rider Across The Line; the time that the Stage winner wins. Experts conduct multiple pages of complex calculations, taking into account the stage length, gradients, and wind direction. Mostly, we guess. 
* **#couchpeloton**: The Twitterati of Australian cycling fans who come together virtually to share in a love of *#toursnacks*, *#tourdogs*, *#tourcats*, *#vache*, and #chateaus. We also like butter and cheese.
- **#sbstdf**: SBS is the Tour de France broadcaster for Australia and maintains a menagerie of characters which it wheels out each year for the *#couchpeloton*'s delight.

# Usage

## About
This scripts finds tweets from the last 24 hours using the *#fratl* hashtag and parses them to find the time prediction. It creates a local `csv` file and can plot the times and save the `csv` to a Google Sheets for sharing the data publicly. 

The script is a python script and is executed using the command line. It was developed on Python 3.8 and uses a number of python packages, all of which need to be installed on the host system.

Execute as:
'''
python fratl.py [arguments]
'''

For my own memory, on `Neovim` in development, I use:
'''
:terminal ipython % -i -- -s -p -g "FRATL_Stage_20(TT)"
'''

## Arguments
`-h` or `--help`
Provides brief help for each argument.

`-t` or `--test` 
Runs a suite of tests to check the parsing accuracy. Tweet text is provided with a "correct" time (as read by a human) and the parser output is compared with this correct time. Not all tests currently pass, illustrating the limits of the regex used.

Currently hard coded - better to extract to a `csv` or other file for future tests.

`-s` or `--scrape`
Runs the scraping of tweets and the *#FRATL* parsing algorithm and writes a `csv` file in a `./data/` subfolder of where the script is located. Create this subfolder before running the script for the first time. 

*The user must provide Twitter credentials in a `json` file*. Refer to the [Tweepy documentation](https://www.tweepy.org/) for instructions.

`-p` or `--plot`
Creates a horizontal bar plot of the sorted scrapped *#FRATL* time estimates in AEST.

`-r` or `--read`
For re-plotting or other purposes, reads in a `csv` file rather than scraping tweets to get *#FRATL* data with which to work. Defaults to a hard-coded `csv` file. For example, to plot the *#FRATL* times from the file, use as:
'''
python fratl.py -r "Filename.csv" -p
'''

`-g` or `--gsheet`
Exports the scrapped or read *#FRATL*s to a newly created Google Sheet and sets the sharing of that sheet to public. The new sheet's URL is output to the command line.

*Credentials for writing to the users Google Drive must be provided* See the [authentication instructions](https://gspread.readthedocs.io/en/latest/oauth2.html) for the `gspread` python package.

## Assumptions
All times are converted to Australian Eastern Standard time (AEST). See the code for the range of tags that users have used to indicate tha they are located in central (ACST) or western (AWST) timezones. Where no tags are provided it is assumed that the time is given as AEST. Differences in daylight savings between the Australian timezones are ignored.

# To do
- [] Improve the documentation and credentials instructions!
- [] Include Time Trial stage finsh time predictions (`%M:%S`).
- [] Include *#BridieBingo* (add parser for `XX.Xkm`). 
- [] Option to write to existing Google Sheet by adding sheet.
- [] Massive expansion would be to track users' *#FRATL* predictions throughout the whole race and report accuracies and report cumulative accuracies

