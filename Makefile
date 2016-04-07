PACKAGE_VERSION = 0
prefix = /usr

all:

clean:
	find . -name *.pyc | xargs rm -f
	rm -f fpemud-vmake

install:
	install -d -m 0755 "$(DESTDIR)/$(prefix)/bin"
	install -m 0755 fpemud-vmake "$(DESTDIR)/$(prefix)/bin"

	install -d -m 0755 "$(DESTDIR)/$(prefix)/lib/fpemud-vmake"
	cp -r lib/* "$(DESTDIR)/$(prefix)/lib/fpemud-vmake"
	cp -r plugin-* "$(DESTDIR)/$(prefix)/lib/fpemud-vmake"
	find "$(DESTDIR)/$(prefix)/lib/fpemud-vmake" -type f -print0 | xargs -0 chmod 644
	find "$(DESTDIR)/$(prefix)/lib/fpemud-vmake" -type d -print0 | xargs -0 chmod 755

uninstall:
	rm -Rf "$(DESTDIR)/$(prefix)/bin/fpemud-vmake"
	rm -Rf "$(DESTDIR)/$(prefix)/lib/fpemud-vmake"

.PHONY: all clean install uninstall
