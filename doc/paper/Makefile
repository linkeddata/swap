W=$(HOME)/w3ccvs/WWW
# http://www.w3.org/2004/04/xhlt91/
XHLT=$(W)/2004/04/xhlt91


DOC=index
BIB=index
STATUS=draf

#ftp://ftp.cup.cam.ac.uk/pub/texarchive/journals/latex/tlp-cls/
TPLP=$(HOME)/src/TPLP
TEXINPUTS=.:$(TPLP):
BSTINPUTS=.:$(TPLP):

HLPARAMS=--stringparam Bib $(BIB) \
		--stringparam Status $(STATUS) \

include $(XHLT)/html2latex.mak

$(DOC).pdf: $(DOC).aux $(DOC).bbl

$(DOC).aux: $(DOC).tex

$(DOC).tex: $(DOC).html $(XHLT)/xh2latex.xsl

$(DOC).bib: $(DOC).html $(XHLT)/xh2bib.xsl

$(DOC).bbl: $(DOC).tex $(DOC).bib

clean:
	$(RM) $(DOC).{pdf,tex,tex_,aux,log,bbl} $(BIB).bib
