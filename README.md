# org-lesson-schedule

This is a graphical utility for generating a set of [org-mode](https://orgmode.org/) files for teachers' lesson plans.

One org file is generated for each class, and these are expected to be added to the agenda file list.  Then each day's agenda will show the teacher's schedule for that day.  Each lesson plan may be inserted into the org file under the level 2 heading for that date.

It is currently Python 2 only (sorry).

## Example

The following setup generates the files shown as excerpts below.

![Screenshot](doc/scheenshot.png)

### 9.org
```
** <2012-01-30 Mon 12:50>
** <2012-01-31 Tue 11:10>
** <2012-02-01 Wed 09:35>
** <2012-02-02 Thu 14:05>
** <2012-02-03 Fri 08:35>
<snip>
```

### 10.org
```
** <2012-01-30 Mon 09:35>
** <2012-01-31 Tue 08:35>
** <2012-02-01 Wed 12:50>
** <2012-02-02 Thu 08:35>
** <2012-02-03 Fri 11:10>
<snip>
```

### 11.org
```
** <2012-01-30 Mon 08:35>
** <2012-01-31 Tue 09:35>
** <2012-02-01 Wed 08:35>
** <2012-02-02 Thu 11:10>
** <2012-02-03 Fri 14:05>
<snip>
```

### 12.org
```
** <2012-01-30 Mon 14:05>
** <2012-01-31 Tue 14:05>
** <2012-02-01 Wed 14:05>
** <2012-02-02 Thu 12:50>
** <2012-02-03 Fri 09:35>
<snip>
```

### 13.org
```
** <2012-01-30 Mon 11:10>
** <2012-01-31 Tue 12:50>
** <2012-02-01 Wed 11:10>
** <2012-02-02 Thu 09:35>
** <2012-02-03 Fri 12:50>
<snip>
```

