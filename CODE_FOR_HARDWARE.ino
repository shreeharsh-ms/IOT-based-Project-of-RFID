#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

/* ---------- WIFI CONFIG ---------- */
const char* ssid = "anamik";
const char* password = "12121212";

/* ---------- API CONFIG ---------- */
const char* CHECK_API = "http://10.192.26.193:5000/api/admin/check-expiry";
const char* FINE_API  = "http://10.192.26.193:5000/api/admin/impose-fine";


/* ---------- OLED ---------- */
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define OLED_ADDR 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

/* ---------- RFID ---------- */
#define SS_PIN  D4
#define RST_PIN D3
MFRC522 rfid(SS_PIN, RST_PIN);

/* ---------- FUNCTIONS ---------- */
void showMessage(String l1, String l2 = "", String l3 = "") {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println(l1);
  if (l2 != "") display.println(l2);
  if (l3 != "") display.println(l3);
  display.display();
}

void connectWiFi() {
  showMessage("Connecting WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected");
  showMessage("WiFi Connected", WiFi.localIP().toString());
  delay(1500);
}

/* ---------- SETUP ---------- */
void setup() {
  Serial.begin(9600);

  Wire.begin(D2, D1);

  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println("OLED failed");
    while (true);
  }

  display.setTextSize(1);
  display.setTextColor(WHITE);

  SPI.begin();
  rfid.PCD_Init();

  connectWiFi();

  showMessage("RFID SYSTEM", "Scan Card...");
}

/* ---------- LOOP ---------- */
void loop() {

  if (!rfid.PICC_IsNewCardPresent()) return;
  if (!rfid.PICC_ReadCardSerial()) return;

  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();

  Serial.println("RFID: " + uid);
  showMessage("RFID Read:", uid);

  if (WiFi.status() == WL_CONNECTED) {

    HTTPClient http;
    WiFiClient client;

    http.begin(client, CHECK_API);
    http.addHeader("Content-Type", "application/json");

    String payload = "{\"rfid\":\"" + uid + "\"}";
    int code = http.POST(payload);

    if (code == 200) {
      String res = http.getString();
      Serial.println(res);

      StaticJsonDocument<512> doc;
      deserializeJson(doc, res);

      bool insExpired = doc["insurance_expired"];
      bool pucExpired = doc["puc_expired"];

      if (insExpired || pucExpired) {
        showMessage("EXPIRED!", "Imposing Fine...");
        imposeFine(uid);
      } else {
        showMessage("ALL OK", "No Fine");
      }
    } else {
      showMessage("Vehicle Not Found");
    }

    http.end();
  }

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(3000);
}

/* ---------- IMPOSE FINE ---------- */
void imposeFine(String uid) {

  HTTPClient http;
  WiFiClient client;

  http.begin(client, FINE_API);
  http.addHeader("Content-Type", "application/json");

  String payload = "{\"rfid\":\"" + uid + "\"}";
  int code = http.POST(payload);

  if (code == 200) {
    showMessage("FINE ISSUED", "SMS Sent");
  } else {
    showMessage("Fine Failed");
  }

  http.end();
}
