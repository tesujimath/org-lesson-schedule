#!/usr/bin/env python
# -*-python-*-
# Create org mode files for a year's lessons.
#
# This program is free software, licensed under the GNU Public License v3.
# See http://www.gnu.org/copyleft/gpl.html
# 
# Simon Guest, v1 29/11/12


import Tkinter
import tkFileDialog
import tkMessageBox
import tkFont
import datetime
import cPickle as pickle
import os.path
import sys

colours = ["#4cc", "#c4c", "#cc4", "#c44", "#4c4", "#44c", "#088", "#808", "#880", "#eee"] 
#colours = ["#4cc", "#c4c", "#cc4", "#eee"] 
dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri"]

thisVersion = 1

#
#  M O D E L   C L A S S E S
#

class Lesson:
    def __init__(self, dayNumber, time, group = None):
        self.dayNumber = dayNumber
        self.time = time
        self.group = group

    def __repr__(self):
        return "Lesson(" + str(self.dayNumber) + ", " + formatTime(self.time) + "," + str(self.group) + ")"

    def setTime(self, time):
        self.time = time

    def setGroup(self, group):
        self.group = group

class Row:
    def __init__(self, time = None):
        self.time = time
        self.lessons = []
        for i,dayName in enumerate(dayNames):
            self.lessons.append( Lesson(i, time) )

    def __repr__(self):
        return "Row(" + str(self.time) + "," + str(self.lessons) + ")"

class Timetable:
    def __init__(self):
        self.rows = []
        # setup some sensible defaults
        for t in ["08:35AM", "09:35AM", "11:10AM", "12:50PM", "2:05PM"]:
            self.rows.append(Row(time = parseTime(t)))
        
    def __repr__(self):
        return "Timetable(" + str(self.rows) + ")"
    
    def appendRow(self, row):
        self.rows.append( row )

    def createGroupedTimetable(self):
        gt = GroupedTimetable()
        for row in self.rows:
            for dayNumber,lesson in enumerate(row.lessons):
                if lesson.group:
                    gt.insertLesson(lesson.group, lesson.dayNumber, lesson.time)
        return gt

class Term:
    def __init__(self, begin, end):
        self.begin = begin
        self.end = end

class Year:
    def __init__(self):
        self.defaultBegin = ["30/1/12", "23/4/12", "16/7/12", "15/10/12"]
        self.defaultEnd = ["6/4/12", "29/6/12", "28/9/12", "14/12/12"]
        self.terms = []
        for i,d in enumerate(self.defaultBegin):
            self.terms.append( Term( parseDate(self.defaultBegin[i]),
                                     parseDate(self.defaultEnd[i]) ) )

    def setNumberOfTerms(self, n):
        while len(self.terms) > n:
            del self.terms[-1]
        while len(self.terms) < n:
            self.terms.append(Term(parseDate("1/1/10"), parseDate("31/12/10")))
            
class PersistentData:
    def __init__(self):
        self.version = thisVersion
        self.defaultStaffCode = ""
        self.timetables = {}
        self.year = Year()

    def hasTimetable(self, staffCode):
        return self.timetables.has_key(staffCode)

    def getTimetable(self, staffCode):
        if self.timetables.has_key(staffCode):
            return self.timetables[ staffCode ]
        else:
            t = Timetable()
            self.timetables[ staffCode ] = t
            return t

