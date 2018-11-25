Based on blog info (json),
	Feature 1. creates text files with all youtube/soundcloud urls embedded in posts in that blog
	Feature 2. tags and retitles existing mp3s whose names correspond to those in tumblr posts

So, you have:
A JSON of a tumblr blog (like what you can get from tumblr2json.com)
(If you want feature #2,) MP3s titled things like "tumblr_liqnig0ILh1qcp3wf.mp3", corresponding to the MP3s in the tumblr blog JSON (like what you can get running TumblThree)
Python, so you can run the .py file. (I used 3.6 and anything higher should definitely be fine)

Put the .py in the same directory as the MP3s and JSON file, and run the .py like so:
	python tump3info.py jsonfilename.json
replacing jsonfilename with the actual name (probably the blog name.)

Output- (youtube urls, soundcloud urls, and nameless or skipped files for which renaming failed) are saved to /write_dir.

Known issues: prints errors instead of writing to stderr, doesn't take a list of files as an argument, filename parsing may be locale-dependent (eg. has trouble with Japanese!)
