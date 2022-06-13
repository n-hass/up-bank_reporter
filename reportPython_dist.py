from datetime import datetime, timezone
import datetime
from dateutil.parser import parse
import time
import requests
import json
import csv
import os
import sys

def validLogical(message):
                ##      Booleon input function      ##
    # This simple function attempts to gain a yes or no input form user and
    # returns a true or false bool once a valid input has been attained.
    #
    # This function rejects other inputs, classifies 'y', 'Y', 'yes' and 'Yes'
    # as a true booleon & 'n', 'N', 'no' and 'No' as false.
    #
    # 1 funtion parameter, takes in a string which will print with every
    # prompt, this is your message which will be displayed to user.
    #
    # Function is used only to return a value, use to assign a booleon to
    # a variable in main program.

    test = input(message + " (y/n): ")
    if test == 'y' or test == 'Y' or test == 'yes' or test == 'Yes' or test == '1':
        test = True
    elif test == 'n' or test == 'N' or test == 'no' or test == 'No' or test == '0':
        test = False

    # error catching for bad input
    while test != True and test != False:
        test = input("Please type y or n. " + message + ": ")
        if test == 'y' or test == 'Y' or test == 'yes' or test == 'Yes' or test == '1':
            test = True
        elif test == 'n' or test == 'N' or test == 'no' or test == 'No' or test == '0':
            test = False


    return test


def dateISO(label):
                        ##      dateISO function        ##
    # This function is built for entering and converting dates, testing if the input
    # date was correctly formatted as yyyy-MM-dd. It will try to convert the
    # string into a formatted rfc-3339 timestamp of time 00:00:00 with the local timezone.
    #
    # This function is intended to read in a string that represents a
    # 'yyyy-MM-dd' value, then convert it into a string in the standard format rfc-3339.
    #
    # Function reads in [label] string as parameter. The output is the
    # datetime value of [date] in rfc-3339 format.

    date = input("Enter " + label + " date: ")
    isFormatted = True
    isValidDate = True
    retry = True

    # loop to test if date is valid and in right format
    while retry == True:

        if len(date) != 10 or date[4] != '-' or date[7] != '-':
            isFormatted = False
        else:
            try:
                year,month,day = date.split('-')
                datetime.datetime(int(year),int(month),int(day))
            except:
                isValidDate = False

        if isFormatted == False:
            print("Date did not match required format 'yyyy-mm-dd'.")
            retry = True
        if isValidDate == False:
            print("Invalid date.")
            retry = True

        if isFormatted == True and isValidDate == True:
            retry = False

        if retry == True:
            date = input("Enter " + label + " date: ")
            isFormatted = True
            isValidDate = True
        
    # Up bank API times are in +10:00 timezone
    date = date + "T00:00:00"

    #
    zone = datetime.datetime.utcnow().astimezone().strftime('%z')
    zone = zone[0:3] + ":" + zone[3:5]

    date = date + zone
    
    return date
        
##      Beginning of main program       ##

# set the API token

apiToken = input("Please enter API token: ")

print("\nReport period dates must be in format YYYY-MM-DD.\n")
startDate = dateISO("the start")
endDate = dateISO("the end")

## BUILD URLS ##
# set auth header
headers = {
    "Authorization": "Bearer {0}".format(apiToken)
}

# load list of accounts and decode
homeURL = "https://api.up.com.au/api/v1/accounts"
accs = requests.get(homeURL,headers=headers)
if accs.status_code == 200:
    accDecode = json.loads(accs.content.decode('utf-8'))
else:
    print("Error loading account list.")
    sys.exit()
    
# grab transaction account ID
transID = accDecode['data'][0]['id']

# build URL for transaction data
transURL = homeURL + "/" + transID + "/transactions"

## DONE BUILDING URL ##

## GETTING TRANSACTION LIST ##
parameters = {
    "page[size]": "99",
    "filter[since]": startDate,
    "filter[until]": endDate
}
print("\nLoading page 1 of transactions...")
pageData = requests.get(transURL,headers=headers, params=parameters)
apiData = json.loads(pageData.content.decode('utf-8'))
nPage = apiData['links']['next']

if nPage != None: # check if 2nd page exists
    print("Loading page 2 of transactions...")
    pageData = requests.get(nPage,headers=headers)
    pageData = json.loads(pageData.content.decode('utf-8'))
    
    nPage = pageData['links']['next']
    
    apiData = apiData['data'] + pageData['data']
    i = 2
    
    while nPage != None:
        print("Loading page %d of transactions..." % (i+1))
        pageData = requests.get(nPage,headers=headers)
        pageData = json.loads(pageData.content.decode('utf-8'))

        nPage = pageData['links']['next']
        apiData = apiData + pageData['data']

        i = i+1



                    ## DATA ANALYTICS ##
print("\nInternal transfers between savings accounts can be filtered.\n" +
    "Sometimes you may wish to see the effect of these transactions.\n" +
    "It may be useful to include them when using some functions but\n" +
    "they can skew results of totals and averages, so use them how you see fit.")
