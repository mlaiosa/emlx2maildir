#/usr/bin/env python

import xml.sax, xml.sax.handler
import sys, os, socket, time

class PlistHandler(xml.sax.handler.ContentHandler):
	def __init__(self):
		xml.sax.handler.ContentHandler.__init__(self)
		self.key = None
		def set_top(k,v):
			self.top = v
		self.stack = [set_top]
	def generate(self, value):
		self.stack[-1](self.key, value)
	def startElement(self, name, attrs):
		self.elem = name
		self.value = ""
		if name == "array":
			ar = []
			self.stack.append(ar)
			self.stack.append(lambda k,v: ar.append(v))
		elif name == "dict":
			d = {}
			def add(k, v):
				d[k] = v
			self.stack.append(d)
			self.stack.append(add)
	def endElement(self, name):
		if name == "string":
			self.generate(self.value)
		elif name == "integer":
			self.generate(long(self.value))
		elif name == "real":
			self.generate(float(self.value))
		elif name == "key":
			self.key = self.value
		elif name in ("dict", "array"):
			x = self.stack[-2]
			self.stack = self.stack[:-2]
			self.generate(x)
		elif name in ("plist", "data"):
			pass
		else:
			print "Unknown tag: %s" % name
	def characters(self, chars):
		self.value += chars

def parse_plist(plist_xml):
	p = PlistHandler()
	xml.sax.parseString(plist_xml, p)
	return p.top

FL_READ = (1<<0)
FL_DELETED = (1<<1)
FL_ANSWERED = (1<<2)
FL_ENCRYPTED = (1<<3)
FL_FLAGGED = (1<<4)
FL_RECENT = (1<<5)
FL_DRAFT = (1<<6)
FL_INITIAL = (1<<7)
FL_FORWARDED = (1<<8)
FL_REDIRECTED = (1<<9)
FL_SIGNED = (1<<23)
FL_IS_JUNK = (1<<24)
FL_IS_NOT_JUNK = (1<<25)
FL_JUNK_LEVEL_RECORDED = (1<<29)
FL_HIGHLIGHT_IN_TOC = (1<<30)

flag_mapping = [
	(FL_DRAFT, "D"),
	(FL_FLAGGED, "F"),
	((FL_FORWARDED | FL_REDIRECTED), "P"),
	(FL_ANSWERED, "R"),
	(FL_READ, "S"),
	(FL_DELETED, "T"),
]

hostname = socket.gethostname()
pid = os.getpid()
gSeq = 0

def md_filename(date, flags):
	global gSeq
	gSeq += 1
	return "%d.M%dP%dQ%d.%s:2,%s" % (date, time.time(), pid, gSeq, hostname, flags)

def convert_one(emlx_file, maildir):
	contents = open(emlx_file, "rb").read()
	boundry = contents.find("\x0a")
	length = long(contents[:boundry])
	body = contents[boundry+1:boundry+1+length]
	metadata = parse_plist(contents[boundry+1+length:])

	flags = ""
	if "flags" in metadata:
		for fl, let in flag_mapping:
			if metadata['flags'] & fl:
				flags += let

	date = long(metadata.get('date-sent', time.time()))
	filename = md_filename(date, flags)
	open(os.path.join(maildir, "tmp", filename), "wb").write(body)
	os.rename(os.path.join(maildir, "tmp", filename), os.path.join(maildir, "new", filename))

def main():
	if len(sys.argv) != 3:
		print "Usage: emlx2maildir emlx_folder maildir"
		sys.exit(1)
	emlx_dir, maildir = sys.argv[1:3]

if __name__ == "__main__":
	#print parse_plist(open("/tmp/x.plist").read())
	convert_one("/tmp/emlx2maildir/../Mail/Mailboxes/Downieville.mbox/Messages/60419.emlx", "/tmp/md")
	#main()
