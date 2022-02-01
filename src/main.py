import re
from datetime import date

import requests

from format_tweets.new_updates import format_new_updates, format_ios_modules
from format_tweets.release_changes import format_entry_changes, format_release_notes_available
from format_tweets.yearly_report import format_yearly_report
from format_tweets.zero_days import format_zero_days
from gather_info import determine_latest_versions, get_info
from save_data import read_file, save_file
from twitter import tweet

main_page = requests.get("https://support.apple.com/en-us/HT201222").text
all_releases = re.findall(r"<tr>(.*?)<\/tr>", main_page.replace("\n", ""))[1:]

for i, _ in enumerate(all_releases):
    all_releases[i] = re.findall(r"<td>(.*?)<\/td>", all_releases[i])

# var releases is storing only the last hundred releases
releases = all_releases[:100]
releases_info = get_info(releases)

# get all new releases
date_format_one = (
    f"{date.today().day:02d} {date.today().strftime('%b')} {date.today().year}"
)
# Format: 08 Jan 2022

new_releases_info = {}
for key, value in releases_info.items():
    if value["release_date"] == date_format_one:
        new_releases_info[key] = value

stored_data = read_file()


# if the latest iOS series got a new release
latest_versions = determine_latest_versions(releases)
ios_releases_info = {}

for key, value in new_releases_info.items():
    if (
        "iOS" in key
        and str(latest_versions["iOS and iPadOS"][0]) in key
        and value["release_notes"] is not None
        and int(re.findall(r"\d+", value["num_of_bugs"])[0])
        != len(value["list_of_zero_days"])
    ):
        ios_releases_info[key] = value

if ios_releases_info:
    tweet(format_ios_modules(ios_releases_info, stored_data))


# if any releases that said "soon" got releases notes
notes_releases_info = {}

for key, value in releases_info.items():
    if (
        key in stored_data["details_available_soon"]
        and value["release_notes"] is not None
    ):
        notes_releases_info[key] = value

    if value["num_of_bugs"] == "no details yet":
        notes_releases_info[key] = value

if notes_releases_info:
    tweet(format_release_notes_available(dict(notes_releases_info), stored_data))


# if there were any zero-days fixed
check_zero_days_info = new_releases_info | notes_releases_info
zero_day_releases_info = {}

for key, value in check_zero_days_info.items():
    if value["num_of_zero_days"]:
        zero_day_releases_info[key] = value

if len(zero_day_releases_info) > 0:
    tweet(format_zero_days(dict(zero_day_releases_info), stored_data))


# if there were any changes in the release notes
changes_releases_info = {}

for key, value in releases_info.items():
    if value["entries_added"] or value["entries_updated"]:
        changes_releases_info[key] = value

if len(changes_releases_info) > 0:
    tweet(format_entry_changes(changes_releases_info, stored_data))


# new updates should be tweeted last, after all of the above
if new_releases_info:
    tweet(format_new_updates(dict(new_releases_info), stored_data))


# if there was a new major release
for key, value in latest_versions.items():
    for key2, _ in new_releases_info.items():
        if key2 in (f"{key} {value[0]}", f"{key} {value[0]}.0"):
            tweet(format_yearly_report(all_releases, key, value[0], stored_data))

        elif key == "macOS":
            if key2 in (
                f"{key} {value[1]} {value[0]}",
                f"{key} {value[1]} {value[0]}.0",
            ):
                tweet(format_yearly_report(all_releases, key, value[0], stored_data))

save_file(stored_data)
