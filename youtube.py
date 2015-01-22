import requests
import re
import sqlite3
conn = sqlite3.connect("ytVideoId.db")
c = conn.cursor()

c.execute("""CREATE TABLE if not exists videoss(video_id TEXT)""")

def data_add(video):
    for video_id in video:
        counter = 0
        storage = video[counter]
        c.execute('''INSERT INTO videos VALUES(?)''', [storage])
        conn.commit()
        counter += 1


def get_videos(url, channel):
    page = 1
    found = 0
    video_list = []
    print "\nGrabbing videos from the {0} channel...".format(channel)
    #data_add(video_list)
    while True:
        make_request = requests.get(url.format(channel, page))
        re_pattern = "a href=\"http://www.youtube.com/watch\?v=(.*?)&amp;"
        reg = re.compile(re_pattern)
        videos = reg.findall(make_request.text)
        found += len(videos)
        video_list.extend(videos)


        if len(videos) == 0:
            break
        page += 50

    print "{0} videos found...".format(found)


    return video_list
def main():
    channel_name = raw_input("Enter the channel name (i.e., music): ")
    base_url = "http://gdata.youtube.com/feeds/base/users/{0}/uploads?max-results=50&start-index={1}"
    urls = get_videos(base_url, channel_name)
    print urls
    data_add(urls)
    conn.close()

if __name__ == "__main__":
    main()
