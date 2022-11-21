import requests, ast, re, json, time
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime, timedelta
  
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
webhookUrl = userSettings['discordWebhook']
refreshRate = userSettings['refreshRate']


dates = [beginDate, endDate]

## Total information:
allPricesDict = {}
sentFlights = {}

## Helper functions:
def transformDate(dates):
    beginDate, endDate = list(dates)
    beginDate = datetime.strptime(beginDate, '%Y-%m-%d').date()
    
    if beginDate.today() != beginDate:
        beginDate -= timedelta(days=8)
   
    endDate = datetime.strptime(list(dates)[0], '%Y-%m-%d').date()
    endDate += timedelta(days=52)
    
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


def sendWebhook(flight, origin, destination):

    originDate, daysToAdd = flight[0].split(' - ')[0], flight[0].split(' - ')[1].replace(" days", "")
    price = flight[1]
    beginDate = datetime.strptime(originDate, '%Y-%m-%d').date() 
    endDate = beginDate + timedelta(days=int(daysToAdd))

    webhook = DiscordWebhook(url=webhookUrl, rate_limit_retry=True,)

    embed = DiscordEmbed(title="USE THIS TEXT TO GO TO GOOGLE FLIGHTS", url="https://www.google.com/travel/flights", description="Open Google Flights and search with dates below", color=0x64e6e8)
    embed.set_timestamp()

    embed.add_embed_field(name="Trip:", value=f'{origin} - {destination}')
    embed.add_embed_field(name="Start date", value=str(beginDate), inline=True)
    embed.add_embed_field(name="End date", value=str(endDate), inline=True)
    embed.add_embed_field(name="Price", value=f'€{price},-', inline=False)
    webhook.add_embed(embed)

    response = webhook.execute()
    json_response = json.loads(response.text)


# Request function:
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



while True:
    
    currentDays = 1
    print(f"--------------------------------------- Checking for {currentDays} days -------------------------------------")
    while currentDays <= maxDays:
        make_request(dates, currentDays, origin, destination)
        print(f'Fetching prices for {currentDays} days')
        currentDays += 1

    ## return top 10 cheapest flights with dates from allPricesDict:
    cheapestTenFlights = sorted(allPricesDict.items(), key=lambda x: int(x[1]))[:10]

    
    
    for event in cheapestTenFlights:
        unix_timestamp = int(time.time())
        date, price = event
        event = date, price, unix_timestamp
        if int(event[1]) < alertPrice:
            if date not in sentFlights:
                sendWebhook(event, origin, destination)
                sentFlights[date] = [price, unix_timestamp]
                print(f"*NEW* ALERT: {event[0]}: {event[1]}")
        if date in sentFlights:
            if sentFlights[date][1] - 86400 > int(time.time()):
                sendWebhook(event, origin, destination)
                sentFlights[date] = [price, unix_timestamp]
                print(f"*UPDATE* ALERT: {event[0]}: {event[1]}")

    print(f"Waiting {refreshRate} seconds...")
    time.sleep(refreshRate)
