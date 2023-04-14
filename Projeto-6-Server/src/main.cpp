#include <Arduino.h>

// Constants
const int digitalRxPin = 6; // Digital pin that emulates the Tx pin
const long baudRate = 9600;   // Chose any baud rate you want
const long bitDelay = 1000000L / baudRate; // Calculate the delay between bits

void setup() {
  Serial.begin(9600);
  pinMode(digitalRxPin, INPUT); // Sets the digital pin as an output to emulate the Rx pin
}

char receiveData() {
  // Looping until the start bit is received
  while (digitalRead(digitalRxPin) == HIGH) {
  }

  for (size_t i = 0; i < 3280; i++){
    asm("nop");
  }
  // Data bits
  char data = 0;
  int numberOfOnes = 0;
  for (byte mask = 0x01; mask != 0; mask <<= 1) {
    if (digitalRead(digitalRxPin) == HIGH) {
      data |= mask;
      numberOfOnes++; 
    }
    for (size_t i = 0; i < 2187; i++){
      asm("nop");
    }
  }

  // Parity bit
  if (digitalRead(digitalRxPin) == HIGH && numberOfOnes % 2 == 0) {
    Serial.println("Parity error");
  }
  for (size_t i = 0; i < 2187; i++){
    asm("nop");
  }

  // Stop bit
  if (digitalRead(digitalRxPin) == HIGH) {
    return data;
  }
  return 'e';
}

void loop() {
  char receivedByte = receiveData();
  if (receivedByte != 'e'){
    Serial.println(receivedByte);
  }
}