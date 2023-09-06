=========
Changelog
=========

Version 0.2
===========

- Add caompatibility to run on Fram and Betzy
- Fix unit bug. "10 GiB" > "5 TiB" is now False as expected

Version 0.1
===========

- Add first version of motd_quota_warn.py
- Runs on Saga
- Known bug: Scritp doesn't understand units, so "10 GiB" > "5 TiB" is True at the moment
