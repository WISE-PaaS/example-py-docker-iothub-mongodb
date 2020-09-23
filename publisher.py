import paho.mqtt.client as mqtt
import random

# mqtt credentials in RabbitMQ
# ExternalHosts
broker="rabbitmq-001-pub.sa.wise-paas.com"
# mqtt_port
mqtt_port=1883
# mqtt_username
username="ed6e5a2a-5899-11ea-8729-f6bfce9fbbfd:83096744-d45a-4269-8163-feee669bd5d8"
# mqtt_password
password="YmQowqVI2KOjguEkXDi0"

def on_publish(client,userdata,result):             #create function for callback
    print("data published")

client= mqtt.Client()                           #create client object

client.username_pw_set(username,password)

client.on_publish = on_publish                          #assign function to callback
client.connect(broker,mqtt_port)                                 #establish connection
client.publish("/hello",random.randint(10,30))
