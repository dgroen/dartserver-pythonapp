// Network Stuff
#include <ArduinoJson.h>
#include <WiFi.h>
#include <ArduinoHttpClient.h>

const char* ssid = "<SSID>";
const char* password = "<SSID_KEY>";
const char* serverAddress = "85.214.85.65";
const char* userName = "Crivit";
const int serverPort = 5001;

WiFiClient wifiClient;
HttpClient http(wifiClient, serverAddress, serverPort);

//vars for ESP32
// const int bigRedBtn = 15;
int bigRedState = 0;
int lastButtonState = HIGH;
unsigned long lastPressTime = 0;
unsigned long debounceDelay = 1000;

const int masterLines = 8;  //The number of rows in your dartboard matrix (higher number)
const int slaveLines = 8;    //The number of columns in your dartboard matrix (lower number)

// int matrixMaster[] = { 26, 27, 14, 12, 13, 23, 22, 21, 19, 18, 5, 17 };  //arduino pins for matrix rows
int matrixSlave[] = {13, 12, 14, 27, 26, 25, 33, 32};
// int matrixSlave[] = { 39, 36, 35, 34, 33, 32, 25 };                      //arduino pins for matrix columns
int matrixMaster[] = {15 ,2 ,4 ,16 ,17 ,5 ,18 ,19};

// point values based on row/column combinations. Comments are for pin reference
int values01[masterLines][slaveLines] = {
  // 13 ,12 ,14 ,27 ,26 ,25 ,33 ,32
  { 12, 50, 36, 15, 5, 10, 24, 0 },     //15
  { 9, 25, 27, 60, 20, 60, 18, 0 },    //2
  { 28, 22, 16, 32, 14, 38, 6, 34 },      //4
  { 14, 11, 8, 16, 7, 19, 3, 17 },  //16
  { 3, 54, 12, 39, 18, 30, 45, 6 },   //17
  { 42, 33, 24, 48, 21, 57, 9, 51 },    //5
  { 1, 18, 4, 13, 6, 10, 15, 2 },    //18
  { 2, 36, 8, 26, 12, 20, 30, 4 },       // 19
};

//create arrays specifying special multiplier points - triple, double, bull
//each number in the array is simply to corresponding pin combo concatenated
const int x3Len = 20;
const int x2Len = 21;
int x3[] = { 1713, 1712, 1714, 1727, 1726, 1725, 1733, 1732, 532, 533, 525, 526, 527, 514, 512, 513, 214, 1514, 1527, 227 };
int x2[] = { 1913, 1912, 1914, 1927, 1926, 1925, 1933, 1932, 432, 433, 425, 426, 427, 414, 412, 413, 233, 1533, 1525, 225, 1512 };

String multi = "";

//timer stuff
unsigned long previousMillis = 0;
const long interval = 1000;

void setup() {
  Serial.begin(115200);
  Serial.println("Starting");
  WiFi.config(INADDR_NONE, INADDR_NONE, INADDR_NONE, INADDR_NONE);
  WiFi.setHostname("esp32-dartboard");  //define hostname
  // Connect to Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.print("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  // Serial.println();
  Serial.println("Connected to Wi-Fi");
  Serial.println(WiFi.localIP());

  // pinMode(bigRedBtn, INPUT_PULLUP);
  // digitalWrite(bigRedBtn, LOW);


  // Initialize matrix pins

  for (int j = 0; j < slaveLines; j++) {
    pinMode(matrixSlave[j], INPUT_PULLUP);
  }
  for (int i = 0; i < masterLines; i++) {
    pinMode(matrixMaster[i], OUTPUT);
    digitalWrite(matrixMaster[i], LOW);
  }

  delay(1000);
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    throwCheck();
    //bigRedCheck();
    // Serial.print('.');
    previousMillis = currentMillis;
  }

  throwCheck();
  // bigRedCheck();
}


//Checks to see if physical button on dartboard has been pressed
void bigRedCheck() {
  // bigRedState = digitalRead(bigRedBtn);
  if (lastButtonState == LOW && bigRedState == LOW) {
    Serial.println("don't do anything, button is held");
  } else if (lastButtonState == HIGH && bigRedState == LOW) {
    Serial.println("this is where everything is done");
    lastButtonState = LOW;
    Serial.println("Big Red");
    sendData(0, "bigRed");
  } else {
    if (lastButtonState != HIGH) {
      Serial.println("set it back to high");
      lastButtonState = HIGH;
    }
  }
}

//button cycler
void throwCheck() {
  // Serial.println("Throwcheck");
  for (int i = 0; i < masterLines; i++) {
    // Serial.print("Throwcheck: Loop masterlines");
    digitalWrite(matrixMaster[i], LOW);
    for (int j = 0; j < slaveLines; j++) {
      // Serial.print("Throwcheck: Loop slavelines");
      if (digitalRead(matrixSlave[j]) == LOW) {
        // Serial.print("Throwcheck: matrixSlave=LOW");
        multiCheck(matrixMaster[i], matrixSlave[j]);
        Serial.print("matrixMaster:");
        Serial.println(matrixMaster[i]);
        Serial.print("matrixSlave:");
        Serial.println(matrixSlave[j]);
        Serial.print("Score:");
        Serial.println(values01[i][j]);
        sendData(values01[i][j], multiCheck(matrixMaster[i], matrixSlave[j]));

        // Use these lines to map the values to the matrix
        // Serial.print(i);
        // Serial.print(",");
        // Serial.println(j);
        delay(500);
        break;
      }
    }
    digitalWrite(matrixMaster[i], HIGH);
  }
}
//checks to see if multiiplier or bulls eye have been hit.
String multiCheck(int M, int S) {
  int count = 0;
  int zoneCheck = M * 100 + S;
  for (int i = 0; i < x2Len; i++) {
    if (x2[i] == zoneCheck) {
      count = 1;
      multi = "DOUBLE";
    } else if (x3[i] == zoneCheck) {
      count = 1;
      multi = "TRIPLE";
    }
    if (zoneCheck == 1512) {
      count = 1;
      multi = "DBLBULL";
    };
    if (zoneCheck == 212) {
      count = 1;
      multi = "BULL";
    };
    if (count == 0) multi = "SINGLE";
  }
  return multi;
  //Serial.println(multi);
}


void sendData(int point, String msg) {

  if (WiFi.status() == WL_CONNECTED) {
    StaticJsonDocument<200> doc;
    doc["score"] = String(point);
    doc["multiplier"] = String(msg);
    doc["user"] = String("dgroen");
    // doc["registrationTime"] = DateTime.now();

    // Serialize JSON to a String
    String jsonString;
    serializeJson(doc, jsonString);
    Serial.println(jsonString);
    // Send HTTP POST request with JSON data
    http.beginRequest();

    http.post("/api/Throw", "application/json", jsonString);
    int httpResponseCode = http.responseStatusCode();
    String response = http.responseBody();    
    Serial.println(response);
    http.endRequest();
  } else if (WiFi.status() == WL_CONNECT_FAILED || WiFi.status() == WL_CONNECTION_LOST || WiFi.status() == WL_DISCONNECTED) {
    Serial.println("lost connection");
  }
}