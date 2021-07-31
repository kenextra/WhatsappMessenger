""" Import Libraries """

from flask import Flask, render_template, request, jsonify
import requests
import os
import json
import math
import string
import pandas as pd
import numpy as np
import scipy as sp
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.compose import TransformedTargetRegressor
from twilio.twiml.messaging_response import MessagingResponse
from ibm_watson_machine_learning import APIClient
from twilio.rest import Client
from PIL import Image, ImageDraw, ImageFont
from news_bot import get_news


""" Initialize Flask Variables """
app = Flask(__name__)

app.config["SERVICES"] = "static/watsonservices/"
app.config["CREDENTIALS"] = "static/watsoncredentials/"
app.config["DATASET"] = "static/datasets/"

account_sid = ""
auth_token = ""
wml_credentials = {}
space_id = ""

receivedMsg = ""
sentMsg = ""


@app.route("/getWmlCredentials")
def getWmlCredentials():
    try:
        global wml_credentials, space_id
        with open(app.config["CREDENTIALS"] + "wmlCredentials.json") as wmlCreds:
            wmlcred = json.loads(wmlCreds.read())

        wml_credentials = {"apikey": wmlcred.get("apikey"), "url": wmlcred.get("url")}

        space_id = wmlcred.get("space_id")

        returnablejson = wml_credentials
        returnablejson.update({"status": "Configured"})

        return jsonify(returnablejson)
    except:
        return jsonify({"status": "Not Configured"})


@app.route("/getWatsonCredentials")
def getWatsonCredentials():
    try:
        x = scanAvailableFiles(app.config["CREDENTIALS"])

        returnableObj = {"services": x}

        return jsonify(returnableObj)
    except:
        return jsonify({"services": ["No Service Configured"]})


@app.route("/getTwilioCredentials")
def getTwilioCredentials():
    try:
        global account_sid
        global auth_token
        with open("twiliocredentials.json") as creds:
            twiliocred = json.loads(creds.read())

        account_sid = twiliocred.get("account_sid")
        auth_token = twiliocred.get("auth_token")
        return jsonify({"status": "Configured"})
    except:
        return jsonify({"status": "Not Configured"})


@app.route("/getDeploymentState")
def getDeploymentState():
    try:
        with open(app.config["SERVICES"] + "wmlDeployment.json") as temp:
            cred = json.loads(temp.read())
        model_id = cred["entity"]["asset"]["id"]
        model_name = cred["entity"]["name"]
        model_status = cred["entity"]["status"]["state"]
        return jsonify(
            {
                "status": model_status,
                "modelId": model_id,
                "modelName": model_name,
            }
        )
    except Exception:
        return jsonify({"status": "Model not Deployed"})


@app.route("/storeTwilioCredentials", methods=["GET", "POST"])
def storeTwilioCredentials():
    receivedPayload = json.loads(request.form["Credentials"])

    data = {
        "account_sid": receivedPayload.get("account_sid"),
        "auth_token": receivedPayload.get("auth_token"),
    }

    with open("twiliocredentials.json", "w") as fs:
        json.dump(data, fs, indent=2)

    return jsonify({"status": "Configured"})


@app.route("/storeWatsonCredentials", methods=["GET", "POST"])
def storeWatsonCredentials():
    receivedPayload = json.loads(request.form["Credentials"])

    if receivedPayload.get("type") == "wml":

        data = receivedPayload
        data.pop("type")

        with open(app.config["CREDENTIALS"] + "wmlCredentials.json", "w") as fs:
            json.dump(data, fs, indent=2)

        return jsonify({"status": "Configured"})

    data = json.loads(receivedPayload.get("apikey"))
    data.update({"cloudfunctionurl": receivedPayload.get("cloudfunctionurl") + ".json"})
    data.update({"windowURL": receivedPayload.get("windowURL")})
    with open(
        app.config["CREDENTIALS"] + receivedPayload.get("type") + "Credentials.json",
        "w",
    ) as fs:
        json.dump(data, fs, indent=2)

    return jsonify({"status": "Configured"})