class GroupLessons:
    def __init__(self, name):
        self.name = name
        self.lessons = {}

    def __repr__(self):
        return "GroupLessons(" + self.name + ", " + str(self.lessons) + ")"

    def insertLessonOnDay(self, newLesson):
        """Insert, preserving chronological order.  Replaces any at same day/time."""
        for i,lesson_i in enumerate(self.lessons):
            if newLesson.dayNumber == lesson_i.dayNumber and newLesson.time == lesson_i.time:
                self.lessons[i] = newLesson
                newLesson = None
                break
            elif newLesson.dayNumber < lesson_i.dayNumber or (newLesson.dayNumber == lesson_i.dayNumber and newLesson.time < lesson_i.time):
                self.lessons.insert(i, newLesson)
                newLesson = None
                break
        if newLesson:
            self.lessons.append(newLesson)
            newLesson = None

    def insertLesson(self, newLesson):
        """Insert, preserving chronological order.  Replaces any at same day/time."""
        if not self.lessons.has_key(newLesson.dayNumber):
            self.lessons[newLesson.dayNumber] = []
        lessonsForDay = self.lessons[newLesson.dayNumber]
        for i,lesson_i in enumerate(lessonsForDay):
            if newLesson.time == lesson_i.time:
                self.lessonsForDay[i] = newLesson
                newLesson = None
                break
            elif newLesson.time < lesson_i.time:
                lessonsForDay.insert(i, newLesson)
                newLesson = None
                break
        if newLesson:
            lessonsForDay.append(newLesson)
            newLesson = None

    def writeLessonsForDate(self, file, d):
        if self.lessons.has_key(d.weekday()):
            for lesson in self.lessons[d.weekday()]:
                file.write(d.strftime("** <%Y-%m-%d %a ") + lesson.time.strftime("%H:%M> \n"))

    def writeLessonsForYear(self, file, year):
        for term in year.terms:
            for dn in range(term.begin.toordinal(), term.end.toordinal() + 1):
                d = datetime.date.fromordinal(dn)
                self.writeLessonsForDate(file, d)

class GroupedTimetable:
    def __init__(self):
        self.groups = {}

    def insertLesson(self, group, dayNumber, time):
        newLesson = Lesson(dayNumber, time, group)
        if not self.groups.has_key(group):
            self.groups[ group ] = GroupLessons(group)
        self.groups[ group ].insertLesson( newLesson )

    def writeFiles(self, year):
        orgdir = tkFileDialog.askdirectory( title = "Lessons Folder" )
        if not os.path.exists(orgdir):
            os.mkdir(orgdir, 0755)
        for groupName in self.groups.keys():
            orgfile = os.path.join(orgdir, groupName + ".org")
            try:
                of = open(orgfile, 'w')
                self.groups[ groupName ].writeLessonsForYear(of, year)
                of.close()
            except IOError:
                tkMessageBox.showerror("File Error", "Can't write to file " + orgfile)

#
#  G U I   C L A S S E S
#

def parseTime(ws, prev = None, next = None):
    s = ws.replace(" ", "")
    formats = [ "%I:%M%p", "%I.%M%p", "%I%p", "%H:%M", "%H.%M" ]
    t = None
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(s, fmt)
            t = dt.time()
        except ValueError:
            pass
        if t:
            break
    # may have omitted pm, so check for this
    if prev and t < prev:
        if t.hour() < 12:
            t = datetime.time( t.hour() + 12, t.minute() )
        if t < prev:
            t = prev
    if next and t > next:
        t = next
    return t

def formatTime(t):
    if t:
        ts = t.strftime("%I:%M%p")
    else:
        ts = ""
    return ts

def parseDate(ws):
    s = ws.replace(" ", "")
    formats = [ "%d/%m/%y" ]
    d = None
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(s, fmt)
            d = dt.date()
        except ValueError:
            pass
        if d:
            break
    return d

def formatDate(d):
    if d:
        ds = d.strftime("%d/%m/%y")
    else:
        ds = ""
    return ds

