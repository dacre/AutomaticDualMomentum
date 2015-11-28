#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# -*- coding: utf-8 -*-

# this script checks which fund is best to hold for the coming month according to Antonaccis dual momentum theory

# get percentage YTD for global, local and risk free interst
local_fund_ticker = "0P00000FYQ"
local_fund_name =  "SPP Aktiefond Sverige A (NAV)"

global_fund_ticker = "0P00000LST"
global_fund_name = "SPP Aktiefond Global A (NAV)"

risk_free_interest_fund_ticker = "0P00009NT9"
risk_free_interest_fund_name = "Spiltan Räntefond Sverige (NAV)"

# select the best
morningstar_base_url = "http://performance.morningstar.com/Performance/cef/trailing-total-returns.action?t="


def get_12_month_gain(fund_ticker, fund_name):
    from bs4 import BeautifulSoup
    import urllib2
    
    html = urllib2.urlopen(morningstar_base_url + fund_ticker).read()
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', {"class" : "r_table3 width955px print97"})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        if row.th.string.encode('utf-8') == fund_name:
            tds = table_body.find_all('td')
            return unicode(tds[6].string)
    raise LookupError("Could not find the fund data when looking for fund: " + fund_name)
    
local_fund_12_month_gain = get_12_month_gain(local_fund_ticker, local_fund_name)
global_fund_12_month_gain = get_12_month_gain(global_fund_ticker, global_fund_name)
risk_free_interest_fund_12_month_gain = get_12_month_gain(risk_free_interest_fund_ticker, risk_free_interest_fund_name)

global_fund_tuple = (float(global_fund_12_month_gain), global_fund_name);
local_fund_tuple = (float(local_fund_12_month_gain), local_fund_name);
risk_free_fund_tuple = (float(risk_free_interest_fund_12_month_gain), risk_free_interest_fund_name);

if(global_fund_tuple[0] > local_fund_tuple[0]):
    if(global_fund_tuple[0] > risk_free_fund_tuple[0]):
        winner = global_fund_tuple
        losers = (risk_free_fund_tuple, local_fund_tuple);
    else:
        winner = risk_free_fund_tuple
        losers = (global_fund_tuple, local_fund_tuple);        
else:
    if(local_fund_tuple[0] > risk_free_fund_tuple[0]):
        winner = local_fund_tuple
        losers = (global_fund_tuple, risk_free_fund_tuple);        
    else:
        winner = risk_free_fund_tuple
        losers = (global_fund_tuple, local_fund_tuple);        
print "winner: " + winner[1] + ". With increase of: " + str(winner[0])




# send email with decision to list of email adresses
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
 
import sys

fromaddr = sys.argv[1]
toaddr = sys.argv[3]
msg = MIMEMultipart()
msg['From'] = fromaddr
msg['To'] = toaddr
msg['Subject'] = "Bästa fonden för den kommande månaden!"
 
body = """Hej! \r\nJust nu är det bäst att investera i """ + winner[1] + """ som har haft """ + str(winner[0]) + """% utveckling de senaste 12 månaderna. \r\n
De andra alternativen är """ + losers[0][1] + """ med """ + str(losers[0][0]) + """% utveckling och """ + losers[1][1] + """ med """ + str(losers[1][0]) + """% utveckling. \r\n Lycka till!"""

print body
msg.attach(MIMEText(body, 'plain'))
 
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(fromaddr, sys.argv[2])
text = msg.as_string()
server.sendmail(fromaddr, toaddr, text)
server.quit()
