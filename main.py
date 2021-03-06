# -*- coding: utf-8 -*-
# Module: default
# Author: Roman V. M.
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import pickle
import logging
import sys
from urlparse import parse_qsl
import requests
from bs4 import BeautifulSoup
import re
import xbmcgui
import xbmcplugin

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

VIDEOS = {}
baseurl = "http://fullmatchesandshows.com"

def get_categories():
	"""
	Get the list of video categories.
	Here you can insert some parsing code that retrieves
	the list of video categories (e.g. 'Movies', 'TV-shows', 'Documentaries' etc.)
	from some site or server.
	:return: list
	"""

	## Latest lookup
	r = requests.get(baseurl + '/category/full-match/')
	if r.status_code != 200:
		print("Something went wrong")
		quit();

	fsoup = BeautifulSoup(r.text, 'html.parser')

	for link in fsoup.find_all('a'):
		url = unicode(link.get('href'))
		m = re.match("(.*fullmatchesandshows.com\/(\d+\/\d+\/\d+)\/(.+)-vs-(.+?)-.*)", url)
		if m:
			logging.error(m.groups()[1])
			tempti = '(' + m.groups()[1] + ') ' + link.get('title').replace('&', 'and')
			tempti = tempti.encode('utf-8', 'replace')
			# title = link.get('title').replace('&', 'and').encode('utf-8', 'replace')
			# title = title.replace('\xe2\x80\x93', '-')
			title = tempti.replace('\xe2\x80\x93', '-')
			VIDEOS[title] = [{'name': '', 'url': url, 'video': '', 'thumb': '', 'genre': ''}]
			
	logging.error(VIDEOS.keys())
	pickle.dump(VIDEOS, open('fm.p', 'wb'))
	return VIDEOS.keys()


def get_videos(category):
	"""
	Get the list of videofiles/streams.
	Here you can insert some parsing code that retrieves
	the list of videostreams in a given category from some site or server.
	:param category: str
	:return: list
	"""
	VIDEOS = pickle.load(open('fm.p', 'rb'))
	category = category #[:-1]
	#logging.error(category)
	#logging.error(VIDEOS.keys())
	#logging.error(VIDEOS[category])
	rm = requests.get(VIDEOS[category][0]['url'])
	rsoup = BeautifulSoup(rm.text, 'html.parser')
	ap = rsoup.find('input', id='acp_post')
	strmlks = rsoup.find_all('a', href=re.compile('#\d'))
	for stream in strmlks:
		name = stream.text
		page = str(stream['href'][-1:])
		pid = int(page) - 1
		apid = str(ap.get('value'))
		postdata={'acp_currpage': page, 'acp_pid': apid, 'acp_shortcode': 'acp_shortcode', 'action': 'pp_with_ajax'}
		ssr = requests.post(baseurl + '/wp-admin/admin-ajax.php', data=postdata)
		try:
			jfeed = BeautifulSoup(ssr.text, 'html.parser')
			jurl = jfeed.find('script')['data-config']
		except:
			break
		jsr = requests.get('http:' + jurl)
		manifest = str(jsr.json()['content']['media']['f4m'])
		masoup = BeautifulSoup(requests.get(manifest).text, 'html.parser')
		vidurl = str(masoup.find('baseurl').text) + '/' + str(masoup.find('media')['url'])
		VIDEOS[category].append({'name': name, 'video': vidurl, 'thumb': '', 'url': '', 'genre': ''})

	return VIDEOS[category]


