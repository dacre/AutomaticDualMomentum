#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

# this script checks which fund is best to hold for the coming month according to Antonacci's dual momentum theory
# get percentage YTD for global, local and risk free interest

import argparse
import csv
import time
from bs4 import BeautifulSoup
import urllib2

local_fund_ticker = "0P0000J1JM"
local_fund_name = "Länsförsäkringar Sverige Indexnära"

global_fund_ticker = "0P0000YVZ3"
global_fund_name = "Länsförsäkringar Global Indexnära"

risk_free_interest_fund_ticker = "0P00009NT9"
risk_free_interest_fund_name = "Spiltan Räntefond Sverige"

morningstar_base_url = "http://performance.morningstar.com/Performance/cef/trailing-total-returns.action?t="

use_database_file = False
cli_selected = False
email_selected = False

database_filename = ""
from_email = ""
from_email_password = ""
to_email = ""


def get_12_month_gain(fund_ticker):
    try:
        html = urllib2.urlopen(morningstar_base_url + fund_ticker).read()
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {"class": "r_table3 width955px print97"})
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        for row in rows:
            if row.th.string.encode('utf-8').find('NAV'):
                tds = table_body.find_all('td')
                return unicode(tds[5].string)
    except urllib2.URLError as e:
        raise LookupError("Could not find the fund data when looking for fund ticker: " + fund_ticker +
                          " \r\n Detailed issue: " + e.args[0].strerror)
    except Exception as e:
        raise LookupError("Could not find the fund data when looking for fund ticker: " + fund_ticker +
                          " \r\n Detailed issue: " + e.message)


def create_body(winner, losers, previous_winner):
    previous_winner_text = ""
    if previous_winner is not "" and winner[1] != previous_winner:
        previous_winner_text = "\r\nFöregående vinnare var " + previous_winner + "."
    if winner[1] == previous_winner:
        first_line = "\r\n\r\nSamma fond (" + previous_winner + ") vann även denna månad, med " \
                     + str(winner[0]) + "% utveckling"
    else:
        first_line = "\r\nJust nu är det bäst att investera i " + winner[1] + \
                     " som har haft " + str(winner[0]) + "% utveckling de senaste 12 månaderna."

    result = "Hej!" + first_line + ('{previous_winner}\n'
                                    '\rDe andra alternativen är {loser1_name} med {loser1_result}% utveckling '
                                    'och {loser2_name} med {loser2_result}% utveckling. \r\n\r\nLycka till!').format(
                                        previous_winner=previous_winner_text,
                                        loser1_name=losers[0][1],
                                        loser1_result=str(losers[0][0]),
                                        loser2_name=losers[1][1],
                                        loser2_result=str(losers[1][0]),)
    return result


def send_email(subject, email_body):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(email_body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, from_email_password)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()


def lookup_winner():
    local_fund_12_month_gain = get_12_month_gain(local_fund_ticker)
    global_fund_12_month_gain = get_12_month_gain(global_fund_ticker)
    risk_free_interest_fund_12_month_gain = get_12_month_gain(risk_free_interest_fund_ticker)

    global_fund_tuple = (float(global_fund_12_month_gain), global_fund_name)
    local_fund_tuple = (float(local_fund_12_month_gain), local_fund_name)
    risk_free_fund_tuple = (float(risk_free_interest_fund_12_month_gain), risk_free_interest_fund_name)

    if global_fund_tuple[0] > local_fund_tuple[0]:
        if global_fund_tuple[0] > risk_free_fund_tuple[0]:
            winner = global_fund_tuple
            losers = (risk_free_fund_tuple, local_fund_tuple)
        else:
            winner = risk_free_fund_tuple
            losers = (global_fund_tuple, local_fund_tuple)
    else:
        if local_fund_tuple[0] > risk_free_fund_tuple[0]:
            winner = local_fund_tuple
            losers = (global_fund_tuple, risk_free_fund_tuple)
        else:
            winner = risk_free_fund_tuple
            losers = (global_fund_tuple, local_fund_tuple)

    return winner, losers


def get_previous_winner():
    last_row = ""
    if use_database_file is True:
        with open(database_filename, 'rb') as csv_file:
            db_reader = csv.DictReader(csv_file)
            for row in db_reader:
                last_row = row.values()[1]
    return last_row


def store_winner(winner):
    if use_database_file is True:
        with open(database_filename, 'a+') as csv_file:
            fieldnames = ['date', 'fund_name']
            db_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            db_writer.writerow({'date': time.strftime("%Y-%m-%d"), 'fund_name': winner})


def main():
    setup_input_arguments()

    try:
        result = lookup_winner()
        winner = result[0]
        losers = result[1]

    except LookupError as le:
        print ("Lookup error", le.message)
        if email_selected:
            send_email("Lookup error", le.message)
        else:
            print le.message
    else:
        previous_winner = get_previous_winner()
        store_winner(winner[1])
        body = create_body(winner, losers, previous_winner)
        if email_selected:
            send_email("Bästa fonden för den kommande månaden!", body)
        else:
            print "Best fund: {}. It returned: {:.2f}%".format(winner[1], winner[0])


def setup_input_arguments():
    parser = argparse.ArgumentParser(description='Automatic Dual Momentum (Fund Portfolio Suggestions).')
    parser.add_argument('--cli', help='Outputs results to console. Cannot be selected at the same time as email',
                        action='store_true')
    parser.add_argument('--email', help='Outputs results to email. '
                                        'Cannot be selected at the same time as cli. Requires further arguments:'
                                        'from_email, from_email_password, to_email.',
                        nargs=3, metavar=('from_email', 'from_email_password', 'to_email'))
    parser.add_argument('--db', help='Enables use of file based database to store winners. '
                                     'Requires further argument: file name', nargs=1, metavar='file_name')
    args = parser.parse_args()

    if args.cli is True:
        global cli_selected
        cli_selected = True
    if args.email is not None:
        global email_selected
        email_selected = True
        global from_email
        from_email = args.email[0]
        global from_email_password
        from_email_password = args.email[1]
        global to_email
        to_email = args.email[2]
    if args.db is not None:
        global use_database_file
        use_database_file = True
        global database_filename
        database_filename = args.db[0]


if __name__ == "__main__":
    main()
