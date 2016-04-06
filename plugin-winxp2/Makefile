PACKAGE_VERSION = 0
prefix = /usr

all:

clean:

install:
	install -d -m 0755 "$(DESTDIR)/$(prefix)/lib/windows-virtmanager/plugins/winxp"
	cp -r src/* "$(DESTDIR)/$(prefix)/lib/windows-virtmanager/plugins/winxp"
	chmod 644 "$(DESTDIR)/$(prefix)/lib/windows-virtmanager/plugins/winxp"/*

	install -d -m 0755 "$(DESTDIR)/opt/windows-virtmanager/plugins/winxp"
	cp -r data/* "$(DESTDIR)/opt/windows-virtmanager/plugins/winxp"
	chmod 644 "$(DESTDIR)/opt/windows-virtmanager/plugins/winxp"/*

uninstall:
	rm -Rf "$(DESTDIR)/$(prefix)/lib/windows-virtmanager/plugins/winxp"
	rm -Rf "$(DESTDIR)/opt/windows-virtmanager/plugins/winxp"

.PHONY: all clean install uninstall
