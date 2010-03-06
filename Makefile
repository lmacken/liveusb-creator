PKGNAME=liveusb-creator
PKGRPMFLAGS=--define "_topdir ${PWD}" --define "_specdir ${PWD}" --define "_sourcedir ${PWD}/dist" --define "_srcrpmdir ${PWD}" --define "_rpmdir ${PWD}" --define "_builddir ${PWD}"

dist:
	python setup.py sdist --format=bztar

srpm: dist
	@rpmbuild -bs ${PKGRPMFLAGS} ${PKGNAME}.spec

rpm: dist
	cp dist/* ~/rpmbuild/SOURCES/
	cp *.spec ~/rpmbuild/SPECS/
	rpmbuild -ba ~/rpmbuild/SPECS/liveusb-creator.spec

gui:
	pyrcc4 data/resources.qrc -o liveusb/resources_rc.py
	pyuic4 data/liveusb-creator.ui -o liveusb/windows_dialog.py
	pyuic4 data/liveusb-creator-linux.ui -o liveusb/linux_dialog.py

pyflakes:
	pyflakes liveusb/*.py

pylint:
	pylint liveusb/*.py

pot:
	cd po; python mki18n.py -v --domain=liveusb-creator -p
	#cd po ; intltool-update --pot -g liveusb-creator

mo:
	cd po; for po in `ls *.po`; do cp $$po liveusb-creator_$$po; done
	cd po; python mki18n.py -v --domain=liveusb-creator -m
	rm po/liveusb-creator_*.po*

clean:
	rm -f *.py{c,o} */*.py{c,o} */*/*.py{c,o}
	rm -fr po/${PKGNAME}*.po{,.new} po/locale
	rm -fr build

docs:
		epydoc --name liveusb-creator -u http://liveusb-creator.fedorahosted.org -o docs --exclude urlgrabber liveusb


everything:
	python setup.py  sdist --format=bztar
	rm -f ~/rpmbuild/RPMS/noarch/liveusb-creator*.rpm
	make clean rpm
	sudo rpm -e liveusb-creator
	sudo rpm -Uvh ~/rpmbuild/RPMS/noarch/liveusb-creator*.rpm
	sudo /usr/bin/liveusb-creator -v
