# KaHIMBar
## how to use
if available, place csv file with columns `id`, `name`, `password`, `email`, `balance` , `rating` in the same directory as `app.py`.
If no csv file is provided, edit the `is_admin` attribute of the admin(s) in the database to `1` after registration.

if no csv file is provided:
```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ python3 -m pip install -r requirements.txt
$ python3 app.py
```
else:
```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ python3 -m pip install -r requirements.txt
$ python3 csv_to_db.py
$ python3 app.py
```
Edit rewards for deep cleaning and for cleaning the foam system in `config.toml`
    