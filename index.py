from flask import Flask, render_template
import json
import paho.mqtt.client as mqtt
import os



# mongodb need
from flask_pymongo import PyMongo
from flask import jsonify, request, abort
import datetime

app = Flask(__name__)

# port from cloud environment variable or localhost:3000
port = int(os.getenv("PORT", 3000))


@app.route('/', methods=['GET'])
def root():

    if(port == 3000):
        return 'hello world! i am in the local'
    elif(port == int(os.getenv("PORT"))):
        return render_template('index.html')


vcap_services = os.getenv('VCAP_SERVICES')
vcap_services_js = json.loads(vcap_services)
service_name = 'p-rabbitmq'
DB_SERVICE_NAME = 'mongodb-innoworks'

#mqtt
broker = vcap_services_js[service_name][0]['credentials']['protocols']['mqtt']['host']
username = vcap_services_js[service_name][0]['credentials']['protocols']['mqtt']['username'].strip()
password = vcap_services_js[service_name][0]['credentials']['protocols']['mqtt']['password'].strip()
mqtt_port = vcap_services_js[service_name][0]['credentials']['protocols']['mqtt']['port']


# mongodb
uri = vcap_services_js[DB_SERVICE_NAME][0]['credentials']['uri']
app.config['MONGO_URI'] = uri
mongo = PyMongo(app)
collection = mongo.db.temp


#mqtt
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("/hello")
    print('subscribe on /hello')


def on_message(client, userdata, msg):
    print(msg.topic+','+msg.payload.decode())
    ti =  datetime.datetime.now()
    topic = msg.topic
    data = msg.payload.decode()
    temp_id = collection.insert({'date': ti, 'topic': topic, 'data': data})
    new_temp = collection.find_one({'_id': temp_id})
    output = {'date': new_temp['date'],
              'topic': new_temp['topic'], 'data': new_temp['data']}

    print(output)

client = mqtt.Client()

client.username_pw_set(username, password)
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker, mqtt_port, 60)

client.loop_start()



@app.route('/temp', methods=['GET'])
def get_all_temps():

    output = []
    for s in collection.find():

        output.append(
            {'date': s['date'], 'topic': s['topic'], 'data': s['data']})
    return jsonify({'rsult': output})


@app.route('/insert', methods=['POST'])
def insert_data():

    if not request.json:
        abort(400)
    ti = datetime.datetime.now()
    topic = request.json['topic']
    data = request.json['data']
    temp_id = collection.insert({'date': ti, 'topic': topic, 'data': data})
    new_temp = collection.find_one({'_id': temp_id})
    output = {'date': new_temp['date'],
              'topic': new_temp['topic'], 'data': new_temp['data']}

    return jsonify({'retult': output})

if __name__ == '__main__':
    # Run the app, listening on all IPs with our chosen port number
    app.run(host='0.0.0.0', port=port)
