# bugfarmcc

A small real-estate site with deliberate defects. The browser worker and the
auditors are tested against it; every planted defect is listed in
`defects.json` so detection can be measured.

`/account.html` and `/account-saved.html` are only served with the session
cookie set by `POST /session` (`demo@bugfarm.test` / `correct-horse`); the test
server in `apps/worker/tests/conftest.py` implements that part.