class LessonView:
    """A schedulable lesson.   Has a start-time slot, and a group."""
    def __init__(self, parent, index, day):
        #timeFont = tkFont.Font( size = 6 )
        self.index = index               # 0 to whatever
        self.day = day                   # 0 to 4
        self.group = ""
        self.selected = False
        self.timeStringVar = Tkinter.StringVar()
        self.timeStringVar.set("")
        self.timeEntry = Tkinter.Entry( parent,
                                        textvariable = self.timeStringVar,
                                        width = len("08:45AM") )
                                        #font = timeFont )
        self.timeEntry.bind("<Return>", self.handleTimeUpdate)
        self.timeEntry.bind("<FocusOut>", self.handleTimeUpdate)
        
        self.groupButton = Tkinter.Button(parent,
                                          text = "",
                                          height = 3,
                                          command = self.toggleSelection)
        self.showSelectionStatus()
        self.renumber(index)

    def renumber(self,  index):
        self.index = index
        self.timeEntry.grid(row = self.index * 3 + 2, column = self.day + 1)
        self.groupButton.grid(row = self.index * 3 + 3, column = self.day + 1, sticky = "nesw")

    def grid_remove(self):
        self.timeEntry.grid_remove()
        self.groupButton.grid_remove()

    def setTime(self, t):
        self.time = t
        self.timeStringVar.set( formatTime(self.time) )

    def handleTimeUpdate(self, event):
        t = parseTime( self.timeStringVar.get() )
        if t:
            self.setTime(t)
        else:
            self.timeStringVar.set("")

    def setGroup(self, g, colour = colours[-1]):
        if g == None:
            self.group = ""
        else:
            self.group = g.strip()
        self.groupButton.configure( text = self.group,
                                    background = colour,
                                    activebackground = colour )

    def showSelectionStatus(self):
        if self.selected:
            self.groupButton.configure(relief = Tkinter.SUNKEN)
        else:
            self.groupButton.configure(relief = Tkinter.FLAT)            

    def toggleSelection(self):
        self.selected = not self.selected
        self.showSelectionStatus()

    def setSelected(self, state):
        self.selected = state
        self.showSelectionStatus()

class InsertButton:
    """A button to insert a new row."""

    def __init__(self, parent, index):
        self.parent = parent
        self.index = index
        self.button = Tkinter.Button(parent, text = "+", command = self.insert)
        self.renumber(index)

    def renumber(self, index):
        self.index = index
        self.button.grid(row = index * 3 + 2, column = 6)

    def grid_remove(self):
        self.button.grid_remove()

    def insert(self):
        self.parent.insertRow(self.index)

class DeleteButton:
    """A button to delete a row."""

    def __init__(self, parent, index):
        self.parent = parent
        self.index = index
        self.button = Tkinter.Button(parent, text = "-", command = self.delete)
        self.renumber(index)

    def renumber(self, index):
        self.index = index
        self.button.grid(row = index * 3 + 3, column = 6)

    def grid_remove(self):
        self.button.grid_remove()

    def delete(self):
        self.parent.deleteRow(self.index)

class RowView:
    """A time, group entry for each day, and insert/delete buttons."""
    def __init__(self, parent, index):
        self.index = None
        self.parent = parent
        self.time = None
        self.timeStringVar = Tkinter.StringVar()
        self.timeEntry = Tkinter.Entry( self.parent,
                                        textvariable = self.timeStringVar,
                                        width = len("08:45AM") )
        self.timeEntry.bind("<Return>", self.handleTimeUpdate)
        self.timeEntry.bind("<FocusOut>", self.handleTimeUpdate)
        self.lessonViews = []
        for i,day in enumerate(dayNames):
            self.lessonViews.append( LessonView(self.parent, index, i) )
        self.insertButton = InsertButton(parent, index)
        self.deleteButton = DeleteButton(parent, index)
        self.separatorFrame = Tkinter.Frame(self.parent,
                                            borderwidth = 2,
                                            relief = Tkinter.RAISED,
                                            height = 2)
        self.setTime( None )
        self.renumber(index)
        
    def renumber(self, index):
        if index != self.index:
            self.index = index
            self.separatorFrame.grid(row = self.index * 3 + 1, column = 0, columnspan = 7, sticky = "ew")
            self.timeEntry.grid(row = self.index * 3 + 3, column = 0)
            for lessonView in self.lessonViews:
                lessonView.renumber(index)
            self.insertButton.renumber(index)
            self.deleteButton.renumber(index)

    def grid_remove(self):
        self.timeEntry.grid_remove()
        for lessonView in self.lessonViews:
            lessonView.grid_remove()
        self.insertButton.grid_remove()
        self.deleteButton.grid_remove()
        self.separatorFrame.grid_remove()
        
    def setSelected(self, state):
        for lessonView in self.lessonViews:
            lessonView.setSelected(state)

    def setTime(self, t):
        self.time = t
        self.timeStringVar.set( formatTime(self.time) )
        for lessonView in self.lessonViews:
            lessonView.setTime(t)

    def handleTimeUpdate(self, event):
        t = parseTime( self.timeStringVar.get() )
        if t:
            self.setTime(t)
        else:
            self.timeStringVar.set("")

