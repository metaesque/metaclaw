WORKSPACE.files: .FORCE
	cd ..; find ../workspace/agents -name '*.md' -o -name '*.yaml' | sort > docs/WORKSPACE.files

txt: ../tmp/workspace.txt
../tmp/workspace.txt: WORKSPACE.files
	cd ..; bin/.venv/bin/python bin/newcode.py --setup=docs/WORKSPACE.files > tmp/workspace.txt

.FORCE:

