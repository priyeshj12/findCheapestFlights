import requests, datetime, time, re, json
import ast
  
# reading the data from the file
with open('headers.txt') as f:
    headers = f.read()
    headers = ast.literal_eval(headers)
with open('params.txt') as f:
    params = f.read()
    params = ast.literal_eval(params)

## Loading files in:
userSettings = json.load(open('user_settings.json'))

beginDate = userSettings['beginDate']
endDate = userSettings['endDate']
origin = userSettings['origin']
destination = userSettings['destination']
maxDays = userSettings['maxDays']
alertPrice = userSettings['alertPrice']


currentDays = 1
dates = [beginDate, endDate]

## Total information:
allPricesDict = {}

def transformDate(dates):
    beginDate, endDate = list(dates)
    beginDate = datetime.datetime.strptime(beginDate, '%Y-%m-%d').date()
    
    if beginDate.today() != beginDate:
        beginDate -= datetime.timedelta(days=8)
   
    endDate = datetime.datetime.strptime(list(dates)[0], '%Y-%m-%d').date()
    endDate += datetime.timedelta(days=52)
    
    return [beginDate, endDate]


def formatFlightPrices(flightPrices, currentDays):
    pricesDict = {}
    
    flightPrices = re.findall(r'\[\\"\b\d{4}-\d{2}-\d{2}\\",\\"\b\d{4}-\d{2}-\d{2}\\",\[\[null,\d{1,}\]', str(flightPrices))
    flightPrices = [i.replace("\\", '').replace("[", '').replace("]", '').replace("null,", '').replace('"', '').split(",") for i in flightPrices]
    
    for event in flightPrices:
        startDate, foundEndDate, price = event
        if foundEndDate < endDate:
            pricesDict[f'{startDate} - {currentDays} days'] = price
    
    pricesDict = dict(sorted(pricesDict.items(), key=lambda item: int(item[1])))
    allPricesDict.update(pricesDict)
    
    # return top 3 cheapest flights with dates:
    return {k: pricesDict[k] for k in list(pricesDict)[:3]}

def make_request(dates, currentDays, origin, destination):
    beginDate, endDate = list(dates)
    beginGraphDate, endGraphDate = transformDate(list(dates))

    data = f'f.req=%5Bnull%2C%22%5Bnull%2C%5Bnull%2Cnull%2C1%2Cnull%2C%5B%5D%2C1%2C%5B1%2C0%2C0%2C0%5D%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5B%5B%5B%5B%5C%22{origin}%5C%22%2C0%5D%5D%5D%2C%5B%5B%5B%5C%22{destination}%5C%22%2C0%5D%5D%5D%2Cnull%2C0%2C%5B%5D%2C%5B%5D%2C%5C%22{beginDate}%5C%22%2Cnull%2C%5B%5D%2C%5B%5D%2C%5B%5D%2Cnull%2Cnull%2C%5B%5D%2C1%5D%2C%5B%5B%5B%5B%5C%22{destination}%5C%22%2C0%5D%5D%5D%2C%5B%5B%5B%5C%22{origin}%5C%22%2C0%5D%5D%5D%2Cnull%2C0%2C%5B%5D%2C%5B%5D%2C%5C%22{endDate}%5C%22%2Cnull%2C%5B%5D%2C%5B%5D%2C%5B%5D%2Cnull%2Cnull%2C%5B%5D%2C1%5D%5D%2Cnull%2Cnull%2Cnull%2Ctrue%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%5D%2C%5B%5C%22{beginGraphDate}%5C%22%2C%5C%22{endGraphDate}%5C%22%5D%2Cnull%2C%5B{currentDays}%2C{currentDays}%5D%5D%22%5D&at=ALkaumJ1kAt2jqT2JQUFxFmHvId5%3A1667602918151&'
    
    try:
        response = requests.post('https://www.google.com/_/TravelFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetCalendarGraph', params=params, headers=headers, data=data)
        flightPricesUnformatted = response.text   
        formatFlightPrices(flightPricesUnformatted, currentDays)
    except Exception as e: 
        print(e)
        print("Error: Could not get flight prices")


while currentDays <= maxDays:
    make_request(dates, currentDays, origin, destination)
    print(f'Fetching prices for {currentDays} days')
    currentDays += 1

## return top 10 cheapest flights with dates from allPricesDict:
cheapestTenFlights = sorted(allPricesDict.items(), key=lambda x: int(x[1]))[:10]
for event in cheapestTenFlights:
    if int(event[1]) < alertPrice:
        print(f"ALERT: {event[0]}: {event[1]}")