class TimetableView(Tkinter.Frame):
    """Lesson timetable."""
    def __init__(self, parent):
        Tkinter.Frame.__init__(self, parent)
        self.dayLabels = []
        self.rowViews = []
        self.colourByGroup = {}
        self.groupByColour = len(colours) * [None]

        for i,day in enumerate(dayNames):
            self.dayLabels.append( Tkinter.Label(self, text = day) )
            
        self.insertButton = InsertButton(self, len(self.rowViews))
        self.separatorFrame = Tkinter.Frame(self,
                                            borderwidth = 2,
                                            relief = Tkinter.RAISED,
                                            height = 2)
        self.renumber()

    def renumber(self):
        for i,dayLabel in enumerate(self.dayLabels):
            dayLabel.grid(row = 0, column = i + 1)
            
        for i,rowView in enumerate(self.rowViews):
            rowView.renumber(i)
        n = len(self.rowViews)
        self.insertButton.renumber(n)
        self.separatorFrame.grid(row = n * 3 + 1, column = 0, columnspan = 7, sticky = "ew")

    def insertRow(self, n):
        self.rowViews.insert(n, RowView(self, n))
        self.renumber()

    def deleteRow(self, i):
        self.rowViews[i].grid_remove()
        del self.rowViews[i]
        self.renumber()

    def setGroup(self, group):
        colour = self.allocateColour(group)
        for rowView in self.rowViews:
            for lessonView in rowView.lessonViews:
                if lessonView.selected:
                    lessonView.setGroup(group, colour)
                    lessonView.setSelected(False)

    def getDisplayedGroups(self):
        groups = set()
        for rowView in self.rowViews:
            for lessonView in rowView.lessonViews:
                if lessonView.group != "":
                    groups.add(lessonView.group)
        return groups

    def unallocateUnusedColours(self):
        displayedGroups = self.getDisplayedGroups()
        for group in self.colourByGroup.keys():
            if group not in displayedGroups:
                colour = self.colourByGroup[group]
                self.groupByColour[colour] = None
                del self.colourByGroup[group]

    def allocateColour(self, group):
        colour = None
        self.unallocateUnusedColours()
        if group == "" or group == None:
            colour = colours[-1]
        elif self.colourByGroup.has_key(group):
            colour = colours[self.colourByGroup[group]]
        else:
            for i,colour in enumerate(colours):
                if self.groupByColour[i] == None:
                    self.groupByColour[i] = group
                    self.colourByGroup[group] = i
                    break
            if i >= len(colours):
                i = len(colours) - 1
            colour = colours[i]
        return colour

    def displayTimetable(self, timetable):
        while len(self.rowViews) < len(timetable.rows):
            self.insertRow(0)
        while len(self.rowViews) > len(timetable.rows):
            self.deleteRow(0)
        for i,rowView in enumerate(self.rowViews):
            rowView.setTime( timetable.rows[i].time )
            for j,lessonView in enumerate(self.rowViews[i].lessonViews):
                group = timetable.rows[i].lessons[j].group
                colour = self.allocateColour(group)
                rowView.lessonViews[j].setTime( timetable.rows[i].lessons[j].time )
                rowView.lessonViews[j].setGroup( group, colour )

    def clear(self):
        """Clear whole timetable."""
        for rowView in self.rowViews:
            for lessonView in rowView.lessonViews:
                lessonView.setGroup("")

    def saveTimetable(self, newTimetable):
        newTimetable.rows = []
        for rowView in self.rowViews:
            newRow = Row( rowView.time )
            newTimetable.appendRow( newRow )
            for i,lessonView in enumerate(rowView.lessonViews):
                lesson = newRow.lessons[i]
                lesson.setGroup( lessonView.group )
                if lessonView.time:
                    lesson.setTime( lessonView.time )

