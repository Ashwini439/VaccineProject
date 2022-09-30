import json
from datetime import datetime
from json import dumps, loads

from flask import Flask, request, jsonify

from flask import Response
import pymongo
import json
from bson import json_util, ObjectId
from bson.json_util import loads

app = Flask(__name__)
client = pymongo.MongoClient(
    "mongodb+srv://ashwinig:Test123456@cluster0.qpps0of.mongodb.net/?retryWrites=true&w=majority")
database = client['VaccineDB']
collections = database['Members']
collection = database['VaccineSlots']


@app.route("/newMemberRegistration", methods=['POST'])
def insertNewMembers():
    if request.is_json:
        data = {
            'Name': request.json['Name'],
            'Age': request.json['Age'],
            'PhoneNumber': request.json['PhoneNumber'],
            'PinCode': request.json['Pincode'],
            'AadharNum': request.json['AadharNumber'],
            'Password': request.json['LoginPassword'],
            'VaccineStatus': "",
            'Comments': "None"

        }
        missingvalue = 'None'
        for k, v in data.items():
            if str(k) != 'VaccineStatus' and str(k) != 'Comments':
                if data[k] is None or data[k] == 'null' or data[k] == "":
                    missingvalue = str(k)
                    break
        if missingvalue != 'None':
            return jsonify(str("Please enter the " + missingvalue))
        elif collections.count_documents({'AadharNum': request.json['AadharNumber']}) != 0:
            # print(.find({'AadharNum': request.json['AadharNumber']}))
            return jsonify(str("Member Already Registered"))
        else:
            collections.insert_one(data)
            return jsonify(str("Member Successfully Registered"))


@app.route("/user/login", methods=['POST'])
def validatelogindetails():
    if request.is_json:
        data = {
            'PhoneNumber': request.json['PhoneNumber'],
            'Password': request.json['LoginPassword']
        }
        missingvalue = 'None'
        for k, v in data.items():
            if data[k] is None or data[k] == 'null' or data[k] == "":
                missingvalue = str(k)
                break
        if missingvalue != 'None':
            return jsonify(str("Please enter the " + missingvalue))
        elif collections.count_documents({'$and': [{'PhoneNumber': request.json['PhoneNumber']},
                                                   {'Password': request.json['LoginPassword']}]}) != 0:
            return jsonify(str("Entered Credentials are Valid"))
        else:
            return jsonify(str("Invalid Credentials"))


@app.route("/user/CheckinDate", methods=['POST'])
def checkSlotsBasedOnDate():
    if request.is_json:
        data = {
            'Date': request.json['Date']
        }
        if str(data['Date'])[3:5] != '06' or str(data['Date'])[6:10] != '2021':
            return jsonify(str("Please Select the Date in June 2021 in DD-MM-YYYY"))
        else:

            records = list(collection.find({'$and': [{'Date': data['Date']}, {'TotalVaccineAvailable': {'$gt': 0}}]}))
            return jsonify(json.loads(json_util.dumps(records)))


@app.route("/user/bookSlot", methods=['PUT'])
def bookVaccineSlot():
    if request.json:
        data = {
            'Date': request.json['Date'],
            'VaccineSlot': request.json['Vaccine Slot'],
            'Dose': request.json['Dose'],
            'Aadhar': request.json['AadharNumber']
        }
        if data['Dose'] == "FirstDose":
            record = collections.find_one({"AadharNum": data['Aadhar']})
            if str(record['VaccineStatus']) == 'First Dose':
                return jsonify(str('First Dose is already registered on ' + record['Comments']))
            records = list(collection.find(
                {'$and': [{'Date': data['Date']}, {'Vaccine Slots': data['VaccineSlot']}]}))
            for i in records:
                if i['FirstDoseVaccine'] != 0:
                    collection.update_one(
                        {'$and': [{'Date': data['Date']}, {'Vaccine Slots': data['VaccineSlot']}]},
                        {'$set': {"FirstDoseVaccine": i['FirstDoseVaccine'] - 1,
                                  "TotalVaccineAvailable": i['TotalVaccineAvailable'] - 1,
                                  "VaccineBooked": i['VaccineBooked'] + 1}})
                    slotbooked_timming = data['Date'] + " " + data['VaccineSlot']
                    collections.update_one({"AadharNum": data['Aadhar']}, {
                        '$set': {"VaccineStatus": "First Dose",
                                 "Comments": slotbooked_timming}})
                    return jsonify(
                        str("Successfully Registered for First Dose on " + request.json['Date'] + " on Vaccine Slot" +
                            request.json['Vaccine Slot']))
                else:
                    return jsonify(str("Please select the Different slot for FirstDose"))

        elif data['Dose'] == "SecondDose":
            record = collections.find_one({"AadharNum": data['Aadhar']})
            if str(record['VaccineStatus']) != 'First Dose':
                return jsonify(str('Please register for the First Dose Vaccine'))
            else:
                records = list(collection.find(
                    {'$and': [{'Date': data['Date']}, {'Vaccine Slots': data['VaccineSlot']}]}))
                for i in records:
                    if i['SecondDoseVaccine'] != 0:
                        collection.update_one(
                            {'$and': [{'Date': data['Date']}, {'Vaccine Slots': data['VaccineSlot']}]},
                            {'$set': {"SecondDoseVaccine": i['SecondDoseVaccine'] - 1,
                                      "TotalVaccineAvailable": i['TotalVaccineAvailable'] - 1,
                                      "VaccineBooked": i['VaccineBooked'] + 1}})
                        slotbooked_timming = data['Date'] + " " + data['VaccineSlot']
                        collections.update_one({"AadharNum": data['Aadhar']}, {
                            '$set': {"VaccineStatus": "Second Dose",
                                     "Comments": slotbooked_timming}})
                        return jsonify(
                            str("Successfully Registered for Second Dose on " + data['Date'] + " on Vaccine Slot" +
                                data['VaccineSlot']))
                    else:
                        return jsonify(str("Please select the different slot for Second Dose"))
        else:
            return jsonify(str("Please enter the valid Dose for registration"))


