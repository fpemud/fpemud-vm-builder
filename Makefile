PACKAGE_VERSION = 0
prefix = /usr

all:

clean:
	find . -name *.pyc | xargs rm -f
	rm -f fpemud-vmaker

install:
	install -d -m 0755 "$(DESTDIR)/$(prefix)/bin"
	install -m 0755 fpemud-vmaker "$(DESTDIR)/$(prefix)/bin"

	install -d -m 0755 "$(DESTDIR)/$(prefix)/lib/fpemud-vmaker"
	cp -r lib/* "$(DESTDIR)/$(prefix)/lib/fpemud-vmaker"
	find "$(DESTDIR)/$(prefix)/lib/fpemud-vmaker" -type f -print0 | xargs -0 chmod 644
	find "$(DESTDIR)/$(prefix)/lib/fpemud-vmaker" -type d -print0 | xargs -0 chmod 755

	install -d -m 0755 "$(DESTDIR)/opt/fpemud-vmaker"
	cp -r data/* "$(DESTDIR)/opt/fpemud-vmaker"
	find "$(DESTDIR)/opt/fpemud-vmaker" -type f -print0 | xargs -0 chmod 644
	find "$(DESTDIR)/opt/fpemud-vmaker" -type d -print0 | xargs -0 chmod 755

uninstall:
	rm -Rf "$(DESTDIR)/$(prefix)/bin/fpemud-vmaker"
	rm -Rf "$(DESTDIR)/$(prefix)/lib/fpemud-vmaker"
	rm -Rf "$(DESTDIR)/$(prefix)/share/fpemud-vmaker"

.PHONY: all clean install uninstall
