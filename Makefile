PACKAGE_VERSION = 0
prefix = /usr

all:

clean:
	find . -name *.pyc | xargs rm -f
	rm -f fpemud-vm-builder

install:
	install -d -m 0755 "$(DESTDIR)/$(prefix)/bin"
	install -m 0755 fpemud-vm-builder "$(DESTDIR)/$(prefix)/bin"

	install -d -m 0755 "$(DESTDIR)/$(prefix)/lib/fpemud-vm-builder"
	cp -r lib/* "$(DESTDIR)/$(prefix)/lib/fpemud-vm-builder"
	find "$(DESTDIR)/$(prefix)/lib/fpemud-vm-builder" -type f -print0 | xargs -0 chmod 644
	find "$(DESTDIR)/$(prefix)/lib/fpemud-vm-builder" -type d -print0 | xargs -0 chmod 755

	install -d -m 0755 "$(DESTDIR)/opt/fpemud-vm-builder"
	cp -r data/* "$(DESTDIR)/opt/fpemud-vm-builder"
	find "$(DESTDIR)/opt/fpemud-vm-builder" -type f -print0 | xargs -0 chmod 644
	find "$(DESTDIR)/opt/fpemud-vm-builder" -type d -print0 | xargs -0 chmod 755

uninstall:
	rm -Rf "$(DESTDIR)/$(prefix)/bin/fpemud-vm-builder"
	rm -Rf "$(DESTDIR)/$(prefix)/lib/fpemud-vm-builder"
	rm -Rf "$(DESTDIR)/$(prefix)/share/fpemud-vm-builder"

.PHONY: all clean install uninstall