@app.route("/deployWMLModel")
def deployWMLModel():
    """Step 1: Build the Linear Regression Model"""
    # importing the dataset
    df = pd.read_csv(app.config["DATASET"] + "Data.csv")
    columns_to_use = ["Area", "Item", "Months", "Value", "Year"]
    data = df[columns_to_use]
    data['Item'] = data['Item'].str.replace('Rice, paddy', 'Rice')

    data['Area'] = data.Area.str.lower()
    data['Item'] = data.Item.str.lower()
    data['Months'] = data.Months.str.lower()

    data.query('Value > 0.0', inplace=True)

    X = data.drop(columns=["Value"], axis=1)
    y = data["Value"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.05, random_state=42
    )

    numerical_cols = X_train.select_dtypes(include=['int64', 'float64']).columns
    categorical_cols = X_train.select_dtypes(include=["object", "bool"]).columns

    cat_pipeline = Pipeline([("cat", OneHotEncoder()), ])
    num_pipeline = Pipeline([("num", StandardScaler()), ])

    transformer = ColumnTransformer(
        [
            ("num_pipe", num_pipeline, numerical_cols),
            ("cat_pipe", cat_pipeline, categorical_cols),
        ]
    )

    estimator = DecisionTreeRegressor(max_depth=150, random_state=42)
    tt_model = TransformedTargetRegressor(regressor=estimator,
                                          func=np.log10,
                                          inverse_func=sp.special.exp10
                                          )

    model = Pipeline([("preparation", transformer),
                      ("model", tt_model),
                      ])
    model.fit(X_train, y_train)

    print("Model Built Successfully")

    """ Deploy the Model to Watson Machine Learning """
    getWmlCredentials()

    client = APIClient(wml_credentials)

    client.set.default_space(space_id)

    sofware_spec_uid = client.software_specifications.get_id_by_name("default_py3.7_opence")

    metadata = {
        client.repository.ModelMetaNames.NAME: "Food Data Price Prediction",
        client.repository.ModelMetaNames.TYPE: "scikit-learn_0.23",
        client.repository.ModelMetaNames.SOFTWARE_SPEC_UID: sofware_spec_uid,
    }

    published_model = client.repository.store_model(model, meta_props=metadata)

    published_model_uid = client.repository.get_model_uid(published_model)

    deploy_meta = {
        client.deployments.ConfigurationMetaNames.NAME: "Deployment of Food Data Price Prediction",
        client.deployments.ConfigurationMetaNames.ONLINE: {},
    }
    created_deployment = client.deployments.create(
        published_model_uid, meta_props=deploy_meta
    )

    with open(app.config["SERVICES"] + "wmlDeployment.json", "w") as fp:
        json.dump(created_deployment, fp, indent=2)

    print(json.dumps(created_deployment, indent=2))
    print("Model Successfully Deployed..")
    with open(app.config["SERVICES"] + "wmlDeployment.json") as temp:
        cred = json.loads(temp.read())
    model_id = cred["entity"]["asset"]["id"]
    return jsonify({"status": "Deployed, Model ID: " + model_id})


def predict_price_wml(area, item):
    getWmlCredentials()

    cols = ['Area', 'Item', 'Months', 'Year']

    client = APIClient(wml_credentials)
    client.set.default_space(space_id)

    with open(app.config["SERVICES"] + 'wmlDeployment.json', 'r') as wmlDeployment:
        cred = json.loads(wmlDeployment.read())

    x = [area.lower(), item.lower()]
    today = pd.to_datetime("today")
    x.append(today.month_name().lower())
    x.append(today.year)
    x = np.array([x], dtype=object)
    z = pd.DataFrame(x, columns=cols)

    did = client.deployments.get_uid(cred)

    job_payload = {
        client.deployments.ScoringMetaNames.INPUT_DATA: [{'values': z}]
    }

    scoring_response = client.deployments.score(did, job_payload)
    value = scoring_response['predictions'][0]['values'][0][0]
    return math.ceil(value)


def createImagePrediction(area, item, price, dt_day):
    image = Image.open("static/images/DarkOcean.png")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("static/fonts/Roboto.ttf", size=55)

    (x, y) = (115, 300)
    message = f"Producer Price for {item}"
    color = "rgb(255, 255, 255)"
    draw.text((x, y), message, fill=color, font=font)

    (x, y) = (115, 400)
    message = "in "
    color = "rgb(255, 255, 255)"
    draw.text((x, y), message, fill=color, font=font)

    (x, y) = (165, 400)
    message = f" {area} "
    color = "rgb(255,165,0)"
    draw.text((x, y), message, fill=color, font=font)

    (x, y) = (115, 500)
    message = f"on "
    color = "rgb(255, 255, 255)"
    draw.text((x, y), message, fill=color, font=font)

    (x, y) = (165, 500)
    message = f"  {dt_day} "
    color = "rgb(255,165,0)"
    draw.text((x, y), message, fill=color, font=font)

    (x, y) = (115, 600)
    message = "is "
    color = "rgb(255, 255, 255)"
    draw.text((x, y), message, fill=color, font=font)

    (x, y) = (165, 600)
    name = f"~{price} LCU/tonne"
    color = "rgb(0, 255, 0)"  # white color
    draw.text((x, y), name, fill=color, font=font)

    image.save("static/images/predicted.png", optimize=True, quality=20)


