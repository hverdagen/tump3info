import glob, os, json, datetime, re, sys
from mp3_tagger import MP3File

#get list of mp3 files and remove the extension
def get_mp3_filenames(mp3dir):
	filenames = []
	os.chdir(mp3dir)
	for file in glob.glob("*.mp3"):
		filenames.append(file[:-4])
	return filenames

#open json and order data by mp3 filename (should be same format as those you have)
def get_json_info(json_file):
	mp3s = {}	#format example: {tumblr_nihxja4pJO1rxm3tr: {"url":"www.tumblr.com/11111111111", "id3s":{"id3-artist": "Battles", "id3-album": "Mirrored","id3-title": "Atlas",}}, ... } #tumblr_nihxja4pJO1rxm3tr is a file name. the number of id3 tags varies.
	soundcloud_posts_info = {} # {tumblrpostid1: {"title":"Hoops - Rules", "tumblr-url":"", audio-embed:""}, ... }
	youtube_urls = [] # ["https://www.youtube.com/watch?v=duWTfl4MJ1c", ...]
	with open(json_file, encoding='utf-8') as f:
		json_data = json.load(f)

		posts = json_data["posts"]
		filename_regex = "(tumblr_(?!audio)\w*)(.mp3)" #fixed: without the '.mp3', sometimes the first and second of the matches are different, and it mattered
		soundcloud_regex =  "https://[^\"]*" 
		for post in posts:
			if post["type"] == "audio":

				if "soundcloud" in post["audio-player"]:
					match = re.search(soundcloud_regex, post["audio-embed"])
					if match:
						player_url= match.group(0)
						soundcloud_posts_info[post["id"]] = {	"tumblr-url": post["url"], "soundcloud-player-url": player_url	}
						if post.get("id3-title", ""): soundcloud_posts_info[post["id"]]["title"] = post["id3-title"]

				else: #if it's not a soundcloud post we assume it's a tumblr audio post
					#find the post's corresponding mp3 filename
					ponmatch = False
					if "tumblr_nhg9o4zoV51sx17vxo1" in post["audio-embed"]: ponmatch = True	#delete
					match = re.search(filename_regex, post["audio-embed"])
					if match:
						filename=match.group(1)
						#associate filename with url and id3 tags
						id3s = {(key[4:]):value for key, value in post.items() if key.startswith('id3')}
						mp3s[filename] = {	"url": post["url"], "id3s": id3s	}
						if ponmatch: #delete
							print('whew')
							print(filename)
							print(mp3s[filename])
							ponmatch=False

			elif post["type"] == "video":
				if "youtube" in post["video-source"]:
					youtube_urls.append(post["video-source"])

			#else: nothing, we don't care about file types other than audio and video
		return {"mp3s": mp3s, "soundcloud_posts_info": soundcloud_posts_info, "youtube_urls": youtube_urls}

