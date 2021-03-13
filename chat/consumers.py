from channels.consumer import SyncConsumer

class EchoConsumer(SyncConsumer):

    def websocket_connect(self,event):
        print("connect event is called")
    
    def websocket_receive(self,event):
        print("New event is receivec")
        print(event)