def checkServices(to_, from_, client):
    try:
        files = scanAvailableFiles(app.config["CREDENTIALS"])
        if '.gitkeep' in files:
            _ = files.pop(files.index('.gitkeep'))
        # print(files)
        idx = 0
        inx = 1
        for i in files:
            if i == "wmlCredentials.json":
                x = scanAvailableFiles(app.config["SERVICES"])
                print(x)
                for j in x:
                    if j == "wmlDeployment.json":
                        with open(app.config["SERVICES"] + j) as temp:
                            cred = json.loads(temp.read())
                        files[idx] = "{0}. Watson Machine Learning -> *{1}*".format(
                            inx, cred["entity"]["status"]["state"]
                        )
                        inx += 1
                    else:
                        files[
                            idx
                        ] = "{0}. Watson Machine Learning -> *No Model Deployed*".format(
                            inx
                        )
                        inx += 1
            if i == "waCredentials.json":
                x = scanAvailableFiles(app.config["SERVICES"])
                print(x)
                for j in x:
                    if j == "waDeployment.json":
                        with open(app.config["SERVICES"] + j) as temp:
                            cred = json.loads(temp.read())
                        files[idx] = "{0}. Watson Assistant -> *{1}*".format(
                            inx, cred["entity"]["status"]["state"]
                        )
                        inx += 1
                    else:
                        files[idx] = "{0}. Watson Assistant -> *No Skills*".format(inx)
                        inx += 1
            if i == "wnluCredentials.json":
                x = scanAvailableFiles(app.config["SERVICES"])
                print(x)
                for j in x:
                    if j == "wmlDeployment.json":
                        with open(app.config["SERVICES"] + j) as temp:
                            cred = json.loads(temp.read())
                        files[
                            idx
                        ] = "{0}. Watson Natural Language Understanding -> *{1}*".format(
                            inx, cred["entity"]["status"]["state"]
                        )
                        inx += 1
                    else:
                        files[
                            idx
                        ] = "{0}. Watson Natural Language Understanding -> *No Custom Model Deployed*".format(
                            inx
                        )
                        inx += 1
            if i == "wvrCredentials.json":
                x = scanAvailableFiles(app.config["SERVICES"])
                print(x)
                for j in x:
                    if j == "wvrDeployment.json":
                        with open(app.config["SERVICES"] + j) as temp:
                            cred = json.loads(temp.read())
                        files[idx] = "{0}. Watson Visual Recognition -> *{1}*".format(
                            inx, cred["entity"]["status"]["state"]
                        )
                        inx += 1
                    else:
                        files[
                            idx
                        ] = "{0}. Watson Visual Recognition -> *No Custom Model Deployed*".format(
                            inx
                        )
                        inx += 1
            idx += 1
        files.append(f"{idx+1}. Watson Assistant -> *For Agriculture News*")
        services = "\n".join(files)

        msg = (
            f"I found the following services associated to me: \n\n{services}"
            "\n\nEnter the number to know more."
        )

        message = client.messages.create(from_=from_, body=msg, to=to_)
        global sentMsg
        sentMsg = "I am a bot who is connected to watson services on IBM Cloud! \nTry asking *What are the services you are connected to?*"
        return message.sid
    except Exception as e:
        files = "no service associated, please configure the application on IBM Cloud"
        print(e)
        message = client.messages.create(from_=from_, body=files, to=to_)
        return message.sid


def scanAvailableFiles(path):
    availableFiles = os.listdir(path)
    return availableFiles


@app.route("/getMessages")
def getMessages():
    global receivedMsg
    global sentMsg

    return jsonify({"sentMsg": sentMsg, "receivedMsg": receivedMsg})


