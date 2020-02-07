PY=python3
BUILD_PKG_OPT=sdist

package: clean
	$(PY) setup.py $(BUILD_PKG_OPT)

release: package
	@twine upload dist/*

clean:
	git clean -fdX

.PHONY: clean