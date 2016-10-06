FARAD_Tutorial
==============

GIT tutorial and code for summer students working with the FARAD "SuperWiFi" equipment. This repository contains flash images and instructions for programming WARPv3 + WURC nodes. For more information about the equipment, please see: www.skylarkwireless.com/WURC

Usage Notes
==========
1. I recommend that you clone this repo to your local C:/ directory on Windows machines. Windows has issues with longer filepaths.

2. Note the .gitignore files within the main repo folders: these have been customized to keep the master repo clean of build files and unnecessary junk. They're currently under development, as I'm not sure that I have targeted all the necessary files for tracking yet. Any questions/comments, please email me@ryaneguerra.com


Using git
==========
I plan to update this as I learn more. The idea is that you should be able to clone
this repository locally to your computer. This makes a copy that you own, can make
changes, develop, etc... The .gitignore files should be set up so that you can build
and develops all the included modules and they'll still be clean when they get committed.

Note that since git is a distributed versioning system, this means that when you commit,
you actually commit to your LOCAL repo. To update the master branch on GitHub, you need to
push your branch to the remote MASTER branch.

A typical session looks like the following, assuming the remote (GitHub) has been properly
set up and you open a git terminal within your local repository. You can do that by right-clicking
on the repo as it appears in your GitHub gui and selecting "open a shell here."

Add files to revision control.
**$ git add .**

Check recent changes and modified files/folders for the current repo.
**$ git status**

Commit changes to local repository. You will get a popup with a list of changes to commit and
space to enter your commit notes. You should always put something short there--it will help
identify your revisions later. Save the commit file and close it--your commit will happen
automatically unless you declined to add a comment.
**$ git commit**

Push your changes to the remote master repository on GitHub. Keep in mind that this will change
the master repository for everyone. You can never "break" anything since we can always roll back
to an earlier revision, but if you want to keep personal copies of the files with project-specific
changes, you should set up your own remote with your own GitHub account. If that's the case, then
re-name the branch of the repository so that we can always merge the MASTER and your copy in
the future.
**$ git push origin master**

For more details, take a look at: https://help.github.com/


Quince SuperWiFi Coverage
==============
Example code for wardriving and parsing. This code simply recovers and plots RSSI values (visualization
of the map was done with an online tool), whereas you will probably want to generate and process richer
data sets.

There is some example code with how to use GPSD with USB GPS puck, but it's really first-pass stuff.


WARPv3_Images
===============
A number of bin images for WARPv3 SD cards. Right now 2.4 GHz 80211 images are here, but we will update with
UHF 80211 images later. Right now, you should be able to develop your scripts and test at
2.4 GHz, no problem. The wireless bridge will look no different from the persective of your transmitter and 
receiver computers.

Computer 1 <--> 2.4 GHz WARP <--> 2.4 GHz WARP <--> Computer 2

Computer 1 <--> UHF WARP <--> UHF WARP <--> Computer 2

Python
===============
Contains WSDNode code for easily interacting with a white space daughtercard or WARP board programmed
with the white space 80211 design.

Also contains early Alpha version of the WARPNet transport framework. This is very, very Alpha.