filterInternal = validLogical("Would you like to filter out internal transactions?")

# do the filtering
if filterInternal == True:

    for i in range(len(apiData)-1, -1, -1):
        if apiData[i]['attributes']['rawText'] == None and (apiData[i]['attributes']['message'] == None or apiData[i]['attributes']['message'] == ""):
            del apiData[i]
# done filtering

## PREPARE FOR ANALYTICS ##
credit = 0
debit = 0
creditCount = 0
debitCount = 0
rows = len(apiData)

for i in range(0, rows):
    if apiData[i]['attributes']['amount']['valueInBaseUnits'] > 0:
        credit = credit+apiData[i]['attributes']['amount']['valueInBaseUnits']
        creditCount = creditCount + 1

    else:
        debit = debit+apiData[i]['attributes']['amount']['valueInBaseUnits']
        debitCount = debitCount + 1

credit = credit/100
debit = debit/100

## DONE PREPARING ##

# keep command window in 'menu' to navigate and call functions
sessionActive = True

print("\nYour data has been analysed. Enter an option number below...")

## DATA MENU ##
while sessionActive == True:
    # display options menu
    os.system('clear')
    print("----\nOptions:\n1 - Total debits and credits\n2 - Average daily credit and debit\n" +
        "3 - Breakdown of debits by category\n4 - Total round-ups\n5 - Proection of investment\n" +
        "6 - Search transactions by tag\n7 - Export transactions as CSV\n    Or type 'exit'\n----")
    # set option input
    userOpts = input("Please enter an option: ")
    
    # OPTION 1 - Totals
    if userOpts == '1':
        #display totals
        print("\nTotal debits: {0:.2f}\nTotal credits: {1:.2f}\n".format(debit,credit))

        # halt and ask to return to menu
        print("\n")
        contSession = validLogical("Return to the menu?")
        if contSession == False:
            sessionActive = False

    # OPTION 2 - Average daily debits and credits
    if userOpts == '2':
        startDate_obj = parse(startDate)
        endDate_obj = parse(endDate)
        reportDays = endDate_obj - startDate_obj

        avgCredit = round(credit/reportDays.days,2)
        avgDebit = round(debit/reportDays.days,2)

        # print results
        print("\nAverage daily debit: {}\nAverage daily credit: {}\n".format(avgDebit,avgCredit))

        # halt and ask return to menu
        print("\n")
        contSession = validLogical("Return to the menu?")
        if contSession == False:
            sessionActive = False

    # OPTION 3 - Breakdown of debits by category
    if userOpts == '3':
        # init for summing
        sumGoodLife = 0
        sumTransport = 0
        sumPersonal = 0
        sumHome = 0
        countGoodLife = 0
        countTransport = 0
        countPersonal = 0
        countHome = 0
        catErr = 0

        for i in range(0,rows):
            if apiData[i]['relationships']['parentCategory']['data'] != None:
            
                if apiData[i]['relationships']['parentCategory']['data']['id'] == 'good-life':
                    countGoodLife = countGoodLife+1
                    sumGoodLife = sumGoodLife + (apiData[i]['attributes']['amount']['valueInBaseUnits']/100)
                    
                elif apiData[i]['relationships']['parentCategory']['data']['id'] == 'transport':
                    countTransport = countTransport+1
                    sumTransport = sumTransport + (apiData[i]['attributes']['amount']['valueInBaseUnits']/100)
                    
                elif apiData[i]['relationships']['parentCategory']['data']['id'] == 'personal':
                    countPersonal = countPersonal+1
                    sumPersonal = sumPersonal + (apiData[i]['attributes']['amount']['valueInBaseUnits']/100)
                    
                elif apiData[i]['relationships']['parentCategory']['data']['id'] == 'home':
                    countHome = countHome+1
                    sumHome = sumHome + (apiData[i]['attributes']['amount']['valueInBaseUnits']/100)                                                                        
                
            else:
                catErr = catErr+1 # tracks uncategorised transactions

        sumGoodLife = abs(round(sumGoodLife,2))
        sumPersonal = abs(round(sumPersonal,2))
        sumTransport = abs(round(sumTransport,2))
        sumHome = abs(round(sumHome,2))

        print("\nGood-Life: ${} ({} transactions)\nPersonal: ${} ({} transactions)"
            .format(sumGoodLife,countGoodLife,sumPersonal,countPersonal))
        print("Transport: ${} ({} transactions)\nHome: ${} ({} transactions)"
            .format(sumTransport,countTransport,sumHome,countHome))
        print("Uncategorised: {}".format(catErr))

        # halt and ask return to menu
        print("\n")
        contSession = validLogical("Return to the menu?")
        if contSession == False:
            sessionActive = False            

    # OPTION 4 - Total round-ups
    if userOpts == '4':
        sumRound = 0
        for i in range(0,rows):
            if apiData[i]['attributes']['roundUp'] != None:
                sumRound = sumRound + apiData[i]['attributes']['roundUp']['amount']['valueInBaseUnits']
        sumRound = round((abs(sumRound))/100,2) # convert cents to dollars

        print("{} total round-ups".format(sumRound))

        # halt and ask return to menu
        print("\n")
        contSession = validLogical("Return to the menu?")
        if contSession == False:
            sessionActive = False     
    
    # OPTION 5 - return on investment estimate
    if userOpts == '5':
        sumInvest = 0

        for i in range(0,rows):
            if apiData[i]['relationships']['category']['data'] != None:
                if apiData[i]['relationships']['category']['data']['id'] == 'investments':
                    sumInvest = sumInvest + apiData[i]['attributes']['amount']['valueInBaseUnits']
        sumInvest = round((abs(sumInvest))/100,2) # cents to dollars
        projInvest1 = round(sumInvest * 1.09, 2) # 1yr projection
        projInvest2 = round(sumInvest*(1+0.09)**10, 2) # 10yr proection

        print("You have invested ${} in this period and, assuming a conservative 9% annualised return ".format(sumInvest)+
            "compounded annually,\nit will be worth {} after 1yr, or {} after 10 years".format(projInvest1,projInvest2))
        
        # halt and ask return to menu
        print("\n")
        contSession = validLogical("Return to the menu?")
        if contSession == False:
            sessionActive = False     

    # OPTION 6 - Search by tag
    if userOpts == '6':
        print('\n')

        # init for summing
        tagSearch = input('Enter tag to be searched (case-sensitive): ')
        tagCountDebit = 0
        tagCountCredit = 0
        tagCredit = 0
        tagDebit = 0

        print("Searching...")

        for i in range(0,rows):
            if apiData[i]['relationships']['tags']['data'] != []: # test if any tags exist
                for j in range(0,len(apiData[i]['relationships']['tags']['data'])):
                    if apiData[i]['relationships']['tags']['data'][j]['id'] == tagSearch:
                        if apiData[i]['attributes']['amount']['valueInBaseUnits'] > 0:
                            tagCredit = tagCredit+(apiData[i]['attributes']['amount']['valueInBaseUnits']/100)
                            tagCountCredit = tagCountCredit + 1
                        else:
                            tagDebit = tagDebit+(apiData[i]['attributes']['amount']['valueInBaseUnits']/100)
                            tagCountDebit = tagCountDebit + 1

        if tagCountDebit == 0 and tagCountCredit == 0:
            print("\nNo results found")
        else:
            print("\nDebits: ${} ({} transactions)\nCredits: ${} ({} transactions)"
                .format(tagDebit,tagCountDebit,tagCredit,tagCountCredit))

        # halt and ask return to menu
        print("\n")
        contSession = validLogical("Return to the menu?")
        if contSession == False:
            sessionActive = False          

    # OPTION 7 - CSV
    if userOpts == '7':
        print("Exporting CSV...")

        # init for export
        csvArr = [["Time","Description","Amount","Tags"]]
        csvTags = ""
        buildRow = ["","","",""]

        for i in range(0,rows):
            #csvArr.insert((i+1), buildRow)
            
            buildRow[0] = apiData[i]['attributes']['createdAt'] # fills time field

            # fills description field
            if apiData[i]['attributes']['rawText'] == None: 
                buildRow[1] = apiData[i]['attributes']['description']
            else:
                buildRow[1] = apiData[i]['attributes']['rawText']
            
            # fills amount field
            buildRow[2] = apiData[i]['attributes']['amount']['value']

            if len(apiData[i]['relationships']['tags']['data']) > 0: # test if any tags exist
                if len(apiData[i]['relationships']['tags']['data']) > 1: # test if more than 1 tag
                    csvTags = apiData[i]['relationships']['tags']['data'][0]['id'] # set first tag with correct format
                    for j in range(1, len(apiData[i]['relationships']['tags']['data'])):
                        csvTags = csvTags + ", " + apiData[i]['relationships']['tags']['data'][j]['id']
                    
                    buildRow[3] = csvTags
                    csvTags = ""

                else: # fill tag coloumn with the single existing tag
                    buildRow[3] = apiData[i]['relationships']['tags']['data'][0]['id']

            # concatenate row to main CSV 2D array
            csvArr.append(buildRow)
            buildRow = ["","","",""]

        # create CSV file and write to macOS user desktop
        with open("transactions.csv","w+") as trans_csv:
            csvWriter = csv.writer(trans_csv,delimiter=',')
            csvWriter.writerows(csvArr)
        
        print("CSV file exported to current working directory as 'transactions.csv'.")

        # halt and ask return to menu
        print("\n")
        contSession = validLogical("Return to the menu?")
        if contSession == False:
            sessionActive = False

    if userOpts == 'exit' or userOpts == 'Exit' or userOpts == 'e':
        sessionActive = False

print("\nExiting...")