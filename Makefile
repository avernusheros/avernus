
clean:
	rm -rf build dist 
	-find . \( -name "*.py[oc]" -o -name "*.orig" \) -exec rm {} \;
.PHONY: clean

sdist:
	rm -rf dist/* build
	python setup.py --quiet sdist
	rm -rf *.egg-info
	rm MANIFEST
.PHONY: sdist


ppa:
	debuild -S -I.bzr
	dput ppa:avernus-heros/ppa <source.changes> 


