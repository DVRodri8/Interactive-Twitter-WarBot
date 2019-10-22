import sqlite3

conn = sqlite3.connect("uvaWarBot_twitter.db")
c    = conn.cursor()
c.execute("CREATE TABLE carreras(\
		nombre varchar(200) PRIMARY KEY,\
		conquista varchar(200)\
	 )")
conn.commit()
c.execute("CREATE TABLE tweets(\
		id integer PRIMARY KEY AUTOINCREMENT,\
		mainTweet varchar(300),\
		tweetc1   varchar(300),\
		tweetc2   varchar(300)\
	 )")

conn.commit()

with open("data_to_war.txt", "r") as f:
	for line in f.readlines():
		l = line.strip()
		c.execute("INSERT INTO carreras(nombre, conquista) VALUES(?,?)", (l, l))
	conn.commit()

