#
# create manpages from the asciidoc files
#

SRC1 = melange.txt

MAN = $(SRC1:.txt=.1) $(SRC5:.txt=.5)
DISTFILES = $(addprefix ../,$(MAN))

all: $(MAN)

dist: $(DISTFILES)

clean:
	rm -fv $(MAN)

%.1 : %.xml
	xmlto man $<

%.5 : %.xml
	xmlto man $<

../%.1: %.1
	cp $< $@

../%.5: %.5
	cp $< $@

%.xml : %.txt
	asciidoc -b docbook -d manpage -o $@ $<
