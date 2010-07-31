from stocktracker.logger import Log

subscriptions = {}

def subscribe(message, subscriber):
    if not message in subscriptions:
        subscriptions[message] = [subscriber]
    else:
        subscriptions[message].append(subscriber)
        
def publish(message, *args, **kwargs):
    if not message in subscriptions:
        Log.info("Message with no Subscribers: " + str(message))
        return
    for subscriber in subscriptions[message]:
        #try:
            subscriber(*args, **kwargs)
        #except Exception, e:
            #logger.error("Subscriber " + str(subscriber) + " could not handle message " + str(message) + ": " + str(args) + str(kwargs) + ". Error: " + str(e))
            
            
def unsubscribe(message, subscriber):
    if not message in subscriptions:
        Log.info("No Message to unsubscribe from: " + str(message))
    elif not subscriber in subscriptions[message]:
        Log.info("Subscriber " + str(subscriber) + " not subscribed for message " + str(message))
    else:
        subscriptions[message].remove(subscriber)
