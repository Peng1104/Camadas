#include <Arduino.h>

// Constants
const int digitalTxPin = 5; // Digital pin that emulates the Tx pin
const char asciiLetter = 'A'; // Choose any letter from the ASCII table to send
const long baudRate = 9600;   // Chose any baud rate you want
const long bitDelay = 1000000L / baudRate; // Calculate the delay between bits

void setup() {
  pinMode(digitalTxPin, OUTPUT); // Sets the digital pin as an output to emulate the Tx pin
  digitalWrite(digitalTxPin, HIGH); // Sets the starting value of the digital pin to HIGH
}

void sendSerialByte(char data) {
  //Start bit
  digitalWrite(digitalTxPin, LOW);
  delayMicroseconds(bitDelay);

  // Data bits
  int numberOfOnes = 0;
  for (byte mask = 0x01; mask != 0; mask <<= 1) {
    if (data & mask) {
      digitalWrite(digitalTxPin, HIGH);
      numberOfOnes++;
    } else {
      digitalWrite(digitalTxPin, LOW);
    }
    delayMicroseconds(bitDelay);
  }

  // Parity bit
  if (numberOfOnes % 2 == 0) {
    digitalWrite(digitalTxPin, LOW); // Even parity
    delayMicroseconds(bitDelay);
  }
  else {
    digitalWrite(digitalTxPin, HIGH); // Odd parity
    delayMicroseconds(bitDelay);
  }

  // Stop bit
  digitalWrite(digitalTxPin, HIGH);
}

void loop() {
  sendSerialByte(asciiLetter); // Send the ASCIIletter each second
  delay(1000);
}