class TermView:
    """Start and end date for a term, and insert/delete buttons."""
    def __init__(self, parent, index):
        self.parent = parent
        self.label = Tkinter.Label( self.parent,
                                    text = "Term " + str(index + 1) )
        self.beginStringVar = Tkinter.StringVar()
        self.beginEntry = Tkinter.Entry( self.parent,
                                         textvariable = self.beginStringVar,
                                         width = len("22/12/22") )
        self.beginEntry.bind("<Return>", self.handleBeginUpdate)
        self.beginEntry.bind("<FocusOut>", self.handleBeginUpdate)
        self.endStringVar = Tkinter.StringVar()
        self.endEntry = Tkinter.Entry( self.parent,
                                         textvariable = self.endStringVar,
                                         width = len("22/12/22") )
        self.endEntry.bind("<Return>", self.handleEndUpdate)
        self.endEntry.bind("<FocusOut>", self.handleEndUpdate)
        self.label.grid(row = index, column = 0)
        self.beginEntry.grid(row = index, column = 1)
        self.endEntry.grid(row = index, column = 2)

    def setBegin(self, d):
        self.begin = d
        self.beginStringVar.set(formatDate(d))
        
    def handleBeginUpdate(self, event):
        self.setBegin( parseDate( self.beginStringVar.get() ) )
    
    def setEnd(self, d):
        self.end = d
        self.endStringVar.set(formatDate(d))
        
    def handleEndUpdate(self, event):
        self.setEnd( parseDate( self.endStringVar.get() ) )

    def displayTerm(self, term):
        self.setBegin(term.begin)
        self.setEnd(term.end)

    def saveTerm(self, term):
        term.begin = self.begin
        term.end = self.end

    def grid_remove(self):
        self.label.grid_remove()
        self.beginEntry.grid_remove()
        self.endEntry.grid_remove()

class YearView(Tkinter.Frame):
    """Term dates for the year."""
    def __init__(self, parent):
        Tkinter.Frame.__init__(self, parent)
        self.termViews = []
        self.numberOfTermsLabel = Tkinter.Label(self, text = "Number of Terms")
        self.numberOfTermsIntVar = Tkinter.IntVar()
        self.numberOfTermsSpinbox = Tkinter.Spinbox(self,
                                                    from_ = 1,
                                                    to_ = 9,
                                                    textvariable = self.numberOfTermsIntVar,
                                                    command = self.updateNumberOfTerms)

    def updateNumberOfTerms(self):
        n = self.numberOfTermsIntVar.get()
        self.setNumberOfTerms(n)

    def setNumberOfTerms(self, n):
        while len(self.termViews) > n:
            self.termViews[-1].grid_remove()
            del self.termViews[-1]
        for i in range(len(self.termViews), n):
            self.termViews.append(TermView(self, i))
            self.termViews[-1].setBegin( parseDate("1/1/11") )
            self.termViews[-1].setEnd( parseDate("31/12/11") )

        self.numberOfTermsIntVar.set(n)
        self.numberOfTermsLabel.grid(row = n, column = 0)
        self.numberOfTermsSpinbox.grid(row = n, column = 1, columnspan = 2)

    def displayYear(self, year):
        self.setNumberOfTerms(len(year.terms))
        for i,t in enumerate(year.terms):
            self.termViews[i].displayTerm( year.terms[i] )

    def saveYear(self, year):
        year.setNumberOfTerms(len(self.termViews))
        for i,t in enumerate(year.terms):
            self.termViews[i].saveTerm( year.terms[i] )

