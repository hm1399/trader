import tweepy
auth = tweepy.OAuth1UserHandler(
    consumer_key = "S6Y9hKslNqNlD3iSyOr2TmZTu",
    consumer_secret = "Vej8mxTJxQlNh5K75Yx33nxnXPjdxW39ezahsCJB2jwrQSo308",
    access_token = "1943147050289500161-qzPduVhvhASsRw4r0ysFscfjWxLhFw",
    access_token_secret = "WghvY5QVWsNqFg4tvcDDDHoKusnfFAFPGWKShcLy8lwzL"
    
)

api = tweepy.API(auth)
public_tweets = api.home_timeline()
for tweet in public_tweets:
    print(tweet.text)