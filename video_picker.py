#make oAUTH call to YouTube channel



#ask for date range the data should be pulled for
print "What type of report do you want? Type 'channel' for channel level, or 'video' for video level"
user_choice = (input('> '))#ask if user wants channel level or video level report

if user_choice == 'video':
  print 'testing video report'
  video_level_report()
elif user_choice == 'channel':
  'testing channel level report'
  channel_level_report()
else:
  print "That's not a valid entry. Please try again"

def video_level_report(date, ids):
  analytics_response = None
  error = None
  retry = 0

#import the scraped video IDs from the database
  video_ids = []
#query the channel by video ID if user selects "video level"
#retrieve the following metrics
  for video_id in ids:


#views
#likes
#comments
#averageViewPercentage
#subscribersGained
#subscribersLost

#query the channel for it's data as a whole if user selects "channel level"
#retrieve the following metrics
#total views
#total views segmented by country
#traffic sources
#likes
#comments
#averageViewPercentage
#subscribersGained
#subscribersLost


