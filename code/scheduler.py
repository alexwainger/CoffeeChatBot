import csv
import random
import mechanize
import re
from datetime import datetime, timedelta
import numpy as np

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

groupSize = 4
iterations = 100000
data_file = "data/2017-18.csv"

class Person:
	def __init__(self, name, email, isNewMember, group_history):
		self.name = name
		self.email = email
		self.isNewMember = isNewMember
		self.group_history = group_history
		self.new_group = 0

	def getEmailDisplayName(self):
		return self.name + " <" + self.email + ">"

	def genCSVRow(self):
		return [self.name, self.email, self.isNewMember] + [str(x) for x in self.group_history] + [str(self.new_group)]

	def __str__(self):
		return self.name

	__repr__ = __str__

def generateGroups(people_list):
	minConflicts = float("inf")
	best_new_member_std = float("inf")
	best_groups = None
	num_groups = len(people_list) / groupSize
	for it in range(iterations):
		random.shuffle(people_list)
		groups = []
		for i in range(num_groups):
			groups.append(people_list[i * groupSize : (i+1) * groupSize])

		conflicts = 0
		conflict_pairs = []
		new_member_score = np.zeros([num_groups])
		for a, group in enumerate(groups):
			for i in range(len(group)):
				person1 = group[i]
				new_member_score[a] += person1.isNewMember
				for j in range(i + 1, len(group)):
					person2 = group[j]
					for k in range(len(person1.group_history)):
						if person1.group_history[k] == person2.group_history[k] and (person1.name != 'Alex Wainger' and person2.name != 'Alex Wainger'):
						        conflict_pairs.append((person1.name, person2.name))
							conflicts += 1

		if (conflicts < minConflicts and np.all(new_member_score < groupSize)) or (conflicts == minConflicts and np.all(new_member_score < groupSize) and np.std(new_member_score) < best_new_member_std):
			print "Iteration", it, "- ",conflicts,"conflicts and", np.std(new_member_score),"std!"
			for pair in conflict_pairs:
				print "\t",pair
			minConflicts = conflicts
			best_groups = groups
			best_new_member_std = np.std(new_member_score)
			groupNum = 1
			for group in groups:
				for person in group:
					person.new_group = groupNum

				groupNum += 1

                if minConflicts == 0:
                    break

	return best_groups

def createWhen2Meet(eventName):
	br = mechanize.Browser()
	br.open("http://www.when2meet.com")
	br.select_form(nr=0)
	br.form["NewEventName"] = eventName
	br.form["PossibleDates"] = "0|1|2|3|4|5|6"
	br.form["DateTypes"] = ["DaysOfTheWeek"]
	br.form["NoLaterThan"] = ["0"]
	response = br.submit()

	urlregex = re.compile(".*<body onload=\"window.location='(.*)'\">.*")
	return urlregex.search(response.read()).group(1)

def emailGroup(group, w2mUrl):
	curr_date = datetime.now()
	curr_date_plus14 = curr_date + timedelta(days=21)
	msg = MIMEMultipart()
	msg['From'] = "CDSS Coffee Chat Bot"
	msg['To'] = ", ".join([x.getEmailDisplayName() for x in group])
	print msg['To']
	msg['Subject'] = "CDSS Coffee Chats - " + curr_date.strftime("%m/%d") + " to " + curr_date_plus14.strftime("%m/%d")
	body = "Hey there!\n\nIt's time for CDSS Coffee Chats! Please meet with your group sometime in the next two weeks (if you don't, your team will have to tell embarrassing stories at the next board meeting!). \n\nFill out this when2meet with times you're typically free to meet: when2meet.com" + w2mUrl + "\n\nLove,\nCDSS Coffee Chat Bot"
	msg.attach(MIMEText(body, 'plain'))

	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login("cdsscoffeechats@gmail.com", "datascienceforever")
	text = msg.as_string()
	server.sendmail("cdsscoffeechats@gmail.com", [x.email for x in group if x.email != ''], text)
	server.quit()

def main():
	people_list = []
	headers = []
	with open(data_file, "rb") as people_file:
		people = csv.reader(people_file)
		headers = next(people)
		for person in people:
			new_person = Person(person[0], person[1], int(person[2]), [int(x) for x in person[3:] if x != ''])
			people_list.append(new_person)

		groups = None
		approved = False
		while not approved:
			groups = generateGroups(people_list)
			if groups:
				for i, group in enumerate(groups):
					print "Group",i,"-",group
				approved = raw_input("Type \"Yes\" to send the emails, or type anything to regroup: ") == "Yes"
			else:
				print "No groups found, running algorithm again..."

		groupNum = 1
		for group in groups:
			eventName = "Coffee Chat for Group " + str(groupNum)
			w2mUrl = createWhen2Meet(eventName)
			emailGroup(group, w2mUrl)
			groupNum += 1

	with open(data_file, "wb") as people_file:
		writer = csv.writer(people_file)
		writer.writerow(headers + ["week" + str(len(headers)-2)])
		for person in people_list:
			writer.writerow(person.genCSVRow())


if __name__ == "__main__":
	main()