class Application:
    def __init__(self):
        self.main_window = Tkinter.Tk()
        self.main_window.title("Emacs Lesson Timetabler")
        self.configFilename = os.path.expanduser("~/.emacs-lesson-schedule")
        self.timetableView = TimetableView(self.main_window)

        self.groupLabel = Tkinter.Label(self.main_window, text = "Group")
        self.groupStringVar = Tkinter.StringVar()
        self.groupStringVar.set("")
        self.groupEntry = Tkinter.Entry( self.main_window,
                                         textvariable = self.groupStringVar,
                                         width = len("XXXXXX"))
        self.groupEntry.bind("<Return>", self.handleGroupUpdate)
        self.groupEntry.bind("<FocusOut>", self.handleGroupUpdate)

        self.staffCode = ""
        self.staffLabel = Tkinter.Label(self.main_window, text = "Staff")
        self.staffStringVar = Tkinter.StringVar()
        self.staffStringVar.set(self.staffCode)
        self.staffEntry = Tkinter.Entry( self.main_window,
                                         textvariable = self.staffStringVar,
                                         width = len("XXXXXX"))
        self.staffEntry.bind("<Return>", self.handleStaffUpdate)
        self.staffEntry.bind("<FocusOut>", self.handleStaffUpdate)

        self.clearButton = Tkinter.Button(self.main_window,
                                          text = "Clear Timetable",
                                          command = self.clearTimetable)

        self.yearView = YearView(self.main_window)
        self.createButton = Tkinter.Button(self.main_window,
                                           text = "Create Org Files",
                                           command = self.createOrgFiles)

        self.timetableView.grid(row = 0, column = 0, rowspan = 4)
        self.groupLabel.grid(row = 0, column = 1, sticky = "E")
        self.groupEntry.grid(row = 0, column = 2, sticky = "W")
        self.staffLabel.grid(row = 0, column = 3, sticky = "E")
        self.staffEntry.grid(row = 0, column = 4, sticky = "W")
        self.clearButton.grid(row = 1, column = 1, columnspan = 4)
        self.yearView.grid(row = 2, column = 1, columnspan = 4)
        self.createButton.grid(row = 3, column = 1, columnspan = 4)
        
        self.main_window.protocol("WM_DELETE_WINDOW", self.closeHandler)

    def start(self):
        self.loadPersistentData()
        self.main_window.mainloop()

    def loadPersistentData(self):
        try:
            f = open(self.configFilename, 'r')
        except IOError:
            f = None

        if f:
            try:
                self.persistent = pickle.load(f)
                if self.persistent.version != thisVersion:
                    self.persistent = PersistentData()
            except:
                self.persistent = PersistentData()
            f.close()
        else:
            self.persistent = PersistentData()
        self.staffCode = self.persistent.defaultStaffCode
        if not self.displayStaffTimetable():
            self.timetableView.displayTimetable( Timetable() )
        self.yearView.displayYear(self.persistent.year)

    def savePersistentData(self):
        self.persistent.defaultStaffCode = self.staffCode
        self.yearView.saveYear(self.persistent.year)
        self.saveStaffTimetable()
        try:
            f = open(self.configFilename, 'w')
        except IOError:
            f = None

        if f:
            pickle.dump(self.persistent, f)
        f.close()

    def handleGroupUpdate(self, event):
        group = self.groupStringVar.get().strip()
        self.timetableView.setGroup( group )

    def handleStaffUpdate(self, event):
        # save previous timetable
        self.saveStaffTimetable()
        self.staffCode = self.staffStringVar.get().strip()
        self.displayStaffTimetable()

    def clearTimetable(self):
        self.timetableView.clear()

    def saveStaffTimetable(self):
        prevTimetable = self.persistent.getTimetable( self.staffCode )
        self.timetableView.saveTimetable( prevTimetable )

    def displayStaffTimetable(self):
        self.staffStringVar.set(self.staffCode)
        # load anything saved for this staff code
        if self.persistent.hasTimetable( self.staffCode ):
            timetable = self.persistent.getTimetable( self.staffCode )
            self.timetableView.displayTimetable( timetable )
            return True
        else:
            return False

    def createOrgFiles(self):
        self.savePersistentData()
        gt = self.persistent.timetables[self.persistent.defaultStaffCode].createGroupedTimetable()
        gt.writeFiles(self.persistent.year)

    def closeHandler(self):
        self.savePersistentData()
        self.main_window.destroy()

app = Application()
app.start()
