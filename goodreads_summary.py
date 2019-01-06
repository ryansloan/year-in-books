#process a goodreads csv file and output json for ingestion into visualization.
import sys
import csv
import json
import datetime
import requests
from xml.etree import ElementTree


goodreads_key="ENTER YOUR API KEY"
if (len(sys.argv)<3):
	print("Expected two arguments: year and path to Goodreads export CSV.")
	exit()

target_year=int(sys.argv[1])
output = []
n = 0
with open(sys.argv[2]) as csvfile:
	reader = csv.DictReader(csvfile)
	for book_data in reader:
		if (book_data["Exclusive Shelf"] != "read"):
			continue
		if (book_data["Date Read"] == ""):
			if (book_data["Date Added"] == ""):
				continue
			#use date added if date read is not available.
			date_read = datetime.datetime.strptime(book_data["Date Added"], '%Y/%m/%d')
		else:
			date_read = datetime.datetime.strptime(book_data["Date Read"], '%Y/%m/%d')
		if (date_read.year!=target_year):
			continue
		book = dict()
		n+=1
		#goodreads makes ISBN a formula for Excel users. This is
		#obviously not what we want. Strips out the = and quotes.
		book["isbn"] = book_data["ISBN"][2:-1]
		book["title"] = book_data["Title"]
		book["author"] = book_data["Author"]
		book["month"] = date_read.month
		book["rating"] = book_data["My Rating"]
		book["avg_rating"] = book_data["Average Rating"]
		book["pages"] = int(book_data["Number of Pages"])
		book["shelves"] = book_data["Bookshelves"]
		yp=float("inf")
		opy=float("inf")
		if (book_data["Year Published"] != ""):
			yp = int(book_data["Year Published"])
		if (book_data["Original Publication Year"] != ""):
			opy = int(book_data["Original Publication Year"])
			book["published"] = min(yp,opy)
		if (book_data["Additional Authors"] is not ""):
			book["author"]+=", "+book_data["Additional Authors"]
		print("fetching thumbnail URL for "+book["title"])

		goodreads_metadata_text=requests.get("https://www.goodreads.com/search/index.xml?key="+goodreads_key+"&q="+book["isbn"])
		gr_meta_root = ElementTree.fromstring(goodreads_metadata_text.content)
		for img in gr_meta_root.findall(".//image_url"):
			book["thumb"]=img.text
			break
		output.append(book)
print("Found "+str(n)+" books for "+str(target_year))
with open("html/"+str(target_year)+"_books.json", "w") as outfile:
    json.dump(output, outfile)
print("Wrote data file to html/"+str(target_year)+"_books.json")
