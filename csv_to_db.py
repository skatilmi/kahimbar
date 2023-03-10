import pandas as pd
import sqlite3
import glob


def main(csv_location):
    df = pd.read_csv(csv_location, header=None, comment="#")
    df.columns = ["id", "username", "password", "email", "balance", "rating"]
    # delete rating column
    df.drop("rating", axis=1, inplace=True)
    # change balance to negative and make it in units of EUR
    df["balance"] = -df["balance"].values.astype(float)/100
    # add is_admin column
    df["is_admin"] = [False for _ in range(len(df))]
    # edit user with id=1 (oliver) to be admin
    df.loc[0, "is_admin"] = 1

    # save to db
    db_loc = "instance/database.sqlite3"
    conn = sqlite3.connect(db_loc)
    conn.execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT, balance REAL, is_admin INTEGER)")
    for user_id, username, password, email, balance, is_admin in df.values:
        conn.execute("INSERT INTO user (id, username, password, email, balance, is_admin) VALUES (?, ?, ?, ?, ?, ?)",
                     (user_id, username, password, email, balance, is_admin))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    csv_locations = glob.glob("*.csv")
    print("Found the following csv files:")
    for i, csv_location in enumerate(csv_locations):
        print(f"{i+1}. {csv_location}")
    csv_location = csv_locations[int(input("Enter the number of the csv file you want to convert: "))-1]
    main(csv_location)
