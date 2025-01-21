install:
	mkdir -p $(HOME)/.fk
	cp fkgit.py $(HOME)/.fk/fkgit.py
	chmod +x $(HOME)/.fk/fkgit.py
	cp fkgit /usr/bin/fkgit
	chmod +x /usr/bin/fkgit
	cp fkgit.desktop /usr/share/applications/fkgit.desktop

uninstall:
	rm -rf $(HOME)/.fk
	rm -f /usr/bin/fkgit
	rm -f /usr/share/applications/fkgit.desktop
