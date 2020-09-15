#!--utf-8
"""
Scrapes twitter and reports FRATL predictions fro tweets.
"""

import argparse
import json
import os
from datetime import date, datetime, timedelta, timezone
import time
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import tweepy
import gspread


def load_twitter_credentials():
    """ Loads twitter keys from pre-formed json file (store_twitter_api) """
    consumer_key = ""
    consumer_secret = ""
    access_key = ""
    access_secret = ""
    with open("twitter_credentials.json") as json_file:
        data = json.load(json_file)
        consumer_key = data["consumer_key"]
        consumer_secret = data["consumer_secret"]
        access_key = data["access_key"]
        access_secret = data["access_secret"]

    return (consumer_key, consumer_secret, access_key, access_secret)


def scrape_for_fratl(api, search_words, date_since, numTweets):
    """ Scrapes tweets for FRATL """
    # Define a pandas dataframe to store the date:
    db_tweets = pd.DataFrame(
        columns=["username", "location", "created at (UTC)", "FRATL", "text"]
    )

    # Time execution
    start_run = time.time()
    noTweets = 0
    # Collect tweets using the Cursor object
    for tweet in tweepy.Cursor(
        api.search, q=search_words, lang="en", since=date_since, tweet_mode="extended"
    ).items(numTweets):
        username = tweet.user.screen_name
        location = tweet.user.location
        created_at = tweet.created_at
        fratl_str = "DNS"
        is_retweet = False
        try:
            text = tweet.retweeted_status.full_text
            is_retweet = True
        except AttributeError:  # Not a Retweet
            text = tweet.full_text
            try:
                fratl = parse_for_fratl(text)
            except:
                print("Parse error: {}".format(text))
            if fratl:
                fratl_str = fratl.strftime("%H:%M")

        if not is_retweet and fratl_str != "DNS":
            # Add the variables to the empty list - ith_tweet:
            ith_tweet = [username, location, created_at, fratl_str, text]
            # Append to dataframe - db_tweets
            # Note this is pretty bad for large dataframes
            # https://stackoverflow.com/questions/10715965/add-one-row-to-pandas-dataframe
            db_tweets.loc[len(db_tweets)] = ith_tweet

        # increase counter - noTweets
        noTweets += 1

    # Run ended:
    end_run = time.time()
    duration_run = round((end_run - start_run) / 60, 2)

    print("no. of tweets scraped is {}".format(noTweets))
    print("time taken is {} mins".format(duration_run))

    # Once all runs have completed, save them to a single csv file:

    # Obtain timestamp in a readable format
    to_csv_timestamp = datetime.today().strftime("%Y%m%d_%H%M%S")
    # Define working path and filename
    path = os.getcwd()
    filename = path + r"\data\\" + to_csv_timestamp + "_fratl_tweets.csv"
    # Store dataframe in csv with creation date timestamp
    db_tweets = db_tweets.sort_values("FRATL")
    db_tweets.to_csv(filename, index=False)

    return db_tweets


def parse_for_fratl(text):
    """Find the FRATL time from the tweet text
    Use regex to extract any times and timezone. https://regexr.com/5b5jh
    Convert to a datetime object and convert to AEST then return.
    """

    time_regexpr = r"((([0]?[1-9]|1[0-2])(:|\.)?[0-5][0-9]((:|\.)[0-5][0-9])?( )?(AM|am|aM|Am|PM|pm|pM|Pm))|((1[0-9]|2[0-3]|[0]?[0-9])(:|\.)?[0-5][0-9]((:|\.)[0-5][0-9])?))"
    zone_regexpr = r"(aest\b|awst\b|acst\b|wa\b|\B#wa\b)"

    time_str = re.search(time_regexpr, text)
    time = None
    if time_str:
        time_str = time_str.group().lower().replace(" ", "").replace(".", ":")
        no_digits = sum(s.isdigit() for s in time_str)

        if time_str.find(":") == -1:  # no separator
            if no_digits == 3:
                time_str = "0" + time_str
            time_str = time_str[:2] + ":" + time_str[2:]
        if time_str[-2:] == "am" or time_str[-2:] == "pm":  # 12-hour clock
            time = datetime.strptime(time_str, "%I:%M%p")
        else:  # 24 hour clock
            if time_str[0:2] == "12":  # no am/pm but assume am
                time_str = time_str.replace("12", "00", 1)
            elif time_str[0:2] == "11":  # assume pm
                time_str = time_str.replace("11", "23", 1)
            if not time_str[-2:] == "km":  # ensure not a distance
                time = datetime.strptime(time_str, "%H:%M")

    zone = re.search(zone_regexpr, text, re.IGNORECASE)
    if zone and time:
        zone = zone.group().lower()
        if zone in ("awst", "wa", "#wa"):
            time += timedelta(hours=2)
        elif zone == "acst":
            time += timedelta(hours=0.5)

    return time


