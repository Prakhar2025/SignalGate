# SignalGate - canonical command surface (docs/10-reproduction.md)
# Windows without make: see README "Windows note" for python -m equivalents.
PY ?= python3

.PHONY: install data baseline agent eval eval-holdout ablation digest serve demo-live \
        test test-fast lint repro-check docker-build clean

install:            ## sync exact deps from lock, then install the package
	$(PY) -m pip install -r requirements-lock.txt
	$(PY) -m pip install -e . --no-deps

data:               ## seeded synthetic market + 60 cases (seed=20260828)
	$(PY) -m generator.build --out data

baseline:           ## static lint over the dev split -> artifacts/baseline/
	$(PY) -m signalgate.eval.run --system baseline --split dev --out artifacts/baseline

agent:              ## agent solution; auto-falls back to LOCAL_MOCK without keys
	$(PY) -m signalgate.eval.run --system agent --split dev --out artifacts/agent

eval:               ## score both, print comparison table + CIs, run regression gate
	$(PY) -m signalgate.eval.score --baseline artifacts/baseline --agent artifacts/agent --out reports
	$(PY) -m signalgate.eval.regression --metrics reports/metrics.json

eval-holdout:       ## sealed split - opened once at final gate (docs/07 §2)
	$(PY) -m signalgate.eval.run --system both --split holdout --out artifacts/holdout
	$(PY) -m signalgate.eval.score --baseline artifacts/holdout/baseline --agent artifacts/holdout/agent --out reports --suffix holdout

ablation:           ## runs the 07 §9 stages for IMPROVEMENT_CHANGELOG.md
	$(PY) -m signalgate.eval.ablation --split dev --out reports

digest:             ## quiet-pipeline digest artifact (product spec J2)
	$(PY) -m signalgate.digest --from artifacts --out reports/digest.md

serve:              ## web gate at http://localhost:8000 (LOCAL_MOCK, zero keys)
	$(PY) -m uvicorn signalgate.api.app:app --host 127.0.0.1 --port 8000

demo-live:          ## LIVE mode; requires SIGNALGATE_* env (optional)
	SIGNALGATE_MODE=live $(PY) -m uvicorn signalgate.api.app:app --host 0.0.0.0 --port 8000

test:               ## full suite including slow end-to-end tests
	$(PY) -m pytest -m ""

test-fast:          ## default fast suite
	$(PY) -m pytest

lint:
	$(PY) -m ruff check src generator tests scripts

repro-check:        ## eval twice on a small fixture; metrics must be byte-identical
	$(PY) -m signalgate.eval.repro

docker-build:
	docker build -t signalgate .

clean:
	rm -rf artifacts data .pytest_cache .ruff_cache
