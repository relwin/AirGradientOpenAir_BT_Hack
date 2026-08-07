/**
    my_ble.cpp
    mods for BLE notify with AG data.
    Based on server demo.
    Using nRF Connect app on phone:
      Connect to "AirG-Server"  (Note logging is started, swipe right to show. Filter on "Info", or "APP")
      Select the 3 vertical dots to show client actions.
      Request MTU 70.
      Enable CCCDs.
  Logging now captures notify messages.
  To stop, disconnect.
  Select disc icon to save logging to CSV TXT file. 
  My Android saves to:
  This PC\LG Escape Plus\Internal storage\Download     


 *  NimBLE_Server Demo:
 *
 *  Demonstrates many of the available features of the NimBLE server library.
 *
 *  Created: on March 22 2020
 *      Author: H2zero
 */



#include <Arduino.h>
#include <NimBLEDevice.h>
#include "AgValue.h"

#define PERIODIC_NOTIFY_MS 3000  //send out notify every x ms

static NimBLEServer* pServer;

/**  None of these are required as they will be handled by the library with defaults. **
 **                       Remove as you see fit for your needs                        */
class ServerCallbacks : public NimBLEServerCallbacks {
  void onConnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo) override {
    Serial.printf("myBLE Client address: %s\n", connInfo.getAddress().toString().c_str());

    /**
         *  We can use the connection handle here to ask for different connection parameters.
         *  Args: connection handle, min connection interval, max connection interval
         *  latency, supervision timeout.
         *  Units; Min/Max Intervals: 1.25 millisecond increments.
         *  Latency: number of intervals allowed to skip.
         *  Timeout: 10 millisecond increments.
         */
    pServer->updateConnParams(connInfo.getConnHandle(), 24, 48, 0, 180);
  }

  void onDisconnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo, int reason) override {
    Serial.printf("myBLE Client disconnected - start advertising\n");
    NimBLEDevice::startAdvertising();
  }

  void onMTUChange(uint16_t MTU, NimBLEConnInfo& connInfo) override {
    Serial.printf("myBLE MTU updated: %u for connection ID: %u\n", MTU, connInfo.getConnHandle());
  }


} serverCallbacks;

/** Handler class for characteristic actions */
class CharacteristicCallbacks : public NimBLECharacteristicCallbacks {
  void onRead(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo) override {
    Serial.printf("%s : onRead(), value: %s\n",
                  pCharacteristic->getUUID().toString().c_str(),
                  pCharacteristic->getValue().c_str());
  }

  void onWrite(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo) override {
    Serial.printf("%s : onWrite(), value: %s\n",
                  pCharacteristic->getUUID().toString().c_str(),
                  pCharacteristic->getValue().c_str());
  }

  /**
     *  The value returned in code is the NimBLE host return code.
     */
  void onStatus(NimBLECharacteristic* pCharacteristic, int code) override {
    Serial.printf("myBLE Notification/Indication return code: %d, %s\n", code, NimBLEUtils::returnCodeToString(code));
  }

  /** Peer subscribed to notifications/indications */
  void onSubscribe(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo, uint16_t subValue) override {
    std::string str = "BLE Client ID: ";
    str += connInfo.getConnHandle();
    str += " Address: ";
    str += connInfo.getAddress().toString();
    if (subValue == 0) {
      str += " Unsubscribed to ";
    } else if (subValue == 1) {
      str += " Subscribed to notifications for ";
    } else if (subValue == 2) {
      str += " Subscribed to indications for ";
    } else if (subValue == 3) {
      str += " Subscribed to notifications and indications for ";
    }
    str += std::string(pCharacteristic->getUUID());

    Serial.printf("%s\n", str.c_str());
  }
} chrCallbacks;

/** Handler class for descriptor actions */
class DescriptorCallbacks : public NimBLEDescriptorCallbacks {
  void onWrite(NimBLEDescriptor* pDescriptor, NimBLEConnInfo& connInfo) override {
    std::string dscVal = pDescriptor->getValue();
    Serial.printf("Descriptor written value: %s\n", dscVal.c_str());
  }