def test_times():
    """
    This function just supplies some text and tests the regex
    """

    str_list = [
        ("#fratl of 135am AEST and #BridieBingo at 29km thanks #couchpeloton", "01:35"),
        ("1259 #FRATL for me please #couchpeloton", "00:59"),
        ("#fratl 12:24 #BridieBingo 24k #couchpeloton #sbstdf", "00:24"),
        ("1.00 for #fratl tonight thanks scoots and team", "01:00"),
        (
            "Hi #couchpeloton #sbstdf #SBSCycling tonight's live feed starts at 2100 AEST on SBS Tour Tracker app, entries now open for #FRATL.",
            "21:00",
        ),
        (
            "@sophoife @evilscootus 11:39 AWST please #FRATL #sbstdf #CouchPeloton",
            "01:39",
        ),
        (
            "100km to go. And on that note, I'm going to retire to bed. Put me down for a 1:38 #FRATL please.",
            "01:38",
        ),
        (
            "@evilscootus @sophoife Weâ€™ll take our second #FRATL win of #TdF2020 with a 2.22 thanks! #SBSCycling #sbstdf #couchpeloton",
            "02:22",
        ),
        ("#FRATL of 1222 pls #couchpeloton", "00:22"),
        ("@sophoife my #fratl is 11.33pm #WA #couchpeloton #sbstdf", "01:33"),
        (
            "#couchpeloton #FRATL of 0145 AEST pls @sophoife @evilscootus. https://t.co/Sr8M0zrIR5",
            "01:45",
        ),
        ("#FRATL 12:22 please @evilscootus @sophoife #couchpeloton", "00:22"),
        (
            "@sophoife my #fratl  for stage 2 is 02:28EST Tks #SBSCycling #couchpeloton  Cheers",
            "02:28",
        ),
        ("ðŸš¨  1.48 AEST   #FRATL  #couchpeloton", "01:48"),
        ("1.44am #FRATL please @sophoife #couchpeloton", "01:44"),
        (
            "*Throws dart at dartboard* Please lock in 2.03am for my #fratl guess tonight. @sophoife #couchpeloton #sbstdf.",
            "02:03",
        ),
        ("#couchpeloton #fratl 2:04 AEST for me please @sophoife please :-)", "02:04"),
        (
            "For my first wild #FRATL in the dark for 2020-covid-season-2, Iâ€™ll go with 1.57am AEST, please.  Thank you @sophoife #CouchPeloton #SBSTdF #CyclingCentral",
            "01:57",
        ),
        (
            "Hi all could I please have 1.37am awst for my #fratl  #couchpeloton",
            "03:37",
        ),
        (
            "OK #couchpeloton I'm calling #FRATL for 1:58 am acst thanks ðŸš²ðŸš²ðŸš²",
            "02:28",
        ),
    ]

    for (text, t_str) in str_list:
        time = parse_for_fratl(text)
        s = time.strftime("%H:%M")
        if s == t_str:
            print("Time = {} AEST. Pass".format(s))
        else:
            print("Time = {} AEST. Fail: {} | {}".format(s, t_str, text))