def list_categories():
	"""
	Create the list of video categories in the Kodi interface.
	:return: None
	"""
	# Get video categories
	categories = get_categories()
	# Create a list for our items.
	listing = []
	# Iterate through categories
	for category in categories:
		# Create a list item with a text label and a thumbnail image.
		list_item = xbmcgui.ListItem(label=category, thumbnailImage=VIDEOS[category][0]['thumb'])
		# Set a fanart image for the list item.
		# Here we use the same image as the thumbnail for simplicity's sake.
		list_item.setProperty('fanart_image', VIDEOS[category][0]['thumb'])
		# Set additional info for the list item.
		# Here we use a category name for both properties for for simplicity's sake.
		# setInfo allows to set various information for an item.
		# For available properties see the following link:
		# http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
		list_item.setInfo('video', {'title': category, 'genre': category})
		# Create a URL for the plugin recursive callback.
		# Example: plugin://plugin.video.example/?action=listing&category=Animals
		url = '{0}?action=listing&category={1}'.format(_url, category)
		# is_folder = True means that this item opens a sub-list of lower level items.
		is_folder = True
		# Add our item to the listing as a 3-element tuple.
		listing.append((url, list_item, is_folder))
	# Add our listing to Kodi.
	# Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
	# instead of adding one by ove via addDirectoryItem.
	xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
	# Add a sort method for the virtual folder items (alphabetically, ignore articles)
	xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	# Finish creating a virtual folder.
	xbmcplugin.endOfDirectory(_handle)


def list_videos(category):
	"""
	Create the list of playable videos in the Kodi interface.
	:param category: str
	:return: None
	"""
	# Get the list of videos in the category.
	videos = get_videos(category)
	# Create a list for our items.
	listing = []
	# Iterate through videos.
	for video in videos:
        # Create a list item with a text label and a thumbnail image.
		list_item = xbmcgui.ListItem(label=video['name'], thumbnailImage=video['thumb'])
		# Set a fanart image for the list item.
		# Here we use the same image as the thumbnail for simplicity's sake.
		list_item.setProperty('fanart_image', video['thumb'])
		# Set additional info for the list item.
		list_item.setInfo('video', {'title': video['name'], 'genre': video['genre']})
		# Set additional graphics (banner, poster, landscape etc.) for the list item.
		# Again, here we use the same image as the thumbnail for simplicity's sake.
		list_item.setArt({'landscape': video['thumb']})
		# Set 'IsPlayable' property to 'true'.
		# This is mandatory for playable items!
		list_item.setProperty('IsPlayable', 'true')
		# Create a URL for the plugin recursive callback.
		# Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/vids/crab.mp4
		url = '{0}?action=play&video={1}'.format(_url, video['video'])
		# Add the list item to a virtual Kodi folder.
		# is_folder = False means that this item won't open any sub-list.
		is_folder = False
		# Add our item to the listing as a 3-element tuple.
		listing.append((url, list_item, is_folder))
		    # Add our listing to Kodi.
		    # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
	# instead of adding one by ove via addDirectoryItem.
	xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
	# Add a sort method for the virtual folder items (alphabetically, ignore articles)
	xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	# Finish creating a virtual folder.
	xbmcplugin.endOfDirectory(_handle)


def play_video(path):
	"""
	Play a video by the provided path.
	:param path: str
	:return: None
	"""
	# Create a playable item with a path to play.
	play_item = xbmcgui.ListItem(path=path)
	# Pass the item to the Kodi player.
	xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
	"""
	Router function that calls other functions
	depending on the provided paramstring
	:param paramstring:
	:return:
	"""
	# Parse a URL-encoded paramstring to the dictionary of
	# {<parameter>: <value>} elements
	params = dict(parse_qsl(paramstring))
	# Check the parameters passed to the plugin
	if params:
		if params['action'] == 'listing':
			# Display the list of videos in a provided category.
			list_videos(params['category'])
		elif params['action'] == 'play':
			# Play a video from a provided URL.
			play_video(params['video'])
	else:
		# If the plugin is called from Kodi UI without any parameters,
		# display the list of video categories
		list_categories()


if __name__ == '__main__':
	# Call the router function and pass the plugin call parameters to it.
	# We use string slicing to trim the leading '?' from the plugin call paramstring
	router(sys.argv[2][1:])
