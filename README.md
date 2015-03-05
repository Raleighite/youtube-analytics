# youtube-analytics
<b>Youtube Analytics Puller</b><br />
This is a small project I started to help automate reporting I do for my company's YouTube channels. This is my first Python project
so I expect it will take some time to get all the functionality right. I'll try to keep this readme updated as the project progresses.
<br />

<b>Current Usage Instructions</b><br />
Clone the repo to your computer. You'll need to have Python 2.7, pip, and virtualenv installed. Install the packages from the requirements.txt file. You'll also need to create a JSON document with your API credentials from the Google Deverloper console. The script youtube.py scrapes the video ID's from a channel you specify and saves it to a sqlite datebase. Next run the youtube_sample.py script. It will ask you to log into your YouTube channel. The script will pull in the video IDs from the sqlite database and pass them into the YouTube analytics API and return the data.
<br />

<b>Options</b><br />
I plan to make this easier to specify options, but currently you'll have to do it manually within the youtube_sample.py script. The script is a modifyed version of the sample Google provides on their YouTube Analytics API page.
<br />
