import datetime
import re

import requests

from format_tweets.new_updates import format_ios_modules, format_new_updates
from format_tweets.release_changes import format_entry_changes, format_release_notes_available
from format_tweets.yearly_report import format_yearly_report
from format_tweets.zero_days import format_zero_days
from gather_info import get_info, determine_latest_versions
from save_data import read_file, save_file
from twitter import tweet


MAIN_PAGE = requests.get("https://support.apple.com/en-us/HT201222").text.replace("\n", "").replace("&nbsp;", " ")
all_releases = re.findall(r"(?<=<tr>).*?(?=<\/tr>)", MAIN_PAGE)[1:]

for i, _ in enumerate(all_releases):
    all_releases[i] = re.findall(r"(?<=<td>).*?(?=<\/td>)", all_releases[i])

# for most functions last 20 releases is enough
releases = all_releases[:20]
releases_info = get_info(releases)

# get new releases
stored_data, midnight = read_file()

if midnight:
    # on midnight do checks with the previous date to not miss any
    # changes made between 11pm and 12pm
    check_date = datetime.date.today() - datetime.timedelta(1)
else:
    check_date = datetime.date.today()

date_format_one = f"{check_date.day:02d} {check_date.strftime('%b')} {check_date.year}"
# Format: 08 Jan 2022

new_releases_info = []
for release in releases_info:
    if release.get_release_date() == date_format_one:
        new_releases_info.append(release)


# if the latest iOS series got a new release
latest_versions = determine_latest_versions(releases)
ios_releases_info = []

for release in new_releases_info:
    if (
        "iOS" in release.get_name()
        and str(latest_versions["iOS and iPadOS"][0]) in release.get_name()
        and release.get_release_notes_link() is not None
        and release.get_num_of_bugs() != len(release.get_zero_days())
    ):
        ios_releases_info.append(release)

if ios_releases_info:
    tweet(format_ios_modules(ios_releases_info, stored_data))


# if any releases that said "soon" got releases notes
# or if any new releases say "no details yet"
notes_releases_info = []

for release in releases_info:
    if (
        release.get_name() in stored_data["details_available_soon"]
        and release.get_release_notes_link() is not None
    ):
        notes_releases_info.append(release)

    if release.get_format_num_of_bugs() == "no details yet":
        notes_releases_info.append(release)

if notes_releases_info:
    tweet(format_release_notes_available(list(notes_releases_info), stored_data))


# if there were any zero-days fixed
check_zero_days_info = new_releases_info + notes_releases_info
zero_day_releases_info = []

for release in check_zero_days_info:
    if release.get_num_of_zero_days() > 0:
        zero_day_releases_info.append(release)

if len(zero_day_releases_info):
    tweet(format_zero_days(list(zero_day_releases_info), stored_data))


# in midnight check for release note changes made on the previous day
# running only once per day, as it is checking last 300 release notes
if midnight:
    check_changes_info = releases_info + get_info(all_releases[20:])

    changes_releases_info = []
    for release in check_changes_info:
        if release.get_num_entries_added() > 0 or release.get_num_entries_updated() > 0:
            changes_releases_info.append(release)

    if len(changes_releases_info):
        tweet(format_entry_changes(changes_releases_info))


# new updates should be tweeted last, after all of the above
if new_releases_info:
    tweet(format_new_updates(list(new_releases_info), stored_data))


# if there was a new major release
for key, value in latest_versions.items():
    for release in new_releases_info:
        if release.get_name() in (f"{key} {value[0]}", f"{key} {value[0]}.0"):
            tweet(format_yearly_report(all_releases, key, value[0], stored_data))

        elif key == "macOS":
            if release.get_name() in (
                f"{key} {value[1]} {value[0]}",
                f"{key} {value[1]} {value[0]}.0",
            ):
                tweet(format_yearly_report(all_releases, key, value[0], stored_data))

save_file(stored_data, midnight)
