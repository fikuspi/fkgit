install:
	cp fkgit.py /usr/bin/fkgit
	chmod +x /usr/bin/fkgit
	cp fkgit.desktop /usr/share/applications/fkgit.desktop

uninstall:
	rm -f /usr/bin/fkgit
	rm -f /usr/share/applications/fkgit.desktop
