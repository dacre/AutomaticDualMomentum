#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

# this script checks which fund is best to hold for the coming month according to Antonacci's dual momentum theory
# get percentage YTD for global, local and risk free interest


import sys

local_fund_ticker = "0P0000J1JM"
local_fund_name = "Länsförsäkringar Sverige Indexnära"

global_fund_ticker = "0P0000YVZ3"
global_fund_name = "Länsförsäkringar Global Indexnära"

risk_free_interest_fund_ticker = "0P00009NT9"
risk_free_interest_fund_name = "Spiltan Räntefond Sverige"

morningstar_base_url = "http://performance.morningstar.com/Performance/cef/trailing-total-returns.action?t="


def get_12_month_gain(fund_ticker):
    from bs4 import BeautifulSoup
    import urllib2

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


def create_body(winner, losers):
    result = """Hej!
            \r\nJust nu är det bäst att investera i {winner1_name} som har haft {winner1_result}% utveckling de senaste 12 månaderna.
            \rDe andra alternativen är {loser1_name} med {loser1_result}% utveckling och {loser2_name} med {loser2_result}% utveckling.
            \r\nLycka till!""".format(
        winner1_name=winner[1],
        winner1_result=str(winner[0]),
        loser1_name=losers[0][1],
        loser1_result=str(losers[0][0]),
        loser2_name=losers[1][1],
        loser2_result=str(losers[1][0]),
    )
    return result


def send_email(subject, email_body):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    fromaddr = sys.argv[1]
    toaddr = sys.argv[3]
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject
    msg.attach(MIMEText(email_body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, sys.argv[2])
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
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

    return(winner, losers)


def main():
    print "Analyzing which fund had best return for previous 12 months..."

    try:
        result = lookup_winner()
        winner = result[0]
        losers = result[1]

    except LookupError as le:
        print ("Lookup error", le.message)
        if len(sys.argv) != 4:
            print le.message
        else:
            send_email("Lookup error", le.message)
    else:
        w1 = winner[1].decode('ISO-8859-1').encode("utf-8")
        w2 = str(winner[0]).decode('ISO-8859-1').encode("utf-8")
        print "Best fund: {0}. It returned: {1}%".format(w1, w2)

        body = create_body(winner, losers)
        if len(sys.argv) == 2 and sys.argv[1] == "cli":
            print "\r\nThe complete message that would have been sent:"
            print "-----"
            utf_ok_body = body.decode('ISO-8859-1').encode("utf-8")
            print utf_ok_body
            print "-----"
        elif len(sys.argv) != 4:
            print """No command line arguments supplied.
            (Looking for: From Email,
            From Email Password, To Email)"""
        else:
            send_email("Bästa fonden för den kommande månaden!", body)


if __name__ == "__main__":
    main()