  void onRead(NimBLEDescriptor* pDescriptor, NimBLEConnInfo& connInfo) override {
    Serial.printf("%s Descriptor read\n", pDescriptor->getUUID().toString().c_str());
  }
} dscCallbacks;

void ble_setup(void) {

  Serial.printf("Starting my NimBLE Server\n");

  /** Initialize NimBLE and set the device name */
  NimBLEDevice::init("myNimBLE");


  pServer = NimBLEDevice::createServer();
  pServer->setCallbacks(&serverCallbacks);


  NimBLEService* pCAFEService = pServer->createService("CAFE");
  NimBLECharacteristic* pB10BChar = pCAFEService->createCharacteristic("B10B", NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::NOTIFY);

  pB10BChar->setValue("test return");
  pB10BChar->setCallbacks(&chrCallbacks);

  /** Start the services when finished creating all Characteristics and Descriptors */
  pCAFEService->start();

  /** Create an advertising instance and add the services to the advertised data */
  NimBLEAdvertising* pAdvertising = NimBLEDevice::getAdvertising();
  pAdvertising->setName("AirG-Server");
  pAdvertising->addServiceUUID(pCAFEService->getUUID());
  /**
     *  If your device is battery powered you may consider setting scan response
     *  to false as it will extend battery life at the expense of less data sent.
     */
  pAdvertising->enableScanResponse(true);
  pAdvertising->start();

  Serial.printf("myBLE Advertising Started\n");
}


//calcs difference between 2 timestamps -- just uint w/rollover.
uint32_t calc_ts_et(uint32_t ts, uint32_t last_ts) {
  if (ts >= last_ts) {
    return (ts - last_ts);
  } else {
    return (1 + ts - (ULONG_MAX - last_ts));
  }
}


//wait tmo ms for a connect
bool ble_wait_for_connect(long tmo)
{ 
  long et = millis();
  while(1){
    if (calc_ts_et(millis(), et) > tmo) return false;
    if (pServer->getConnectedCount()) return true;
    delay(10);
  }
}


static uint16_t notify_val;  //for debugging
static char buff[128];
static long et, cntr;

extern Measurements measurements;  // need un-static

void ble_loop(void) {
  /** periodically send notifications to connected peers */
  if (calc_ts_et(millis(), et) > PERIODIC_NOTIFY_MS) {  //use et formula here
    et = millis();
    if (pServer->getConnectedCount()) {
      NimBLEService* pSvc = pServer->getServiceByUUID("CAFE");
      if (pSvc) {
        NimBLECharacteristic* pChr = pSvc->getCharacteristic("B10B");
        if (pChr) {
          // Get current measures
          auto mc = measurements.getMeasures();
          float correctedPm = measurements.getCorrectedPM25(true);
          float ctemp = round(measurements.getCorrectedTempHum(Measurements::Temperature));
          float chumid = round(measurements.getCorrectedTempHum(Measurements::Humidity));

          // 11 items
          // CSV format: ctr, CO2, TVOCi, NOxi, PC.03, PC.05, PC1.0, PC2.5,  correctedPM,  temp,  humid
          // size (est):  4  , 6  ,  4  ,  4  ,  5   ,  5   ,  5  ,   5  ,     5    ,       5  ,     5    < 70 chars

          snprintf(buff, sizeof(buff), "%04d,%.2f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.2f,%.2f",
                   notify_val, mc.co2, mc.tvoc, mc.nox,
                   mc.pm_03_pc[0], mc.pm_05_pc[0], mc.pm_01_pc[0], mc.pm_25_pc[0],
                   correctedPm, ctemp, chumid);


          Serial.printf("%s (%d)\n", buff, strlen(buff));
          notify_val++;
          if (notify_val >= 10000) notify_val = 0;  //keep 4 digits
          pChr->setValue(buff);
          pChr->notify();
        }
      }
    }
  }
}