#change id3 tags and title for mp3s
def change_mp3s (write_dir, filenames, tumblr_mp3_data, change_tags=True, change_title=True, tag_override=True): #tag_override=False to prompt user before changing an existing tag
#filenames: [tumblr_nihxja4pJO1rxm3tr, tumblr_nihxja4pJO1rxm3tr] #no file extensions, but are assumed to be mp3s
#tumblr_mp3_data:  {tumblr_nihxja4pJO1rxm3tr: {"url":"www.tumblr.com/11111111111", "id3s":{"id3-artist": "Battles", "id3-album": "Mirrored","id3-title": "Atlas",}}, ... } (copied from mp3 data format information in get_json_info)
	skipped = {}
	nameless_ones = {}
	def tryset(mp3_filename, mp3, id3_tag, tag_value, initially_attempted_tag_value):
		try: 
			setattr(mp3, id3_tag, tag_value)
			mp3.save()
		except:
			print("Setting " + id3_tag + ': '+ tag_value + "failed." )
			response = input("Enter a new value to attempt or 's' to skip.")
			if response != 's':
				tryset(mp3_filename, mp3, id3_tag, response, initially_attempted_tag_value)
			else:
				if skipped.get(mp3_filename, ''):
					skipped[mp3_filename][id3_tag] = initially_attempted_tag_value
				else: 
					skipped[mp3_filename] = {id3_tag: initially_attempted_tag_value}

	for mp3_name in filenames:
		#print("mp3_name:" + mp3_name)
		mp3_info = tumblr_mp3_data.get(mp3_name, '')
		#print(mp3_info)
		if mp3_info:
			mp3_filename = mp3_name+".mp3"
			print(mp3_filename)
			mp3 = MP3File(mp3_filename)
			if change_tags:
				print(mp3_info["id3s"].items())
				for id3_tag, tag_value in mp3_info["id3s"].items(): #eg. title: "Fergalicious"

					#format:
					if id3_tag == 'title': id3_tag = 'song'
					if id3_tag == 'track' or id3_tag == 'year': 
						match = re.search("/d+", tag_value)
						if match:
							tag_value = match.group(0)
						else: tag_value = ''

					existing_tag = getattr(mp3, id3_tag)

					if tag_value:
						if tag_override or not existing_tag: #getattr(mp3, id3_tag) becomes eg. mp3.artist
							tryset(mp3_filename, mp3, id3_tag, tag_value, tag_value)
						else:
								prompt = ('Replace ' + str(id3_tag) + ": \n" + str(existing_tag) + " with \n" + tag_value + "\n? y/n")
								print(prompt)
								response = input('')
								while response != 'y' and response != 'n':
									response = input(prompt)
									if response == 'y':
										tryset(mp3_filename, mp3, id3_tag, tag_value, tag_value)
			if change_title:
				if mp3_info["id3s"].get('title', ''): #rename mp3
					new_title = mp3_info["id3s"]["title"]+".mp3"
					try: os.rename(mp3_filename, new_title)
					except: 
						exc_type, _, _ = sys.exc_info()
						print('Renaming ' + mp3_filename + ' failed. (' + str(exc_type) + ')') #not a big deal requiring retrying, as the title is either in the tags or the skipped tags json dump
						if skipped.get(mp3_filename, ''):
							skipped[mp3_filename]['rename_attempt'] = new_title
						else: 
							skipped[mp3_filename] = {'rename_attempt': new_title}
				else:
					nameless_ones[mp3_filename] = (mp3_info["url"], mp3_info[""])
	if nameless_ones:
		with open(write_dir+"/nameless_" + get_timestamp() + ".txt", "w") as f:
			for filename, url in nameless_ones.items():
				f.write(filename + "\t" + url + "\n")
	if skipped:
		with open(write_dir+"/skipped_" + get_timestamp() + ".json", "w") as f:
			json.dump(skipped, f)

#create file of youtube links
def write_youtube(write_dir, youtube_urls):
	with open(write_dir+"/youtube_" + get_timestamp() + ".txt", "w") as f:
		for link in youtube_urls:
			f.write(link)

#create file with soundcloud embed links
def write_soundcloud(write_dir, soundcloud_posts_info):
	with open(write_dir+"/soundcloud_" + get_timestamp() + ".txt", "w") as f:
		for _, value in soundcloud_posts_info.items():
			f.write(value["soundcloud-player-url"] + "\n")
										
def get_timestamp(): #format: #2018-10-24 15:30:30
	time = datetime.datetime.now()
	timestamp = time.strftime("%Y") + "-" + time.strftime("%m") + "-" + time.strftime("%d") + "_" + time.strftime("%H") + "-" + time.strftime("%M") + "-" + time.strftime("%S") 
	return timestamp

def main():
	current_dir = os.path.dirname(os.path.realpath(__file__)) #the directory this python file is in
	mp3_dir = current_dir
	try: 
		json_file = sys.argv[1]
	except: 
		print("Supply the name of the json file, eg. write \"tumblrmp3tool.py systematizations.json\"")
		quit()
	write_dir = current_dir + "/write_dir"
	if not os.path.exists(write_dir):
		os.makedirs(write_dir)

	tumblr_info = get_json_info(json_file)
	files_to_change = get_mp3_filenames(mp3_dir)
	change_mp3s(write_dir, files_to_change, tumblr_info["mp3s"])
	write_youtube(write_dir, tumblr_info["youtube_urls"])
	write_soundcloud(write_dir, tumblr_info["soundcloud_posts_info"])

	print("Done!")

if __name__ == "__main__": #don't run if imported as module
	main()