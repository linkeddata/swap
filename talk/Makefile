################
# W3C slide maker

# MAIN MAKEFILE 



####
PERL=perl
BURSTOPTS=
BURST=../../../../Talks/Tools/w3cburst.pl $(BURSTOPTS)
ARCH="UNIX"

.PHONY: mirror

all: Overview.html

clean: 
	-rm -f slide*.htm* Overview*.htm*

Overview.html: all.htm infos.txt Makefile
	$(PERL) $(BURST) cssStandardFiles=$(STYLE_SHEET) talkTitle=$(TITLE) author=$(AUTHOR) authorUrl=$(AUTHOR_URL) author2=$(AUTHOR2) authorUrl2=$(AUTHOR_URL2) logoFile=$(LOGO) arch=$(ARCH)

infos.txt:
	echo '#---------------------------------------------'		>>$@
	echo '# Slidemaker Tool Parameters'				>>$@
	echo '#---------------------------------------------'		>>$@
	echo '# Check YYMMsub/Overview.html for documentation '		>>$@
	echo '#'							>>$@
	echo ''								>>$@
	echo 'talkTitle	= W3C Slidemaker Tool'				>>$@
	echo 'author		= Stephan Montigaud, Pierre Fillault'	>>$@
	echo 'authorUrl	= mailto:webreq@w3.org'				>>$@
	echo ''								>>$@
	echo '# If there are 2 authors, you can add:'			>>$@
	echo '#author2	= First Last'					>>$@
	echo '#author2Url	= mailto:last@w3.org'			>>$@
	echo ''								>>$@
	echo '# Uncomment and change these if needed:'			>>$@
	echo '#logoFile	= ../Icons/w3c_home.gif'			>>$@
	echo '#logoLink	= http://www.w3.org/'				>>$@
	echo '#logoAlt	= W3C'						>>$@
	echo ''								>>$@
	echo '# Set this for an extra logo & link in the footer'	>>$@
	echo '#logoFile2	= extra-logo.gif'			>>$@
	echo '#logoLink2	= http://www.w3.org/Somewhere'		>>$@
	echo '#logoAlt2	= SomeAltText'					>>$@
	echo ''								>>$@
	echo '# Standard style sheets are usually not changed'		>>$@
	echo 'cssStandardFiles = ../Tools/w3ctalk-640w.css,../Tools/w3ctalk-800w.css,../Tools/w3ctalk-1024w.css,../Tools/w3ctalk-640.css,../Tools/w3ctalk-800.css,../Tools/w3ctalk-1024.css'	>>$@
	echo ''								>>$@
	echo '# With cssUserFiles you overload the standard css files;'	>>$@
	echo '# this can be one file or a list of files'		>>$@
	echo '#cssUserFiles = '						>>$@
	echo ''								>>$@
	echo '# Uncomment and change language and charset if needed'	>>$@
	echo '#baselang	= en-US'					>>$@
	echo '#charset	= ISO-8859-1'					>>$@
	echo ''								>>$@
	echo '# Uncomment and change access keys if needed'		>>$@
	echo '#prevKey	= P'						>>$@
	echo '#nextKey	= N'						>>$@
	echo '#tocKey	= C'						>>$@
	echo '#styleKey	= S'						>>$@
	echo "Please edit" $@ >&2

mirror: Overview.html
	mirror2team.pl -l *