def auth():
    """
    Authenticate twitter account and return api.
    """

    (
        consumer_key,
        consumer_secret,
        access_key,
        access_secret,
    ) = load_twitter_credentials()

    # Authenticate to Twitter
    # Pass your twitter credentials to tweepy via its OAuthHandler
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)

    # Create API object
    api = tweepy.API(auth)
    auth_ok = False

    try:
        api.verify_credentials()
        auth_ok = True
        print("Authentication OK")
    except:
        print("Error during authentication")

    return auth_ok, api


def plot_fratl(df):
    """ Plot the pandas dataframe """
    try:
        df.FRATL = pd.to_datetime(df.FRATL, format="%H:%M")
        yr = date.today().year
        mn = date.today().month
        dy = date.today().day + 1  # assumes all stage finishes after midnight
        df.FRATL = df.FRATL.apply(lambda dt: dt.replace(year=yr, day=dy, month=mn))
        df = df.sort_values(by="FRATL", ascending=False)
        df = df.reset_index(drop=True)  # re-index for plotting sorted
        df.plot(kind="barh", y="FRATL")
        fig = plt.gcf()
        ax = plt.gca()
        axes_buff = timedelta(hours=2)  # Time each side
        mean_fratl = df.FRATL.mean()
        ax.set_xlim(mean_fratl - axes_buff, mean_fratl + axes_buff)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        fig.autofmt_xdate()
        plt.tick_params(left=False, labelleft=False)
        plt.title(r"Unofficial #FRATL distribution")
        ax.annotate(
            "@PuffingColly",
            xy=(0.78, 0.08),
            xycoords="figure fraction",
            horizontalalignment="left",
            verticalalignment="top",
            fontsize=8,
        )
        ax.get_legend().remove()
        plt.show()

    except IndexError:
        print("Plot failed: too few data")

    return


def read_dataframe(file):
    """ Reads a pandas df given a filename """

    df = pd.read_csv(file)
    return df


def save_gsheet(df, filename):
    """
    Saves a dataframe to a new spreadsheet using account with credentials
    on the local system. No try-except loop so that any errors are reported
    for easier debugging. Not totally user friendly!
    """

    url = None
    gc = gspread.oauth()
    # Manually add the Stage number afterwards for now
    ss = gc.create(filename)
    ws = ss.get_worksheet(0)
    # Needed for writing NaNs
    df.fillna("", inplace=True)
    # Columns of type TimeStamp cannot be JSON serialised to GSheets
    # Hardcoding column name which has time - not ideal
    col_name = "created at (UTC)"
    df[col_name] = df[col_name].astype(str)
    # Finally write the df
    ws.update([df.columns.values.tolist()] + df.values.tolist())
    ws.set_basic_filter(name=(r"A:E"))
    url = "https://docs.google.com/spreadsheets/d/{}".format(ss.id)
    print(url)

    return url


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", help="Runs the tests", action="store_true")
    parser.add_argument("-s", "--scrape", help="Scrape tweets", action="store_true")
    parser.add_argument(
        "-p", "--plot", help="Plot fratl distribution", action="store_true"
    )
    parser.add_argument(
        "-r",
        "--read",
        help="Read file",
        nargs="?",
        type=argparse.FileType("r"),
        # setting default overrides is None when option not set
        # const is default when nothing is passed
        const=r".\data\20200906_232619_fratl_tweets.csv",
    )
    parser.add_argument(
        "-g",
        "--gsheet",
        help="Create GSheet file",
        nargs="?",
        type=str,
        const=r"FRATL_Stage_",
    )
    args = parser.parse_args()

    ####### Start of main code #######

    df = None

    if args.test:
        print("Running test...")
        test_times()

    if args.scrape:
        print("Authorising...")
        auth_ok, api = auth()
        if auth_ok:
            print("Scraping...")
            df = scrape_for_fratl(
                api,
                "#fratl",
                # Using UTC means if we pass midnight in Aus, it will still be
                # right date for France
                datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                500,
            )
        else:
            print("Authorization failed")

    if args.read is not None:
        print("Reading file: {}".format(args.read.name))
        df = read_dataframe(args.read.name)

    if args.plot and df is not None:
        print("Plotting dataframe...")
        plot_fratl(df)

    if args.gsheet is not None and df is not None:
        print("Creating gsheet...")
        url = save_gsheet(df, args.gsheet)
