# Example-Python-Docker-Iothub-MongoDB

- [1. Introduction](#1-introduction)
- [2. Before You Start](#2-before-you-start)
- [3. Downloading the Project](#3-downloading-the-project)
- [4. Deploy the app to WISE-PaaS](#4-deploy-the-app-to-wise-paas)
- [5. Application Introduce](#5-application-introduce)
  - [5-1. index.py](#5-1-indexpy)
  - [5-2. publisher.py](#5-2-publisherpy)
- [6. Kubernetes Config](#6-kubernetes-config)
  - [6-1. deployment.yaml](#6-1-deploymentyaml)
  - [6-2. ingress.yaml](#6-2-ingressyaml)
  - [6-3. service.yaml](#6-3-serviceyaml)
- [7. Docker](#7-docker)
  - [7-1. dockerfile](#7-1-dockerfile)
- [8. Deployment Application Steps](#8-deployment-application-steps)
  - [8-1. build Docker image](#8-1-build-docker-image)
  - [8-2. push it to Docker Hub](#8-2-push-it-to-docker-hub)
  - [8-3. create kubernetes object ( All object are in the k8s folder)](#8-3-create-kubernetes-object--all-object-are-in-the-k8s-folder)
  - [8-4. Check（Pod status is running for success）](#8-4-checkpod-status-is-running-for-success)
  - [8-5. Send message to wise-paas by MQTT](#8-5-send-message-to-wise-paas-by-mqtt)
  - [8-6. Check that mongodb has received data](#8-6-check-that-mongodb-has-received-data)

## 1. Introduction

This sample code shows how to deploy an application to the EnSaaS 4.0 environment and connect to the the database (MongoDB) and message broker (RabbitMQ) services provided by the platform.

## 2. Before You Start

1. Create a [Docker](https://www.docker.com/get-started) Account
2. Development Environment
   - Install [Docker](https://docs.docker.com/install/)
   - Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
   - Install [MongoDB-Server](https://www.mongodb.com/download-center/community)
   - Install [Robo-3T](https://robomongo.org/download)

## 3. Downloading the Project

    git clone https://github.com/WISE-PaaS/example-py-docker-iothub-mongodb.git

## 4. Deploy the app to WISE-PaaS

WISE-PaaS has 2 types of data centers

**SA DataCenter**：[https://portal-mp-ensaas.sa.wise-paas.com/](https://portal-mp-ensaas.sa.wise-paas.com/)

- **Cluster**：eks004
  - **Workspace**：adv-training
    - **Namespace**：level2

**HZ DataCenter**：[https://portal-mp-ensaas.hz.wise-paas.com.cn/](https://portal-mp-ensaas.hz.wise-paas.com.cn/)

- **Cluster**：eks006
  - **Workspace**：advtraining
    - **Namespace**：level2

## 5. Application Introduce

### 5-1. index.py

Simply backend appliaction。

```py
app = Flask(__name__)

# port from cloud environment variable or localhost:3000
port = int(os.getenv("PORT", 3000))


@app.route('/', methods=['GET'])
def root():

    if(port == 3000):
        return 'py-docker-iothub-mongodb successful'
    elif(port == int(os.getenv("PORT"))):
        return render_template('index.html')
```

This is the MQTT and MongoDB connect config code，`ENSAAS_SERVICESS` can get the application environment in WISE-PaaS。

```py
ENSAAS_SERVICES = os.getenv('ENSAAS_SERVICES')
ENSAAS_SERVICES_js = json.loads(ENSAAS_SERVICES)
service_name = 'p-rabbitmq'
DB_SERVICE_NAME = 'mongodb'

#mqtt
broker = ENSAAS_SERVICES_js[service_name][0]['credentials']['protocols']['mqtt']['host']
username = ENSAAS_SERVICES_js[service_name][0]['credentials']['protocols']['mqtt']['username'].strip()
password = ENSAAS_SERVICES_js[service_name][0]['credentials']['protocols']['mqtt']['password'].strip()
mqtt_port = ENSAAS_SERVICES_js[service_name][0]['credentials']['protocols']['mqtt']['port']
```

The `temp` is collection name and you can name by yourself

```py
#mongodb
uri = ENSAAS_SERVICES_js[DB_SERVICE_NAME][0]['credentials']['uri']
app.config['MONGO_URI'] = uri
mongo = PyMongo(app)
collection = mongo.db.temp

```

Retrieve the secret, which iothub the secret contains

    # List all secrets in the namespace
    $ kubectl get secret --namespace=level2
    # Output the secret content
    $ kubectl get secret {secret_name} --namespace=level2 -o yaml

![-oyaml](https://tva1.sinaimg.cn/large/007S8ZIlgy1giz6sk4hb3j30ta0c3n5j.jpg)

Copy the decoded content and paste it into the editor, such as Visual Studio Code, and let the plugin prettify it. You can now inspect the structure and start to construct your code.

    # Decoding the secret
    $ kubectl get secret {secret_name} --namespace=level2 -o jsonpath="{.data.ENSAAS_SERVICES}" | base64 --decode; echo

![-ojsonpath](https://tva1.sinaimg.cn/large/007S8ZIlgy1giz88jndhjj30up04gtd9.jpg)

Copy the decoded content to vscode and Save as **json** format
**Notice**：the `DB_SERVICE_NAME` and `IOTHUB_SERVICE_NAME` need to be same name in secret instance name。**PS（ Not the instance name in portal-service ）**

![copyDataVS](https://tva1.sinaimg.cn/large/007S8ZIlgy1giz80nrjndj317k0rk10h.jpg)

![copyDataVS](https://tva1.sinaimg.cn/large/007S8ZIlgy1gizhkhix9tj313h0u0ws0.jpg)

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

### 5-2. publisher.py

This file can help us publish message to topic。

Edit the **publisher.py** `broker、port、username、password` you can find in **ENSAAS_SERVICES**

- bokrer:"ENSAAS_SERVICES => p-rabbitmq => externalHosts"
- port :"ENSAAS_SERVICES => p-rabbitmq => mqtt => port"
- username :"ENSAAS_SERVICES => p-rabbitmq => mqtt => username"
- password: "ENSAAS_SERVICES => p-rabbitmq => mqtt => password"

![publisher](https://tva1.sinaimg.cn/large/007S8ZIlgy1gish55bh5nj318v0u0qg3.jpg)

## 6. Kubernetes Config

### 6-1. deployment.yaml

Each user needs to adjust the variables for certification, as follows：

1. metadata >> name：py-docker-iothub-**{user_name}**
2. student：**{user_name}**
3. image：**{docker_account}** / py-docker-iothub：latest
4. containerPort：listen 3000
5. env >> valueFrom >> secretRef >> name：need same name in Portal-service **secret name**

![deployment](https://tva1.sinaimg.cn/large/007S8ZIlgy1gizi3huzmwj30n00s6dlq.jpg)

**Notice：In Portal-Services secret name**
![createSecret](https://tva1.sinaimg.cn/large/007S8ZIlly1gishp9o8q5j30qo09ignf.jpg)

### 6-2. ingress.yaml

Each user needs to adjust the variables for certification, as follows：

1. metadata >> name：py-docker-iothub-**{user_name}**
2. host：py-docker-iothub-**{user_name}** . **{namespace_name}** . **{cluster_name}**.en.internal
3. serviceName：need to be same name in Service.yaml **{metadata name}**
4. servicePort：same **port** in Service.yaml
   ![ingress](https://tva1.sinaimg.cn/large/007S8ZIlgy1gizi0dm8ubj30n70dbmzt.jpg)

### 6-3. service.yaml

Each user needs to adjust the variables for certification, as follows：

1. metadata >> name：server-**{user_name}**
2. student：**{user_name}**
3. port：same **{port}** in ingress.yaml
4. targetPort：same **{port}** in deployment.yaml **{containerPort}**
   ![service](https://tva1.sinaimg.cn/large/007S8ZIlgy1gizhyahn75j30l10af0uj.jpg)

## 7. Docker

### 7-1. dockerfile

We first download the python:3.6 and copy this application to `/app`，and install library define in `requirements.txt`

```
FROM python:3.6-slim
WORKDIR /app
ADD . /app
RUN pip3 install -r requirements.txt
EXPOSE 3000
CMD ["python", "-u", "index.py"]
```

## 8. Deployment Application Steps

### 8-1. build Docker image

Adjust to your docker account

    $ docker build -t {docker_account / py-docker-iothub-mongodb：latest} .

### 8-2. push it to Docker Hub

    $ docker push {docker_account / py-docker-iothub-mongodb：latest}

### 8-3. create kubernetes object ( All object are in the k8s folder)

    $ kubectl apply -f k8s/

![createSecret](https://tva1.sinaimg.cn/large/007S8ZIlgy1gizi8lr9flj31c205gwi7.jpg)

### 8-4. Check（Pod status is running for success）

    # grep can quickly find key words
    $ kubectl get all --namespace=level2 | grep mongodb-sk-chen

![createSecret](https://tva1.sinaimg.cn/large/007S8ZIlgy1giziaymkq6j31fy06cjwy.jpg)

### 8-5. Send message to wise-paas by MQTT

**Open two terminal first.**

    # 1. View the log of the container
    kubectl logs -f pod/{pod_name} --namespace=level2

![createSecret](https://tva1.sinaimg.cn/large/007S8ZIlgy1gizid2iyb7j31ca0bygtx.jpg)

    # 2. Send message to application in WISE-PaaS
    python publisher.py

![createSecret](https://tva1.sinaimg.cn/large/007S8ZIlgy1gizigtkkk8j31c2030mz0.jpg)

### 8-6. Check that mongodb has received data

You can use Robo 3T to check our your insert data，so you need to go to Portal-service or decode data to get your config

![copyDataVS](https://tva1.sinaimg.cn/large/007S8ZIlgy1gizinslnm2j31is0u0k11.jpg)

Robo 3T create server (File => connect => Create)

- address => ENSAAS_SERVICES => mongodb-innoworks => 0 => external_host
- Database => ENSAAS_SERVICES => mongodb-innoworks => 0 => credentials => database
- Username => ENSAAS_SERVICES => mongodb-innoworks => 0 => credentials => username
- Password => ENSAAS_SERVICES => mongodb-innoworks => 0 => credentials => password

![Imgur](https://tva1.sinaimg.cn/large/007S8ZIlgy1giziuclbpxj30ib0addgq.jpg)

![robo3t](https://tva1.sinaimg.cn/large/007S8ZIlgy1giziup366ij30i70af3zm.jpg)