@app.route("/user/changeBookedSlot", methods=['PUT'])
def updateBookedSlot():
    if request.is_json:
        data = {
            'CurrentDateTime': request.json['SlotUpdatingDateTime'],
            'Date': request.json['NewDateVaccineSlot'],
            'VaccineSlot': request.json['NewVaccine Slot'],
            'Aadhar': request.json['AadharNumber']
        }

        record = collections.find_one({"AadharNum": data['Aadhar']})
        difference = datetime.strptime(record['Comments'], '%d-%m-%Y %I:%M %p') - datetime.strptime(
            data['CurrentDateTime'], '%d-%m-%Y %I:%M %p')
        if difference.total_seconds() > 24 * 3600:
            slotbooked_timeing = data['Date'] + " " + data['VaccineSlot']
            if slotbooked_timeing == record['Comments']:
                return jsonify(str("Please Select the New SLot for Updating "))
            else:
                if str(record['VaccineStatus']) == 'First Dose':
                    records = list(collection.find(
                        {'$and': [{'Date': data['Date']}, {'Vaccine Slots': data['VaccineSlot']}]}))
                    for i in records:
                        if i['FirstDoseVaccine'] != 0:
                            collection.update_one(
                                {'$and': [{'Date': data['Date']}, {'Vaccine Slots': data['VaccineSlot']}]},
                                {'$set': {"FirstDoseVaccine": i['FirstDoseVaccine'] - 1,
                                          "TotalVaccineAvailable": i['TotalVaccineAvailable'] - 1,
                                          "VaccineBooked": i['VaccineBooked'] + 1}})

                            collections.update_one({"AadharNum": data['Aadhar']}, {
                                '$set': {"VaccineStatus": "First Dose",
                                         "Comments": slotbooked_timeing}})

                            return jsonify(
                                str("Successfully Updated your First Dose Vaccine Slot to " + data['Date'] + " on " +
                                    data['VaccineSlot']))
                        else:
                            return jsonify(str("Please select the Different slot"))
                elif str(record['VaccineStatus']) == 'Second Dose':
                    records = list(collection.find(
                        {'$and': [{'Date': data['Date']}, {'Vaccine Slots': data['VaccineSlot']}]}))
                    for i in records:
                        if i['SecondDoseVaccine'] != 0:
                            collection.update_one(
                                {'$and': [{'Date': data['Date']}, {'Vaccine Slots': data['VaccineSlot']}]},
                                {'$set': {"SecondDoseVaccine": i['SecondDoseVaccine'] - 1,
                                          "TotalVaccineAvailable": i['TotalVaccineAvailable'] - 1,
                                          "VaccineBooked": i['VaccineBooked'] + 1}})
                            slotbooked_timeing = data['Date'] + " " + data['VaccineSlot']
                            collections.update_one({"AadharNum": data['Aadhar']}, {
                                '$set': {"VaccineStatus": "Second Dose",
                                         "Comments": slotbooked_timeing}})
                            return jsonify(
                                str("Successfully Registered for Second Dose on " + data['Date'] + " on Vaccine Slot" +
                                    data['VaccineSlot']))
                        else:
                            return jsonify(str("Please select the different slot for Second Dose"))
        else:
            return jsonify(str("Sorry You are not allowed to change the Slot within 24 Hours"))


@app.route("/getRegisteredSlot/<date>", methods=['GET'])
def getRegisteredSlots(date):
        print(date)
        getDate = date              #request.args.get("date")
        if getDate[3:5] != '06' or getDate[6:10] != '2021':
            return jsonify(str("Please Select the Date in June 2021 in DD-MM-YYYY"))
        else:
           # records = collection.aggregate({'$match': {"Date": date }},[{'$group': {sum: {'$sum': 'VaccineBooked'}}}]))

            return jsonify(json.loads(json_util.dumps("Addedvalue")))


if __name__ == '__main__':
    app.run()
