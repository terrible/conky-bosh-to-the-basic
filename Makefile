.PHONY: audit test benchmark doctor
OPT01_REF ?= $(HOME)/.local/share/bosh-opt01-audited/bosh-to-the-basic
audit:
	@set -eu; \
	for tool in bash python3 luac shellcheck; do \
	  if ! command -v "$$tool" >/dev/null 2>&1; then echo "SKIP audit: $$tool unavailable"; exit 0; fi; \
	done; \
	bash -n install.sh uninstall.sh bosh-to-the-basic/scripts/*.sh bosh-to-the-basic/startup/*.sh tools/*.sh || { echo "FAIL audit: Bash syntax"; exit 1; }; \
	shellcheck -x install.sh uninstall.sh bosh-to-the-basic/scripts/*.sh bosh-to-the-basic/startup/*.sh tools/*.sh || { echo "FAIL audit: ShellCheck"; exit 1; }; \
	echo "PASS audit: ShellCheck"; \
	PYTHONPYCACHEPREFIX=/tmp/bosh-pycache python3 -B -m py_compile bosh-to-the-basic/scripts/*.py installer/*.py resources/intel/*.py tools/*.py || { echo "FAIL audit: Python syntax"; exit 1; }; \
	luac -p bosh-to-the-basic/lua/bosh-to-the-basic.lua || { echo "FAIL audit: Lua syntax"; exit 1; }; \
	if command -v systemd-analyze >/dev/null 2>&1; then \
	  output=$$(mktemp /tmp/bosh-systemd-audit.XXXXXX); \
	  if systemd-analyze verify --man=no resources/intel/bosh-conky-intel.service >"$$output" 2>&1; then cat "$$output"; rm -f "$$output"; echo "PASS audit: systemd unit"; \
	  elif grep -q "Failed to turn off SO_PASSRIGHTS" "$$output" && grep -q "Failed to enable SO_PASSCRED" "$$output"; then cat "$$output"; rm -f "$$output"; echo "SKIP audit: sandbox blocks systemd credential sockets"; \
	  else cat "$$output"; rm -f "$$output"; echo "FAIL audit: systemd unit"; exit 1; fi; \
	else echo "SKIP audit: systemd-analyze unavailable"; fi; \
	echo "PASS audit: Bash, Python and Lua"
test:
	python3 -B -m unittest discover -s tests -v
benchmark:
	python3 -B tools/benchmark.py --mode synthetic --reference "$(OPT01_REF)"
doctor:
	@command -v conky >/dev/null 2>&1 && conky -v || echo "SKIP doctor: conky unavailable"
	@python3 --version || echo "SKIP doctor: python3 unavailable"
	@command -v shellcheck >/dev/null 2>&1 && shellcheck -x install.sh uninstall.sh bosh-to-the-basic/scripts/*.sh bosh-to-the-basic/startup/*.sh || echo "SKIP doctor: shellcheck unavailable"
