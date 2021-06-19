import re

import emoji
import tweepy

from auth_secrets import keys


api_key             = keys["ApplSec"]["api_key"]
api_key_secret      = keys["ApplSec"]["api_key_secret"]
access_token        = keys["ApplSec"]["access_token"]
access_token_secret = keys["ApplSec"]["access_token_secret"]

auth = tweepy.OAuthHandler(api_key, api_key_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)


def tweetOrCreateAThread(whatFunction, title, functionResults, results, secondResults, thirdResults, uniqueZeroDays):
    mainLink = "https://support.apple.com/en-us/HT201222"

    if len(functionResults) <= 4:
        # if there are less than four releases put them all in one tweet
        for result in functionResults:
            results += result

        # attach a link to new updates released tweet
        results += "" if whatFunction != "tweetNewUpdates" else f"{mainLink}\n"


    elif len(functionResults) > 4:
        # if there are more than four releases create a thread
        regex = "-" if whatFunction != "changedResults" else ":[^:]+:"

        for result in functionResults:
            if int(len(re.findall(regex, results)) + 1) <= 4:
                results += result
            else:
                secondResults += result

        # attach a link to new updates released tweet
        secondResults += "" if whatFunction != "tweetNewUpdates" else f"{mainLink}\n"


    if whatFunction == "tweetZeroDays":
        lengthNew = len(uniqueZeroDays["new"])
        lengthOld = len(uniqueZeroDays["old"])

        if lengthNew > 0:
            uniqueZeroDays["new"] = ", ".join(uniqueZeroDays["new"])
        if lengthOld > 0:
            uniqueZeroDays["old"] = ", ".join(uniqueZeroDays["old"])

        if lengthNew == 1 and lengthOld == 0:
            title += f'Today, Apple pushed updates for one new zero-day ({uniqueZeroDays["new"]}) that was already used to attack users'
        elif lengthNew == 0 and lengthOld == 1:
            title += f'Today, Apple pushed additional updates for one zero-day ({uniqueZeroDays["old"]}) that was already used to attack users'
        elif lengthNew == 1 and lengthOld == 1:
            title += f'Today, Apple pushed updates for one new zero-day ({uniqueZeroDays["new"]}) that was already used to attack users and additional updates for {uniqueZeroDays["old"]} zero-day'
        elif lengthNew > 1 and lengthOld == 0:
            title += f'Today, Apple pushed updates for {lengthNew} new zero-days that had already been used to attack users - {uniqueZeroDays["new"]}'
        elif lengthNew == 0 and lengthOld > 1:
            title += f'Today, Apple pushed additional updates for {lengthOld} zero-days that had already been used to attack users - {uniqueZeroDays["old"]}'
        elif lengthNew > 1 and lengthOld > 1:
            title += f'Today, Apple pushed updates for {lengthNew} new zero-days that had already been used to attack users and additional updates for {lengthNew} zero-days.'

        if len(re.findall("in", results)) <= 2:
            results = f"{title} :rotating_light:\n\nRELEASED UPDATES:\n{results}"
        else:
            thirdResults = secondResults
            secondResults = results
            results = f"{title} :rotating_light:\n\nRELEASED UPDATES:"
    else:
        results = str(title + results) if title != None else results


    originalTweet = api.update_status(emoji.emojize(results, use_aliases=True))

    if secondResults:
        secondTweet = api.update_status(emoji.emojize(secondResults, use_aliases=True), in_reply_to_status_id=originalTweet.id, auto_populate_reply_metadata=True)

    if thirdResults:
        api.update_status(emoji.emojize(thirdResults, use_aliases=True), in_reply_to_status_id=secondTweet.id, auto_populate_reply_metadata=True)