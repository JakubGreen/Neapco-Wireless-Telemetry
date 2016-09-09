#include <SPI.h>
#include <avr/dtostrf.h>
#include <Adafruit_WINC1500.h>
#include <Adafruit_WINC1500Udp.h>



const int analogPort = A0;
int data = 0;
String constructString = "";
char outstr[1024];

// Define the WINC1500 board connections below.
// If you're following the Adafruit WINC1500 board
// guide you don't need to modify these:
#define WINC_CS   8
#define WINC_IRQ  7
#define WINC_RST  4
#define WINC_EN   2     // or, tie EN to VCC and comment this out
// The SPI pins of the WINC1500 (SCK, MOSI, MISO) should be
// connected to the hardware SPI port of the Arduino.
// On an Uno or compatible these are SCK = #13, MISO = #12, MOSI = #11.
// On an Arduino Zero use the 6-pin ICSP header, see:
//   https://www.arduino.cc/en/Reference/SPI

// Setup the WINC1500 connection with the pins above and the default hardware SPI.
Adafruit_WINC1500 WiFi(WINC_CS, WINC_IRQ, WINC_RST);

// Or just use hardware SPI (SCK/MOSI/MISO) and defaults, SS -> #10, INT -> #7, RST -> #5, EN -> 3-5V
//Adafruit_WINC1500 WiFi;

int status = WL_IDLE_STATUS;
char ssid[] = "UNL-Baja";  //  your network SSID (name)
char pass[] = "raspberry";       // your network password
int keyIndex = 0;            // your network key Index number (needed only for WEP)
int i=0;
int ready=0;
int size=10;

IPAddress ip(172, 24, 1, 1);
unsigned int localPort = 9050;      // local port to listen on

Adafruit_WINC1500UDP Udp;

void setup() {
  analogReadResolution(12);
  pinMode(analogPort, INPUT);
  
#ifdef WINC_EN
  pinMode(WINC_EN, OUTPUT);
  digitalWrite(WINC_EN, HIGH);
#endif

  //Initialize //Serial and wait for port to open:
  //Serial.begin(9600);
 // while (!Serial) {
 //   ; // wait for serial port to connect. Needed for native USB port only
 // }

  // check for the presence of the shield:
  if (WiFi.status() == WL_NO_SHIELD) {
    Serial.println("WiFi shield not present");
    // don't continue:
    while (true);
  }

  // attempt to connect to Wifi network:
  while ( status != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(ssid);
    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
    status = WiFi.begin(ssid, pass);

    // wait 10 seconds for connection:
    delay(10000);
  }
  Serial.println("Connected to wifi");
 // printWifiStatus();

  Serial.println("\nStarting connection to server...");
  // if you get a connection, report back via serial:
  Udp.begin(localPort);
  SPISettings(28000000, MSBFIRST, SPI_MODE0);
  //Udp.beginPacket(ip, localPort);

   // Set up the generic clock (GCLK4) used to clock timers
  REG_GCLK_GENDIV = GCLK_GENDIV_DIV(3) |          // Divide the 48MHz clock source by divisor 3: 48MHz/3=16MHz
                    GCLK_GENDIV_ID(4);            // Select Generic Clock (GCLK) 4
  while (GCLK->STATUS.bit.SYNCBUSY);              // Wait for synchronization

  REG_GCLK_GENCTRL = GCLK_GENCTRL_IDC |           // Set the duty cycle to 50/50 HIGH/LOW
                     GCLK_GENCTRL_GENEN |         // Enable GCLK4
                     GCLK_GENCTRL_SRC_DFLL48M |   // Set the 48MHz clock source
                     GCLK_GENCTRL_ID(4);          // Select GCLK4
  while (GCLK->STATUS.bit.SYNCBUSY);              // Wait for synchronization

  // Feed GCLK4 to TC4 and TC5
  REG_GCLK_CLKCTRL = GCLK_CLKCTRL_CLKEN |         // Enable GCLK4 to TC4 and TC5
                     GCLK_CLKCTRL_GEN_GCLK4 |     // Select GCLK4
                     GCLK_CLKCTRL_ID_TC4_TC5;     // Feed the GCLK4 to TC4 and TC5
  while (GCLK->STATUS.bit.SYNCBUSY);              // Wait for synchronization
  
  REG_TC4_CTRLA |= TC_CTRLA_MODE_COUNT8;           // Set the counter to 8-bit mode
  while (TC4->COUNT8.STATUS.bit.SYNCBUSY);        // Wait for synchronization 

  REG_TC4_COUNT8_CC0 = 0x55;                      // Set the TC4 CC0 register to some arbitary value
  while (TC4->COUNT8.STATUS.bit.SYNCBUSY);        // Wait for synchronization
  REG_TC4_COUNT8_CC1 = 0xAA;                      // Set the TC4 CC1 register to some arbitary value
  while (TC4->COUNT8.STATUS.bit.SYNCBUSY);        // Wait for synchronization
  REG_TC4_COUNT8_PER = 0xFF;                      // Set the PER (period) register to its maximum value
  while (TC4->COUNT8.STATUS.bit.SYNCBUSY);        // Wait for synchronization

  //NVIC_DisableIRQ(TC4_IRQn);
  //NVIC_ClearPendingIRQ(TC4_IRQn);
  NVIC_SetPriority(TC4_IRQn, 0);    // Set the Nested Vector Interrupt Controller (NVIC) priority for TC4 to 0 (highest) 
  NVIC_EnableIRQ(TC4_IRQn);         // Connect TC4 to Nested Vector Interrupt Controller (NVIC) 

  REG_TC4_INTFLAG |= TC_INTFLAG_MC1 | TC_INTFLAG_MC0 | TC_INTFLAG_OVF;        // Clear the interrupt flags
  REG_TC4_INTENSET = TC_INTENSET_MC1 | TC_INTENSET_MC0 | TC_INTENSET_OVF;     // Enable TC4 interrupts
  // REG_TC4_INTENCLR = TC_INTENCLR_MC1 | TC_INTENCLR_MC0 | TC_INTENCLR_OVF;     // Disable TC4 interrupts
  
  REG_TC4_CTRLA |= TC_CTRLA_PRESCALER_DIV64 |     // Set prescaler to 64, 16MHz/64 = 256kHz
                   TC_CTRLA_ENABLE;               // Enable TC4
  while (TC4->COUNT8.STATUS.bit.SYNCBUSY);        // Wait for synchronization
}

