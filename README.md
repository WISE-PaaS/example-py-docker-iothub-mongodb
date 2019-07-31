# Example-python-Iothub-MongoDB


This is WIES-PaaS Iothub example-code include the sso and rabbitmq service insert data to MongoDB，and we use the Docker package this file。

[IotHub](https://advantech.wistia.com/medias/up3q2vxvn3)

[SSO](https://advantech.wistia.com/medias/vay5uug5q6)

## Quick Start

#### Environment prepare

#### python3(need include pip3)

[python3](https://www.python.org/downloads/)

#### cf-cli

[cf-cli](https://docs.cloudfoundry.org/cf-cli/install-go-cli.html)

Use to push application to WISE-PaaS，if you want to know more you can see this video


#### docker

[docker](https://www.docker.com/)

Use to packaged our application

MongoDB && Robo 3T

[MongoDB-Server](https://www.mongodb.com/download-center/community)

[Robo-3T](https://robomongo.org/download)

python3 package(those library can run this application in local):

    #mqtt
    pip3 install paho-mqtt
    #python-backend
    pip3 install Flask
    #python-mongodb
    pip3 install flask_pymongo
    

#### Download this file

    git clone this repository

#### Login to WISE-PaaS 
    
![Imgur](https://i.imgur.com/JNJmxFy.png)

    #cf login -skip-ssl-validation -a {api.domain_name}  -u "account" -p "password"
    cf login –skip-ssl-validation -a api.wise-paas.io -u xxxxx@advtech.com.tw -p xxxxxx
    
    #check the cf status
    cf target

## Application Introduce

#### Dockerfile

We first download the python:3.6 and copy this application to  `/app`，and install library define in `requirements.txt` 
```
FROM python:3.6-slim  
WORKDIR /app  
ADD . /app  
RUN pip3 install -r requirements.txt

#Use in local
# EXPOSE 3000
# CMD ["python", "hello.py"]  
```

#### index.py

Simply backend appliaction。
```py
app = Flask(__name__)

# port from cloud environment variable or localhost:3000
port = int(os.getenv("PORT", 3000))


@app.route('/', methods=['GET'])
def root():

    if(port == 3000):
        return 'hello world! i am in the local'
    elif(port == int(os.getenv("PORT"))):
        return render_template('index.html')
```

This is the mqtt and mongodb connect config code，`vcap_services` can get the application environment in WISE-PaaS，you need to attention，and the service_name it need to be same name in WISE-PaaS rabbitmq(iothub) service name。

```py
vcap_services = os.getenv('VCAP_SERVICES')
vcap_services_js = json.loads(vcap_services)
service_name = 'p-rabbitmq'
DB_SERVICE_NAME = 'mongodb-innoworks'

#mqtt
broker = vcap_services_js[service_name][0]['credentials']['protocols']['mqtt']['host']
username = vcap_services_js[service_name][0]['credentials']['protocols']['mqtt']['username'].strip()
password = vcap_services_js[service_name][0]['credentials']['protocols']['mqtt']['password'].strip()
mqtt_port = vcap_services_js[service_name][0]['credentials']['protocols']['mqtt']['port']
```

The `temp` is collection name and you can name by yourself
```py
#mongodb
uri = vcap_services_js[DB_SERVICE_NAME][0]['credentials']['uri']
app.config['MONGO_URI'] = uri
mongo = PyMongo(app)
collection = mongo.db.temp

```

![Imgur](https://i.imgur.com/6777rmg.png)

This code can connect to IohHub，if it connect successful， `on_connect` will print successful result and subscribe topic `/hello`，you can define topic by yourself，and when we receive message `on_message` will save data to the mongodb and get the time immediate。
```py

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
```


#### mainfest config

Open **manifest.yml** and editor the **application name**，because the appication can't duplicate in same domain name。

Check the service instance name same as WISE-PaaS

![Imgur](https://i.imgur.com/4eynKmE.png)

![Imgur](https://i.imgur.com/VVMcYO8.png)

## SSO(Single sign on)

This is the [sso](https://advantech.wistia.com/medias/vay5uug5q6) applicaition，if you don't want it，you can ignore it。

Open **`templates/index.html`** and editor the `ssoUrl` to your application name。
    
    #change this **`python-demo-try`** to your **application name**
    var ssoUrl = myUrl.replace('python-demo-try', 'portal-sso');

## Build Dokcer image

Build image，and image you can name by yourself。

    docker build -t {image} .
    docker build -t example-python-docker .


Tag image to a docker hub  
[Docker Hub](https://hub.docker.com/)

Create a repository

![Imgur](https://i.imgur.com/SxiLcOH.png)

    #docker login to the docker hub
    docker login

    #docker tag {image name} {your account/dockerhub-resp name}
    docker tag example-py-docker WISE-PaaS/example-py-docker

Push it to Docker Hub
    
    #docker push {your account/dockerhub-repo name}
    docker push WISE-PaaS/example-py-docker

Push application and get environment


    #cf push --docker-image{WISE-PaaS/dockerhub-repo name}
    cf push --docker-image WISE-PaaS/example-py-docker
    
    #get the application environment
    cf env python-demo-try > env.json 



#### publisher.py

This file can help us publishW message to topic。 

Edit the **publisher.py** `broker、port、username、password` you can find in env.json

* bokrer:"VCAP_SERVICES => p-rabbitmq => externalHosts"
* port :"VCAP_SERVICES => p-rabbitmq => mqtt => port"
* username :"VCAP_SERVICES => p-rabbitmq => mqtt => username"
* password: "VCAP_SERVICES => p-rabbitmq => mqtt => password"

open two terminal
    
    Listen the console
    
    #cf logs {application name}
    cf logs python-demo-try

    send message to application in WISE-PaaS

    python publisher.py

![Imgur](https://i.imgur.com/9HEJ9OF.png)

## Result in MongoDB 

#### You can watch the row data use Robo 3T，and the config can find in WISE-PaaS Application Environment
(WISE-PaaS/EnSaaS => application List => click application => environment)

![Imgur](https://i.imgur.com/hasorjh.png)

Robo 3T create server(File => connect => Create)

- address => VCAP_SERVICES => mongodb-innoworks => 0 => external_host
- Database => VCAP_SERVICES => mongodb-innoworks => 0 => credentials => database
- Username => VCAP_SERVICES => mongodb-innoworks => 0 => credentials => username
- Password => VCAP_SERVICES => mongodb-innoworks => 0 => credentials => password

![Imgur](https://i.imgur.com/50RNl8y.png)