""" Default Route """


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        getTwilioCredentials()

        with open(app.config["CREDENTIALS"] + "wmlCredentials.json") as wmlCreds:
            wmlcred = json.loads(wmlCreds.read())

        ResponseMsg = json.dumps(request.form.to_dict(), indent=2)
        respo = json.loads(ResponseMsg)
        # print(respo)
        global receivedMsg
        global sentMsg
        receivedMsg = respo.get("Body")

        trans = str.maketrans('', '', string.punctuation)

        if str(respo.get("Body")).strip().lower().translate(trans) == "what can you do":
            client = Client(account_sid, auth_token)
            to_ = respo.get("From")
            from_ = respo.get("To")
            message = client.messages.create(
                from_=from_,
                body="I am a bot who is connected to watson services on IBM Cloud! \nTry asking *What are the services you are connected to?*",
                media_url=wmlcred.get("windowURL") + "static/images/architecture.png",
                to=to_,
            )
            sentMsg = "I am a bot who is connected to watson services on IBM Cloud! \nTry asking *What are the services you are connected to?*"
            return message.sid

        if str(respo.get("Body")).strip().lower().translate(trans) == "what are the services you are connected to":

            to_ = respo.get("From")
            from_ = respo.get("To")
            client = Client(account_sid, auth_token)
            checkServices(to_, from_, client)

            return str("ok")

        if respo.get("Body") == "1":
            message = "Watson Machine Learning Details"
            resp = MessagingResponse()
            resp.message(message)
            sentMsg = message
            x = scanAvailableFiles(app.config["SERVICES"])
            for j in x:
                if j == "wmlDeployment.json":
                    with open(app.config["SERVICES"] + j) as temp:
                        cred = json.loads(temp.read())
                    model_id = cred["entity"]["asset"]["id"]
                    model_name = cred["entity"]["name"]
                    model_status = cred["entity"]["status"]["state"]

                    if model_status == "ready":
                        message = (
                            f"WML Model id: *{model_id}*"
                            f"\nWML Model Name: *{model_name}*"
                            f"\nWML Model Status: *{model_status}*"
                            "\n\nTry asking *I want to know food prices*"
                        )
                    else:
                        message = (
                            f"Model id: *{model_id}*"
                            f"\nModel Name: *{model_name}*"
                            f"\nModel Status: *{model_status}*"
                        )
                    resp.message(message)
                    sentMsg = message
                    return str(resp)
                else:
                    message = "Service configured, but no model deployed!\nType *Deploy* to deploy a test model"
                    resp.message(message)
                    sentMsg = message
                    return str(resp)

        if respo.get("Body") == "2":
            message = "Watson Assistant"
            resp = MessagingResponse()
            resp.message(message)
            sentMsg = message

            message = "Type *News* for Agriculture News"
            resp.message(message)
            sentMsg = message

            return str(resp)

        if respo.get("Body").strip().lower().translate(trans) == "i want to know food prices":
            message = "Please enter the details with the below format:\n\n*Predict:<Country>,<Item>*\n\nExample: *Predict:Germany,Apples*"
            resp = MessagingResponse()
            resp.message(message)
            sentMsg = message
            return str(resp)

        if respo.get("Body")[:7].strip().lower() == "predict":

            temp = respo.get("Body").split(":")[1].split(",")
            area = temp[0].strip()
            item = temp[1].strip()

            price = predict_price_wml(area, item)
            today = pd.to_datetime("today")
            dt_day = today.date().strftime("%A, %d %B %Y")

            messageTxt = f"Item: *{item}*\n\nwill cost you approx: *{price}* LCU/tonne\n\nin  *{area}*\n\n on *{dt_day}*"
            createImagePrediction(area, item, price, dt_day)
            client = Client(account_sid, auth_token)
            to_ = respo.get("From")
            from_ = respo.get("To")
            message = client.messages.create(
                from_=from_,
                body=messageTxt,
                media_url=wmlcred.get("windowURL") + "static/images/predicted.png",
                to=to_,
            )
            sentMsg = messageTxt
            return message.sid

        if respo.get("Body").strip().lower().translate(trans) == "news":
            message = get_news()
            resp = MessagingResponse()
            resp.message(message)
            sentMsg = message
            return str(resp)

        if "google" in respo.get("Body").strip().lower():
            query = str(respo.get("Body")).lower().replace("google", "")
            query = query.replace(" ", "+")
            message = f"https://www.google.com/search?q={query}"
            resp = MessagingResponse()
            resp.message(message)
            sentMsg = message
            return str(resp)

        if respo.get("MediaUrl0") is not None:
            imageURL = respo.get("MediaUrl0")

            with open(app.config["CREDENTIALS"] + "wvrCredentials.json") as wmlCreds:
                wvrcred = json.loads(wmlCreds.read())

            payload = {
                "apikey": wvrcred.get("apikey"),
                "url": wvrcred.get("url"),
                "imageURL": imageURL,
            }

            r = requests.post(wvrcred.get("cloudfunctionurl"), data=payload)
            response = r.json()

            messageTxt = "Classified as *{0}*\nwith an accuracy of *{1}*".format(
                response.get("class"), response.get("score")
            )

            # createImageVisual(response.get("class"), response.get("score"))
            client = Client(account_sid, auth_token)
            to_ = respo.get("From")
            from_ = respo.get("To")
            message = client.messages.create(
                from_=from_,
                body=messageTxt,
                media_url=wvrcred.get("windowURL") + "static/images/visualclass.png",
                to=to_,
            )
            sentMsg = messageTxt
            return message.sid

        msg = "The message,\n'_{0}_'\nthat you typed on your phone, went through\nWhatsapp -> Twilio -> Python App hosted on IBM Cloud and returned back to you from\nPython App hosted on IBM Cloud -> Twilio -> Whatsapp.\n\n*How Cool is that!!*\n\n Try asking *What can you do?*".format(
            respo.get("Body")
        )
        resp = MessagingResponse()
        resp.message(msg)
        sentMsg = msg
        return str(resp)

    return render_template("index.html")


""" Start the Server """
port = os.getenv("VCAP_APP_PORT", "8080")
if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True, host="0.0.0.0", port=port)
