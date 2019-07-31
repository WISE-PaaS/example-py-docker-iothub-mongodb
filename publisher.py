import paho.mqtt.client as mqtt
import random
#externalHosts
broker="xx.81.xx.10"
#mqtt_port
mqtt_port=1883
#mqtt_username
username="xxxxxxxx-b76f-43e9-8b35-xxxxxxxxf941:xxxxxxxx-c438-4aee-8a0f-bbc791afd307"
password="xxxxxxxxsP8VJZXBb32Z5JNwn"
def on_publish(client,userdata,result):             #create function for callback
    print("data published")
   
client= mqtt.Client()                           #create client object

client.username_pw_set(username,password)

client.on_publish = on_publish                          #assign function to callback
client.connect(broker,mqtt_port)                                 #establish connection
client.publish("/hello",random.randint(10,30))    