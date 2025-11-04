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

const int masterLines = 7;  //The number of rows in your dartboard matrix (higher number)
const int slaveLines = 12;    //The number of columns in your dartboard matrix (lower number)

// int matrixMaster[] = { 26, 27, 14, 12, 13, 23, 22, 21, 19, 18, 5, 17 };  //arduino pins for matrix rows
// int matrixMaster[] = {21, 22, 23, 13, 12, 14, 27, 26, 25, 33, 32,35};
int matrixSlave[] = {21,22, 23, 13, 12, 14, 27, 26, 25, 33, 32, 15};
// int matrixSlave[] = { 39, 36, 35, 34, 33, 32, 25 };                      //arduino pins for matrix columns
int matrixMaster[] = {2 ,4 ,16 ,17 ,5 ,18 ,19};

// point values based on row/column combinations. Comments are for pin reference
int values01[masterLines][slaveLines] = {
  // 21,22, 23, 13, 12, 14 ,27 ,26 ,25 ,33 ,32, 15
  { 14, 32, 16, 22, 28, 38, 18, 24, 10, 40,  2, 36 },    //2
  {  1, 16,  8, 11, 14,  6,  9,  8,  5, 20,  1, 18 },      //4
  { 19, 48, 24, 33, 42, 34, 12, 26, 15, 60,  3,  4 },  //16
  { 21,  3,  0,  0,  0,  4, 27,  0, 12,  0, 13, 54 },   //17
  {  0,  9, 51,  6, 45, 25,  0, 50,  0,  0,  0,  0 },    //5
  {  0,  0,  0,  0,  0,  0,  0,  0, 30, 18, 13,  0 },    //18
  { 57,  0, 17,  2, 15, 30, 36, 20, 10,  6,  0, 12  },       // 19
};

//create arrays specifying special multiplier points - triple, double, bull
//each number in the array is simply to corresponding pin combo concatenated
const int x3Len = 20;
const int x2Len = 21;
int x3[] = { 1622, 1623, 1613, 1612, 1625, 1633, 1632, 1721, 1727, 1715, 522, 523, 513, 512, 1825, 1833, 1832, 1921, 1927, 1915  };
int x2[] = { 221, 222, 223, 213, 212, 214, 227, 226, 225, 233, 232, 215, 414, 426, 1614, 1626, 1714, 1725, 526, 1914, 1926 };

String multi = "";

//timer stuff
unsigned long previousMillis = 0;
const long interval = 1000;

void setup() {
  Serial.begin(115200);
  delay(1000);
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
    // throwCheck();
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
    if (zoneCheck == 526) {
      count = 1;
      multi = "DBLBULL";
    };
    if (zoneCheck == 514) {
      count = 1;
      multi = "BULL";
    };
    if (count == 0) multi = "SINGLE";
  }
  Serial.println(multi);
  return multi;
  
}


void sendData(int point, String msg) {

  if (WiFi.status() == WL_CONNECTED) {
    StaticJsonDocument<200> doc;
    doc["score"] = String(point);
    doc["multiplier"] = String(msg);
    doc["user"] = String(userName);
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