void loop() {
      if(ready == 1){
      Udp.beginPacket(ip, localPort);
      Serial.println(outstr);
      Udp.write(outstr);
      Udp.endPacket();
      ////Serial.print(outstr);
      ready = 0;
      }
}

void TC4_Handler()                              // Interrupt Service Routine (ISR) for timer TC4
{     
  // Check for overflow (OVF) interrupt 
  if (TC4->COUNT8.INTFLAG.bit.OVF && TC4->COUNT8.INTENSET.bit.OVF)             
  {
    // Put your timer overflow (OVF) code here:     
    // ...
    i=i+1;    
    constructString += String(micros()) + "," + String(analogRead(analogPort)) + "\n";
    //constructString += String(micros()) + "\n";
    if ( i == size )
    {
      int str_len = constructString.length();
      constructString.toCharArray(outstr, str_len);
      constructString = "";
      ready = 1;
      i=0;
    }
    REG_TC4_INTFLAG = TC_INTFLAG_OVF;         // Clear the OVF interrupt flag 
  }

  // Check for match counter 0 (MC0) interrupt
  if (TC4->COUNT8.INTFLAG.bit.MC0 && TC4->COUNT8.INTENSET.bit.MC0)             
  {
    // Put your counter compare 0 (CC0) code here:
    // ...
    ////Serial.println(millis());
    REG_TC4_INTFLAG = TC_INTFLAG_MC0;         // Clear the MC0 interrupt flag 
  }

  // Check for match counter 1 (MC1) interrupt
  if (TC4->COUNT8.INTFLAG.bit.MC1 && TC4->COUNT8.INTENSET.bit.MC1)            
  {
    // Put your counter compare 1 (CC1) code here:
    // ...
    
    REG_TC4_INTFLAG = TC_INTFLAG_MC1;        // Clear the MC1 interrupt flag 
  }
}
void printWifiStatus() {
  // print the SSID of the network you're attached to:
  //Serial.print("SSID: ");
  //Serial.println(WiFi.SSID());

  // print your WiFi shield's IP address:
  IPAddress ip = WiFi.localIP();
  //Serial.print("IP Address: ");
  //Serial.println(ip);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  //Serial.print("signal strength (RSSI):");
  //Serial.print(rssi);
  //Serial.println(" dBm");
}
